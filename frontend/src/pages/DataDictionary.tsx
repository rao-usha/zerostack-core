import { useState, useEffect } from 'react'
import { 
  Book, 
  Search, 
  Database, 
  Table as TableIcon, 
  Tag,
  ChevronRight,
  ChevronDown,
  FileText,
  AlertCircle,
  Play,
  Loader2,
  Edit2,
  Save,
  X as XIcon,
  History,
  Check
} from 'lucide-react'
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
import { useNavigate } from 'react-router-dom'
import Toast from '../components/Toast'

interface DatabaseInfo {
  id: string
  name: string
  description: string
  host: string
  port: number
}

interface Schema {
  name: string
  table_count?: number
}

interface Table {
  schema: string
  name: string
  type: string
  row_estimate?: number
}

export default function DataDictionary() {
  // Database navigation
  const navigate = useNavigate()
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
  const [selectedTable, setSelectedTable] = useState<{ schema: string; table: string } | null>(null)
  
  // Editing state
  const [editingEntry, setEditingEntry] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<{
    business_name?: string
    business_description?: string
    technical_description?: string
    tags?: string[]
  }>({})
  const [versionNotes, setVersionNotes] = useState<string>('')
  const [saving, setSaving] = useState(false)
  
  // Versioning state
  const [viewingVersions, setViewingVersions] = useState<DictionaryEntry | null>(null)
  const [versions, setVersions] = useState<DictionaryEntry[]>([])
  const [loadingVersions, setLoadingVersions] = useState(false)
  
  // Toast notification state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info' } | null>(null)

  const showToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    setToast({ message, type })
  }

  // Approval modal state
  const [approvalModal, setApprovalModal] = useState<{ 
    isOpen: boolean; 
    entryId: number | null; 
    action: 'approve' | 'reject' | null 
  }>({ isOpen: false, entryId: null, action: null })
  const [approvalNotes, setApprovalNotes] = useState<string>('')

  useEffect(() => {
    loadDatabases()
  }, [])

  useEffect(() => {
    if (selectedDbId) {
      console.log('[DataDictionary] Database changed to:', selectedDbId)
      // Clear cached data when database changes
      setTablesBySchema({})
      setSchemas([])
      setEntries([])
      setSelectedTable(null)

      // Load new data for the selected database
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
      console.log('[DataDictionary] Loading schemas for:', dbId)
      const schemasData = await getExplorerSchemas(dbId)
      setSchemas(schemasData)

      // Auto-load public schema tables if it exists
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
      console.log('[DataDictionary] Loading tables for schema:', schema, 'db:', effectiveDbId)
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
      console.log('[DataDictionary] Loading dictionary for:', dbId)
      const data = await fetchDictionaryEntries(dbId)

      // Validate data before setting
      if (!Array.isArray(data)) {
        throw new Error('Invalid response format: expected array')
      }

      setEntries(data)
      console.log(`[DataDictionary] Loaded ${data.length} dictionary entries for ${dbId}`)
    } catch (err: any) {
      console.error('Failed to load dictionary:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load data dictionary'
      setError(errorMessage)
      // Don't throw - just set error state
    } finally {
      setLoading(false)
    }
  }

  const toggleSchema = (schemaName: string) => {
    const newExpanded = new Set(expandedSchemas)
    if (newExpanded.has(schemaName)) {
      newExpanded.delete(schemaName)
    } else {
      newExpanded.add(schemaName)
      // Load tables when expanding (only if not already loaded)
      if (!tablesBySchema[schemaName]) {
        loadTables(schemaName, selectedDbId)
      }
    }
    setExpandedSchemas(newExpanded)
  }

  const selectTable = (schema: string, table: string) => {
    setSelectedTable({ schema, table })
    setSearchTerm('')
  }

  const generateDocumentation = (schema: string, table: string) => {
    // Navigate to Data Analysis page with pre-selected table
    navigate('/analysis', { 
      state: { 
        preselectedTables: [{ schema, name: table }],
        preselectedAction: 'column_documentation',
        dbId: selectedDbId
      } 
    })
  }

  // Check if a table has documentation
  const getTableDocStatus = (schema: string, table: string) => {
    const tableEntries = entries.filter(
      e => e.database_name === selectedDbId && 
           e.schema_name === schema && 
           e.table_name === table
    )
    return {
      hasDoc: tableEntries.length > 0,
      columnCount: tableEntries.length
    }
  }

  const startEditing = (entry: DictionaryEntry) => {
    setEditingEntry(entry.id)
    setEditForm({
      business_name: entry.business_name || '',
      business_description: entry.business_description || '',
      technical_description: entry.technical_description || '',
      tags: entry.tags || []
    })
  }

  const cancelEditing = () => {
    setEditingEntry(null)
    setEditForm({})
    setVersionNotes('')
  }

  const saveEntry = async (entryId: number) => {
    try {
      setSaving(true)
      
      // Find the entry being edited to check its state
      const entryBeingEdited = entries.find(e => e.id === entryId)
      const isPublished = entryBeingEdited?.state === 'published'
      
      // If editing a published entry, always create a new version (as a draft)
      // If editing a draft, update in place
      await updateDictionaryEntry(entryId, {
        ...editForm,
        create_new_version: isPublished,
        version_notes: isPublished 
          ? (versionNotes || 'Edited published entry - new draft created')
          : undefined
      })
      
      // Save succeeded! Show success message immediately
      showToast('Changes saved successfully!', 'success')
      
      // Clear editing state
      setEditingEntry(null)
      setEditForm({})
      setVersionNotes('')
      
      // Reload entries in the background (don't block on this)
      loadDictionary().catch(reloadErr => {
        console.warn('Failed to reload dictionary after save, but save succeeded:', reloadErr)
        // Silently retry after a delay
        setTimeout(() => loadDictionary().catch(() => {}), 2000)
      })
    } catch (err: any) {
      console.error('Failed to save entry:', err)
      const errorMsg = err.response?.data?.detail || err.message || 'Unknown error'
      showToast('Failed to save changes: ' + errorMsg, 'error')
    } finally {
      setSaving(false)
    }
  }

  const viewVersionHistory = async (entry: DictionaryEntry) => {
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
  }

  const activateVersion = async (versionId: number) => {
    try {
      setSaving(true)
      const activatedEntry = await activateDictionaryVersion(versionId)
      
      // Activation succeeded! Show success and close modal
      showToast(`Version ${activatedEntry.version_number} is now active`, 'success')
      setViewingVersions(null)
      setVersions([])
      
      // Reload entries in background
      loadDictionary().catch(err => {
        console.warn('Failed to reload after activation, but activation succeeded:', err)
        setTimeout(() => loadDictionary().catch(() => {}), 2000)
      })
    } catch (err: any) {
      console.error('Failed to activate version:', err)
      showToast('Failed to activate version: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSaving(false)
    }
  }

  const addTag = (newTag: string) => {
    if (newTag && !editForm.tags?.includes(newTag)) {
      setEditForm({ ...editForm, tags: [...(editForm.tags || []), newTag] })
    }
  }

  const removeTag = (tagToRemove: string) => {
    setEditForm({ ...editForm, tags: editForm.tags?.filter(t => t !== tagToRemove) })
  }

  // Workflow actions
  const handleSubmitForApproval = async (entryId: number) => {
    try {
      setSaving(true)
      await submitForApproval(entryId)
      
      // Submit succeeded! Show success message
      showToast('Entry submitted for approval successfully', 'success')
      
      // Reload in background
      loadDictionary().catch(err => {
        console.warn('Failed to reload after submit, but submit succeeded:', err)
        setTimeout(() => loadDictionary().catch(() => {}), 2000)
      })
    } catch (err: any) {
      console.error('Failed to submit for approval:', err)
      showToast('Failed to submit: ' + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleApprove = async (entryId: number) => {
    setApprovalModal({ isOpen: true, entryId, action: 'approve' })
  }

  const handleReject = async (entryId: number) => {
    setApprovalModal({ isOpen: true, entryId, action: 'reject' })
  }

  const submitApprovalAction = async () => {
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
      
      // Close modal and reset
      setApprovalModal({ isOpen: false, entryId: null, action: null })
      setApprovalNotes('')
      
      // Reload in background
      loadDictionary().catch(err => {
        console.warn('Failed to reload after approval action, but action succeeded:', err)
        setTimeout(() => loadDictionary().catch(() => {}), 2000)
      })
    } catch (err: any) {
      console.error(`Failed to ${approvalModal.action} entry:`, err)
      showToast(`Failed to ${approvalModal.action}: ` + (err.response?.data?.detail || err.message), 'error')
    } finally {
      setSaving(false)
    }
  }

  const cancelApprovalAction = () => {
    setApprovalModal({ isOpen: false, entryId: null, action: null })
    setApprovalNotes('')
  }

  // Direct publish function (for future admin override feature)
  // const handlePublish = async (entryId: number) => {
  //   if (!confirm('Publish this entry directly without approval?')) return
  //   try {
  //     setSaving(true)
  //     await publishEntry(entryId, 'Direct publish')
  //     await loadDictionary()
  //     alert('Entry published')
  //   } catch (err: any) {
  //     console.error('Failed to publish entry:', err)
  //     alert('Failed to publish entry: ' + (err.response?.data?.detail || err.message))
  //   } finally {
  //     setSaving(false)
  //   }
  // }

  // Filter entries for selected table
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

  // Count documented tables
  const documentedTables = new Set(
    entries
      .filter(e => e.database_name === selectedDbId)
      .map(e => `${e.schema_name}.${e.table_name}`)
  )
  const totalTables = Object.values(tablesBySchema).reduce((sum, tables) => sum + tables.length, 0)

  // Helper to render state badge
  const renderStateBadge = (state: string) => {
    const colors = {
      draft: { bg: 'rgba(168, 216, 255, 0.1)', text: '#a8d8ff', border: 'rgba(168, 216, 255, 0.3)' },
      pending_approval: { bg: 'rgba(251, 191, 36, 0.1)', text: '#fbbf24', border: 'rgba(251, 191, 36, 0.3)' },
      published: { bg: 'rgba(34, 197, 94, 0.1)', text: '#22c55e', border: 'rgba(34, 197, 94, 0.3)' }
    }
    const color = colors[state as keyof typeof colors] || colors.draft
    return (
      <span style={{
        padding: '2px 8px',
        borderRadius: '12px',
        fontSize: '0.75rem',
        fontWeight: '500',
        backgroundColor: color.bg,
        color: color.text,
        border: `1px solid ${color.border}`,
        display: 'inline-block',
        textTransform: 'capitalize'
      }}>
        {state.replace('_', ' ')}
      </span>
    )
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)', padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <Book className="h-8 w-8" style={{ color: '#a8d8ff' }} />
              <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f0f0f5' }}>
                Data Dictionary
              </h1>
            </div>
            <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
              AI-generated column documentation for your database tables
            </p>
          </div>

          {/* Database Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <select
              value={selectedDbId}
              onChange={(e) => setSelectedDbId(e.target.value)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#0f0f17',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontSize: '0.875rem',
                minWidth: '200px'
              }}
            >
              {databases.map(db => (
                <option key={db.id} value={db.id}>{db.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats */}
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1.5rem', fontSize: '0.875rem', color: '#9ca3af' }}>
          <span>{documentedTables.size} of {totalTables} tables documented</span>
          <span>{entries.filter(e => e.database_name === selectedDbId).length} columns</span>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Sidebar - Table Navigator */}
        <div style={{ 
          width: '320px', 
          borderRight: '1px solid rgba(168, 216, 255, 0.2)',
          backgroundColor: '#0f0f17',
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          overflow: 'hidden'
        }}>
          {/* Scrollable content area */}
          <div style={{ 
            flex: 1,
            overflowY: 'auto',
            overflowX: 'hidden'
          }}>
          {loadingNav ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>
              <Loader2 className="h-6 w-6 animate-spin mx-auto" />
              <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>Loading tables...</p>
            </div>
          ) : (
            <div style={{ padding: '1rem' }}>
              {schemas.map(schema => {
                const isExpanded = expandedSchemas.has(schema.name)
                const tables = tablesBySchema[schema.name] || []
                
                return (
                  <div key={schema.name} style={{ marginBottom: '0.5rem' }}>
                    {/* Schema Header */}
                    <button
                      onClick={() => toggleSchema(schema.name)}
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.5rem',
                        backgroundColor: isExpanded ? 'rgba(168, 216, 255, 0.1)' : 'transparent',
                        border: 'none',
                        borderRadius: '0.375rem',
                        color: '#f0f0f5',
                        cursor: 'pointer',
                        fontSize: '0.875rem',
                        fontWeight: '500'
                      }}
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" style={{ color: '#a8d8ff' }} />
                      ) : (
                        <ChevronRight className="h-4 w-4" style={{ color: '#a8d8ff' }} />
                      )}
                      <Database className="h-4 w-4" style={{ color: '#a8d8ff' }} />
                      <span>{schema.name}</span>
                      <span style={{ 
                        marginLeft: 'auto', 
                        fontSize: '0.75rem', 
                        color: '#9ca3af',
                        padding: '0.125rem 0.375rem',
                        backgroundColor: 'rgba(168, 216, 255, 0.1)',
                        borderRadius: '9999px'
                      }}>
                        {tables.length}
                      </span>
                    </button>

                    {/* Tables */}
                    {isExpanded && (
                      <div style={{ marginLeft: '1.5rem', marginTop: '0.25rem' }}>
                        {tables.map(table => {
                          const docStatus = getTableDocStatus(schema.name, table.name)
                          const isSelected = selectedTable?.schema === schema.name && selectedTable?.table === table.name
                          
                          return (
                            <div
                              key={table.name}
                              style={{
                                marginBottom: '0.25rem'
                              }}
                            >
                              <button
                                onClick={() => selectTable(schema.name, table.name)}
                                style={{
                                  width: '100%',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '0.5rem',
                                  padding: '0.5rem',
                                  backgroundColor: isSelected ? 'rgba(168, 216, 255, 0.15)' : 'transparent',
                                  border: isSelected ? '1px solid rgba(168, 216, 255, 0.3)' : '1px solid transparent',
                                  borderRadius: '0.375rem',
                                  color: '#f0f0f5',
                                  cursor: 'pointer',
                                  fontSize: '0.8125rem',
                                  textAlign: 'left'
                                }}
                              >
                                {docStatus.hasDoc ? (
                                  <FileText className="h-3.5 w-3.5" style={{ color: '#22c55e' }} />
                                ) : (
                                  <AlertCircle className="h-3.5 w-3.5" style={{ color: '#f59e0b' }} />
                                )}
                                <span style={{ flex: 1 }}>{table.name}</span>
                                {docStatus.hasDoc && (
                                  <span style={{ 
                                    fontSize: '0.6875rem', 
                                    color: '#9ca3af'
                                  }}>
                                    {docStatus.columnCount}
                                  </span>
                                )}
                              </button>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
          </div>
        </div>

        {/* Right Panel - Documentation Display */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Search Bar */}
          <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid rgba(168, 216, 255, 0.2)' }}>
            <div style={{ position: 'relative' }}>
              <Search className="h-5 w-5" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#6b7280' }} />
              <input
                type="text"
                placeholder="Search columns, descriptions, tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem 0.5rem 2.5rem',
                  backgroundColor: '#0f0f17',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.5rem',
                  color: '#f0f0f5',
                  fontSize: '0.875rem'
                }}
              />
            </div>
          </div>

          {/* Content Area */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
            {loading && (
              <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                <p>Loading dictionary...</p>
              </div>
            )}

            {error && (
              <div style={{ 
                padding: '1rem', 
                backgroundColor: 'rgba(239, 68, 68, 0.1)', 
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '0.5rem',
                color: '#fca5a5'
              }}>
                {error}
              </div>
            )}

            {!loading && !error && selectedTable && (
              <>
                {/* Table Header */}
                <div style={{ marginBottom: '2rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <TableIcon className="h-6 w-6" style={{ color: '#a8d8ff' }} />
                        <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#f0f0f5' }}>
                          {selectedTable.schema}.{selectedTable.table}
                        </h2>
                      </div>
                      <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                        {displayedEntries.length} columns documented
                      </p>
                    </div>
                    
                    {displayedEntries.length === 0 && (
                      <button
                        onClick={() => generateDocumentation(selectedTable.schema, selectedTable.table)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          padding: '0.625rem 1.25rem',
                          backgroundColor: '#a8d8ff',
                          color: '#0a0a0f',
                          border: 'none',
                          borderRadius: '0.5rem',
                          fontSize: '0.875rem',
                          fontWeight: '500',
                          cursor: 'pointer'
                        }}
                      >
                        <Play className="h-4 w-4" />
                        Generate Documentation
                      </button>
                    )}
                  </div>

                  {displayedEntries.length === 0 && (
                    <div style={{
                      padding: '2rem',
                      textAlign: 'center',
                      backgroundColor: 'rgba(168, 216, 255, 0.05)',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.5rem'
                    }}>
                      <AlertCircle className="h-12 w-12 mx-auto mb-3" style={{ color: '#f59e0b' }} />
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '0.5rem', color: '#f0f0f5' }}>
                        No Documentation Yet
                      </h3>
                      <p style={{ fontSize: '0.875rem', color: '#9ca3af', marginBottom: '1rem' }}>
                        This table hasn't been documented yet. Run a Column Documentation analysis to generate AI-powered descriptions.
                      </p>
                    </div>
                  )}
                </div>

                {/* Column Documentation */}
                {displayedEntries.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {displayedEntries.map(column => {
                      const isEditing = editingEntry === column.id
                      
                      return (
                        <div 
                          key={column.id}
                          style={{
                            padding: '1rem',
                            backgroundColor: '#0f0f17',
                            border: isEditing ? '1px solid rgba(168, 216, 255, 0.5)' : '1px solid rgba(168, 216, 255, 0.2)',
                            borderRadius: '0.5rem'
                          }}
                        >
                          {/* Column Name & Type */}
                          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            <code style={{ 
                              fontSize: '0.875rem', 
                              fontWeight: '600', 
                              color: '#a8d8ff',
                              fontFamily: 'monospace'
                            }}>
                              {column.column_name}
                            </code>
                            {column.data_type && (
                              <span style={{ 
                                fontSize: '0.75rem', 
                                color: '#9ca3af',
                                fontFamily: 'monospace'
                              }}>
                                : {column.data_type}
                              </span>
                            )}
                            <span style={{
                              fontSize: '0.625rem',
                              color: '#6b7280',
                              padding: '0.125rem 0.375rem',
                              backgroundColor: 'rgba(107, 114, 128, 0.2)',
                              borderRadius: '0.25rem'
                            }}>
                              {column.source}
                            </span>
                            {renderStateBadge(column.state)}
                            
                            {/* Edit/Save/Cancel/Version/Workflow Buttons */}
                            <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
                              {!isEditing ? (
                                <>
                                  <button
                                    onClick={() => viewVersionHistory(column)}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                      padding: '0.25rem 0.5rem',
                                      backgroundColor: 'rgba(139, 92, 246, 0.1)',
                                      border: '1px solid rgba(139, 92, 246, 0.3)',
                                      borderRadius: '0.375rem',
                                      color: '#a78bfa',
                                      fontSize: '0.75rem',
                                      cursor: 'pointer'
                                    }}
                                    title={column.is_active ? "View version history (This is the active/published version)" : "View version history (Draft - not yet published)"}
                                  >
                                    <History className="h-3 w-3" />
                                    v{column.version_number} {column.is_active ? '(Active)' : column.state === 'draft' ? '(Draft)' : ''}
                                  </button>
                                  {(column.state === 'draft' || column.state === 'published') && (
                                    <button
                                      onClick={() => startEditing(column)}
                                      style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.25rem',
                                        padding: '0.25rem 0.5rem',
                                        backgroundColor: 'rgba(168, 216, 255, 0.1)',
                                        border: '1px solid rgba(168, 216, 255, 0.3)',
                                        borderRadius: '0.375rem',
                                        color: '#a8d8ff',
                                        fontSize: '0.75rem',
                                        cursor: 'pointer'
                                      }}
                                      title={column.state === 'published' ? 'Edit (creates new draft version)' : 'Edit entry'}
                                    >
                                      <Edit2 className="h-3 w-3" />
                                      Edit
                                    </button>
                                  )}
                                  {column.state === 'draft' && (
                                    <button
                                      onClick={() => handleSubmitForApproval(column.id)}
                                      disabled={saving}
                                      style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.25rem',
                                        padding: '0.25rem 0.5rem',
                                        backgroundColor: 'rgba(251, 191, 36, 0.1)',
                                        border: '1px solid rgba(251, 191, 36, 0.3)',
                                        borderRadius: '0.375rem',
                                        color: '#fbbf24',
                                        fontSize: '0.75rem',
                                        cursor: saving ? 'wait' : 'pointer',
                                        opacity: saving ? 0.5 : 1
                                      }}
                                      title="Submit for approval"
                                    >
                                      <Play className="h-3 w-3" />
                                      Submit
                                    </button>
                                  )}
                                  {column.state === 'pending_approval' && (
                                    <>
                                      <button
                                        onClick={() => handleApprove(column.id)}
                                        disabled={saving}
                                        style={{
                                          display: 'flex',
                                          alignItems: 'center',
                                          gap: '0.25rem',
                                          padding: '0.25rem 0.5rem',
                                          backgroundColor: 'rgba(34, 197, 94, 0.1)',
                                          border: '1px solid rgba(34, 197, 94, 0.3)',
                                          borderRadius: '0.375rem',
                                          color: '#22c55e',
                                          fontSize: '0.75rem',
                                          cursor: saving ? 'wait' : 'pointer',
                                          opacity: saving ? 0.5 : 1
                                        }}
                                        title="Approve and publish"
                                      >
                                        <Check className="h-3 w-3" />
                                        Approve
                                      </button>
                                      <button
                                        onClick={() => handleReject(column.id)}
                                        disabled={saving}
                                        style={{
                                          display: 'flex',
                                          alignItems: 'center',
                                          gap: '0.25rem',
                                          padding: '0.25rem 0.5rem',
                                          backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                          border: '1px solid rgba(239, 68, 68, 0.3)',
                                          borderRadius: '0.375rem',
                                          color: '#ef4444',
                                          fontSize: '0.75rem',
                                          cursor: saving ? 'wait' : 'pointer',
                                          opacity: saving ? 0.5 : 1
                                        }}
                                        title="Reject and return to draft"
                                      >
                                        <XIcon className="h-3 w-3" />
                                        Reject
                                      </button>
                                    </>
                                  )}
                                </>
                              ) : (
                                <>
                                  <button
                                    onClick={() => saveEntry(column.id)}
                                    disabled={saving}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                      padding: '0.25rem 0.5rem',
                                      backgroundColor: '#22c55e',
                                      border: 'none',
                                      borderRadius: '0.375rem',
                                      color: '#fff',
                                      fontSize: '0.75rem',
                                      cursor: saving ? 'wait' : 'pointer',
                                      opacity: saving ? 0.5 : 1
                                    }}
                                    title={column.state === 'published' ? 'Save (creates new draft version)' : 'Save changes'}
                                  >
                                    <Save className="h-3 w-3" />
                                    {saving ? 'Saving...' : 'Save'}
                                  </button>
                                  <button
                                    onClick={cancelEditing}
                                    disabled={saving}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                      padding: '0.25rem 0.5rem',
                                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                      border: '1px solid rgba(239, 68, 68, 0.3)',
                                      borderRadius: '0.375rem',
                                      color: '#ef4444',
                                      fontSize: '0.75rem',
                                      cursor: saving ? 'not-allowed' : 'pointer'
                                    }}
                                  >
                                    <XIcon className="h-3 w-3" />
                                    Cancel
                                  </button>
                                </>
                              )}
                            </div>
                          </div>

                          {isEditing ? (
                            /* Edit Form */
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.75rem' }}>
                              {/* Version Notes */}
                              <div style={{ 
                                padding: '0.75rem',
                                backgroundColor: 'rgba(139, 92, 246, 0.05)',
                                border: '1px solid rgba(139, 92, 246, 0.2)',
                                borderRadius: '0.375rem'
                              }}>
                                <label style={{ display: 'block', fontSize: '0.75rem', color: '#a78bfa', marginBottom: '0.25rem', fontWeight: '500' }}>
                                  Version Notes (optional)
                                </label>
                                <input
                                  type="text"
                                  value={versionNotes}
                                  onChange={(e) => setVersionNotes(e.target.value)}
                                  style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    backgroundColor: '#0a0a0f',
                                    border: '1px solid rgba(139, 92, 246, 0.3)',
                                    borderRadius: '0.375rem',
                                    color: '#f0f0f5',
                                    fontSize: '0.875rem'
                                  }}
                                  placeholder="What changed? (used when saving as new version)"
                                />
                                <p style={{ fontSize: '0.6875rem', color: '#9ca3af', marginTop: '0.375rem', lineHeight: '1.3' }}>
                                  💡 Click "New Version" to preserve current version and create a new one
                                </p>
                              </div>

                              {/* Business Name */}
                              <div>
                                <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                                  Business Name
                                </label>
                                <input
                                  type="text"
                                  value={editForm.business_name || ''}
                                  onChange={(e) => setEditForm({ ...editForm, business_name: e.target.value })}
                                  style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    backgroundColor: '#0a0a0f',
                                    border: '1px solid rgba(168, 216, 255, 0.3)',
                                    borderRadius: '0.375rem',
                                    color: '#f0f0f5',
                                    fontSize: '0.875rem'
                                  }}
                                />
                              </div>

                              {/* Business Description */}
                              <div>
                                <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                                  Business Description
                                </label>
                                <textarea
                                  value={editForm.business_description || ''}
                                  onChange={(e) => setEditForm({ ...editForm, business_description: e.target.value })}
                                  rows={3}
                                  style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    backgroundColor: '#0a0a0f',
                                    border: '1px solid rgba(168, 216, 255, 0.3)',
                                    borderRadius: '0.375rem',
                                    color: '#f0f0f5',
                                    fontSize: '0.875rem',
                                    resize: 'vertical'
                                  }}
                                />
                              </div>

                              {/* Technical Description */}
                              <div>
                                <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                                  Technical Description
                                </label>
                                <textarea
                                  value={editForm.technical_description || ''}
                                  onChange={(e) => setEditForm({ ...editForm, technical_description: e.target.value })}
                                  rows={2}
                                  style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    backgroundColor: '#0a0a0f',
                                    border: '1px solid rgba(168, 216, 255, 0.3)',
                                    borderRadius: '0.375rem',
                                    color: '#f0f0f5',
                                    fontSize: '0.875rem',
                                    fontStyle: 'italic',
                                    resize: 'vertical'
                                  }}
                                />
                              </div>

                              {/* Tags */}
                              <div>
                                <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
                                  Tags
                                </label>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', marginBottom: '0.5rem' }}>
                                  {editForm.tags?.map((tag, i) => (
                                    <span
                                      key={i}
                                      style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '0.25rem',
                                        fontSize: '0.6875rem',
                                        padding: '0.125rem 0.5rem',
                                        backgroundColor: 'rgba(168, 216, 255, 0.15)',
                                        color: '#a8d8ff',
                                        borderRadius: '9999px'
                                      }}
                                    >
                                      <Tag className="h-3 w-3" />
                                      {tag}
                                      <button
                                        onClick={() => removeTag(tag)}
                                        style={{
                                          display: 'inline-flex',
                                          border: 'none',
                                          background: 'none',
                                          color: '#a8d8ff',
                                          cursor: 'pointer',
                                          padding: 0,
                                          marginLeft: '0.125rem'
                                        }}
                                      >
                                        <XIcon className="h-3 w-3" />
                                      </button>
                                    </span>
                                  ))}
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                  <input
                                    type="text"
                                    placeholder="Add tag (e.g., PII, metric)"
                                    onKeyPress={(e) => {
                                      if (e.key === 'Enter') {
                                        addTag((e.target as HTMLInputElement).value);
                                        (e.target as HTMLInputElement).value = ''
                                      }
                                    }}
                                    style={{
                                      flex: 1,
                                      padding: '0.375rem 0.5rem',
                                      backgroundColor: '#0a0a0f',
                                      border: '1px solid rgba(168, 216, 255, 0.3)',
                                      borderRadius: '0.375rem',
                                      color: '#f0f0f5',
                                      fontSize: '0.75rem'
                                    }}
                                  />
                                </div>
                              </div>
                            </div>
                          ) : (
                            /* View Mode */
                            <>
                              {/* Business Name */}
                              {column.business_name && column.business_name !== column.column_name && (
                                <div style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
                                  <strong>Business Name:</strong> {column.business_name}
                                </div>
                              )}

                              {/* Business Description */}
                              {column.business_description && (
                                <p style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
                                  {column.business_description}
                                </p>
                              )}

                              {/* Technical Description */}
                              {column.technical_description && (
                                <p style={{ fontSize: '0.8125rem', color: '#9ca3af', fontStyle: 'italic', marginBottom: '0.5rem' }}>
                                  {column.technical_description}
                                </p>
                              )}

                              {/* Examples */}
                              {column.examples && column.examples.length > 0 && (
                                <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
                                  <strong>Examples:</strong>{' '}
                                  {column.examples.map((ex, i) => (
                                    <code 
                                      key={i} 
                                      style={{ 
                                        backgroundColor: 'rgba(168, 216, 255, 0.1)', 
                                        padding: '0.125rem 0.25rem',
                                        borderRadius: '0.25rem',
                                        marginRight: '0.25rem'
                                      }}
                                    >
                                      {ex}
                                    </code>
                                  ))}
                                </div>
                              )}

                              {/* Tags */}
                              {column.tags && column.tags.length > 0 && (
                                <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
                                  {column.tags.map((tag, i) => (
                                    <span
                                      key={i}
                                      style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '0.25rem',
                                        fontSize: '0.6875rem',
                                        padding: '0.125rem 0.5rem',
                                        backgroundColor: 'rgba(168, 216, 255, 0.15)',
                                        color: '#a8d8ff',
                                        borderRadius: '9999px'
                                      }}
                                    >
                                      <Tag className="h-3 w-3" />
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </>
            )}

            {!loading && !error && !selectedTable && (
              <div style={{ textAlign: 'center', padding: '4rem 2rem', color: '#9ca3af' }}>
                <Book className="h-16 w-16 mx-auto mb-4" style={{ color: '#4b5563' }} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '0.5rem', color: '#d1d5db' }}>
                  Select a Table
                </h3>
                <p style={{ fontSize: '0.875rem' }}>
                  Choose a table from the left sidebar to view its column documentation.
                </p>
                <div style={{ marginTop: '1.5rem', fontSize: '0.8125rem' }}>
                  <p style={{ marginBottom: '0.5rem' }}>Legend:</p>
                  <div style={{ display: 'inline-flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <FileText className="h-4 w-4" style={{ color: '#22c55e' }} />
                      <span>Documented table</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <AlertCircle className="h-4 w-4" style={{ color: '#f59e0b' }} />
                      <span>Undocumented table</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Version History Modal */}
      {viewingVersions && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: '#0f0f17',
            border: '1px solid rgba(168, 216, 255, 0.3)',
            borderRadius: '0.75rem',
            padding: '2rem',
            maxWidth: '800px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#f0f0f5', marginBottom: '0.25rem' }}>
                  Version History
                </h2>
                <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                  {viewingVersions.schema_name}.{viewingVersions.table_name}.{viewingVersions.column_name}
                </p>
              </div>
              <button
                onClick={() => {
                  setViewingVersions(null)
                  setVersions([])
                }}
                style={{
                  padding: '0.5rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '0.375rem',
                  color: '#ef4444',
                  cursor: 'pointer'
                }}
              >
                <XIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Version List */}
            {loadingVersions ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" style={{ color: '#a8d8ff' }} />
                <p style={{ color: '#9ca3af' }}>Loading versions...</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {versions.map(version => (
                  <div
                    key={version.id}
                    style={{
                      padding: '1rem',
                      backgroundColor: version.is_active ? 'rgba(34, 197, 94, 0.1)' : 'rgba(168, 216, 255, 0.05)',
                      border: version.is_active ? '2px solid #22c55e' : '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.5rem'
                    }}
                  >
                    {/* Version Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{
                          fontSize: '1rem',
                          fontWeight: '600',
                          color: version.is_active ? '#22c55e' : '#a8d8ff'
                        }}>
                          Version {version.version_number}
                        </span>
                        {renderStateBadge(version.state)}
                        {version.is_active && (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            fontSize: '0.75rem',
                            padding: '0.25rem 0.5rem',
                            backgroundColor: 'rgba(34, 197, 94, 0.2)',
                            color: '#22c55e',
                            borderRadius: '9999px'
                          }}>
                            <Check className="h-3 w-3" />
                            Active
                          </span>
                        )}
                        <span style={{
                          fontSize: '0.75rem',
                          color: '#6b7280',
                          padding: '0.125rem 0.375rem',
                          backgroundColor: 'rgba(107, 114, 128, 0.2)',
                          borderRadius: '0.25rem'
                        }}>
                          {version.source}
                        </span>
                      </div>
                      {!version.is_active && version.state === 'published' && (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
                          <button
                            onClick={() => activateVersion(version.id)}
                            disabled={saving}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                              padding: '0.375rem 0.75rem',
                              backgroundColor: 'rgba(168, 216, 255, 0.1)',
                              border: '1px solid rgba(168, 216, 255, 0.3)',
                              borderRadius: '0.375rem',
                              color: '#a8d8ff',
                              fontSize: '0.75rem',
                              cursor: saving ? 'wait' : 'pointer',
                              opacity: saving ? 0.5 : 1
                            }}
                            title="Create a new draft version with this content"
                          >
                            <History className="h-3 w-3" />
                            {saving ? 'Creating...' : 'Rollback to This Version'}
                          </button>
                          <span style={{ fontSize: '0.7rem', color: '#6b7280', fontStyle: 'italic' }}>
                            Creates new draft for approval
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Version Notes */}
                    {version.version_notes && (
                      <p style={{ fontSize: '0.875rem', color: '#d1d5db', fontStyle: 'italic', marginBottom: '0.75rem' }}>
                        {version.version_notes}
                      </p>
                    )}

                    {/* Content */}
                    <div style={{ fontSize: '0.875rem', color: '#d1d5db' }}>
                      {version.business_name && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          <strong style={{ color: '#a8d8ff' }}>Business Name:</strong> {version.business_name}
                        </div>
                      )}
                      {version.business_description && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          <strong style={{ color: '#a8d8ff' }}>Description:</strong> {version.business_description}
                        </div>
                      )}
                      {version.technical_description && (
                        <div style={{ marginBottom: '0.5rem', fontStyle: 'italic', color: '#9ca3af' }}>
                          {version.technical_description}
                        </div>
                      )}
                      {version.tags && version.tags.length > 0 && (
                        <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                          {version.tags.map((tag, i) => (
                            <span
                              key={i}
                              style={{
                                fontSize: '0.6875rem',
                                padding: '0.125rem 0.5rem',
                                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                                color: '#a8d8ff',
                                borderRadius: '9999px'
                              }}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Metadata */}
                    <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(168, 216, 255, 0.1)', fontSize: '0.75rem', color: '#6b7280' }}>
                      Created: {new Date(version.created_at).toLocaleString()} • Updated: {new Date(version.updated_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Approval/Rejection Modal */}
      {approvalModal.isOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
          onClick={cancelApprovalAction}
        >
          <div
            style={{
              backgroundColor: '#1a1d2e',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              borderRadius: '0.75rem',
              padding: '2rem',
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ 
              fontSize: '1.5rem', 
              fontWeight: '600', 
              marginBottom: '1.5rem',
              color: '#f0f0f5'
            }}>
              {approvalModal.action === 'approve' ? 'Approve Entry' : 'Reject Entry'}
            </h2>

            <div style={{ marginBottom: '1.5rem' }}>
              <label
                htmlFor="approval-notes"
                style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  marginBottom: '0.5rem',
                  color: '#a8d8ff'
                }}
              >
                {approvalModal.action === 'approve' ? 'Approval notes (optional)' : 'Rejection reason (optional)'}
              </label>
              <textarea
                id="approval-notes"
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder={
                  approvalModal.action === 'approve' 
                    ? 'Add any notes about this approval...' 
                    : 'Explain why this entry is being rejected...'
                }
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  backgroundColor: '#0a0e1a',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.5rem',
                  color: '#f0f0f5',
                  fontSize: '0.875rem',
                  fontFamily: 'inherit',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                onClick={cancelApprovalAction}
                disabled={saving}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'rgba(168, 216, 255, 0.1)',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.5rem',
                  color: '#a8d8ff',
                  fontSize: '0.875rem',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.5 : 1
                }}
              >
                Cancel
              </button>
              <button
                onClick={submitApprovalAction}
                disabled={saving}
                style={{
                  padding: '0.5rem 1rem',
                  background: approvalModal.action === 'approve'
                    ? 'linear-gradient(90deg, rgba(34, 197, 94, 0.2), rgba(22, 163, 74, 0.2))'
                    : 'linear-gradient(90deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2))',
                  border: approvalModal.action === 'approve'
                    ? '1px solid rgba(34, 197, 94, 0.4)'
                    : '1px solid rgba(239, 68, 68, 0.4)',
                  borderRadius: '0.5rem',
                  color: approvalModal.action === 'approve' ? '#22c55e' : '#ef4444',
                  fontSize: '0.875rem',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.5 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {approvalModal.action === 'approve' ? 'Approving...' : 'Rejecting...'}
                  </>
                ) : (
                  <>
                    {approvalModal.action === 'approve' ? 'Approve' : 'Reject'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

