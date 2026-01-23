"""
Column-Level Lineage Tracking

Tracks transformations at the column level, showing how source columns
flow through queries and produce target columns.

Example:
    sales.amount -> SUM(sales.amount) -> summary.total_sales
    customers.name -> UPPER(customers.name) -> report.customer_name
"""
import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from uuid import UUID, uuid4

from .sql_parser import SQLLineageParser, QueryLineage, ColumnReference, TableReference


@dataclass
class ColumnTransformation:
    """Represents a column-level transformation"""
    source_table: Optional[str]
    source_column: str
    target_column: str
    transformation_type: str  # DIRECT, AGGREGATE, FUNCTION, EXPRESSION, CALCULATED
    transformation_sql: Optional[str]  # e.g., "SUM(amount)", "UPPER(name)"
    function_used: Optional[str]  # e.g., "SUM", "AVG", "CONCAT"
    
    @property
    def source_full_name(self) -> str:
        """Get full source column name"""
        if self.source_table:
            return f"{self.source_table}.{self.source_column}"
        return self.source_column
    
    @property
    def lineage_edge_label(self) -> str:
        """Get human-readable edge label"""
        if self.transformation_type == "AGGREGATE":
            return f"{self.function_used}({self.source_column})"
        elif self.transformation_type == "FUNCTION":
            return f"{self.function_used}({self.source_column})"
        elif self.transformation_type == "EXPRESSION":
            return self.transformation_sql or "CALCULATED"
        else:
            return "DIRECT"


@dataclass
class ColumnLineage:
    """Complete column-level lineage for a query"""
    transformations: List[ColumnTransformation]
    unmapped_columns: List[str]  # Target columns we couldn't trace


