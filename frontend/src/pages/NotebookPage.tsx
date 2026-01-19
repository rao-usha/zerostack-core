import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Toast from '../components/Toast'

// ============================================================================
// TYPES
// ============================================================================
interface Cell {
  id: string
  notebook_id: string
  cell_type: 'sql' | 'python' | 'markdown'
  content: string
  position: number
  last_run_at?: string
  last_run_duration_ms?: number
  last_run_status?: 'success' | 'error' | 'running'
  last_run_error?: string
  last_run_row_count?: number
  cached_results?: any[]
  connection_id?: string
}

interface Notebook {
  id: string
  name: string
  description?: string
  folder: string
  tags: string[]
  default_connection_id?: string
  cells: Cell[]
  created_at: string
  updated_at: string
}

interface DataConnection {
  id: string
  name: string
  connection_type: string
  database: string
  status: string
}

interface SQLExecuteResult {
  cell_id: string
  status: string
  duration_ms: number
  row_count: number
  columns: { name: string; type: string }[]
  rows: Record<string, any>[]
  truncated: boolean
  error?: string
}

interface PythonOutput {
  type: 'text' | 'dataframe' | 'image' | 'error'
  data: any
  name?: string
  columns?: string[]
  shape?: number[]
  truncated?: boolean
  format?: string
}

interface PythonExecuteResult {
  cell_id: string
  status: string
  duration_ms: number
  stdout: string
  stderr: string
  result?: any
  outputs: PythonOutput[]
  variables: string[]
  error?: string
  traceback?: string
}

type CellResult = SQLExecuteResult | PythonExecuteResult

