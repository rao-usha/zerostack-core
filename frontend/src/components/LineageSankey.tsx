import React, { useState, useEffect, useMemo } from 'react'
import Plot from 'react-plotly.js'

interface LineageSankeyProps {
  nodes: Array<{
    entity_type: string
    entity_name: string
    row_count?: number
  }>
  edges: Array<{
    source_name: string
    target_name: string
    source_row_count?: number
    target_row_count?: number
    edge_type: string
  }>
}

/**
 * Smart Sankey Diagram - Keeps lineage visualization clean
 * 
 * Features to prevent mess:
 * 1. Automatic grouping by entity type
 * 2. Row count threshold filtering
 * 3. Top N flows only
 * 4. Interactive expand/collapse
 * 5. Focus mode
 */
const LineageSankey: React.FC<LineageSankeyProps> = ({ nodes, edges }) => {
  // Controls to keep it clean
  const [threshold, setThreshold] = useState(0) // Minimum row count to show
  const [maxFlows, setMaxFlows] = useState(20) // Max number of flows
  const [groupByType, setGroupByType] = useState(true) // Group nodes by type
  const [focusNode, setFocusNode] = useState<string | null>(null) // Focus on one node
  const [showSmallFlows, setShowSmallFlows] = useState(false) // Show flows < 1% of total

  // Calculate total data volume
  const totalRows = useMemo(() => {
    return edges.reduce((sum, edge) => 
      sum + (edge.source_row_count || 0), 0
    )
  }, [edges])

  // Smart filtering to avoid mess
  const filteredData = useMemo(() => {
    let filteredEdges = [...edges]

    // 1. Filter by threshold (hide tiny flows)
    if (threshold > 0) {
      filteredEdges = filteredEdges.filter(e => 
        (e.source_row_count || 0) >= threshold
      )
    }

    // 2. Hide flows < 1% unless explicitly shown
    if (!showSmallFlows && totalRows > 0) {
      const minSize = totalRows * 0.01 // 1% threshold
      filteredEdges = filteredEdges.filter(e =>
        (e.source_row_count || 0) >= minSize
      )
    }

    // 3. Focus mode - only show flows connected to selected node
    if (focusNode) {
      filteredEdges = filteredEdges.filter(e =>
        e.source_name === focusNode || e.target_name === focusNode
      )
    }

    // 4. Sort by size and take top N
    filteredEdges = filteredEdges
      .sort((a, b) => (b.source_row_count || 0) - (a.source_row_count || 0))
      .slice(0, maxFlows)

    return filteredEdges
  }, [edges, threshold, maxFlows, focusNode, showSmallFlows, totalRows])

  // Group nodes by type if enabled
  const processedNodes = useMemo(() => {
    if (!groupByType) {
      return nodes
    }

    // Group nodes by entity type
    const typeGroups: Record<string, typeof nodes> = {}
    nodes.forEach(node => {
      const type = node.entity_type
      if (!typeGroups[type]) {
        typeGroups[type] = []
      }
      typeGroups[type].push(node)
    })

    // Create aggregated nodes
    return Object.entries(typeGroups).flatMap(([type, groupNodes]) => {
      if (groupNodes.length <= 3) {
        return groupNodes // Don't group if only 2-3 nodes
      }
      
      // Create group node
      return [{
        entity_type: type,
        entity_name: `${type.replace(/_/g, ' ')} (${groupNodes.length})`,
        row_count: groupNodes.reduce((sum, n) => sum + (n.row_count || 0), 0),
        _isGroup: true,
        _members: groupNodes
      }]
    })
  }, [nodes, groupByType])

  // Build Sankey data
  const sankeyData = useMemo(() => {
    // Create node list with indices
    const nodeNames = new Set<string>()
    filteredData.forEach(edge => {
      nodeNames.add(edge.source_name)
      nodeNames.add(edge.target_name)
    })
    const nodeList = Array.from(nodeNames)
    const nodeIndices = Object.fromEntries(
      nodeList.map((name, idx) => [name, idx])
    )

    // Build links
    const source = filteredData.map(e => nodeIndices[e.source_name])
    const target = filteredData.map(e => nodeIndices[e.target_name])
    const value = filteredData.map(e => e.source_row_count || 1)
    
    // Color by entity type
    const getNodeColor = (name: string) => {
      const node = nodes.find(n => n.entity_name === name)
      const typeColors: Record<string, string> = {
        file: 'rgba(59, 130, 246, 0.8)',          // blue
        file_table: 'rgba(99, 102, 241, 0.8)',    // indigo
        database_table: 'rgba(139, 92, 246, 0.8)', // purple
        dataset: 'rgba(168, 85, 247, 0.8)',       // purple-dark
        notebook: 'rgba(236, 72, 153, 0.8)',      // pink
        model: 'rgba(239, 68, 68, 0.8)',          // red
        report: 'rgba(34, 197, 94, 0.8)',         // green
      }
      return node ? typeColors[node.entity_type] || 'rgba(156, 163, 175, 0.8)' : 'rgba(156, 163, 175, 0.8)'
    }

    const nodeColors = nodeList.map(getNodeColor)
    const linkColors = filteredData.map((e, idx) => {
      const opacity = focusNode 
        ? (e.source_name === focusNode || e.target_name === focusNode ? 0.6 : 0.1)
        : 0.4
      return getNodeColor(e.source_name).replace('0.8', String(opacity))
    })

    return {
      type: 'sankey' as const,
      orientation: 'h',
      node: {
        pad: 20,
        thickness: 30,
        line: {
          color: 'white',
          width: 2
        },
        label: nodeList.map(name => {
          const node = nodes.find(n => n.entity_name === name)
          const rowCount = node?.row_count
          return rowCount 
            ? `${name}\n(${(rowCount / 1000).toFixed(0)}K rows)`
            : name
        }),
        color: nodeColors,
        customdata: nodeList.map(name => {
          const node = nodes.find(n => n.entity_name === name)
          return {
            type: node?.entity_type,
            rows: node?.row_count
          }
        }),
        hovertemplate: '<b>%{label}</b><br>Type: %{customdata.type}<br>Rows: %{customdata.rows:,}<extra></extra>',
      },
      link: {
        source,
        target,
        value,
        color: linkColors,
        customdata: filteredData.map(e => ({
          type: e.edge_type,
          rows: e.source_row_count
        })),
        hovertemplate: 'Flow: %{value:,} rows<br>Type: %{customdata.type}<extra></extra>',
      }
    }
  }, [filteredData, nodes, focusNode])

  const handleNodeClick = (event: any) => {
    if (event?.points?.[0]?.label) {
      const nodeName = event.points[0].label.split('\n')[0] // Remove row count
      setFocusNode(focusNode === nodeName ? null : nodeName)
    }
  }

  const hiddenFlowsCount = edges.length - filteredData.length

  return (
    <div className="space-y-4">
      {/* Controls Panel */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Smart Controls</h3>
          <div className="text-sm text-gray-500">
            Showing {filteredData.length} of {edges.length} flows
            {hiddenFlowsCount > 0 && (
              <span className="text-blue-600 ml-1">
                ({hiddenFlowsCount} hidden)
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Max Flows */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Max Flows: {maxFlows}
            </label>
            <input
              type="range"
              min="5"
              max="50"
              value={maxFlows}
              onChange={(e) => setMaxFlows(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-xs text-gray-500 mt-1">
              Limit to top {maxFlows} largest flows
            </div>
          </div>

          {/* Threshold */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Min Rows: {threshold.toLocaleString()}
            </label>
            <input
              type="range"
              min="0"
              max={Math.max(...edges.map(e => e.source_row_count || 0))}
              step={1000}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-xs text-gray-500 mt-1">
              Hide flows smaller than threshold
            </div>
          </div>

          {/* Group Toggle */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Grouping
            </label>
            <button
              onClick={() => setGroupByType(!groupByType)}
              className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                groupByType
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {groupByType ? '✓ Group by Type' : 'Show All Nodes'}
            </button>
          </div>

          {/* Small Flows Toggle */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Small Flows
            </label>
            <button
              onClick={() => setShowSmallFlows(!showSmallFlows)}
              className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                showSmallFlows
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {showSmallFlows ? 'Hide < 1%' : 'Show < 1%'}
            </button>
          </div>
        </div>

        {/* Focus Mode Info */}
        {focusNode && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-blue-600">🎯</span>
              <span className="text-sm text-blue-900">
                <strong>Focus Mode:</strong> {focusNode}
              </span>
            </div>
            <button
              onClick={() => setFocusNode(null)}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear Focus
            </button>
          </div>
        )}

        {/* Tips */}
        <div className="mt-4 text-xs text-gray-600 bg-gray-50 rounded p-3">
          <strong>💡 Tips:</strong>
          <ul className="list-disc list-inside mt-1 space-y-1">
            <li>Click a node to focus on its connections</li>
            <li>Adjust "Max Flows" to reduce clutter</li>
            <li>Use "Min Rows" to hide tiny flows</li>
            <li>Group by type to simplify complex lineage</li>
          </ul>
        </div>
      </div>

      {/* Sankey Diagram */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        {filteredData.length > 0 ? (
          <Plot
            data={[sankeyData]}
            layout={{
              title: {
                text: focusNode 
                  ? `Data Flow: ${focusNode}` 
                  : 'Data Lineage Flow',
                font: { size: 18 }
              },
              font: { size: 12 },
              height: 600,
              margin: { l: 20, r: 20, t: 60, b: 20 },
            }}
            config={{
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            }}
            onClick={handleNodeClick}
            style={{ width: '100%' }}
          />
        ) : (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-3">📊</div>
            <div>No flows to display</div>
            <div className="text-sm mt-1">
              Try adjusting filters or threshold
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Legend</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(59, 130, 246, 0.8)' }}></div>
            <span className="text-sm text-gray-700">File</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(99, 102, 241, 0.8)' }}></div>
            <span className="text-sm text-gray-700">File Table</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(139, 92, 246, 0.8)' }}></div>
            <span className="text-sm text-gray-700">Database Table</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(168, 85, 247, 0.8)' }}></div>
            <span className="text-sm text-gray-700">Dataset</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(236, 72, 153, 0.8)' }}></div>
            <span className="text-sm text-gray-700">Notebook</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(239, 68, 68, 0.8)' }}></div>
            <span className="text-sm text-gray-700">ML Model</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(34, 197, 94, 0.8)' }}></div>
            <span className="text-sm text-gray-700">Report</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LineageSankey