class ColumnLineageTracker:
    """
    Extracts column-level lineage from SQL queries.
    
    Detects:
    - Direct column mappings (SELECT col -> result.col)
    - Aggregate transformations (SUM(col) -> result.total)
    - Function transformations (UPPER(col) -> result.col_upper)
    - Calculated fields (col1 + col2 -> result.calculated)
    """
    
    def __init__(self):
        self.parser = SQLLineageParser()
        
        # Aggregate functions
        self.aggregate_funcs = {
            'SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'STDDEV', 'VARIANCE',
            'STRING_AGG', 'ARRAY_AGG', 'JSON_AGG', 'GROUP_CONCAT'
        }
        
        # String functions
        self.string_funcs = {
            'UPPER', 'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'SUBSTRING', 'SUBSTR',
            'CONCAT', 'CONCAT_WS', 'LEFT', 'RIGHT', 'LENGTH', 'REPLACE',
            'SPLIT_PART', 'REGEXP_REPLACE'
        }
        
        # Date functions
        self.date_funcs = {
            'DATE', 'DATE_TRUNC', 'DATE_PART', 'EXTRACT', 'TO_TIMESTAMP',
            'TO_DATE', 'NOW', 'CURRENT_DATE', 'CURRENT_TIMESTAMP'
        }
        
        # Math functions
        self.math_funcs = {
            'ROUND', 'FLOOR', 'CEIL', 'ABS', 'POWER', 'SQRT', 'EXP', 'LN', 'LOG'
        }
        
        self.all_funcs = self.aggregate_funcs | self.string_funcs | self.date_funcs | self.math_funcs
    
    def extract_column_lineage(self, sql: str, target_columns: Optional[List[str]] = None) -> ColumnLineage:
        """
        Extract column-level lineage from SQL query.
        
        Args:
            sql: SQL query
            target_columns: Optional list of target column names (for INSERT/CREATE)
            
        Returns:
            ColumnLineage with transformations and unmapped columns
        """
        # Parse SQL for table-level lineage
        query_lineage = self.parser.parse(sql)
        
        # Extract column transformations from SELECT clause
        transformations = self._parse_select_columns(sql, query_lineage)
        
        # Identify unmapped columns
        mapped_targets = {t.target_column for t in transformations}
        unmapped = []
        if target_columns:
            unmapped = [col for col in target_columns if col not in mapped_targets]
        
        return ColumnLineage(
            transformations=transformations,
            unmapped_columns=unmapped
        )
    
    def _parse_select_columns(self, sql: str, query_lineage: QueryLineage) -> List[ColumnTransformation]:
        """Parse SELECT clause to extract column transformations"""
        transformations = []
        
        # Extract SELECT clause
        select_match = re.search(
            r'\bSELECT\s+(.*?)\s+FROM\b',
            sql,
            re.IGNORECASE | re.DOTALL
        )
        
        if not select_match:
            return []
        
        select_clause = select_match.group(1)
        
        # Handle SELECT *
        if select_clause.strip() == '*':
            # All columns from all source tables (direct mapping)
            for table in query_lineage.source_tables:
                transformations.append(ColumnTransformation(
                    source_table=table.table,
                    source_column='*',
                    target_column='*',
                    transformation_type='DIRECT',
                    transformation_sql=None,
                    function_used=None
                ))
            return transformations
        
        # Split by commas (naive - doesn't handle nested functions perfectly)
        column_exprs = self._split_column_expressions(select_clause)
        
        for expr in column_exprs:
            transformation = self._parse_column_expression(expr.strip(), query_lineage)
            if transformation:
                transformations.append(transformation)
        
        return transformations
    
    def _split_column_expressions(self, select_clause: str) -> List[str]:
        """Split SELECT clause by commas, respecting parentheses"""
        expressions = []
        current_expr = []
        paren_depth = 0
        
        for char in select_clause:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                expressions.append(''.join(current_expr))
                current_expr = []
                continue
            
            current_expr.append(char)
        
        if current_expr:
            expressions.append(''.join(current_expr))
        
        return expressions
    
    def _parse_column_expression(self, expr: str, query_lineage: QueryLineage) -> Optional[ColumnTransformation]:
        """Parse a single column expression"""
        # Check for AS alias
        as_match = re.search(r'\s+[Aa][Ss]\s+(["\']?(\w+)["\']?)\s*$', expr)
        if as_match:
            target_column = as_match.group(2)
            source_expr = expr[:as_match.start()].strip()
        else:
            # Try to extract column name from end (e.g., "table.column" -> "column")
            source_expr = expr.strip()
            parts = source_expr.split('.')
            if len(parts) >= 2 and re.match(r'^[a-zA-Z_]\w*$', parts[-1]):
                target_column = parts[-1]
            else:
                # Use the whole expression as target
                target_column = re.sub(r'[^a-zA-Z0-9_]', '_', source_expr[:50])
        
        # Detect transformation type
        
        # Check for aggregate functions
        for agg_func in self.aggregate_funcs:
            pattern = rf'\b{agg_func}\s*\('
            if re.search(pattern, source_expr, re.IGNORECASE):
                # Extract column from inside function
                col_match = re.search(rf'{agg_func}\s*\(\s*(\w+\.)?(\w+|\*)\s*\)', source_expr, re.IGNORECASE)
                if col_match:
                    source_table = col_match.group(1).rstrip('.') if col_match.group(1) else None
                    source_column = col_match.group(2)
                    
                    return ColumnTransformation(
                        source_table=source_table,
                        source_column=source_column,
                        target_column=target_column,
                        transformation_type='AGGREGATE',
                        transformation_sql=source_expr,
                        function_used=agg_func.upper()
                    )
        
        # Check for other functions
        for func in self.all_funcs:
            pattern = rf'\b{func}\s*\('
            if re.search(pattern, source_expr, re.IGNORECASE):
                # Extract column from inside function
                col_match = re.search(rf'{func}\s*\(\s*(\w+\.)?(\w+)\s*[,\)]', source_expr, re.IGNORECASE)
                if col_match:
                    source_table = col_match.group(1).rstrip('.') if col_match.group(1) else None
                    source_column = col_match.group(2)
                    
                    return ColumnTransformation(
                        source_table=source_table,
                        source_column=source_column,
                        target_column=target_column,
                        transformation_type='FUNCTION',
                        transformation_sql=source_expr,
                        function_used=func.upper()
                    )
        
        # Check for arithmetic expressions
        if any(op in source_expr for op in ['+', '-', '*', '/', '%']):
            # Find first column reference
            col_match = re.search(r'(\w+\.)?(\w+)', source_expr)
            if col_match:
                source_table = col_match.group(1).rstrip('.') if col_match.group(1) else None
                source_column = col_match.group(2)
                
                return ColumnTransformation(
                    source_table=source_table,
                    source_column=source_column,
                    target_column=target_column,
                    transformation_type='EXPRESSION',
                    transformation_sql=source_expr,
                    function_used=None
                )
        
        # Direct column reference
        col_match = re.match(r'(\w+\.)?(\w+)$', source_expr)
        if col_match:
            source_table = col_match.group(1).rstrip('.') if col_match.group(1) else None
            source_column = col_match.group(2)
            
            return ColumnTransformation(
                source_table=source_table,
                source_column=source_column,
                target_column=target_column,
                transformation_type='DIRECT',
                transformation_sql=None,
                function_used=None
            )
        
        # Couldn't parse - return generic expression
        return ColumnTransformation(
            source_table=None,
            source_column='<expression>',
            target_column=target_column,
            transformation_type='EXPRESSION',
            transformation_sql=source_expr,
            function_used=None
        )
    
    def generate_column_lineage_graph(self, transformations: List[ColumnTransformation]) -> Dict:
        """
        Generate a graph representation of column lineage.
        
        Returns:
            Dictionary with nodes and edges for visualization
        """
        nodes = []
        edges = []
        node_ids = {}
        
        # Create source nodes
        for trans in transformations:
            source_id = f"source_{trans.source_full_name}"
            if source_id not in node_ids:
                nodes.append({
                    'id': source_id,
                    'label': trans.source_full_name,
                    'type': 'source',
                    'table': trans.source_table,
                    'column': trans.source_column
                })
                node_ids[source_id] = True
        
        # Create target nodes
        for trans in transformations:
            target_id = f"target_{trans.target_column}"
            if target_id not in node_ids:
                nodes.append({
                    'id': target_id,
                    'label': trans.target_column,
                    'type': 'target',
                    'column': trans.target_column
                })
                node_ids[target_id] = True
        
        # Create edges
        for trans in transformations:
            source_id = f"source_{trans.source_full_name}"
            target_id = f"target_{trans.target_column}"
            
            edges.append({
                'source': source_id,
                'target': target_id,
                'label': trans.lineage_edge_label,
                'type': trans.transformation_type,
                'transformation': trans.transformation_sql
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }


# Convenience function
def extract_column_lineage(sql: str, target_columns: Optional[List[str]] = None) -> ColumnLineage:
    """
    Extract column-level lineage from SQL.
    
    Example:
        lineage = extract_column_lineage(
            "SELECT customer_id, SUM(amount) as total FROM sales GROUP BY customer_id"
        )
        for trans in lineage.transformations:
            print(f"{trans.source_column} -> {trans.target_column} ({trans.transformation_type})")
    """
    tracker = ColumnLineageTracker()
    return tracker.extract_column_lineage(sql, target_columns)
