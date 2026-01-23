import React, { useState, useEffect } from 'react'
import { getLineage, getLineageSummary } from '../api/client'
import LineageTimeline from './LineageTimeline'
import LineageSankey from './LineageSankey'

interface LineageViewProps {
  entityType: string
  entityId: string
  entityName?: string
}

interface LineageNode {
  entity_type: string
  entity_id: string
  entity_name: string
  schema_name?: string
  row_count?: number
  column_count?: number
  depth: number
}

interface LineageEdge {
  id: string
  source_type: string
  source_id: string
  source_name: string
  target_type: string
  target_id: string
  target_name: string
  edge_type: string
  source_row_count?: number
  target_row_count?: number
}

const LineageView: React.FC<LineageViewProps> = ({ entityType, entityId, entityName }) => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lineageData, setLineageData] = useState<any>(null)
  const [viewMode, setViewMode] = useState<'table' | 'flow' | 'graph' | 'timeline'>('table')
  const [maxDepth, setMaxDepth] = useState(3)

  useEffect(() => {
    loadLineage()
  }, [entityType, entityId, maxDepth])

  const loadLineage = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getLineage(entityType, entityId, {
        direction: 'both',
        maxDepth,
        includeColumns: false,
      })
      setLineageData(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load lineage')
      console.error('Lineage error:', err)
    } finally {
      setLoading(false)
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

  const formatEdgeType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading lineage...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800 font-medium">Error loading lineage</div>
        <div className="text-red-600 text-sm mt-1">{error}</div>
      </div>
    )
  }

  if (!lineageData) {
    return (
      <div className="text-gray-500 text-center py-8">No lineage data available</div>
    )
  }

  const { center_node, upstream_nodes, downstream_nodes, edges } = lineageData

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {getEntityIcon(entityType)} {entityName || center_node.entity_name}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            {upstream_nodes.length} upstream sources • {downstream_nodes.length} downstream targets
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <select
            value={maxDepth}
            onChange={(e) => setMaxDepth(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="1">Depth: 1</option>
            <option value="2">Depth: 2</option>
            <option value="3">Depth: 3</option>
            <option value="5">Depth: 5</option>
          </select>
          
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'table'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Table
            </button>
            <button
              onClick={() => setViewMode('flow')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'flow'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Flow
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'timeline'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === 'graph'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Graph
            </button>
          </div>
        </div>
      </div>

      {/* Table View (MVP) */}
      {viewMode === 'table' && (
        <div className="space-y-6">
          {/* Upstream Sources */}
          {upstream_nodes.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  ⬆️ Upstream Sources ({upstream_nodes.length})
                </h3>
                <p className="text-sm text-gray-500 mt-1">Data that this entity was derived from</p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Source
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Rows
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Columns
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Depth
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {upstream_nodes.map((node: LineageNode) => (
                      <tr key={node.entity_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span className="mr-2">{getEntityIcon(node.entity_type)}</span>
                            <div>
                              <div className="text-sm font-medium text-gray-900">{node.entity_name}</div>
                              {node.schema_name && (
                                <div className="text-xs text-gray-500">{node.schema_name}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatEdgeType(node.entity_type)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {node.row_count?.toLocaleString() || '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {node.column_count || '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {node.depth === 1 && '• Direct'}
                          {node.depth === 2 && '•• 2nd level'}
                          {node.depth >= 3 && `${'•'.repeat(Math.min(node.depth, 5))} ${node.depth} levels`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Transformations */}
          {edges.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  🔄 Transformations
                </h3>
                <p className="text-sm text-gray-500 mt-1">Operations applied to create this data</p>
              </div>
              
              <div className="p-6 space-y-3">
                {edges.filter((e: LineageEdge) => 
                  e.target_type === entityType || e.source_type === entityType
                ).map((edge: LineageEdge) => (
                  <div key={edge.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold text-sm">
                      →
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900">
                          {formatEdgeType(edge.edge_type)}
                        </span>
                        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                          {edge.source_name} → {edge.target_name}
                        </span>
                      </div>
                      {(edge.source_row_count || edge.target_row_count) && (
                        <div className="text-xs text-gray-500 mt-1">
                          {edge.source_row_count?.toLocaleString()} rows → {edge.target_row_count?.toLocaleString()} rows
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Downstream Targets */}
          {downstream_nodes.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  ⬇️ Downstream Targets ({downstream_nodes.length})
                </h3>
                <p className="text-sm text-gray-500 mt-1">Data and outputs derived from this entity</p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Target
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Rows
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Columns
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Depth
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {downstream_nodes.map((node: LineageNode) => (
                      <tr key={node.entity_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span className="mr-2">{getEntityIcon(node.entity_type)}</span>
                            <div>
                              <div className="text-sm font-medium text-gray-900">{node.entity_name}</div>
                              {node.schema_name && (
                                <div className="text-xs text-gray-500">{node.schema_name}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatEdgeType(node.entity_type)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {node.row_count?.toLocaleString() || '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {node.column_count || '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {node.depth === 1 && '• Direct'}
                          {node.depth === 2 && '•• 2nd level'}
                          {node.depth >= 3 && `${'•'.repeat(Math.min(node.depth, 5))} ${node.depth} levels`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* No Lineage */}
          {upstream_nodes.length === 0 && downstream_nodes.length === 0 && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
              <div className="text-gray-400 text-4xl mb-3">🔍</div>
              <div className="text-gray-600 font-medium">No lineage data found</div>
              <div className="text-gray-500 text-sm mt-1">
                This entity has no tracked upstream sources or downstream targets.
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sankey Flow View */}
      {viewMode === 'flow' && (
        <LineageSankey 
          nodes={[...upstream_nodes, center_node, ...downstream_nodes]}
          edges={edges}
        />
      )}

      {/* Graph View Placeholder */}
      {viewMode === 'graph' && (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <div className="text-gray-400 text-5xl mb-4">🕸️</div>
          <div className="text-gray-600 font-medium text-lg">Interactive Network Graph</div>
          <div className="text-gray-500 text-sm mt-2">
            Coming soon: Interactive graph visualization using React Flow
          </div>
        </div>
      )}

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Transformation Timeline</h3>
            <p className="text-sm text-gray-500 mt-1">
              Chronological view of data lineage events
            </p>
          </div>
          {edges.length > 0 ? (
            <LineageTimeline nodes={[...upstream_nodes, center_node, ...downstream_nodes]} edges={edges} />
          ) : (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-3">⏱️</div>
              <div>No transformation events recorded</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LineageView
