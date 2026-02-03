import React from 'react'

interface LineageTimelineProps {
  nodes: Array<{
    entity_type: string
    entity_name: string
    created_at?: string
    depth: number
  }>
  edges: Array<{
    source_name: string
    target_name: string
    edge_type: string
    created_at: string
  }>
}

/**
 * Lineage Timeline - Chronological view of data transformations
 * Shows data flow over time with transformation events
 */
const LineageTimeline: React.FC<LineageTimelineProps> = ({ nodes: _nodes, edges }) => {
  // Sort edges by created_at
  const sortedEdges = [...edges].sort((a, b) =>
    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  )

  const formatEdgeType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  return (
    <div className="relative">
      {/* Timeline Line */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-indigo-500 to-purple-500"></div>

      {/* Timeline Events */}
      <div className="space-y-6">
        {sortedEdges.map((edge, idx) => (
          <div key={idx} className="relative pl-20">
            {/* Timeline Dot */}
            <div className="absolute left-6 -mt-1.5">
              <div className="w-5 h-5 bg-white border-4 border-blue-500 rounded-full"></div>
            </div>

            {/* Event Card */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow p-4">
              {/* Timestamp */}
              <div className="text-xs text-gray-500 mb-2">
                {formatDate(edge.created_at)}
              </div>

              {/* Event Type */}
              <div className="flex items-center gap-2 mb-3">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                  {formatEdgeType(edge.edge_type)}
                </span>
              </div>

              {/* Flow Visualization */}
              <div className="flex items-center gap-3">
                {/* Source */}
                <div className="flex-1 bg-gray-50 rounded-lg p-3 border border-gray-200">
                  <div className="text-xs text-gray-500 mb-1">From</div>
                  <div className="font-medium text-sm text-gray-900 flex items-center gap-2">
                    <span>{edge.source_name}</span>
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex-shrink-0">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </div>

                {/* Target */}
                <div className="flex-1 bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <div className="text-xs text-blue-600 mb-1">To</div>
                  <div className="font-medium text-sm text-gray-900 flex items-center gap-2">
                    <span>{edge.target_name}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}

        {sortedEdges.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-3">⏱️</div>
            <div>No transformation events recorded</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LineageTimeline
