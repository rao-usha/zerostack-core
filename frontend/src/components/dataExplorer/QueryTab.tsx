/**
 * SQL Query editor and results tab.
 */
import {
  Play,
  Loader2,
  AlertCircle,
  CheckCircle2
} from 'lucide-react'
import { QueryResponse } from '../../types/dataExplorer'
import DataTable from '../DataTable'

interface QueryTabProps {
  query: string
  queryResult: QueryResponse | null
  executingQuery: boolean
  onQueryChange: (query: string) => void
  onExecute: () => void
}

export default function QueryTab({
  query,
  queryResult,
  executingQuery,
  onQueryChange,
  onExecute
}: QueryTabProps) {
  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium" style={{ color: '#a8d8ff' }}>
            SQL Query
          </label>
          <button
            onClick={onExecute}
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
          onChange={(e) => onQueryChange(e.target.value)}
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
  )
}
