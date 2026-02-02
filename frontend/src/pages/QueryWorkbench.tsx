import { useState, useEffect } from 'react'
import {
  Database,
  Play,
  Save,
  Folder,
  Clock,
  Search,
  Plus,
  Trash2,
  Copy,
  ChevronRight,
  ChevronDown,
  Loader2,
  CheckCircle2,
  AlertCircle,
  History,
  Settings2,
  X
} from 'lucide-react'
import {
  listSavedQueries,
  getSavedQuery,
  createSavedQuery,
  updateSavedQuery,
  deleteSavedQuery,
  cloneSavedQuery,
  executeSavedQuery,
  executeWorkbenchQuery,
  getQueryExecutions,
  getQueryFolders,
  getExplorerDatabases,
  SavedQuery,
  SavedQueryListItem,
  QueryExecution,
  QueryResult,
  FolderInfo,
  QueryParameter
} from '../api/client'
import DataTable from '../components/DataTable'

interface DatabaseInfo {
  id: string
  name: string
  description: string
}

export default function QueryWorkbench() {
  // Database state
  const [databases, setDatabases] = useState<DatabaseInfo[]>([])
  const [selectedDbId, setSelectedDbId] = useState<string>('default')

  // Query list state
  const [queries, setQueries] = useState<SavedQueryListItem[]>([])
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [selectedQuery, setSelectedQuery] = useState<SavedQuery | null>(null)
  const [loadingQueries, setLoadingQueries] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  // Editor state
  const [editorSql, setEditorSql] = useState('')
  const [editorName, setEditorName] = useState('')
  const [editorDescription, setEditorDescription] = useState('')
  const [editorFolder, setEditorFolder] = useState('')
  const [editorTags, setEditorTags] = useState<string[]>([])
  const [editorParameters, setEditorParameters] = useState<QueryParameter[]>([])
  const [parameterValues, setParameterValues] = useState<Record<string, string>>({})
  const [isNewQuery, setIsNewQuery] = useState(false)
  const [isDirty, setIsDirty] = useState(false)

  // Execution state
  const [executing, setExecuting] = useState(false)
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null)
  const [executions, setExecutions] = useState<QueryExecution[]>([])
  const [loadingExecutions, setLoadingExecutions] = useState(false)

  // UI state
  const [activeTab, setActiveTab] = useState<'results' | 'history' | 'settings'>('results')
  const [saving, setSaving] = useState(false)
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load databases and queries on mount
  useEffect(() => {
    loadDatabases()
  }, [])

  useEffect(() => {
    if (selectedDbId) {
      loadQueries()
      loadFolders()
    }
  }, [selectedDbId])

  const loadDatabases = async () => {
    try {
      const dbs = await getExplorerDatabases()
      setDatabases(dbs)
      if (dbs.length > 0) {
        setSelectedDbId(dbs[0].id)
      }
    } catch (err) {
      console.error('Failed to load databases:', err)
    }
  }

  const loadQueries = async () => {
    setLoadingQueries(true)
    try {
      const result = await listSavedQueries({ db_id: selectedDbId, search: searchTerm || undefined })
      setQueries(result.queries)
    } catch (err) {
      console.error('Failed to load queries:', err)
    } finally {
      setLoadingQueries(false)
    }
  }

  const loadFolders = async () => {
    try {
      const data = await getQueryFolders(selectedDbId)
      setFolders(data)
    } catch (err) {
      console.error('Failed to load folders:', err)
    }
  }

  const selectQuery = async (queryItem: SavedQueryListItem) => {
    try {
      const query = await getSavedQuery(queryItem.id)
      setSelectedQuery(query)
      setEditorSql(query.sql)
      setEditorName(query.name)
      setEditorDescription(query.description || '')
      setEditorFolder(query.folder || '')
      setEditorTags(query.tags || [])
      setEditorParameters(query.parameters || [])
      setParameterValues({})
      setIsNewQuery(false)
      setIsDirty(false)
      setQueryResult(null)
      setActiveTab('results')

      // Load execution history
      loadExecutionHistory(query.id)
    } catch (err) {
      console.error('Failed to load query:', err)
      setError('Failed to load query')
    }
  }

  const loadExecutionHistory = async (queryId: string) => {
    setLoadingExecutions(true)
    try {
      const result = await getQueryExecutions(queryId, 20)
      setExecutions(result.executions)
    } catch (err) {
      console.error('Failed to load executions:', err)
    } finally {
      setLoadingExecutions(false)
    }
  }

  const handleNewQuery = () => {
    setSelectedQuery(null)
    setEditorSql('SELECT * FROM table_name LIMIT 100;')
    setEditorName('New Query')
    setEditorDescription('')
    setEditorFolder('')
    setEditorTags([])
    setEditorParameters([])
    setParameterValues({})
    setIsNewQuery(true)
    setIsDirty(true)
    setQueryResult(null)
    setExecutions([])
    setActiveTab('results')
  }

  const handleSqlChange = (sql: string) => {
    setEditorSql(sql)
    setIsDirty(true)

    // Auto-detect parameters like {{param_name}}
    const paramRegex = /\{\{(\w+)\}\}/g
    const matches = [...sql.matchAll(paramRegex)]
    const paramNames = [...new Set(matches.map(m => m[1]))]

    // Update parameters list
    const newParams = paramNames.map(name => {
      const existing = editorParameters.find(p => p.name === name)
      return existing || { name, type: 'string' }
    })
    setEditorParameters(newParams)
  }

  const executeQuery = async () => {
    setExecuting(true)
    setError(null)
    setActiveTab('results')

    try {
      let result: QueryResult

      if (selectedQuery && !isDirty) {
        // Execute saved query
        result = await executeSavedQuery(selectedQuery.id, {
          parameters: Object.keys(parameterValues).length > 0 ? parameterValues : undefined
        })
      } else {
        // Execute ad-hoc or modified query
        let sql = editorSql
        // Substitute parameters for ad-hoc execution
        for (const [name, value] of Object.entries(parameterValues)) {
          sql = sql.replace(new RegExp(`\\{\\{${name}\\}\\}`, 'g'), `'${value}'`)
        }
        result = await executeWorkbenchQuery({
          sql,
          db_id: selectedDbId
        })
      }

      setQueryResult(result)

      // Reload execution history if we have a saved query
      if (selectedQuery) {
        loadExecutionHistory(selectedQuery.id)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Query execution failed')
      setQueryResult(null)
    } finally {
      setExecuting(false)
    }
  }

  const saveQuery = async () => {
    setSaving(true)
    setError(null)

    try {
      if (isNewQuery) {
        const newQuery = await createSavedQuery({
          name: editorName,
          sql: editorSql,
          db_id: selectedDbId,
          description: editorDescription || undefined,
          folder: editorFolder || undefined,
          tags: editorTags.length > 0 ? editorTags : undefined,
          parameters: editorParameters.length > 0 ? editorParameters : undefined
        })
        setSelectedQuery(newQuery)
        setIsNewQuery(false)
      } else if (selectedQuery) {
        const updated = await updateSavedQuery(selectedQuery.id, {
          name: editorName,
          sql: editorSql,
          description: editorDescription || undefined,
          folder: editorFolder || undefined,
          tags: editorTags.length > 0 ? editorTags : undefined,
          parameters: editorParameters.length > 0 ? editorParameters : undefined
        })
        setSelectedQuery(updated)
      }

      setIsDirty(false)
      setShowSaveModal(false)
      loadQueries()
      loadFolders()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save query')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedQuery) return
    if (!confirm(`Delete query "${selectedQuery.name}"?`)) return

    try {
      await deleteSavedQuery(selectedQuery.id)
      setSelectedQuery(null)
      setEditorSql('')
      setEditorName('')
      setQueryResult(null)
      loadQueries()
      loadFolders()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete query')
    }
  }

  const handleClone = async () => {
    if (!selectedQuery) return
    const newName = prompt('Name for cloned query:', `${selectedQuery.name} (Copy)`)
    if (!newName) return

    try {
      const cloned = await cloneSavedQuery(selectedQuery.id, newName)
      await selectQuery(cloned)
      loadQueries()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to clone query')
    }
  }

  const toggleFolder = (folderName: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(folderName)) {
      newExpanded.delete(folderName)
    } else {
      newExpanded.add(folderName)
    }
    setExpandedFolders(newExpanded)
  }

  // Group queries by folder
  const queriesByFolder = queries.reduce((acc, q) => {
    const folder = q.folder || '__none__'
    if (!acc[folder]) acc[folder] = []
    acc[folder].push(q)
    return acc
  }, {} as Record<string, SavedQueryListItem[]>)

  return (
    <div className="space-y-6" style={{ maxWidth: '100vw', overflow: 'hidden' }}>
      {/* Header */}
      <div className="text-left space-y-4">
        <div>
          <h1
            className="text-5xl font-bold"
            style={{
              background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 50%, #ffc4e5 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Query Workbench
          </h1>
          <p className="mt-2" style={{ color: '#b0b8c0' }}>
            Save, organize, and execute reusable SQL queries
          </p>
        </div>

        {/* Database Selector */}
        {databases.length > 1 && (
          <div className="flex items-center space-x-3">
            <label className="text-sm font-medium" style={{ color: '#a8d8ff' }}>
              Database:
            </label>
            <select
              value={selectedDbId}
              onChange={(e) => setSelectedDbId(e.target.value)}
              className="px-4 py-2 rounded-lg transition-colors cursor-pointer"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.1)',
                color: '#f0f0f5',
                border: '1px solid rgba(168, 216, 255, 0.3)',
              }}
            >
              {databases.map((db) => (
                <option key={db.id} value={db.id} style={{ backgroundColor: '#1a1a24' }}>
                  {db.name} ({db.description})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex gap-6" style={{ minHeight: '600px' }}>
        {/* Left Sidebar: Saved Queries */}
        <div
          className="w-80 flex-shrink-0 rounded-xl p-4 overflow-y-auto"
          style={{
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(168, 216, 255, 0.15)',
            maxHeight: '700px'
          }}
        >
          {/* Search and New */}
          <div className="space-y-3 mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4" style={{ color: '#8090a0' }} />
              <input
                type="text"
                placeholder="Search queries..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadQueries()}
                className="w-full pl-10 pr-4 py-2 rounded-lg text-sm"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.05)',
                  color: '#f0f0f5',
                  border: '1px solid rgba(168, 216, 255, 0.2)'
                }}
              />
            </div>
            <button
              onClick={handleNewQuery}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg transition-colors"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                color: '#a8d8ff',
                border: '1px solid rgba(168, 216, 255, 0.3)'
              }}
            >
              <Plus className="h-4 w-4" />
              <span>New Query</span>
            </button>
          </div>

          {/* Query List */}
          {loadingQueries ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin" style={{ color: '#a8d8ff' }} />
            </div>
          ) : (
            <div className="space-y-1">
              {/* Folders */}
              {folders.map((folder) => (
                <div key={folder.name}>
                  <button
                    onClick={() => toggleFolder(folder.name)}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors"
                    style={{
                      backgroundColor: expandedFolders.has(folder.name) ? 'rgba(168, 216, 255, 0.1)' : 'transparent',
                      color: '#f0f0f5'
                    }}
                  >
                    <div className="flex items-center space-x-2">
                      {expandedFolders.has(folder.name) ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                      <Folder className="h-4 w-4" style={{ color: '#ffc4e5' }} />
                      <span className="text-sm">{folder.name}</span>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.15)', color: '#a8d8ff' }}>
                      {folder.query_count}
                    </span>
                  </button>

                  {expandedFolders.has(folder.name) && queriesByFolder[folder.name] && (
                    <div className="ml-6 mt-1 space-y-1">
                      {queriesByFolder[folder.name].map((q) => (
                        <button
                          key={q.id}
                          onClick={() => selectQuery(q)}
                          className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left"
                          style={{
                            backgroundColor: selectedQuery?.id === q.id ? 'rgba(196, 181, 253, 0.15)' : 'transparent',
                            color: '#f0f0f5'
                          }}
                        >
                          <span className="text-sm truncate">{q.name}</span>
                          {q.run_count > 0 && (
                            <span className="text-xs" style={{ color: '#8090a0' }}>
                              {q.run_count}x
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Unfiled queries */}
              {queriesByFolder['__none__'] && (
                <div className="pt-2 border-t" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
                  <div className="text-xs px-3 py-1" style={{ color: '#8090a0' }}>Unfiled</div>
                  {queriesByFolder['__none__'].map((q) => (
                    <button
                      key={q.id}
                      onClick={() => selectQuery(q)}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left"
                      style={{
                        backgroundColor: selectedQuery?.id === q.id ? 'rgba(196, 181, 253, 0.15)' : 'transparent',
                        color: '#f0f0f5'
                      }}
                    >
                      <span className="text-sm truncate">{q.name}</span>
                      {q.run_count > 0 && (
                        <span className="text-xs" style={{ color: '#8090a0' }}>
                          {q.run_count}x
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}

              {queries.length === 0 && !loadingQueries && (
                <div className="text-center py-8" style={{ color: '#8090a0' }}>
                  <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No saved queries yet</p>
                  <p className="text-xs mt-1">Click "New Query" to get started</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Main Editor Area */}
        <div className="flex-1" style={{ minWidth: 0 }}>
          <div
            className="rounded-xl"
            style={{
              backgroundColor: '#1a1a24',
              border: '1px solid rgba(168, 216, 255, 0.15)'
            }}
          >
            {/* Toolbar */}
            <div
              className="flex items-center justify-between px-4 py-3 border-b"
              style={{ borderColor: 'rgba(168, 216, 255, 0.15)' }}
            >
              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  value={editorName}
                  onChange={(e) => { setEditorName(e.target.value); setIsDirty(true) }}
                  className="bg-transparent text-lg font-semibold focus:outline-none"
                  style={{ color: '#f0f0f5', minWidth: '200px' }}
                  placeholder="Query name..."
                />
                {isDirty && (
                  <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: 'rgba(251, 191, 36, 0.2)', color: '#fbbf24' }}>
                    Unsaved
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={executeQuery}
                  disabled={executing || !editorSql.trim()}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors disabled:opacity-30"
                  style={{
                    backgroundColor: 'rgba(34, 197, 94, 0.15)',
                    color: '#22c55e',
                    border: '1px solid rgba(34, 197, 94, 0.3)'
                  }}
                >
                  {executing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Running...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      <span>Run</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => setShowSaveModal(true)}
                  disabled={!editorSql.trim()}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors disabled:opacity-30"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.15)',
                    color: '#a8d8ff',
                    border: '1px solid rgba(168, 216, 255, 0.3)'
                  }}
                >
                  <Save className="h-4 w-4" />
                  <span>Save</span>
                </button>
                {selectedQuery && (
                  <>
                    <button
                      onClick={handleClone}
                      className="p-2 rounded-lg transition-colors"
                      style={{ color: '#b0b8c0' }}
                      title="Clone query"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                    <button
                      onClick={handleDelete}
                      className="p-2 rounded-lg transition-colors"
                      style={{ color: '#ff6b6b' }}
                      title="Delete query"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* SQL Editor */}
            <div className="p-4">
              <textarea
                value={editorSql}
                onChange={(e) => handleSqlChange(e.target.value)}
                className="w-full p-4 rounded-lg font-mono text-sm"
                style={{
                  backgroundColor: '#0d0d14',
                  color: '#f0f0f5',
                  border: '1px solid rgba(168, 216, 255, 0.2)',
                  minHeight: '200px',
                  resize: 'vertical'
                }}
                placeholder="SELECT * FROM table_name LIMIT 100;"
              />

              {/* Parameters */}
              {editorParameters.length > 0 && (
                <div className="mt-4 p-4 rounded-lg" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                  <div className="flex items-center space-x-2 mb-3">
                    <Settings2 className="h-4 w-4" style={{ color: '#a8d8ff' }} />
                    <span className="text-sm font-medium" style={{ color: '#a8d8ff' }}>Parameters</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    {editorParameters.map((param) => (
                      <div key={param.name}>
                        <label className="text-xs block mb-1" style={{ color: '#b0b8c0' }}>
                          {`{{${param.name}}}`}
                        </label>
                        <input
                          type="text"
                          value={parameterValues[param.name] || param.default || ''}
                          onChange={(e) => setParameterValues({ ...parameterValues, [param.name]: e.target.value })}
                          placeholder={param.description || param.name}
                          className="w-full px-3 py-2 rounded text-sm"
                          style={{
                            backgroundColor: '#0d0d14',
                            color: '#f0f0f5',
                            border: '1px solid rgba(168, 216, 255, 0.2)'
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Tabs */}
            <div
              className="flex border-t"
              style={{ borderColor: 'rgba(168, 216, 255, 0.15)' }}
            >
              {(['results', 'history', 'settings'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className="px-6 py-3 font-medium transition-colors capitalize flex items-center space-x-2"
                  style={{
                    backgroundColor: activeTab === tab ? 'rgba(168, 216, 255, 0.1)' : 'transparent',
                    color: activeTab === tab ? '#a8d8ff' : '#b0b8c0',
                    borderBottom: activeTab === tab ? '2px solid #a8d8ff' : 'none'
                  }}
                >
                  {tab === 'results' && <CheckCircle2 className="h-4 w-4" />}
                  {tab === 'history' && <History className="h-4 w-4" />}
                  {tab === 'settings' && <Settings2 className="h-4 w-4" />}
                  <span>{tab}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="p-4" style={{ minHeight: '300px' }}>
              {/* Results Tab */}
              {activeTab === 'results' && (
                <>
                  {error && (
                    <div
                      className="p-4 rounded-lg mb-4"
                      style={{ backgroundColor: 'rgba(255, 107, 107, 0.1)', border: '1px solid rgba(255, 107, 107, 0.3)' }}
                    >
                      <div className="flex items-start space-x-2">
                        <AlertCircle className="h-5 w-5 flex-shrink-0" style={{ color: '#ff6b6b' }} />
                        <div>
                          <p className="font-semibold" style={{ color: '#ff6b6b' }}>Error</p>
                          <p className="text-sm mt-1" style={{ color: '#b0b8c0' }}>{error}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {queryResult ? (
                    <div className="space-y-4">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          <CheckCircle2 className="h-5 w-5" style={{ color: '#22c55e' }} />
                          <span className="text-sm font-medium" style={{ color: '#22c55e' }}>
                            Query successful
                          </span>
                        </div>
                        <span className="text-sm" style={{ color: '#b0b8c0' }}>
                          {queryResult.total_rows} rows in {queryResult.execution_time_ms.toFixed(1)}ms
                        </span>
                      </div>
                      <DataTable
                        data={queryResult.rows}
                        columns={queryResult.columns}
                        totalRows={queryResult.total_rows}
                        currentPage={queryResult.page}
                        pageSize={queryResult.page_size}
                        onPageChange={() => {}}
                      />
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-48" style={{ color: '#8090a0' }}>
                      <Play className="h-12 w-12 mb-4 opacity-30" />
                      <p>Run a query to see results</p>
                    </div>
                  )}
                </>
              )}

              {/* History Tab */}
              {activeTab === 'history' && (
                <>
                  {loadingExecutions ? (
                    <div className="flex items-center justify-center h-48">
                      <Loader2 className="h-6 w-6 animate-spin" style={{ color: '#a8d8ff' }} />
                    </div>
                  ) : executions.length > 0 ? (
                    <div className="space-y-2">
                      {executions.map((exec) => (
                        <div
                          key={exec.id}
                          className="p-3 rounded-lg flex items-center justify-between"
                          style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                        >
                          <div className="flex items-center space-x-3">
                            {exec.status === 'success' ? (
                              <CheckCircle2 className="h-4 w-4" style={{ color: '#22c55e' }} />
                            ) : exec.status === 'error' ? (
                              <AlertCircle className="h-4 w-4" style={{ color: '#ff6b6b' }} />
                            ) : (
                              <Loader2 className="h-4 w-4 animate-spin" style={{ color: '#a8d8ff' }} />
                            )}
                            <div>
                              <p className="text-sm" style={{ color: '#f0f0f5' }}>
                                {exec.status === 'success'
                                  ? `${exec.row_count} rows in ${exec.execution_time_ms?.toFixed(1)}ms`
                                  : exec.status === 'error'
                                  ? exec.error_message?.substring(0, 50)
                                  : 'Running...'}
                              </p>
                              <p className="text-xs" style={{ color: '#8090a0' }}>
                                {new Date(exec.started_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                          <span
                            className="text-xs px-2 py-1 rounded"
                            style={{
                              backgroundColor: exec.source === 'manual' ? 'rgba(168, 216, 255, 0.15)' : 'rgba(196, 181, 253, 0.15)',
                              color: exec.source === 'manual' ? '#a8d8ff' : '#c4b5fd'
                            }}
                          >
                            {exec.source}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-48" style={{ color: '#8090a0' }}>
                      <Clock className="h-12 w-12 mb-4 opacity-30" />
                      <p>No execution history yet</p>
                    </div>
                  )}
                </>
              )}

              {/* Settings Tab */}
              {activeTab === 'settings' && selectedQuery && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm block mb-1" style={{ color: '#a8d8ff' }}>Description</label>
                    <textarea
                      value={editorDescription}
                      onChange={(e) => { setEditorDescription(e.target.value); setIsDirty(true) }}
                      className="w-full p-3 rounded-lg text-sm"
                      style={{
                        backgroundColor: '#0d0d14',
                        color: '#f0f0f5',
                        border: '1px solid rgba(168, 216, 255, 0.2)',
                        minHeight: '80px'
                      }}
                      placeholder="Describe what this query does..."
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm block mb-1" style={{ color: '#a8d8ff' }}>Folder</label>
                      <input
                        type="text"
                        value={editorFolder}
                        onChange={(e) => { setEditorFolder(e.target.value); setIsDirty(true) }}
                        className="w-full px-3 py-2 rounded-lg text-sm"
                        style={{
                          backgroundColor: '#0d0d14',
                          color: '#f0f0f5',
                          border: '1px solid rgba(168, 216, 255, 0.2)'
                        }}
                        placeholder="e.g., Analytics, Reports"
                      />
                    </div>
                    <div>
                      <label className="text-sm block mb-1" style={{ color: '#a8d8ff' }}>Tags (comma-separated)</label>
                      <input
                        type="text"
                        value={editorTags.join(', ')}
                        onChange={(e) => {
                          setEditorTags(e.target.value.split(',').map(t => t.trim()).filter(Boolean))
                          setIsDirty(true)
                        }}
                        className="w-full px-3 py-2 rounded-lg text-sm"
                        style={{
                          backgroundColor: '#0d0d14',
                          color: '#f0f0f5',
                          border: '1px solid rgba(168, 216, 255, 0.2)'
                        }}
                        placeholder="e.g., revenue, monthly"
                      />
                    </div>
                  </div>
                  {selectedQuery && (
                    <div className="pt-4 border-t" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
                      <h4 className="text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>Query Stats</h4>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p style={{ color: '#8090a0' }}>Run Count</p>
                          <p style={{ color: '#f0f0f5' }}>{selectedQuery.run_count}</p>
                        </div>
                        <div>
                          <p style={{ color: '#8090a0' }}>Avg Time</p>
                          <p style={{ color: '#f0f0f5' }}>
                            {selectedQuery.avg_execution_time_ms ? `${selectedQuery.avg_execution_time_ms.toFixed(1)}ms` : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p style={{ color: '#8090a0' }}>Last Run</p>
                          <p style={{ color: '#f0f0f5' }}>
                            {selectedQuery.last_run_at ? new Date(selectedQuery.last_run_at).toLocaleDateString() : 'Never'}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}>
          <div
            className="w-full max-w-md rounded-xl p-6"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: '#f0f0f5' }}>Save Query</h3>
              <button onClick={() => setShowSaveModal(false)}>
                <X className="h-5 w-5" style={{ color: '#8090a0' }} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm block mb-1" style={{ color: '#a8d8ff' }}>Name *</label>
                <input
                  type="text"
                  value={editorName}
                  onChange={(e) => setEditorName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0d0d14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.2)'
                  }}
                />
              </div>
              <div>
                <label className="text-sm block mb-1" style={{ color: '#a8d8ff' }}>Description</label>
                <textarea
                  value={editorDescription}
                  onChange={(e) => setEditorDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg"
                  rows={3}
                  style={{
                    backgroundColor: '#0d0d14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.2)'
                  }}
                />
              </div>
              <div>
                <label className="text-sm block mb-1" style={{ color: '#a8d8ff' }}>Folder</label>
                <input
                  type="text"
                  value={editorFolder}
                  onChange={(e) => setEditorFolder(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0d0d14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.2)'
                  }}
                  placeholder="e.g., Analytics"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  onClick={() => setShowSaveModal(false)}
                  className="px-4 py-2 rounded-lg"
                  style={{ color: '#b0b8c0' }}
                >
                  Cancel
                </button>
                <button
                  onClick={saveQuery}
                  disabled={saving || !editorName.trim()}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg disabled:opacity-30"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.15)',
                    color: '#a8d8ff',
                    border: '1px solid rgba(168, 216, 255, 0.3)'
                  }}
                >
                  {saving ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      <span>Save</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
