/**
 * Types for Notebook feature.
 */

export interface Cell {
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

export interface Notebook {
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

export interface DataConnection {
  id: string
  name: string
  connection_type: string
  database: string
  status: string
}

export interface SQLExecuteResult {
  cell_id: string
  status: string
  duration_ms: number
  row_count: number
  columns: { name: string; type: string }[]
  rows: Record<string, any>[]
  truncated: boolean
  error?: string
}

export interface PythonOutput {
  type: 'text' | 'dataframe' | 'image' | 'error'
  data: any
  name?: string
  columns?: string[]
  shape?: number[]
  truncated?: boolean
  format?: string
}

export interface PythonExecuteResult {
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

export type CellResult = SQLExecuteResult | PythonExecuteResult

export interface SessionVariable {
  name: string
  type: string
  preview: string
}

export interface ToastState {
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

// Type guard
export function isPythonResult(result: CellResult): result is PythonExecuteResult {
  return 'stdout' in result || 'outputs' in result
}
