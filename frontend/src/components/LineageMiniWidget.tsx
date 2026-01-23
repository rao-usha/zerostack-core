import React, { useState, useEffect } from 'react'
import { getLineageSummary } from '../api/client'

interface LineageMiniWidgetProps {
  entityType: string
  entityId: string
  onViewFull?: () => void
}

/**
 * Mini Lineage Widget - Shows quick lineage summary in a compact view
 * Perfect for sidebars and table detail views
 */
const LineageMiniWidget: React.FC<LineageMiniWidgetProps> = ({ 
  entityType, 
  entityId, 
  onViewFull 
}) => {
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSummary()
  }, [entityType, entityId])

  const loadSummary = async () => {
    try {
      setLoading(true)
      const data = await getLineageSummary(entityType, entityId)
      setSummary(data)
    } catch (err) {
      console.error('Failed to load lineage summary:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
          <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    )
  }

  if (!summary) return null

  const hasLineage = summary.upstream_count > 0 || summary.downstream_count > 0

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900">Data Lineage</h3>
        </div>
        {summary.is_stale && (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
            Stale
          </span>
        )}
      </div>

      {hasLineage ? (
        <>
          {/* Stats */}
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">
                {summary.upstream_count}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                ⬆️ Upstream
              </div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="text-2xl font-bold text-indigo-600">
                {summary.downstream_count}
              </div>
              <div className="text-xs text-gray-600 mt-1">
                ⬇️ Downstream
              </div>
            </div>
          </div>

          {/* Quick Lists */}
          {summary.immediate_sources?.length > 0 && (
            <div className="mb-3">
              <div className="text-xs font-medium text-gray-600 mb-1">Sources:</div>
              <div className="space-y-1">
                {summary.immediate_sources.slice(0, 3).map((source: string, idx: number) => (
                  <div key={idx} className="text-xs text-gray-700 truncate bg-white px-2 py-1 rounded">
                    📁 {source}
                  </div>
                ))}
                {summary.immediate_sources.length > 3 && (
                  <div className="text-xs text-gray-500 px-2">
                    +{summary.immediate_sources.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )}

          {summary.immediate_targets?.length > 0 && (
            <div className="mb-3">
              <div className="text-xs font-medium text-gray-600 mb-1">Used By:</div>
              <div className="space-y-1">
                {summary.immediate_targets.slice(0, 3).map((target: string, idx: number) => (
                  <div key={idx} className="text-xs text-gray-700 truncate bg-white px-2 py-1 rounded">
                    📊 {target}
                  </div>
                ))}
                {summary.immediate_targets.length > 3 && (
                  <div className="text-xs text-gray-500 px-2">
                    +{summary.immediate_targets.length - 3} more
                  </div>
                )}
              </div>
            </div>
          )}

          {/* View Full Button */}
          {onViewFull && (
            <button
              onClick={onViewFull}
              className="w-full mt-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <span>View Full Lineage</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}
        </>
      ) : (
        <div className="text-center py-4">
          <div className="text-gray-400 text-3xl mb-2">🔍</div>
          <div className="text-sm text-gray-600">No lineage tracked</div>
          <div className="text-xs text-gray-500 mt-1">
            This entity has no upstream or downstream relationships yet.
          </div>
        </div>
      )}
    </div>
  )
}

export default LineageMiniWidget
