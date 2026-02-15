/**
 * Custom hook for Data Dictionary state and logic.
 */
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchDictionaryEntries,
  DictionaryEntry,
  getExplorerDatabases,
  getExplorerSchemas,
  getExplorerTables,
  updateDictionaryEntry,
  getColumnVersions,
  activateDictionaryVersion,
  submitForApproval,
  approveEntry,
  rejectEntry
} from '../api/client'
import {
  DatabaseInfo,
  Schema,
  Table,
  EditFormData,
  ApprovalModalState,
  ToastState,
  SelectedTable
} from '../types/dataDictionary'

export interface DataDictionaryState {
  // Database navigation
  databases: DatabaseInfo[]
  selectedDbId: string
  schemas: Schema[]
  expandedSchemas: Set<string>
  tablesBySchema: Record<string, Table[]>
  loadingNav: boolean

  // Dictionary entries
  entries: DictionaryEntry[]
  loading: boolean
  error: string | null
  searchTerm: string
  selectedTable: SelectedTable | null

  // Editing state
  editingEntry: number | null
  editForm: EditFormData
  versionNotes: string
  saving: boolean

  // Versioning state
  viewingVersions: DictionaryEntry | null
  versions: DictionaryEntry[]
  loadingVersions: boolean

  // Toast notification
  toast: ToastState | null

  // Approval modal
  approvalModal: ApprovalModalState
  approvalNotes: string

  // Computed values
  displayedEntries: DictionaryEntry[]
  documentedTables: Set<string>
  totalTables: number
}

export interface DataDictionaryActions {
  setSelectedDbId: (id: string) => void
  setSearchTerm: (term: string) => void
  toggleSchema: (schemaName: string) => void
  selectTable: (schema: string, table: string) => void
  generateDocumentation: (schema: string, table: string) => void
  getTableDocStatus: (schema: string, table: string) => { hasDoc: boolean; columnCount: number }

  // Editing
  startEditing: (entry: DictionaryEntry) => void
  cancelEditing: () => void
  saveEntry: (entryId: number) => Promise<void>
  setEditForm: (form: EditFormData) => void
  setVersionNotes: (notes: string) => void
  addTag: (tag: string) => void
  removeTag: (tag: string) => void

  // Versioning
  viewVersionHistory: (entry: DictionaryEntry) => Promise<void>
  activateVersion: (versionId: number) => Promise<void>
  closeVersionHistory: () => void

  // Approval
  handleSubmitForApproval: (entryId: number) => Promise<void>
  handleApprove: (entryId: number) => void
  handleReject: (entryId: number) => void
  submitApprovalAction: () => Promise<void>
  cancelApprovalAction: () => void
  setApprovalNotes: (notes: string) => void

  // Toast
  showToast: (message: string, type: ToastState['type']) => void
  closeToast: () => void
}

