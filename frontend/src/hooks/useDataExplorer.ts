/**
 * Custom hook for Data Explorer state and logic.
 */
import { useState, useEffect, useCallback } from 'react'
import {
  getExplorerDatabases,
  getExplorerHealth,
  getExplorerSchemas,
  getExplorerTables,
  getExplorerTableColumns,
  getExplorerTableRows,
  getExplorerTableSummary,
  executeExplorerQuery,
  fetchDictionaryEntries,
  DictionaryEntry
} from '../api/client'
import {
  DatabaseInfo,
  Schema,
  Table,
  Column,
  TableRowsResponse,
  QueryResponse,
  TableSummary,
  ActiveTab
} from '../types/dataExplorer'

export interface DataExplorerState {
  // Database
  databases: DatabaseInfo[]
  selectedDbId: string
  connected: boolean
  loading: boolean
  connectionError: string

  // Schema/Table navigation
  schemas: Schema[]
  expandedSchemas: Set<string>
  tablesBySchema: Record<string, Table[]>

  // Selected table
  selectedTable: Table | null
  columns: Column[]
  tableRows: TableRowsResponse | null
  tablePage: number
  loadingTable: boolean

  // Dictionary
  dictionaryEntries: DictionaryEntry[]
  loadingDictionary: boolean

  // Query
  query: string
  queryResult: QueryResponse | null
  executingQuery: boolean

  // Tabs
  activeTab: ActiveTab
  summary: TableSummary | null
  loadingSummary: boolean
}

export interface DataExplorerActions {
  setSelectedDbId: (id: string) => void
  toggleSchema: (schemaName: string) => void
  selectTable: (table: Table) => void
  setActiveTab: (tab: ActiveTab) => void
  setQuery: (query: string) => void
  executeQuery: () => Promise<void>
  handleTablePageChange: (page: number) => void
  loadTableSummary: () => Promise<void>
}

export function useDataExplorer(): [DataExplorerState, DataExplorerActions] {
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

  // Dictionary entries
  const [dictionaryEntries, setDictionaryEntries] = useState<DictionaryEntry[]>([])
  const [loadingDictionary, setLoadingDictionary] = useState(false)

  // Query editor state
  const [query, setQuery] = useState('')
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null)
  const [executingQuery, setExecutingQuery] = useState(false)

  // Active tab
  const [activeTab, setActiveTab] = useState<ActiveTab>('preview')
  const [summary, setSummary] = useState<TableSummary | null>(null)
  const [loadingSummary, setLoadingSummary] = useState(false)

  // Load databases on mount
  useEffect(() => {
    loadDatabases()
  }, [])

  // Check connection when database changes
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
    setConnectionError('')
    setSchemas([])
    setTablesBySchema({})
    setSelectedTable(null)

    const currentDbId = selectedDbId

    try {
      const health = await getExplorerHealth(currentDbId)
      if (currentDbId !== selectedDbId) return

      setConnected(health.connected)
      if (!health.connected) {
        setConnectionError(health.error || 'Unknown connection error')
      } else {
        await loadSchemas(currentDbId)
      }
    } catch (error: any) {
      if (currentDbId === selectedDbId) {
        setConnected(false)
        setConnectionError(error.message || 'Failed to connect to database')
      }
    } finally {
      if (currentDbId === selectedDbId) {
        setLoading(false)
      }
    }
  }

  const loadSchemas = async (dbId: string) => {
    try {
      const data = await getExplorerSchemas(dbId)
      if (dbId !== selectedDbId) return

      setSchemas(data)
      if (data.some((s: Schema) => s.name === 'public')) {
        await loadTablesForDb('public', dbId)
      }
    } catch (error) {
      console.error('Failed to load schemas:', error)
    }
  }

  const loadTablesForDb = async (schema: string, dbId: string) => {
    try {
      const tables = await getExplorerTables(schema, dbId)
      if (dbId !== selectedDbId) return

      setTablesBySchema(prev => ({ ...prev, [schema]: tables }))
    } catch (error) {
      console.error(`Failed to load tables for ${schema}:`, error)
    }
  }

  const loadTables = async (schema: string) => {
    if (tablesBySchema[schema]) return
    await loadTablesForDb(schema, selectedDbId)
  }

  const toggleSchema = useCallback((schemaName: string) => {
    setExpandedSchemas(prev => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(schemaName)) {
        newExpanded.delete(schemaName)
      } else {
        newExpanded.add(schemaName)
        loadTables(schemaName)
      }
      return newExpanded
    })
  }, [tablesBySchema, selectedDbId])

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

  const loadTableDictionary = async (table: Table) => {
    setLoadingDictionary(true)
    try {
      const entries = await fetchDictionaryEntries(selectedDbId, table.schema, table.name)
      setDictionaryEntries(entries)
    } catch (error) {
      console.error('Failed to load dictionary:', error)
      setDictionaryEntries([])
    } finally {
      setLoadingDictionary(false)
    }
  }

  const selectTable = useCallback(async (table: Table) => {
    setSelectedTable(table)
    setActiveTab('preview')
    setTablePage(1)
    setQuery(`SELECT * FROM ${table.schema}.${table.name} LIMIT 100;`)
    setSummary(null)
    loadTableData(table, 1)
    loadTableDictionary(table)
  }, [selectedDbId])

  const loadTableSummary = useCallback(async () => {
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
  }, [selectedTable, selectedDbId])

  const executeQueryFn = useCallback(async () => {
    if (!query.trim()) return

    setExecutingQuery(true)
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
  }, [query, selectedDbId])

  const handleTablePageChange = useCallback((newPage: number) => {
    if (!selectedTable) return
    setTablePage(newPage)
    loadTableData(selectedTable, newPage)
  }, [selectedTable, selectedDbId])

  const state: DataExplorerState = {
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
  }

  const actions: DataExplorerActions = {
    setSelectedDbId,
    toggleSchema,
    selectTable,
    setActiveTab,
    setQuery,
    executeQuery: executeQueryFn,
    handleTablePageChange,
    loadTableSummary
  }

  return [state, actions]
}
