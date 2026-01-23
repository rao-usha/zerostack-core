import React, { useState, useEffect } from 'react'
import { analyzeImpact } from '../api/client'

interface LineageImpactAnalysisProps {
  entityType: string
  entityId: string
  entityName: string
}

/**
 * Lineage Impact Analysis - Shows what would be affected by changes
 * Perfect for "What if?" scenarios before making changes
 */
const LineageImpactAnalysis: React.FC<LineageImpactAnalysisProps> = ({ 
  entityType, 
  entityId,
  entityName
}) => {
  const [impact, setImpact] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    loadImpact()
  }, [entityType, entityId])

  const loadImpact = async () => {
    try {
      setLoading(true)
      const data = await analyzeImpact(entityType, entityId)
      setImpact(data)
    } catch (err) {
      console.error('Failed to analyze impact:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    )
  }

  if (!impact) return null

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-red-100 border-red-300 text-red-800'
      case 'medium':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800'
      default:
        return 'bg-green-100 border-green-300 text-green-800'
    }
  }

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'high':
        return '🔴'
      case 'medium':
        return '🟡'
      default:
        return '🟢'
    }
  }

  const getEntityIcon = (type: string) => {
    const icons: Record<string, string> = {
      file: '📁',
      file_table: '📊',
      database_table: '🗄️',
      dataset: '💾',
      notebook: '📓',
      model: '🤖',
      report: '📈',
    }
    return icons[type] || '📄'
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className={`border-2 rounded-lg p-6 ${getRiskColor(impact.risk_level)}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-3xl">{getRiskIcon(impact.risk_level)}</span>
              <div>
                <h3 className="text-xl font-bold">
                  {impact.risk_level === 'high' && 'High Impact Changes'}
                  {impact.risk_level === 'medium' && 'Medium Impact Changes'}
                  {impact.risk_level === 'low' && 'Low Impact Changes'}
                </h3>
                <p className="text-sm opacity-90 mt-1">
                  Analyzing potential impact of changes to <strong>{entityName}</strong>
                </p>
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-3xl font-bold">{impact.affected_downstream_count}</div>
            <div className="text-sm opacity-90">Affected Entities</div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {impact.recommendations && impact.recommendations.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>💡</span>
            <span>Recommendations</span>
          </h4>
          <ul className="space-y-3">
            {impact.recommendations.map((rec: string, idx: number) => (
              <li key={idx} className="flex items-start gap-3 text-sm">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">
                  {idx + 1}
                </span>
                <span className="text-gray-700 pt-0.5">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Affected Entities */}
      {impact.affected_entities && impact.affected_entities.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h4 className="font-semibold text-gray-900">Affected Downstream Entities</h4>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              {showDetails ? 'Hide Details' : 'Show Details'}
            </button>
          </div>
          
          {showDetails && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {impact.affected_entities.map((entity: any, idx: number) => (
                  <div 
                    key={idx}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{getEntityIcon(entity.entity_type)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {entity.entity_name}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {entity.entity_type.replace(/_/g, ' ')}
                        </div>
                        {entity.row_count && (
                          <div className="text-xs text-gray-500 mt-1">
                            {entity.row_count.toLocaleString()} rows
                          </div>
                        )}
                        {entity.depth > 0 && (
                          <div className="text-xs text-blue-600 mt-1">
                            {entity.depth} level{entity.depth > 1 ? 's' : ''} downstream
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Impact */}
      {impact.affected_downstream_count === 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <div className="text-green-600 text-5xl mb-3">✅</div>
          <div className="text-green-900 font-semibold text-lg">Safe to Modify</div>
          <div className="text-green-700 text-sm mt-2">
            No downstream dependencies detected. Changes to this entity won't affect other data.
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={loadImpact}
          className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Refresh Analysis</span>
        </button>
        
        {impact.affected_downstream_count > 0 && (
          <button
            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Notify Affected Teams</span>
          </button>
        )}
      </div>
    </div>
  )
}

export default LineageImpactAnalysis