// Type guard
function isPythonResult(result: CellResult): result is PythonExecuteResult {
  return 'stdout' in result || 'outputs' in result
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function NotebookPage() {
  const { notebookId } = useParams<{ notebookId: string }>()
  const navigate = useNavigate()

  // Toast state
  const [toast, setToast] = useState<{
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
  } | null>(null)

  // State
  const [notebook, setNotebook] = useState<Notebook | null>(null)
  const [connections, setConnections] = useState<DataConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [executingCell, setExecutingCell] = useState<string | null>(null)
  const [cellResults, setCellResults] = useState<Record<string, CellResult>>({})
  const [editingName, setEditingName] = useState(false)
  const [showSaveDataset, setShowSaveDataset] = useState<string | null>(null)
  const [datasetName, setDatasetName] = useState('')
  const [sessionVariables, setSessionVariables] = useState<any[]>([])
  
  // Refs for auto-focus
  const newCellRef = useRef<HTMLTextAreaElement>(null)

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  const loadNotebook = useCallback(async () => {
    if (!notebookId) return
    try {
      const res = await fetch(`/api/v1/notebooks/${notebookId}`)
      if (!res.ok) throw new Error('Failed to load notebook')
      const data = await res.json()
      setNotebook(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [notebookId])

  const loadConnections = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/data-connections')
      if (res.ok) {
        const data = await res.json()
        setConnections(data.connections || [])
      }
    } catch (err) {
      console.error('Failed to load connections:', err)
    }
  }, [])

  const loadSessionVariables = useCallback(async () => {
    if (!notebookId) return
    try {
      const res = await fetch(`/api/v1/notebooks/${notebookId}/session/variables`)
      if (res.ok) {
        const data = await res.json()
        setSessionVariables(data.variables || [])
      }
    } catch (err) {
      console.error('Failed to load session variables:', err)
    }
  }, [notebookId])

  useEffect(() => {
    loadNotebook()
    loadConnections()
  }, [loadNotebook, loadConnections])

  // ============================================================================
  // ACTIONS
  // ============================================================================
  const addCell = async (type: 'sql' | 'python' | 'markdown', position?: number) => {
    if (!notebook) return
    
    const defaultContent = {
      sql: '-- Write your SQL here\nSELECT * FROM ',
      python: '# Python cell\nimport pandas as pd\n\n',
      markdown: '# Markdown cell\n'
    }
    
    try {
      const res = await fetch(`/api/v1/notebooks/${notebook.id}/cells`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          cell_type: type, 
          content: defaultContent[type],
          position 
        })
      })
      if (!res.ok) throw new Error('Failed to add cell')
      await loadNotebook()
      setTimeout(() => newCellRef.current?.focus(), 100)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const updateCell = async (cellId: string, content: string) => {
    if (!notebook) return
    
    // Optimistic update
    setNotebook(prev => prev ? {
      ...prev,
      cells: prev.cells.map(c => c.id === cellId ? { ...c, content } : c)
    } : null)
    
    try {
      await fetch(`/api/v1/notebooks/${notebook.id}/cells/${cellId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      })
    } catch (err: any) {
      console.error('Failed to save cell:', err)
    }
  }

  const deleteCell = async (cellId: string) => {
    if (!notebook || !confirm('Delete this cell?')) return
    
    try {
      await fetch(`/api/v1/notebooks/${notebook.id}/cells/${cellId}`, {
        method: 'DELETE'
      })
      await loadNotebook()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const executeCell = async (cell: Cell) => {
    if (!notebook) return
    if (cell.cell_type === 'markdown') return
    
    setExecutingCell(cell.id)
    
    try {
      if (cell.cell_type === 'sql') {
        await executeSQLCell(cell)
      } else if (cell.cell_type === 'python') {
        await executePythonCell(cell)
      }
      await loadNotebook()
    } finally {
      setExecutingCell(null)
    }
  }

  const executeSQLCell = async (cell: Cell) => {
    if (!notebook) return
    
    setCellResults(prev => ({ ...prev, [cell.id]: { status: 'running' } as any }))
    
    try {
      const res = await fetch(`/api/v1/notebooks/${notebook.id}/cells/${cell.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: 1000, timeout_seconds: 60 })
      })
      const result = await res.json()
      setCellResults(prev => ({ ...prev, [cell.id]: result }))
    } catch (err: any) {
      setCellResults(prev => ({ 
        ...prev, 
        [cell.id]: { 
          cell_id: cell.id, 
          status: 'error', 
          error: err.message,
          duration_ms: 0,
          row_count: 0,
          columns: [],
          rows: [],
          truncated: false
        } 
      }))
    }
  }

  const executePythonCell = async (cell: Cell) => {
    if (!notebook) return
    
    setCellResults(prev => ({ ...prev, [cell.id]: { status: 'running' } as any }))
    
    try {
      const res = await fetch(`/api/v1/notebooks/${notebook.id}/cells/${cell.id}/execute-python`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timeout_seconds: 60 })
      })
      const result = await res.json()
      setCellResults(prev => ({ ...prev, [cell.id]: result }))
      
      // Refresh session variables after Python execution
      await loadSessionVariables()
    } catch (err: any) {
      setCellResults(prev => ({ 
        ...prev, 
        [cell.id]: { 
          cell_id: cell.id, 
          status: 'error', 
          error: err.message,
          duration_ms: 0,
          stdout: '',
          stderr: '',
          outputs: [],
          variables: []
        } 
      }))
    }
  }

  const executeAllCells = async () => {
    if (!notebook) return
    for (const cell of notebook.cells.filter(c => c.cell_type !== 'markdown')) {
      await executeCell(cell)
    }
  }

  const resetSession = async () => {
    if (!notebook || !confirm('Reset Python session? This will clear all variables.')) return
    
    try {
      await fetch(`/api/v1/notebooks/${notebook.id}/session/reset`, { method: 'POST' })
      setSessionVariables([])
      setCellResults({})
    } catch (err: any) {
      setError(err.message)
    }
  }

  const saveAsDataset = async (cellId: string) => {
    if (!notebook || !datasetName.trim()) return
    
    try {
      const res = await fetch(`/api/v1/notebooks/${notebook.id}/cells/${cellId}/save-dataset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: datasetName, format: 'parquet' })
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to save dataset')
      }
      setShowSaveDataset(null)
      setDatasetName('')
      setToast({ message: 'Dataset saved successfully!', type: 'success' })
    } catch (err: any) {
      setError(err.message)
    }
  }

  const updateNotebookName = async (name: string) => {
    if (!notebook) return
    try {
      await fetch(`/api/v1/notebooks/${notebook.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
      setNotebook(prev => prev ? { ...prev, name } : null)
      setEditingName(false)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const updateDefaultConnection = async (connectionId: string) => {
    if (!notebook) return
    try {
      await fetch(`/api/v1/notebooks/${notebook.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ default_connection_id: connectionId || null })
      })
      setNotebook(prev => prev ? { ...prev, default_connection_id: connectionId || undefined } : null)
    } catch (err: any) {
      setError(err.message)
    }
  }

  // ============================================================================
  // HELPERS
  // ============================================================================
  const formatDuration = (ms?: number) => {
    if (!ms) return '—'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const getCellTypeIcon = (type: string) => {
    switch (type) {
      case 'sql': return '⚡'
      case 'python': return '🐍'
      case 'markdown': return '📝'
      default: return '📄'
    }
  }

  const getCellTypeLabel = (type: string) => {
    switch (type) {
      case 'sql': return 'SQL'
      case 'python': return 'Python'
      case 'markdown': return 'Markdown'
      default: return type
    }
  }

  const getCellPlaceholder = (type: string) => {
    switch (type) {
      case 'sql': return 'SELECT * FROM table_name'
      case 'python': return '# Write Python code here\ndf = pd.DataFrame(...)'
      case 'markdown': return 'Write markdown here...'
      default: return ''
    }
  }

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================
  const renderSQLResults = (result: SQLExecuteResult, cellIndex: number, cellId: string) => {
    if (result.status === 'error') {
      return <div style={styles.errorResult}>❌ {result.error}</div>
    }
    if (result.status === 'running') {
      return <div style={styles.runningResult}>⏳ Running query...</div>
    }
    
    return (
      <>
        <div style={styles.resultHeader}>
          <span>
            ✓ {result.row_count} rows
            {result.truncated && ' (truncated)'}
            {' • '}{formatDuration(result.duration_ms)}
          </span>
          <button
            onClick={() => { setShowSaveDataset(cellId); setDatasetName(`Dataset from Cell ${cellIndex + 1}`) }}
            style={styles.saveDatasetBtn}
          >
            💾 Save as Dataset
          </button>
        </div>
        <div style={styles.resultTable}>
          <table style={styles.table}>
            <thead>
              <tr>
                {result.columns.map((col, i) => (
                  <th key={i} style={styles.th}>{col.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.rows.slice(0, 50).map((row, i) => (
                <tr key={i} style={styles.tr}>
                  {result.columns.map((col, j) => (
                    <td key={j} style={styles.td}>
                      {row[col.name] === null ? (
                        <em style={{ color: '#6b7280' }}>null</em>
                      ) : typeof row[col.name] === 'object' ? (
                        JSON.stringify(row[col.name]).slice(0, 50)
                      ) : (
                        String(row[col.name]).slice(0, 100)
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {result.rows.length > 50 && (
            <div style={styles.moreRows}>... and {result.rows.length - 50} more rows</div>
          )}
        </div>
      </>
    )
  }

  const renderPythonResults = (result: PythonExecuteResult) => {
    if (result.status === 'error') {
      return (
        <div style={styles.pythonError}>
          <div style={styles.errorResult}>❌ {result.error}</div>
          {result.traceback && (
            <pre style={styles.traceback}>{result.traceback}</pre>
          )}
        </div>
      )
    }
    if (result.status === 'running') {
      return <div style={styles.runningResult}>⏳ Executing Python...</div>
    }
    
    return (
      <div style={styles.pythonOutputs}>
        {/* Duration */}
        <div style={styles.pythonHeader}>
          ✓ Completed in {formatDuration(result.duration_ms)}
          {result.variables.length > 0 && (
            <span style={styles.newVars}>
              New variables: {result.variables.join(', ')}
            </span>
          )}
        </div>

        {/* Stdout */}
        {result.stdout && (
          <pre style={styles.stdout}>{result.stdout}</pre>
        )}

        {/* Stderr */}
        {result.stderr && (
          <pre style={styles.stderr}>{result.stderr}</pre>
        )}

        {/* Rich outputs */}
        {result.outputs.map((output, i) => (
          <div key={i} style={styles.outputItem}>
            {renderOutput(output)}
          </div>
        ))}

        {/* Last expression result */}
        {result.result !== null && result.result !== undefined && (
          <div style={styles.resultValue}>
            <span style={styles.resultLabel}>Out:</span>
            <span>{typeof result.result === 'object' ? JSON.stringify(result.result) : String(result.result)}</span>
          </div>
        )}
      </div>
    )
  }

  const renderOutput = (output: PythonOutput) => {
    switch (output.type) {
      case 'dataframe':
        return (
          <div style={styles.dataframeOutput}>
            {output.name && <div style={styles.dfName}>{output.name}</div>}
            <div style={styles.dfShape}>
              DataFrame: {output.shape?.[0]} rows × {output.shape?.[1]} columns
              {output.truncated && ' (showing first 100)'}
            </div>
            <div style={styles.resultTable}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    {output.columns?.map((col, i) => (
                      <th key={i} style={styles.th}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {output.data?.slice(0, 50).map((row: any, i: number) => (
                    <tr key={i} style={styles.tr}>
                      {output.columns?.map((col, j) => (
                        <td key={j} style={styles.td}>
                          {row[col] === null ? (
                            <em style={{ color: '#6b7280' }}>null</em>
                          ) : (
                            String(row[col]).slice(0, 100)
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      
      case 'image':
        return (
          <div style={styles.imageOutput}>
            <img 
              src={`data:image/${output.format || 'png'};base64,${output.data}`}
              alt="Output"
              style={{ maxWidth: '100%', borderRadius: '4px' }}
            />
          </div>
        )
      
      case 'text':
      default:
        return <pre style={styles.textOutput}>{output.data}</pre>
    }
  }

  // ============================================================================
  // RENDER
  // ============================================================================
  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingState}>
          <div style={styles.spinner} />
          <p>Loading notebook...</p>
        </div>
      </div>
    )
  }

  if (!notebook) {
    return (
      <div style={styles.container}>
        <div style={styles.errorState}>
          <p>Notebook not found</p>
          <button onClick={() => navigate('/notebooks')} style={styles.backButton}>
            ← Back to Notebooks
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <button onClick={() => navigate('/notebooks')} style={styles.backLink}>←</button>
          {editingName ? (
            <input
              type="text"
              defaultValue={notebook.name}
              autoFocus
              onBlur={(e) => updateNotebookName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && updateNotebookName((e.target as HTMLInputElement).value)}
              style={styles.nameInput}
            />
          ) : (
            <h1 style={styles.title} onClick={() => setEditingName(true)}>
              📓 {notebook.name}
            </h1>
          )}
        </div>
        
        <div style={styles.headerActions}>
          <select
            value={notebook.default_connection_id || ''}
            onChange={(e) => updateDefaultConnection(e.target.value)}
            style={styles.connectionSelect}
          >
            <option value="">Select connection...</option>
            {connections.map(c => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.database})
              </option>
            ))}
          </select>
          
          <button onClick={resetSession} style={styles.resetButton} title="Reset Python session">
            🔄 Reset
          </button>
          
          <button onClick={executeAllCells} style={styles.runAllButton}>
            ▶ Run All
          </button>
        </div>
      </header>

      {error && (
        <div style={styles.errorBanner}>
          {error}
          <button onClick={() => setError(null)} style={styles.errorClose}>×</button>
        </div>
      )}

      {/* Cells */}
      <main style={styles.main}>
        {notebook.cells.length === 0 ? (
          <div style={styles.emptyState}>
            <p>No cells yet. Add your first cell to start.</p>
            <div style={styles.addCellButtons}>
              <button onClick={() => addCell('sql')} style={styles.addCellBtn}>
                ⚡ SQL
              </button>
              <button onClick={() => addCell('python')} style={{ ...styles.addCellBtn, backgroundColor: 'rgba(16, 185, 129, 0.2)', borderColor: 'rgba(16, 185, 129, 0.4)', color: '#10b981' }}>
                🐍 Python
              </button>
              <button onClick={() => addCell('markdown')} style={{ ...styles.addCellBtn, backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', color: '#9ca3af' }}>
                📝 Markdown
              </button>
            </div>
          </div>
        ) : (
          <>
            {notebook.cells.map((cell, index) => (
              <div key={cell.id} style={{
                ...styles.cell,
                borderColor: cell.cell_type === 'python' ? 'rgba(16, 185, 129, 0.3)' : 
                             cell.cell_type === 'sql' ? 'rgba(59, 130, 246, 0.3)' : 'rgba(255,255,255,0.1)'
              }}>
                {/* Cell Header */}
                <div style={{
                  ...styles.cellHeader,
                  borderBottomColor: cell.cell_type === 'python' ? 'rgba(16, 185, 129, 0.2)' : 
                                     cell.cell_type === 'sql' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.1)'
                }}>
                  <div style={styles.cellInfo}>
                    <span style={{
                      ...styles.cellType,
                      color: cell.cell_type === 'python' ? '#10b981' : 
                             cell.cell_type === 'sql' ? '#60a5fa' : '#9ca3af'
                    }}>
                      {getCellTypeIcon(cell.cell_type)} {getCellTypeLabel(cell.cell_type)}
                    </span>
                    <span style={styles.cellPosition}>[{index + 1}]</span>
                    {cell.last_run_status && (
                      <span style={{
                        ...styles.cellStatus,
                        color: cell.last_run_status === 'success' ? '#10b981' : 
                               cell.last_run_status === 'error' ? '#ef4444' : '#fbbf24'
                      }}>
                        {cell.last_run_status === 'success' ? '✓' : 
                         cell.last_run_status === 'error' ? '✗' : '⏳'}
                        {' '}{formatDuration(cell.last_run_duration_ms)}
                      </span>
                    )}
                  </div>
                  <div style={styles.cellActions}>
                    {cell.cell_type !== 'markdown' && (
                      <button
                        onClick={() => executeCell(cell)}
                        disabled={executingCell === cell.id || (cell.cell_type === 'sql' && !notebook.default_connection_id)}
                        style={{
                          ...styles.cellActionBtn,
                          backgroundColor: cell.cell_type === 'python' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                          color: cell.cell_type === 'python' ? '#10b981' : '#60a5fa',
                          opacity: (executingCell === cell.id || (cell.cell_type === 'sql' && !notebook.default_connection_id)) ? 0.5 : 1
                        }}
                      >
                        {executingCell === cell.id ? '⏳' : '▶'}
                      </button>
                    )}
                    <button
                      onClick={() => deleteCell(cell.id)}
                      style={{ ...styles.cellActionBtn, color: '#ef4444' }}
                    >
                      🗑
                    </button>
                  </div>
                </div>

                {/* Cell Content */}
                <textarea
                  ref={index === notebook.cells.length - 1 ? newCellRef : undefined}
                  value={cell.content}
                  onChange={(e) => updateCell(cell.id, e.target.value)}
                  onKeyDown={(e) => {
                    if (e.ctrlKey && e.key === 'Enter' && cell.cell_type !== 'markdown') {
                      executeCell(cell)
                    }
                  }}
                  placeholder={getCellPlaceholder(cell.cell_type)}
                  style={{
                    ...styles.cellContent,
                    fontFamily: cell.cell_type !== 'markdown' ? 'monospace' : 'inherit'
                  }}
                  rows={Math.max(3, cell.content.split('\n').length + 1)}
                />

                {/* Cell Results */}
                {cell.cell_type !== 'markdown' && cellResults[cell.id] && (
                  <div style={styles.cellResults}>
                    {cell.cell_type === 'sql' && !isPythonResult(cellResults[cell.id]) && 
                      renderSQLResults(cellResults[cell.id] as SQLExecuteResult, index, cell.id)}
                    {cell.cell_type === 'python' && isPythonResult(cellResults[cell.id]) && 
                      renderPythonResults(cellResults[cell.id] as PythonExecuteResult)}
                  </div>
                )}
              </div>
            ))}

            {/* Add Cell Buttons */}
            <div style={styles.addCellRow}>
              <button onClick={() => addCell('sql')} style={styles.addCellBtn}>
                ⚡ SQL
              </button>
              <button onClick={() => addCell('python')} style={{ ...styles.addCellBtn, backgroundColor: 'rgba(16, 185, 129, 0.2)', borderColor: 'rgba(16, 185, 129, 0.4)', color: '#10b981' }}>
                🐍 Python
              </button>
              <button onClick={() => addCell('markdown')} style={{ ...styles.addCellBtn, backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', color: '#9ca3af' }}>
                📝 Markdown
              </button>
            </div>
          </>
        )}
      </main>

      {/* Variables Sidebar (only show if there are Python variables) */}
      {sessionVariables.length > 0 && (
        <div style={styles.variablesSidebar}>
          <h4 style={styles.sidebarTitle}>Variables</h4>
          {sessionVariables.map((v, i) => (
            <div key={i} style={styles.variableItem}>
              <span style={styles.varName}>{v.name}</span>
              <span style={styles.varType}>{v.type}</span>
              <span style={styles.varPreview}>{v.preview}</span>
            </div>
          ))}
        </div>
      )}

      {/* Save Dataset Modal */}
      {showSaveDataset && (
        <div style={styles.modalOverlay} onClick={() => setShowSaveDataset(null)}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <h3 style={{ margin: '0 0 16px 0', color: '#f0f0f5' }}>💾 Save as Dataset</h3>
            <input
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="Dataset name"
              style={styles.modalInput}
              autoFocus
            />
            <div style={styles.modalActions}>
              <button onClick={() => setShowSaveDataset(null)} style={styles.modalCancel}>Cancel</button>
              <button onClick={() => saveAsDataset(showSaveDataset)} style={styles.modalSubmit}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts */}
      <div style={styles.shortcuts}>
        <span>Ctrl+Enter to run cell</span>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}

// ============================================================================
// STYLES
// ============================================================================
const styles: Record<string, React.CSSProperties> = {
  container: { minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  
  // Header
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 32px', borderBottom: '1px solid rgba(255,255,255,0.1)', position: 'sticky', top: 0, backgroundColor: '#0a0a0f', zIndex: 100 },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '12px' },
  headerActions: { display: 'flex', alignItems: 'center', gap: '12px' },
  backLink: { padding: '6px 12px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', fontSize: '16px', cursor: 'pointer' },
  title: { fontSize: '18px', fontWeight: '600', margin: 0, cursor: 'pointer' },
  nameInput: { fontSize: '18px', fontWeight: '600', backgroundColor: '#1a1a24', border: '1px solid rgba(59, 130, 246, 0.5)', borderRadius: '4px', padding: '4px 8px', color: '#f0f0f5' },
  connectionSelect: { padding: '8px 12px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '13px', minWidth: '200px' },
  resetButton: { padding: '8px 12px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer' },
  runAllButton: { padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: '600', fontSize: '13px', cursor: 'pointer' },
  
  // Main
  main: { padding: '24px 32px', maxWidth: '1000px', margin: '0 auto' },
  
  // Cells
  cell: { marginBottom: '16px', backgroundColor: '#12121a', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', overflow: 'hidden' },
  cellHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', backgroundColor: '#0f0f14', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  cellInfo: { display: 'flex', alignItems: 'center', gap: '10px' },
  cellType: { fontSize: '11px', fontWeight: '600' },
  cellPosition: { fontSize: '11px', color: '#6b7280' },
  cellStatus: { fontSize: '11px' },
  cellActions: { display: 'flex', gap: '6px' },
  cellActionBtn: { width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.05)', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' },
  cellContent: { width: '100%', padding: '12px', backgroundColor: 'transparent', border: 'none', color: '#f0f0f5', fontSize: '13px', lineHeight: '1.5', resize: 'vertical', outline: 'none' },
  
  // Results
  cellResults: { borderTop: '1px solid rgba(255,255,255,0.1)', backgroundColor: '#0f0f14' },
  resultHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', fontSize: '12px', color: '#10b981', borderBottom: '1px solid rgba(255,255,255,0.05)' },
  resultTable: { maxHeight: '400px', overflow: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: '12px' },
  th: { textAlign: 'left', padding: '8px 10px', backgroundColor: '#0a0a0f', color: '#9ca3af', fontWeight: '500', position: 'sticky', top: 0 },
  tr: { borderBottom: '1px solid rgba(255,255,255,0.05)' },
  td: { padding: '6px 10px', color: '#d1d5db', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  moreRows: { padding: '8px 12px', textAlign: 'center', color: '#6b7280', fontSize: '11px' },
  errorResult: { padding: '12px', color: '#ef4444', fontSize: '13px' },
  runningResult: { padding: '12px', color: '#fbbf24', fontSize: '13px' },
  saveDatasetBtn: { padding: '4px 10px', backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', borderRadius: '4px', color: '#60a5fa', fontSize: '11px', cursor: 'pointer' },
  
  // Python outputs
  pythonOutputs: { padding: '8px 0' },
  pythonHeader: { padding: '8px 12px', fontSize: '12px', color: '#10b981', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  newVars: { color: '#9ca3af', fontSize: '11px' },
  stdout: { margin: '0 12px 8px', padding: '8px', backgroundColor: '#0a0a0f', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace', color: '#d1d5db', whiteSpace: 'pre-wrap', maxHeight: '200px', overflow: 'auto' },
  stderr: { margin: '0 12px 8px', padding: '8px', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace', color: '#fca5a5', whiteSpace: 'pre-wrap' },
  pythonError: {},
  traceback: { margin: '8px 12px', padding: '8px', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace', color: '#fca5a5', whiteSpace: 'pre-wrap', maxHeight: '300px', overflow: 'auto' },
  outputItem: { margin: '8px 12px' },
  dataframeOutput: {},
  dfName: { fontSize: '12px', fontWeight: '600', color: '#10b981', marginBottom: '4px' },
  dfShape: { fontSize: '11px', color: '#9ca3af', marginBottom: '8px' },
  imageOutput: { padding: '8px', backgroundColor: '#1a1a24', borderRadius: '4px' },
  textOutput: { padding: '8px', backgroundColor: '#0a0a0f', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace', color: '#d1d5db', whiteSpace: 'pre-wrap' },
  resultValue: { padding: '8px 12px', display: 'flex', gap: '8px', alignItems: 'baseline' },
  resultLabel: { color: '#ef4444', fontSize: '11px', fontWeight: '600' },
  
  // Variables sidebar
  variablesSidebar: { position: 'fixed', right: '16px', top: '80px', width: '200px', backgroundColor: '#12121a', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', padding: '12px', maxHeight: '400px', overflow: 'auto' },
  sidebarTitle: { fontSize: '12px', fontWeight: '600', color: '#9ca3af', margin: '0 0 8px 0', textTransform: 'uppercase' },
  variableItem: { padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', gap: '2px' },
  varName: { fontSize: '12px', color: '#60a5fa', fontWeight: '500' },
  varType: { fontSize: '10px', color: '#6b7280' },
  varPreview: { fontSize: '11px', color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  
  // Add Cell
  addCellRow: { display: 'flex', gap: '8px', justifyContent: 'center', padding: '16px' },
  addCellButtons: { display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '16px' },
  addCellBtn: { padding: '8px 16px', backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', borderRadius: '6px', color: '#60a5fa', fontSize: '13px', cursor: 'pointer' },
  
  // Empty/Loading/Error States
  emptyState: { textAlign: 'center', padding: '60px 32px', backgroundColor: '#12121a', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.2)' },
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' },
  spinner: { width: '32px', height: '32px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' },
  errorState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#ef4444' },
  backButton: { marginTop: '16px', padding: '10px 20px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  errorBanner: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 32px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontSize: '13px' },
  errorClose: { background: 'none', border: 'none', color: '#ef4444', fontSize: '18px', cursor: 'pointer' },
  
  // Modal
  modalOverlay: { position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', width: '90%', maxWidth: '400px', border: '1px solid rgba(255,255,255,0.1)' },
  modalInput: { width: '100%', padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '14px', marginBottom: '16px' },
  modalActions: { display: 'flex', justifyContent: 'flex-end', gap: '10px' },
  modalCancel: { padding: '8px 16px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', cursor: 'pointer' },
  modalSubmit: { padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: '600', cursor: 'pointer' },
  
  // Shortcuts
  shortcuts: { position: 'fixed', bottom: '16px', right: '16px', padding: '8px 12px', backgroundColor: 'rgba(0,0,0,0.8)', borderRadius: '6px', fontSize: '11px', color: '#6b7280' }
}
