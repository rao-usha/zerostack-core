/**
 * Data Explorer page - Browse and query database tables.
 * Refactored to use modular components.
 */
import {
  Database,
  AlertCircle,
  Loader2,
  Info
} from 'lucide-react'
import { useDataExplorer } from '../hooks/useDataExplorer'
import {
  SchemaSidebar,
  ColumnsTab,
  QueryTab,
  SummaryTab
} from '../components/dataExplorer'
import DataTable from '../components/DataTable'
import { ActiveTab } from '../types/dataExplorer'

export default function DataExplorer() {
  const [state, actions] = useDataExplorer()

  const {
    databases,
    selectedDbId,
    connected,
    loading,
    connectionError,
    schemas,
    expandedSchemas,
    tablesBySchema,
    selectedTable,
    columns,
    tableRows,
    tablePage,
    loadingTable,
    dictionaryEntries,
    loadingDictionary,
    query,
    queryResult,
    executingQuery,
    activeTab,
    summary,
    loadingSummary
  } = state

  const {
    setSelectedDbId,
    toggleSchema,
    selectTable,
    setActiveTab,
    setQuery,
    executeQuery,
    handleTablePageChange,
    loadTableSummary
  } = actions

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff' }} />
      </div>
    )
  }

  // Connection error state
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

      {/* Main Content */}
      {databases.length > 0 && (
        <div className="flex gap-6" style={{ minHeight: '600px', width: '100%', maxWidth: 'calc(100vw - 4rem)' }}>
          {/* Left Sidebar */}
          <SchemaSidebar
            schemas={schemas}
            expandedSchemas={expandedSchemas}
            tablesBySchema={tablesBySchema}
            selectedTable={selectedTable}
            onToggleSchema={toggleSchema}
            onSelectTable={selectTable}
          />

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
                  {/* Tab Navigation */}
                  <div
                    className="flex border-b"
                    style={{ borderColor: 'rgba(168, 216, 255, 0.15)' }}
                  >
                    {(['preview', 'columns', 'query', 'summary'] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => {
                          setActiveTab(tab as ActiveTab)
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

                  {/* Tab Content */}
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
                      <ColumnsTab
                        columns={columns}
                        dictionaryEntries={dictionaryEntries}
                        loadingDictionary={loadingDictionary}
                      />
                    )}

                    {/* Query Tab */}
                    {activeTab === 'query' && (
                      <QueryTab
                        query={query}
                        queryResult={queryResult}
                        executingQuery={executingQuery}
                        onQueryChange={setQuery}
                        onExecute={executeQuery}
                      />
                    )}

                    {/* Summary Tab */}
                    {activeTab === 'summary' && (
                      <SummaryTab
                        summary={summary}
                        loading={loadingSummary}
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
