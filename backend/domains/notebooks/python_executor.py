"""Python cell execution service for notebooks."""
import io
import sys
import json
import base64
import logging
import traceback
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from contextlib import redirect_stdout, redirect_stderr

logger = logging.getLogger(__name__)

# In-memory session store (notebook_id -> namespace dict)
# In production, consider Redis or similar for persistence
_notebook_sessions: Dict[str, Dict[str, Any]] = {}
_session_lock = threading.Lock()


class PythonExecutor:
    """
    Executes Python code in isolated namespaces per notebook.
    Maintains variable state between cell executions.
    """
    
    # Packages available by default
    PRELOADED_IMPORTS = """
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import json
import math
"""
    
    # Dangerous built-ins to remove
    BLOCKED_BUILTINS = [
        'exec', 'eval', 'compile', '__import__', 
        'open', 'input', 'breakpoint'
    ]
    
    def __init__(self, notebook_id: UUID):
        self.notebook_id = str(notebook_id)
        self._ensure_session()
    
    def _ensure_session(self):
        """Initialize or get the session namespace for this notebook."""
        with _session_lock:
            if self.notebook_id not in _notebook_sessions:
                # Create new namespace with safe builtins
                namespace = {
                    '__builtins__': self._get_safe_builtins(),
                    '__name__': '__notebook__',
                    '_outputs': [],  # Store rich outputs
                    '_dataframes': {},  # Named DataFrames
                }
                
                # Pre-run imports
                try:
                    exec(self.PRELOADED_IMPORTS, namespace)
                except Exception as e:
                    logger.warning(f"Failed to preload imports: {e}")
                
                _notebook_sessions[self.notebook_id] = namespace
                logger.info(f"Created new Python session for notebook {self.notebook_id}")
    
    def _get_safe_builtins(self) -> dict:
        """Get a restricted set of builtins."""
        import builtins
        safe = dict(vars(builtins))
        for name in self.BLOCKED_BUILTINS:
            safe.pop(name, None)
        return safe
    
    def _get_namespace(self) -> dict:
        """Get the current namespace for this notebook."""
        with _session_lock:
            return _notebook_sessions.get(self.notebook_id, {})
    
    def execute(
        self,
        code: str,
        timeout_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Execute Python code in the notebook's namespace.
        
        Args:
            code: Python code to execute
            timeout_seconds: Execution timeout
            
        Returns:
            {
                'status': 'success' | 'error',
                'stdout': str,
                'stderr': str,
                'result': any,  # Last expression value
                'outputs': [...],  # Rich outputs (DataFrames, plots)
                'variables': [...],  # Updated variable names
                'error': str | None,
                'traceback': str | None,
                'duration_ms': int
            }
        """
        start_time = datetime.utcnow()
        namespace = self._get_namespace()
        
        # Clear previous outputs
        namespace['_outputs'] = []
        
        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result = {
            'status': 'success',
            'stdout': '',
            'stderr': '',
            'result': None,
            'outputs': [],
            'variables': [],
            'error': None,
            'traceback': None,
            'duration_ms': 0
        }
        
        # Track variables before execution
        vars_before = set(namespace.keys())
        
        try:
            # Inject helper functions
            namespace['display'] = lambda x: self._display(x, namespace)
            namespace['show_df'] = lambda df, name=None: self._show_dataframe(df, name, namespace)
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Try to get the last expression's value
                # Split code into statements and last expression
                exec_result = self._exec_with_result(code, namespace, timeout_seconds)
                result['result'] = exec_result
                
        except TimeoutError:
            result['status'] = 'error'
            result['error'] = f'Execution timed out after {timeout_seconds} seconds'
        except SyntaxError as e:
            result['status'] = 'error'
            result['error'] = f'Syntax error: {e}'
            result['traceback'] = traceback.format_exc()
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['traceback'] = traceback.format_exc()
        
        # Capture outputs
        result['stdout'] = stdout_capture.getvalue()
        result['stderr'] = stderr_capture.getvalue()
        
        # Get rich outputs
        result['outputs'] = namespace.get('_outputs', [])
        
        # Track new/modified variables
        vars_after = set(namespace.keys())
        new_vars = vars_after - vars_before - {'_outputs', 'display', 'show_df'}
        result['variables'] = list(new_vars)
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        result['duration_ms'] = int(duration)
        
        # Serialize result if needed
        result['result'] = self._serialize_value(result['result'])
        
        return result
    
    def _exec_with_result(self, code: str, namespace: dict, timeout: int) -> Any:
        """
        Execute code and return the value of the last expression.
        Similar to Jupyter's behavior.
        """
        import ast
        
        # Parse the code
        tree = ast.parse(code)
        
        if not tree.body:
            return None
        
        # Check if last statement is an expression
        last_stmt = tree.body[-1]
        result = None
        
        if isinstance(last_stmt, ast.Expr):
            # Execute all but last statement
            if len(tree.body) > 1:
                exec_tree = ast.Module(body=tree.body[:-1], type_ignores=[])
                exec(compile(exec_tree, '<cell>', 'exec'), namespace)
            
            # Evaluate last expression
            expr_tree = ast.Expression(body=last_stmt.value)
            result = eval(compile(expr_tree, '<cell>', 'eval'), namespace)
            
            # Auto-display DataFrames
            if self._is_dataframe(result):
                self._show_dataframe(result, None, namespace)
        else:
            # Execute all statements
            exec(compile(tree, '<cell>', 'exec'), namespace)
        
        return result
    
    def _display(self, obj: Any, namespace: dict):
        """Display helper - adds object to outputs."""
        output = self._create_output(obj)
        if output:
            namespace['_outputs'].append(output)
    
    def _show_dataframe(self, df: Any, name: Optional[str], namespace: dict):
        """Display a DataFrame with optional name."""
        if not self._is_dataframe(df):
            return
        
        output = {
            'type': 'dataframe',
            'name': name,
            'columns': list(df.columns),
            'dtypes': {col: str(df[col].dtype) for col in df.columns},
            'shape': list(df.shape),
            'data': df.head(100).to_dict(orient='records'),
            'truncated': len(df) > 100
        }
        
        # Make data JSON-safe
        for row in output['data']:
            for key, val in row.items():
                row[key] = self._serialize_value(val)
        
        namespace['_outputs'].append(output)
        
        # Store named DataFrames
        if name:
            namespace['_dataframes'][name] = df
    
    def _is_dataframe(self, obj: Any) -> bool:
        """Check if object is a pandas DataFrame."""
        return hasattr(obj, 'to_dict') and hasattr(obj, 'columns') and hasattr(obj, 'shape')
    
    def _create_output(self, obj: Any) -> Optional[dict]:
        """Create an output dict for various object types."""
        if obj is None:
            return None
        
        # DataFrame
        if self._is_dataframe(obj):
            return {
                'type': 'dataframe',
                'columns': list(obj.columns),
                'shape': list(obj.shape),
                'data': [self._serialize_row(row) for row in obj.head(100).to_dict(orient='records')],
                'truncated': len(obj) > 100
            }
        
        # Series
        if hasattr(obj, 'to_frame') and hasattr(obj, 'name'):
            df = obj.to_frame()
            return self._create_output(df)
        
        # Matplotlib figure
        if hasattr(obj, 'savefig'):
            return self._figure_to_output(obj)
        
        # Plain text/repr
        return {
            'type': 'text',
            'data': repr(obj)
        }
    
    def _figure_to_output(self, fig) -> dict:
        """Convert matplotlib figure to base64 image."""
        try:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            return {
                'type': 'image',
                'format': 'png',
                'data': img_base64
            }
        except Exception as e:
            logger.error(f"Failed to convert figure: {e}")
            return {'type': 'text', 'data': f'<Figure: {e}>'}
    
    def _serialize_row(self, row: dict) -> dict:
        """Serialize a row dict to JSON-safe values."""
        return {k: self._serialize_value(v) for k, v in row.items()}
    
    def _serialize_value(self, val: Any) -> Any:
        """Convert a value to JSON-safe format."""
        if val is None:
            return None
        if isinstance(val, (bool, int, float, str)):
            return val
        if isinstance(val, (datetime,)):
            return val.isoformat()
        if hasattr(val, 'isoformat'):
            return val.isoformat()
        if isinstance(val, (bytes, bytearray)):
            return val.hex()
        if isinstance(val, (list, tuple)):
            return [self._serialize_value(v) for v in val]
        if isinstance(val, dict):
            return {str(k): self._serialize_value(v) for k, v in val.items()}
        if self._is_dataframe(val):
            return f"<DataFrame {val.shape}>"
        # NumPy types
        if hasattr(val, 'item'):
            try:
                return val.item()
            except:
                pass
        # Check for NaN
        try:
            import math
            if isinstance(val, float) and math.isnan(val):
                return None
        except:
            pass
        return str(val)
    
    def get_variables(self) -> List[Dict[str, Any]]:
        """Get list of user-defined variables in the namespace."""
        namespace = self._get_namespace()
        variables = []
        
        skip_keys = {
            '__builtins__', '__name__', '_outputs', '_dataframes',
            'display', 'show_df', 'pd', 'np', 'datetime', 'date', 
            'timedelta', 'json', 'math'
        }
        
        for name, value in namespace.items():
            if name.startswith('_') or name in skip_keys:
                continue
            
            var_info = {
                'name': name,
                'type': type(value).__name__,
                'preview': self._get_preview(value)
            }
            
            if self._is_dataframe(value):
                var_info['shape'] = list(value.shape)
            
            variables.append(var_info)
        
        return variables
    
    def _get_preview(self, value: Any) -> str:
        """Get a short preview string for a value."""
        if value is None:
            return 'None'
        if isinstance(value, str):
            if len(value) > 50:
                return f'"{value[:50]}..."'
            return f'"{value}"'
        if isinstance(value, (int, float, bool)):
            return str(value)
        if self._is_dataframe(value):
            return f'DataFrame{tuple(value.shape)}'
        if isinstance(value, (list, tuple)):
            return f'{type(value).__name__}[{len(value)}]'
        if isinstance(value, dict):
            return f'dict[{len(value)}]'
        return type(value).__name__
    
    def reset_session(self):
        """Clear the session and start fresh."""
        with _session_lock:
            if self.notebook_id in _notebook_sessions:
                del _notebook_sessions[self.notebook_id]
        self._ensure_session()
        logger.info(f"Reset Python session for notebook {self.notebook_id}")
    
    @staticmethod
    def clear_all_sessions():
        """Clear all notebook sessions (for cleanup)."""
        with _session_lock:
            _notebook_sessions.clear()
        logger.info("Cleared all Python sessions")


def get_executor(notebook_id: UUID) -> PythonExecutor:
    """Get a Python executor for a notebook."""
    return PythonExecutor(notebook_id)
