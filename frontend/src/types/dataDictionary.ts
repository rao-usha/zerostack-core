/**
 * TypeScript types for Data Dictionary feature.
 */
import { DictionaryEntry } from '../api/client'

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

export interface EditFormData {
  business_name?: string
  business_description?: string
  technical_description?: string
  tags?: string[]
}

export interface ApprovalModalState {
  isOpen: boolean
  entryId: number | null
  action: 'approve' | 'reject' | null
}

export interface ToastState {
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

export interface SelectedTable {
  schema: string
  table: string
}

// Re-export DictionaryEntry for convenience
export type { DictionaryEntry }
