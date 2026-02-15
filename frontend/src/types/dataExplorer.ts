/**
 * Types for Data Explorer feature.
 */

export interface DatabaseInfo {
  id: string
  name: string
  description: string
  host: string
  port: number
}

export interface Schema {
  name: string
  table_count?: number
}

export interface Table {
  schema: string
  name: string
  type: string
  row_estimate?: number
}

export interface Column {
  name: string
  data_type: string
  is_nullable: boolean
  default?: string
  ordinal_position: number
}

export interface TableRowsResponse {
  schema: string
  table: string
  columns: string[]
  rows: any[][]
  page: number
  page_size: number
  total_rows?: number
}

export interface QueryResponse {
  columns: string[]
  rows: any[][]
  total_rows_estimate?: number
  execution_time_ms: number
  error?: {
    message: string
    code?: string
  }
}

export interface ColumnSummary {
  data_type: string
  distinct_count?: number
  min?: any
  max?: any
  avg?: number
  count?: number
}

export interface TableSummary {
  column_stats: Record<string, ColumnSummary>
}

export type ActiveTab = 'preview' | 'columns' | 'query' | 'summary'
