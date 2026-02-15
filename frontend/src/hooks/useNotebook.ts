/**
 * Custom hook for Notebook state and logic.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Notebook,
  Cell,
  DataConnection,
  CellResult,
  SQLExecuteResult,
  PythonExecuteResult,
  SessionVariable,
  ToastState
} from '../types/notebook'

export interface NotebookState {
  notebook: Notebook | null
  connections: DataConnection[]
  loading: boolean
  error: string | null
  executingCell: string | null
  cellResults: Record<string, CellResult>
  editingName: boolean
  showSaveDataset: string | null
  datasetName: string
  sessionVariables: SessionVariable[]
  toast: ToastState | null
  newCellRef: React.RefObject<HTMLTextAreaElement>
}

export interface NotebookActions {
  loadNotebook: () => Promise<void>
  addCell: (type: 'sql' | 'python' | 'markdown', position?: number) => Promise<void>
  updateCell: (cellId: string, content: string) => Promise<void>
  deleteCell: (cellId: string) => Promise<void>
  executeCell: (cell: Cell) => Promise<void>
  executeAllCells: () => Promise<void>
  resetSession: () => Promise<void>
  saveAsDataset: (cellId: string) => Promise<void>
  updateNotebookName: (name: string) => Promise<void>
  updateDefaultConnection: (connectionId: string) => Promise<void>
  setEditingName: (editing: boolean) => void
  setShowSaveDataset: (cellId: string | null) => void
  setDatasetName: (name: string) => void
  setError: (error: string | null) => void
  setToast: (toast: ToastState | null) => void
  navigateBack: () => void
}

export function useNotebook(notebookId: string | undefined): [NotebookState, NotebookActions] {
  const navigate = useNavigate()

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
  const [sessionVariables, setSessionVariables] = useState<SessionVariable[]>([])
  const [toast, setToast] = useState<ToastState | null>(null)

  // Refs
  const newCellRef = useRef<HTMLTextAreaElement>(null)

  // Data Loading
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

  // Cell Actions
  const addCell = useCallback(async (type: 'sql' | 'python' | 'markdown', position?: number) => {
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
  }, [notebook, loadNotebook])

  const updateCell = useCallback(async (cellId: string, content: string) => {
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
  }, [notebook])

  const deleteCell = useCallback(async (cellId: string) => {
    if (!notebook || !confirm('Delete this cell?')) return

    try {
      await fetch(`/api/v1/notebooks/${notebook.id}/cells/${cellId}`, {
        method: 'DELETE'
      })
      await loadNotebook()
    } catch (err: any) {
      setError(err.message)
    }
  }, [notebook, loadNotebook])

  const executeSQLCell = useCallback(async (cell: Cell) => {
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
        } as SQLExecuteResult
      }))
    }
  }, [notebook])

  const executePythonCell = useCallback(async (cell: Cell) => {
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
        } as PythonExecuteResult
      }))
    }
  }, [notebook, loadSessionVariables])

  const executeCell = useCallback(async (cell: Cell) => {
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
  }, [notebook, executeSQLCell, executePythonCell, loadNotebook])

  const executeAllCells = useCallback(async () => {
    if (!notebook) return
    for (const cell of notebook.cells.filter(c => c.cell_type !== 'markdown')) {
      await executeCell(cell)
    }
  }, [notebook, executeCell])

  const resetSession = useCallback(async () => {
    if (!notebook || !confirm('Reset Python session? This will clear all variables.')) return

    try {
      await fetch(`/api/v1/notebooks/${notebook.id}/session/reset`, { method: 'POST' })
      setSessionVariables([])
      setCellResults({})
    } catch (err: any) {
      setError(err.message)
    }
  }, [notebook])

  const saveAsDataset = useCallback(async (cellId: string) => {
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
  }, [notebook, datasetName])

  const updateNotebookName = useCallback(async (name: string) => {
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
  }, [notebook])

  const updateDefaultConnection = useCallback(async (connectionId: string) => {
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
  }, [notebook])

  const navigateBack = useCallback(() => {
    navigate('/notebooks')
  }, [navigate])

  const state: NotebookState = {
    notebook,
    connections,
    loading,
    error,
    executingCell,
    cellResults,
    editingName,
    showSaveDataset,
    datasetName,
    sessionVariables,
    toast,
    newCellRef
  }

  const actions: NotebookActions = {
    loadNotebook,
    addCell,
    updateCell,
    deleteCell,
    executeCell,
    executeAllCells,
    resetSession,
    saveAsDataset,
    updateNotebookName,
    updateDefaultConnection,
    setEditingName,
    setShowSaveDataset,
    setDatasetName,
    setError,
    setToast,
    navigateBack
  }

  return [state, actions]
}

// Helper functions
export function formatDuration(ms?: number): string {
  if (!ms) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

export function getCellTypeIcon(type: string): string {
  switch (type) {
    case 'sql': return '⚡'
    case 'python': return '🐍'
    case 'markdown': return '📝'
    default: return '📄'
  }
}

export function getCellTypeLabel(type: string): string {
  switch (type) {
    case 'sql': return 'SQL'
    case 'python': return 'Python'
    case 'markdown': return 'Markdown'
    default: return type
  }
}

export function getCellPlaceholder(type: string): string {
  switch (type) {
    case 'sql': return 'SELECT * FROM table_name'
    case 'python': return '# Write Python code here\ndf = pd.DataFrame(...)'
    case 'markdown': return 'Write markdown here...'
    default: return ''
  }
}
