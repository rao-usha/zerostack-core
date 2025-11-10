import { useEffect, useState } from 'react'
import { Search, ChevronLeft, ChevronRight, RefreshCw, Database, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { listExplorerTables, queryTable, getTableCount, checkCollectorHealth } from '../api/client'
import JsonViewer from '../components/JsonViewer'

interface TableInfo {
  name: string
  model: string
  description: string
}

interface TableData {
  table: string
  total: number
  limit: number
  offset: number
  count: number
  data: any[]
}

export default function DataExplorer() {
  const [tables, setTables] = useState<TableInfo[]>([])
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [tableData, setTableData] = useState<TableData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [healthStatus, setHealthStatus] = useState<{ ok: boolean } | null>(null)
  const [currentPage, setCurrentPage] = useState(0)
  const [pageSize, setPageSize] = useState(100)
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedCells, setExpandedCells] = useState<Set<string>>(new Set())

  useEffect(() => {
    checkHealth()
    loadTables()
  }, [])

  useEffect(() => {
    if (selectedTable) {
      loadTableData(selectedTable, currentPage * pageSize, pageSize)
      setExpandedCells(new Set())
    }
  }, [selectedTable, currentPage, pageSize])

  const checkHealth = async () => {
    try {
      const status = await checkCollectorHealth()
      setHealthStatus(status)
    } catch (err: any) {
      setError(`Cannot connect to nex-collector: ${err.message}`)
      setHealthStatus({ ok: false })
    }
  }

  const loadTables = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listExplorerTables()
      setTables(data)
    } catch (err: any) {
      setError(`Failed to load tables: ${err.message}`)
      console.error('Failed to load tables:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadTableData = async (tableName: string, offset: number, limit: number) => {
    try {
      setLoading(true)
      setError(null)
      const data = await queryTable(tableName, limit, offset)
      setTableData(data)
    } catch (err: any) {
      setError(`Failed to load table data: ${err.message}`)
      console.error('Failed to load table data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleTableSelect = (tableName: string) => {
    setSelectedTable(tableName)
    setCurrentPage(0)
    setSearchTerm('')
    setExpandedCells(new Set())
  }

  const handleRefresh = () => {
    if (selectedTable) {
      loadTableData(selectedTable, currentPage * pageSize, pageSize)
    } else {
      loadTables()
    }
  }

  const filteredData = tableData?.data.filter((row) => {
    if (!searchTerm) return true
    const searchLower = searchTerm.toLowerCase()
    return JSON.stringify(row).toLowerCase().includes(searchLower)
  }) || []

  const totalPages = tableData ? Math.ceil(tableData.total / pageSize) : 0

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'null'
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2)
    }
    if (typeof value === 'boolean') {
      return value.toString()
    }
    return String(value)
  }

  const isJsonField = (value: any): boolean => {
    return value !== null && typeof value === 'object'
  }

  const toggleCellExpansion = (rowIdx: number, colName: string) => {
    const key = `${rowIdx}-${colName}`
    const newExpanded = new Set(expandedCells)
    if (newExpanded.has(key)) {
      newExpanded.delete(key)
    } else {
      newExpanded.add(key)
    }
    setExpandedCells(newExpanded)
  }

  const isCellExpanded = (rowIdx: number, colName: string): boolean => {
    return expandedCells.has(`${rowIdx}-${colName}`)
  }

  const getColumnNames = (): string[] => {
    if (!tableData || tableData.data.length === 0) return []
    return Object.keys(tableData.data[0])
  }

  const renderCellValue = (value: any, rowIdx: number, colName: string) => {
    const isJson = isJsonField(value)
    const isExpanded = isCellExpanded(rowIdx, colName)
    const formatted = formatValue(value)
    const preview = formatted.substring(0, 100)
    const isLong = formatted.length > 100

    if (!isJson && !isLong) {
      return <span>{formatted}</span>
    }

    return (
      <div className="space-y-1">
        <div className="flex items-start space-x-2">
          <div className="flex-1">
            {isExpanded ? (
              <div className="json-viewer border rounded p-3" style={{ borderColor: 'rgba(168, 216, 255, 0.2)', backgroundColor: 'rgba(20, 20, 30, 0.5)', maxHeight: '500px', overflow: 'auto' }}>
                <JsonViewer data={value} />
              </div>
            ) : (
              <span className="text-sm cursor-pointer" onClick={() => toggleCellExpansion(rowIdx, colName)}>
                {preview}
                {isLong && '...'}
              </span>
            )}
          </div>
          {isJson && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleCellExpansion(rowIdx, colName)
              }}
              className="flex-shrink-0 p-1 rounded hover:bg-opacity-50"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                color: '#a8d8ff'
              }}
              title={isExpanded ? 'Collapse' : 'Expand JSON'}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
        {isJson && !isExpanded && (
          <div className="text-xs opacity-75 cursor-pointer" style={{ color: '#b3d9ff' }} onClick={() => toggleCellExpansion(rowIdx, colName)}>
            Click to expand JSON
          </div>
        )}
        {isExpanded && (
          <div className="mt-2 flex items-center space-x-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                navigator.clipboard.writeText(formatted)
              }}
              className="text-xs px-2 py-1 rounded"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                border: '1px solid rgba(168, 216, 255, 0.4)',
                color: '#a8d8ff'
              }}
            >
              Copy JSON
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: '#a8d8ff' }}>
            Data Explorer
          </h1>
          <p className="mt-2" style={{ color: '#b3d9ff' }}>
            Explore all tables from nex-collector (localhost:8080)
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {healthStatus && (
            <div className="flex items-center space-x-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  healthStatus.ok ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span style={{ color: '#b3d9ff' }}>
                {healthStatus.ok ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          )}
          <button
            onClick={handleRefresh}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.15)',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              color: '#a8d8ff'
            }}
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div
          className="p-4 rounded-lg flex items-center space-x-2"
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#fca5a5'
          }}
        >
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tables List */}
        <div
          className="lg:col-span-1 rounded-lg p-4"
          style={{
            backgroundColor: 'rgba(30, 30, 40, 0.8)',
            border: '1px solid rgba(168, 216, 255, 0.2)'
          }}
        >
          <h2 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>
            Tables
          </h2>
          <div className="space-y-2">
            {loading && !selectedTable ? (
              <div style={{ color: '#b3d9ff' }}>Loading tables...</div>
            ) : (
              tables.map((table) => (
                <button
                  key={table.name}
                  onClick={() => handleTableSelect(table.name)}
                  className="w-full text-left p-3 rounded-lg transition-all"
                  style={
                    selectedTable === table.name
                      ? {
                          background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                          color: '#a8d8ff',
                          border: '1px solid rgba(168, 216, 255, 0.4)'
                        }
                      : {
                          color: '#f0f0f5',
                          border: '1px solid transparent'
                        }
                  }
                >
                  <div className="font-medium">{table.name}</div>
                  <div className="text-xs mt-1 opacity-75">{table.description}</div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Table Data */}
        <div className="lg:col-span-3">
          {selectedTable ? (
            <div className="space-y-4">
              {/* Table Info and Controls */}
              <div
                className="rounded-lg p-4"
                style={{
                  backgroundColor: 'rgba(30, 30, 40, 0.8)',
                  border: '1px solid rgba(168, 216, 255, 0.2)'
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>
                      {selectedTable}
                    </h2>
                    {tableData && (
                      <p className="text-sm mt-1" style={{ color: '#b3d9ff' }}>
                        Showing {tableData.offset + 1} - {tableData.offset + tableData.count} of {tableData.total} records
                      </p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      placeholder="Search..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="px-3 py-2 rounded-lg"
                      style={{
                        backgroundColor: 'rgba(20, 20, 30, 0.8)',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                        color: '#f0f0f5'
                      }}
                    />
                    <select
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value))
                        setCurrentPage(0)
                      }}
                      className="px-3 py-2 rounded-lg"
                      style={{
                        backgroundColor: 'rgba(20, 20, 30, 0.8)',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                        color: '#f0f0f5'
                      }}
                    >
                      <option value={50}>50 per page</option>
                      <option value={100}>100 per page</option>
                      <option value={200}>200 per page</option>
                      <option value={500}>500 per page</option>
                    </select>
                  </div>
                </div>

                {/* Pagination */}
                {tableData && totalPages > 1 && (
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                      disabled={currentPage === 0}
                      className="flex items-center space-x-1 px-3 py-1 rounded-lg disabled:opacity-50"
                      style={{
                        backgroundColor: currentPage === 0 ? 'transparent' : 'rgba(168, 216, 255, 0.15)',
                        border: '1px solid rgba(168, 216, 255, 0.4)',
                        color: '#a8d8ff'
                      }}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      <span>Previous</span>
                    </button>
                    <span style={{ color: '#b3d9ff' }}>
                      Page {currentPage + 1} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                      disabled={currentPage >= totalPages - 1}
                      className="flex items-center space-x-1 px-3 py-1 rounded-lg disabled:opacity-50"
                      style={{
                        backgroundColor: currentPage >= totalPages - 1 ? 'transparent' : 'rgba(168, 216, 255, 0.15)',
                        border: '1px solid rgba(168, 216, 255, 0.4)',
                        color: '#a8d8ff'
                      }}
                    >
                      <span>Next</span>
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Data Table */}
              {loading ? (
                <div className="text-center py-8" style={{ color: '#b3d9ff' }}>
                  Loading data...
                </div>
              ) : filteredData.length === 0 ? (
                <div className="text-center py-8" style={{ color: '#b3d9ff' }}>
                  No data found
                </div>
              ) : (
                <div
                  className="rounded-lg overflow-hidden"
                  style={{
                    backgroundColor: 'rgba(30, 30, 40, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.2)'
                  }}
                >
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)' }}>
                          {getColumnNames().map((col) => (
                            <th
                              key={col}
                              className="px-4 py-3 text-left text-sm font-semibold"
                              style={{ color: '#a8d8ff' }}
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredData.map((row, idx) => (
                          <tr
                            key={idx}
                            style={{
                              borderBottom: '1px solid rgba(168, 216, 255, 0.1)'
                            }}
                          >
                            {getColumnNames().map((col) => (
                              <td
                                key={col}
                                className="px-4 py-3 text-sm"
                                style={{ color: '#f0f0f5' }}
                              >
                                <div className="max-w-2xl">
                                  {renderCellValue(row[col], idx, col)}
                                </div>
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div
              className="rounded-lg p-8 text-center"
              style={{
                backgroundColor: 'rgba(30, 30, 40, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.2)'
              }}
            >
              <Database className="h-12 w-12 mx-auto mb-4" style={{ color: '#a8d8ff', opacity: 0.5 }} />
              <p style={{ color: '#b3d9ff' }}>Select a table from the left to explore its data</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

