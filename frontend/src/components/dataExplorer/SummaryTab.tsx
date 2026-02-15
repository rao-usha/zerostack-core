/**
 * Column statistics summary tab.
 */
import { Loader2 } from 'lucide-react'
import { TableSummary } from '../../types/dataExplorer'

interface SummaryTabProps {
  summary: TableSummary | null
  loading: boolean
}

export default function SummaryTab({ summary, loading }: SummaryTabProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff' }} />
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="text-center py-12" style={{ color: '#b0b8c0' }}>
        Click to load summary statistics
      </div>
    )
  }

  return (
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
  )
}
