import { useState, useEffect } from 'react'
import { 
  Database, 
  Table2, 
  Play, 
  AlertCircle, 
  ChevronRight,
  ChevronDown,
  Loader2,
  CheckCircle2,
  Info
} from 'lucide-react'
import {
  getExplorerDatabases,
  getExplorerHealth,
  getExplorerSchemas,
  getExplorerTables,
  getExplorerTableColumns,
  getExplorerTableRows,
  getExplorerTableSummary,
  executeExplorerQuery,
} from '../api/client'
import DataTable from '../components/DataTable'
import AIAnalysisTab from '../components/AIAnalysisTab'

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

interface Column {
  name: string
  data_type: string
  is_nullable: boolean
  default?: string
  ordinal_position: number
}

interface TableRowsResponse {
  schema: string
  table: string
  columns: string[]
  rows: any[][]
  page: number
  page_size: number
  total_rows?: number
}

interface QueryResponse {
  columns: string[]
  rows: any[][]
  total_rows_estimate?: number
  execution_time_ms: number
  error?: {
    message: string
    code?: string
  }
}

export default function DataExplorer() {
  // Database selection state
  const [databases, setDatabases] = useState<DatabaseInfo[]>([])
  const [selectedDbId, setSelectedDbId] = useState<string>('default')
  
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [connectionError, setConnectionError] = useState<string>('')
  
  // Schema/Table state
  const [schemas, setSchemas] = useState<Schema[]>([])
  const [expandedSchemas, setExpandedSchemas] = useState<Set<string>>(new Set(['public']))
  const [tablesBySchema, setTablesBySchema] = useState<Record<string, Table[]>>({})
  
  // Selected table state
  const [selectedTable, setSelectedTable] = useState<Table | null>(null)
  const [columns, setColumns] = useState<Column[]>([])
  const [tableRows, setTableRows] = useState<TableRowsResponse | null>(null)
  const [tablePage, setTablePage] = useState(1)
  const [loadingTable, setLoadingTable] = useState(false)
  
  // Query editor state
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [executingQuery, setExecutingQuery] = useState(false)
  const [queryPage, setQueryPage] = useState(1)
  
  // Active tab
  const [activeTab, setActiveTab] = useState<'preview' | 'columns' | 'query' | 'summary' | 'ai-analysis'>('preview')
  const [summary, setSummary] = useState<any>(null)
  const [loadingSummary, setLoadingSummary] = useState(false)

  useEffect(() => {
    loadDatabases()
  }, [])

  useEffect(() => {
    if (selectedDbId) {
      checkConnection()
    }
  }, [selectedDbId])

  const loadDatabases = async () => {
    try {
      const dbs = await getExplorerDatabases()
      setDatabases(dbs)
      if (dbs.length > 0) {
        setSelectedDbId(dbs[0].id)
      }
    } catch (error) {
      console.error('Failed to load databases:', error)
      setLoading(false)
    }
  }

  const checkConnection = async () => {
    setLoading(true)
    setConnected(false)
    setSchemas([])
    setTablesBySchema({})
    setSelectedTable(null)
    
    try {
      const health = await getExplorerHealth(selectedDbId)
      setConnected(health.connected)
      if (!health.connected) {
        setConnectionError(health.error || 'Unknown connection error')
      } else {
        loadSchemas()
      }
    } catch (error: any) {
      setConnected(false)
      setConnectionError(error.message || 'Failed to connect to database')
    } finally {
      setLoading(false)
    }
  }

  const loadSchemas = async () => {
    try {
      const data = await getExplorerSchemas(selectedDbId)
      setSchemas(data)
      // Auto-load public schema tables
      if (data.some((s: Schema) => s.name === 'public')) {
        loadTables('public')
      }
    } catch (error) {
      console.error('Failed to load schemas:', error)
    }
  }

  const loadTables = async (schema: string) => {
    if (tablesBySchema[schema]) return // Already loaded
    
    try {
      const tables = await getExplorerTables(schema, selectedDbId)
      setTablesBySchema(prev => ({ ...prev, [schema]: tables }))
    } catch (error) {
      console.error(`Failed to load tables for ${schema}:`, error)
    }
  }

  const toggleSchema = (schemaName: string) => {
    const newExpanded = new Set(expandedSchemas)
    if (newExpanded.has(schemaName)) {
      newExpanded.delete(schemaName)
    } else {
      newExpanded.add(schemaName)
      loadTables(schemaName)
    }
    setExpandedSchemas(newExpanded)
  }

  const selectTable = async (table: Table) => {
    setSelectedTable(table)
    setActiveTab('preview')
    setTablePage(1)
    setQuery(`SELECT * FROM ${table.schema}.${table.name} LIMIT 100;`)
    loadTableData(table, 1)
  }

  const loadTableData = async (table: Table, page: number) => {
    setLoadingTable(true)
    try {
      const [colData, rowData] = await Promise.all([
        getExplorerTableColumns(table.schema, table.name, selectedDbId),
        getExplorerTableRows(table.schema, table.name, page, 50, selectedDbId),
      ])
      setColumns(colData)
      setTableRows(rowData)
    } catch (error) {
      console.error('Failed to load table data:', error)
    } finally {
      setLoadingTable(false)
    }
  }

  const loadTableSummary = async () => {
    if (!selectedTable) return
    setLoadingSummary(true)
    try {
      const data = await getExplorerTableSummary(selectedTable.schema, selectedTable.name, selectedDbId)
      setSummary(data)
    } catch (error) {
      console.error('Failed to load summary:', error)
    } finally {
      setLoadingSummary(false)
    }
  }

  const executeQuery = async () => {
    if (!query.trim()) return
    
    setExecutingQuery(true)
    setQueryPage(1)
    try {
      const result = await executeExplorerQuery(query, 1, 100, selectedDbId)
      setQueryResult(result)
    } catch (error: any) {
      setQueryResult({
        columns: [],
        rows: [],
        execution_time_ms: 0,
        error: {
          message: error.message || 'Failed to execute query',
          code: 'NETWORK_ERROR',
        },
      })
    } finally {
      setExecutingQuery(false)
    }
  }

  const handleTablePageChange = (newPage: number) => {
    if (!selectedTable) return
    setTablePage(newPage)
    loadTableData(selectedTable, newPage)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff' }} />
      </div>
    )
  }

  if (!connected) {
    return (
      <div className="space-y-8">
        <div className="text-left">
          <h1 
            className="text-5xl font-bold"
            style={{
              background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 50%, #ffc4e5 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Data Explorer
          </h1>
          <p className="mt-2" style={{ color: '#b0b8c0' }}>Browse and query your Postgres database</p>
        </div>

        <div 
          className="rounded-xl p-6"
          style={{ 
            backgroundColor: '#1a1a24', 
            border: '1px solid rgba(255, 107, 107, 0.3)' 
          }}
        >
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-6 w-6 flex-shrink-0" style={{ color: '#ff6b6b' }} />
            <div>
              <h3 className="text-lg font-semibold" style={{ color: '#ff6b6b' }}>
                Database Connection Failed
              </h3>
              <p className="mt-2" style={{ color: '#b0b8c0' }}>
                {connectionError}
              </p>
              <p className="mt-4 text-sm" style={{ color: '#8090a0' }}>
                Please ensure the following environment variables are set correctly:
              </p>
              <ul className="mt-2 space-y-1 text-sm" style={{ color: '#8090a0' }}>
                <li>• EXPLORER_DB_HOST</li>
                <li>• EXPLORER_DB_PORT</li>
                <li>• EXPLORER_DB_USER</li>
                <li>• EXPLORER_DB_PASSWORD</li>
                <li>• EXPLORER_DB_NAME</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6" style={{ maxWidth: '100vw', overflow: 'hidden' }}>
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
            Data Explorer
          </h1>
          <p className="mt-2" style={{ color: '#b0b8c0' }}>Browse and query your Postgres database</p>
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

      {/* Empty State - No Databases */}
      {!loading && databases.length === 0 && (
        <div className="flex items-center justify-center" style={{ minHeight: '500px' }}>
          <div className="text-center max-w-md p-8 rounded-xl" style={{
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(168, 216, 255, 0.2)'
          }}>
            <Database size={64} className="mx-auto mb-4 opacity-50" style={{ color: '#a8d8ff' }} />
            <h2 className="text-2xl font-bold mb-2" style={{ color: '#f0f0f5' }}>
              No Databases Configured
            </h2>
            <p className="mb-4" style={{ color: '#b0b8c0' }}>
              To get started with the Data Explorer, you need to configure at least one database connection.
            </p>
            <p className="text-sm" style={{ color: '#8ab3cc' }}>
              Configure your database connections in <code className="px-2 py-1 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>.env</code> file or add them to the <code className="px-2 py-1 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>db_configs.py</code> file.
            </p>
          </div>
        </div>
      )}

      {databases.length > 0 && (
      <div className="flex gap-6" style={{ minHeight: '600px', width: '100%', maxWidth: 'calc(100vw - 4rem)' }}>
        {/* Left Sidebar: Schema & Tables */}
        <div 
          className="w-80 flex-shrink-0 rounded-xl p-4 overflow-y-auto"
          style={{ 
            backgroundColor: '#1a1a24', 
            border: '1px solid rgba(168, 216, 255, 0.15)',
            maxHeight: '700px',
            width: '320px'
          }}
        >
          <div className="flex items-center space-x-2 mb-4 pb-3 border-b" style={{ borderColor: 'rgba(168, 216, 255, 0.15)' }}>
            <Database className="h-5 w-5" style={{ color: '#a8d8ff' }} />
            <h2 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Schemas & Tables</h2>
          </div>

          <div className="space-y-1">
            {schemas.map((schema) => (
              <div key={schema.name}>
                <button
                  onClick={() => toggleSchema(schema.name)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors hover:bg-opacity-80"
                  style={{ 
                    backgroundColor: expandedSchemas.has(schema.name) ? 'rgba(168, 216, 255, 0.1)' : 'transparent',
                    color: '#f0f0f5'
                  }}
                >
                  <div className="flex items-center space-x-2">
                    {expandedSchemas.has(schema.name) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    <span className="font-medium">{schema.name}</span>
                  </div>
                  {schema.table_count !== undefined && (
                    <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.15)', color: '#a8d8ff' }}>
                      {schema.table_count}
                    </span>
                  )}
                </button>

                {expandedSchemas.has(schema.name) && tablesBySchema[schema.name] && (
                  <div className="ml-6 mt-1 space-y-1">
                    {tablesBySchema[schema.name].map((table) => (
                      <button
                        key={`${table.schema}.${table.name}`}
                        onClick={() => selectTable(table)}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left"
                        style={{
                          backgroundColor: selectedTable?.name === table.name && selectedTable?.schema === table.schema
                            ? 'rgba(196, 181, 253, 0.15)'
                            : 'transparent',
                          color: '#f0f0f5'
                        }}
                      >
                        <div className="flex items-center space-x-2">
                          <Table2 className="h-4 w-4" style={{ color: '#c4b5fd' }} />
                          <span className="text-sm">{table.name}</span>
                        </div>
                        {table.row_estimate !== null && table.row_estimate !== undefined && (
                          <span className="text-xs" style={{ color: '#8090a0' }}>
                            ~{table.row_estimate.toLocaleString()}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1" style={{ minWidth: 0, width: 'calc(100% - 344px)', maxWidth: 'calc(100% - 344px)', overflow: 'hidden' }}>
          {selectedTable ? (
            <div className="space-y-4">
              {/* Table Header */}
              <div 
                className="rounded-xl p-4"
                style={{ 
                  backgroundColor: '#1a1a24', 
                  border: '1px solid rgba(168, 216, 255, 0.15)' 
                }}
              >
                <h2 
                  className="text-2xl font-bold"
                  style={{
                    background: 'linear-gradient(90deg, #a8d8ff, #c4b5fd)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  {selectedTable.schema}.{selectedTable.name}
                </h2>
                <p className="text-sm mt-1" style={{ color: '#b0b8c0' }}>
                  {selectedTable.type === 'table' ? 'Table' : 'View'} • {columns.length} columns
                  {selectedTable.row_estimate && ` • ~${selectedTable.row_estimate.toLocaleString()} rows`}
                </p>
              </div>

              {/* Tabs */}
              <div 
                className="rounded-xl"
                style={{ 
                  backgroundColor: '#1a1a24', 
                  border: '1px solid rgba(168, 216, 255, 0.15)',
                  width: '100%',
                  maxWidth: '100%',
                  overflow: 'hidden'
                }}
              >
                <div 
                  className="flex border-b"
                  style={{ borderColor: 'rgba(168, 216, 255, 0.15)' }}
                >
                  {(['preview', 'columns', 'query', 'summary', 'ai-analysis'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => {
                        setActiveTab(tab)
                        if (tab === 'summary' && !summary) {
                          loadTableSummary()
                        }
                      }}
                      className="px-6 py-3 font-medium transition-colors capitalize"
                      style={{
                        backgroundColor: activeTab === tab ? 'rgba(168, 216, 255, 0.1)' : 'transparent',
                        color: activeTab === tab ? '#a8d8ff' : '#b0b8c0',
                        borderBottom: activeTab === tab ? '2px solid #a8d8ff' : 'none',
                      }}
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                <div className="p-6" style={{ width: '100%', maxWidth: '100%', overflow: 'hidden' }}>
                  {/* Preview Tab */}
                  {activeTab === 'preview' && (
                    <div className="space-y-4">
                      {loadingTable ? (
                        <div className="flex items-center justify-center h-64">
                          <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff' }} />
                        </div>
                      ) : tableRows ? (
                        <DataTable
                          data={tableRows.rows}
                          columns={tableRows.columns}
                          totalRows={tableRows.total_rows}
                          currentPage={tablePage}
                          pageSize={50}
                          onPageChange={handleTablePageChange}
                        />
                      ) : null}
                    </div>
                  )}

                  {/* Columns Tab */}
                  {activeTab === 'columns' && (
                    <div className="space-y-2">
                      {columns.map((col) => (
                        <div
                          key={col.name}
                          className="p-4 rounded-lg"
                          style={{
                            backgroundColor: 'rgba(168, 216, 255, 0.05)',
                            border: '1px solid rgba(168, 216, 255, 0.1)',
                          }}
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-semibold" style={{ color: '#f0f0f5' }}>
                                {col.name}
                              </h4>
                              <p className="text-sm mt-1" style={{ color: '#b0b8c0' }}>
                                {col.data_type}
                                {!col.is_nullable && ' • NOT NULL'}
                                {col.default && ` • Default: ${col.default}`}
                              </p>
                            </div>
                            <span 
                              className="text-xs px-2 py-1 rounded"
                              style={{ backgroundColor: 'rgba(196, 181, 253, 0.15)', color: '#c4b5fd' }}
                            >
                              {col.ordinal_position}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Query Tab */}
                  {activeTab === 'query' && (
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium" style={{ color: '#a8d8ff' }}>
                            SQL Query
                          </label>
                          <button
                            onClick={executeQuery}
                            disabled={executingQuery || !query.trim()}
                            className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors disabled:opacity-30"
                            style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.15)',
                              color: '#a8d8ff',
                              border: '1px solid rgba(168, 216, 255, 0.3)',
                            }}
                          >
                            {executingQuery ? (
                              <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span>Running...</span>
                              </>
                            ) : (
                              <>
                                <Play className="h-4 w-4" />
                                <span>Run Query</span>
                              </>
                            )}
                          </button>
                        </div>
                        <textarea
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          className="w-full p-4 rounded-lg font-mono text-sm"
                          style={{
                            backgroundColor: '#0d0d14',
                            color: '#f0f0f5',
                            border: '1px solid rgba(168, 216, 255, 0.2)',
                            minHeight: '150px',
                          }}
                          placeholder="SELECT * FROM schema.table LIMIT 100;"
                        />
                        <p className="text-xs mt-2" style={{ color: '#8090a0' }}>
                          Only SELECT queries are allowed. Maximum 1000 rows per query.
                        </p>
                      </div>

                      {queryResult && (
                        <div className="space-y-4">
                          {queryResult.error ? (
                            <div 
                              className="p-4 rounded-lg"
                              style={{ 
                                backgroundColor: 'rgba(255, 107, 107, 0.1)', 
                                border: '1px solid rgba(255, 107, 107, 0.3)' 
                              }}
                            >
                              <div className="flex items-start space-x-2">
                                <AlertCircle className="h-5 w-5 flex-shrink-0" style={{ color: '#ff6b6b' }} />
                                <div>
                                  <p className="font-semibold" style={{ color: '#ff6b6b' }}>Query Error</p>
                                  <p className="text-sm mt-1" style={{ color: '#b0b8c0' }}>
                                    {queryResult.error.message}
                                  </p>
                                  {queryResult.error.code && (
                                    <p className="text-xs mt-1" style={{ color: '#8090a0' }}>
                                      Code: {queryResult.error.code}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-4">
                                  <div className="flex items-center space-x-2">
                                    <CheckCircle2 className="h-5 w-5" style={{ color: '#c7f5d4' }} />
                                    <span className="text-sm font-medium" style={{ color: '#c7f5d4' }}>
                                      Query successful
                                    </span>
                                  </div>
                                  <span className="text-sm" style={{ color: '#b0b8c0' }}>
                                    {queryResult.total_rows_estimate} rows • {queryResult.execution_time_ms}ms
                                  </span>
                                </div>
                              </div>

                              <DataTable
                                data={queryResult.rows}
                                columns={queryResult.columns}
                                totalRows={queryResult.total_rows_estimate}
                                currentPage={1}
                                pageSize={queryResult.rows.length}
                                onPageChange={() => {}}
                              />
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Summary Tab */}
                  {activeTab === 'summary' && (
                    <div className="space-y-4">
                      {loadingSummary ? (
                        <div className="flex items-center justify-center h-64">
                          <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff' }} />
                        </div>
                      ) : summary ? (
                        <div className="space-y-4">
                          {Object.entries(summary.column_stats).map(([colName, stats]: [string, any]) => (
                            <div
                              key={colName}
                              className="p-4 rounded-lg"
                              style={{
                                backgroundColor: 'rgba(168, 216, 255, 0.05)',
                                border: '1px solid rgba(168, 216, 255, 0.1)',
                              }}
                            >
                              <h4 className="font-semibold mb-2" style={{ color: '#f0f0f5' }}>
                                {colName}
                              </h4>
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span style={{ color: '#b0b8c0' }}>Type:</span>{' '}
                                  <span style={{ color: '#c4b5fd' }}>{stats.data_type}</span>
                                </div>
                                {stats.distinct_count && (
                                  <div>
                                    <span style={{ color: '#b0b8c0' }}>Distinct:</span>{' '}
                                    <span style={{ color: '#c4b5fd' }}>{stats.distinct_count}</span>
                                  </div>
                                )}
                                {stats.min !== null && stats.min !== undefined && (
                                  <>
                                    <div>
                                      <span style={{ color: '#b0b8c0' }}>Min:</span>{' '}
                                      <span style={{ color: '#c4b5fd' }}>{stats.min}</span>
                                    </div>
                                    <div>
                                      <span style={{ color: '#b0b8c0' }}>Max:</span>{' '}
                                      <span style={{ color: '#c4b5fd' }}>{stats.max}</span>
                                    </div>
                                    <div>
                                      <span style={{ color: '#b0b8c0' }}>Avg:</span>{' '}
                                      <span style={{ color: '#c4b5fd' }}>
                                        {stats.avg !== null ? Number(stats.avg).toFixed(2) : 'N/A'}
                                      </span>
                                    </div>
                                    <div>
                                      <span style={{ color: '#b0b8c0' }}>Count:</span>{' '}
                                      <span style={{ color: '#c4b5fd' }}>{stats.count}</span>
                                    </div>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-12" style={{ color: '#b0b8c0' }}>
                          Click to load summary statistics
                        </div>
                      )}
                    </div>
                  )}

                  {/* AI Analysis Tab */}
                  {activeTab === 'ai-analysis' && (
                    <AIAnalysisTab
                      selectedDbId={selectedDbId}
                      availableTables={Object.values(tablesBySchema).flat()}
                      selectedTableFromTree={selectedTable}
                    />
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div 
              className="rounded-xl p-12 text-center"
              style={{ 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.15)' 
              }}
            >
              <Info className="h-12 w-12 mx-auto mb-4" style={{ color: '#a8d8ff' }} />
              <h3 className="text-xl font-semibold mb-2" style={{ color: '#a8d8ff' }}>
                Select a Table
              </h3>
              <p style={{ color: '#b0b8c0' }}>
                Choose a table from the sidebar to explore its data
              </p>
            </div>
          )}
        </div>
      </div>
      )}
    </div>
  )
}