export function useDataDictionary(): [DataDictionaryState, DataDictionaryActions] {
  const navigate = useNavigate()

  // Database navigation
  const [databases, setDatabases] = useState<DatabaseInfo[]>([])
  const [selectedDbId, setSelectedDbId] = useState<string>('default')
  const [schemas, setSchemas] = useState<Schema[]>([])
  const [expandedSchemas, setExpandedSchemas] = useState<Set<string>>(new Set(['public']))
  const [tablesBySchema, setTablesBySchema] = useState<Record<string, Table[]>>({})
  const [loadingNav, setLoadingNav] = useState(true)

  // Dictionary entries
  const [entries, setEntries] = useState<DictionaryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTable, setSelectedTable] = useState<SelectedTable | null>(null)

  // Editing state
  const [editingEntry, setEditingEntry] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<EditFormData>({})
  const [versionNotes, setVersionNotes] = useState<string>('')
  const [saving, setSaving] = useState(false)

  // Versioning state
  const [viewingVersions, setViewingVersions] = useState<DictionaryEntry | null>(null)
  const [versions, setVersions] = useState<DictionaryEntry[]>([])
  const [loadingVersions, setLoadingVersions] = useState(false)

  // Toast notification
  const [toast, setToast] = useState<ToastState | null>(null)

  // Approval modal
  const [approvalModal, setApprovalModal] = useState<ApprovalModalState>({
    isOpen: false,
    entryId: null,
    action: null
  })
  const [approvalNotes, setApprovalNotes] = useState<string>('')

  // Toast helper
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ message, type })
  }, [])

  const closeToast = useCallback(() => {
    setToast(null)
  }, [])

  // Load databases on mount
  useEffect(() => {
    loadDatabases()
  }, [])

  // Load schemas and dictionary when database changes
  useEffect(() => {
    if (selectedDbId) {
      setTablesBySchema({})
      setSchemas([])
      setEntries([])
      setSelectedTable(null)
      loadSchemas(selectedDbId)
      loadDictionary(selectedDbId)
    }
  }, [selectedDbId])

  const loadDatabases = async () => {
    try {
      const dbs = await getExplorerDatabases()
      setDatabases(dbs)
      if (dbs.length > 0 && !selectedDbId) {
        setSelectedDbId(dbs[0].id)
      }
    } catch (error) {
      console.error('Failed to load databases:', error)
    }
  }

  const loadSchemas = async (dbId: string) => {
    try {
      setLoadingNav(true)
      const schemasData = await getExplorerSchemas(dbId)
      setSchemas(schemasData)
      if (schemasData.some((s: Schema) => s.name === 'public')) {
        loadTables('public', dbId)
      }
    } catch (err) {
      console.error('Failed to load schemas:', err)
      setError('Failed to load schemas. Check your database connection.')
    } finally {
      setLoadingNav(false)
    }
  }

  const loadTables = async (schema: string, dbId?: string) => {
    const effectiveDbId = dbId || selectedDbId
    try {
      const tables = await getExplorerTables(schema, effectiveDbId)
      setTablesBySchema(prev => ({ ...prev, [schema]: tables }))
    } catch (error) {
      console.error(`Failed to load tables for ${schema}:`, error)
      setTablesBySchema(prev => ({ ...prev, [schema]: [] }))
    }
  }

  const loadDictionary = async (dbId: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchDictionaryEntries(dbId)
      if (!Array.isArray(data)) {
        throw new Error('Invalid response format: expected array')
      }
      setEntries(data)
    } catch (err: any) {
      console.error('Failed to load dictionary:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load data dictionary'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const toggleSchema = useCallback((schemaName: string) => {
    setExpandedSchemas(prev => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(schemaName)) {
        newExpanded.delete(schemaName)
      } else {
        newExpanded.add(schemaName)
        if (!tablesBySchema[schemaName]) {
          loadTables(schemaName, selectedDbId)
        }
      }
      return newExpanded
    })
  }, [tablesBySchema, selectedDbId])

  const selectTable = useCallback((schema: string, table: string) => {
    setSelectedTable({ schema, table })
    setSearchTerm('')
  }, [])

  const generateDocumentation = useCallback((schema: string, table: string) => {
    navigate('/analysis', {
      state: {
        preselectedTables: [{ schema, name: table }],
        preselectedAction: 'column_documentation',
        dbId: selectedDbId
      }
    })
  }, [navigate, selectedDbId])

  const getTableDocStatus = useCallback((schema: string, table: string) => {
    const tableEntries = entries.filter(
      e => e.database_name === selectedDbId &&
           e.schema_name === schema &&
           e.table_name === table
    )
    return {
      hasDoc: tableEntries.length > 0,
      columnCount: tableEntries.length
    }
  }, [entries, selectedDbId])

  // Editing actions
  const startEditing = useCallback((entry: DictionaryEntry) => {
    setEditingEntry(entry.id)
    setEditForm({
      business_name: entry.business_name || '',
      business_description: entry.business_description || '',
      technical_description: entry.technical_description || '',
      tags: entry.tags || []
    })
  }, [])

  const cancelEditing = useCallback(() => {
    setEditingEntry(null)
    setEditForm({})
    setVersionNotes('')
  }, [])

  const saveEntry = useCallback(async (entryId: number) => {
    try {
      setSaving(true)
      const entryBeingEdited = entries.find(e => e.id === entryId)
      const isPublished = entryBeingEdited?.state === 'published'

      await updateDictionaryEntry(entryId, {
        ...editForm,
        create_new_version: isPublished,
        version_notes: isPublished
          ? (versionNotes || 'Edited published entry - new draft created')
          : undefined
      })

      showToast('Changes saved successfully!', 'success')
      setEditingEntry(null)
      setEditForm({})
      setVersionNotes('')

      loadDictionary(selectedDbId).catch(err => {
        console.warn('Failed to reload after save:', err)
        setTimeout(() => loadDictionary(selectedDbId).catch(() => {}), 2000)
      })
    } catch (err: any) {
      console.error('Failed to save entry:', err)
      showToast('Failed to save: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSaving(false)
    }
  }, [entries, editForm, versionNotes, selectedDbId, showToast])

  const addTag = useCallback((newTag: string) => {
    if (newTag && !editForm.tags?.includes(newTag)) {
      setEditForm(prev => ({ ...prev, tags: [...(prev.tags || []), newTag] }))
    }
  }, [editForm.tags])

  const removeTag = useCallback((tagToRemove: string) => {
    setEditForm(prev => ({ ...prev, tags: prev.tags?.filter(t => t !== tagToRemove) }))
  }, [])

  // Versioning actions
  const viewVersionHistory = useCallback(async (entry: DictionaryEntry) => {
    try {
      setLoadingVersions(true)
      setViewingVersions(entry)
      const versionList = await getColumnVersions(
        entry.database_name,
        entry.schema_name,
        entry.table_name,
        entry.column_name
      )
      setVersions(versionList)
    } catch (err: any) {
      console.error('Failed to load versions:', err)
      showToast('Failed to load version history: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setLoadingVersions(false)
    }
  }, [showToast])

  const activateVersion = useCallback(async (versionId: number) => {
    try {
      setSaving(true)
      const activatedEntry = await activateDictionaryVersion(versionId)
      showToast(`Version ${activatedEntry.version_number} is now active`, 'success')
      setViewingVersions(null)
      setVersions([])
      loadDictionary(selectedDbId).catch(() => {})
    } catch (err: any) {
      console.error('Failed to activate version:', err)
      showToast('Failed to activate version: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSaving(false)
    }
  }, [selectedDbId, showToast])

  const closeVersionHistory = useCallback(() => {
    setViewingVersions(null)
    setVersions([])
  }, [])

  // Approval actions
  const handleSubmitForApproval = useCallback(async (entryId: number) => {
    try {
      setSaving(true)
      await submitForApproval(entryId)
      showToast('Entry submitted for approval successfully', 'success')
      loadDictionary(selectedDbId).catch(() => {})
    } catch (err: any) {
      console.error('Failed to submit for approval:', err)
      showToast('Failed to submit: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSaving(false)
    }
  }, [selectedDbId, showToast])

  const handleApprove = useCallback((entryId: number) => {
    setApprovalModal({ isOpen: true, entryId, action: 'approve' })
  }, [])

  const handleReject = useCallback((entryId: number) => {
    setApprovalModal({ isOpen: true, entryId, action: 'reject' })
  }, [])

  const submitApprovalAction = useCallback(async () => {
    if (!approvalModal.entryId) return

    try {
      setSaving(true)
      if (approvalModal.action === 'approve') {
        await approveEntry(approvalModal.entryId, approvalNotes || undefined)
        showToast('Entry approved and published successfully', 'success')
      } else if (approvalModal.action === 'reject') {
        await rejectEntry(approvalModal.entryId, approvalNotes || undefined)
        showToast('Entry rejected and returned to draft', 'warning')
      }
      setApprovalModal({ isOpen: false, entryId: null, action: null })
      setApprovalNotes('')
      loadDictionary(selectedDbId).catch(() => {})
    } catch (err: any) {
      console.error(`Failed to ${approvalModal.action} entry:`, err)
      showToast(`Failed to ${approvalModal.action}: ` + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSaving(false)
    }
  }, [approvalModal, approvalNotes, selectedDbId, showToast])

  const cancelApprovalAction = useCallback(() => {
    setApprovalModal({ isOpen: false, entryId: null, action: null })
    setApprovalNotes('')
  }, [])

  // Computed values
  const displayedEntries = selectedTable
    ? entries.filter(
        e => e.database_name === selectedDbId &&
             e.schema_name === selectedTable.schema &&
             e.table_name === selectedTable.table &&
             (!searchTerm ||
              e.column_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              e.business_description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
              e.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())))
      )
    : entries.filter(
        e => e.database_name === selectedDbId &&
             (!searchTerm ||
              e.column_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
              e.business_description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
              e.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())))
      )

  const documentedTables = new Set(
    entries
      .filter(e => e.database_name === selectedDbId)
      .map(e => `${e.schema_name}.${e.table_name}`)
  )

  const totalTables = Object.values(tablesBySchema).reduce((sum, tables) => sum + tables.length, 0)

  const state: DataDictionaryState = {
    databases,
    selectedDbId,
    schemas,
    expandedSchemas,
    tablesBySchema,
    loadingNav,
    entries,
    loading,
    error,
    searchTerm,
    selectedTable,
    editingEntry,
    editForm,
    versionNotes,
    saving,
    viewingVersions,
    versions,
    loadingVersions,
    toast,
    approvalModal,
    approvalNotes,
    displayedEntries,
    documentedTables,
    totalTables
  }

  const actions: DataDictionaryActions = {
    setSelectedDbId,
    setSearchTerm,
    toggleSchema,
    selectTable,
    generateDocumentation,
    getTableDocStatus,
    startEditing,
    cancelEditing,
    saveEntry,
    setEditForm,
    setVersionNotes,
    addTag,
    removeTag,
    viewVersionHistory,
    activateVersion,
    closeVersionHistory,
    handleSubmitForApproval,
    handleApprove,
    handleReject,
    submitApprovalAction,
    cancelApprovalAction,
    setApprovalNotes,
    showToast,
    closeToast
  }

  return [state, actions]
}
