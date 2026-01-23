import React from 'react'

interface QueryLineageInfoProps {
  sourceTables: string[]
  transformations: string[]
  isAggregate: boolean
}

const QueryLineageInfo: React.FC<QueryLineageInfoProps> = ({
  sourceTables,
  transformations,
  isAggregate,
}) => {
  if (!sourceTables || sourceTables.length === 0) {
    return null
  }

  const getTransformIcon = (transform: string) => {
    switch (transform) {
      case 'join':
        return '🔗'
      case 'where':
        return '🔍'
      case 'group_by':
        return '📊'
      case 'aggregate':
        return '∑'
      case 'union':
        return '⊕'
      case 'cte':
        return '📋'
      case 'subquery':
        return '🔄'
      default:
        return '→'
    }
  }

  const getTransformLabel = (transform: string) => {
    switch (transform) {
      case 'join':
        return 'JOIN'
      case 'where':
        return 'FILTER'
      case 'group_by':
        return 'GROUP BY'
      case 'aggregate':
        return 'AGGREGATE'
      case 'union':
        return 'UNION'
      case 'cte':
        return 'WITH (CTE)'
      case 'subquery':
        return 'SUBQUERY'
      default:
        return 'SELECT'
    }
  }

  return (
    <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-start gap-4">
        {/* Source Tables */}
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            📦 Source Tables ({sourceTables.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {sourceTables.map((table, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-white border border-blue-300 rounded-full text-sm text-blue-800 font-mono"
              >
                {table}
              </span>
            ))}
          </div>
        </div>

        {/* Transformations */}
        {transformations && transformations.length > 0 && (
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">
              ⚙️ Transformations
            </h4>
            <div className="flex flex-wrap gap-2">
              {transformations.map((transform, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-purple-100 border border-purple-300 rounded-full text-sm text-purple-800 font-medium"
                >
                  {getTransformIcon(transform)} {getTransformLabel(transform)}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Aggregate Badge */}
        {isAggregate && (
          <div>
            <span className="px-3 py-1 bg-orange-100 border border-orange-300 rounded-full text-sm text-orange-800 font-medium">
              📈 Aggregation
            </span>
          </div>
        )}
      </div>

      {/* Lineage Flow Visualization */}
      <div className="mt-4 pt-4 border-t border-blue-200">
        <div className="flex items-center gap-2 text-sm text-blue-700">
          <span className="font-semibold">Data Flow:</span>
          <div className="flex items-center gap-2 flex-wrap">
            {sourceTables.map((table, idx) => (
              <React.Fragment key={idx}>
                <span className="font-mono bg-white px-2 py-1 rounded border border-blue-200">
                  {table}
                </span>
                {idx < sourceTables.length - 1 && (
                  <span className="text-blue-400">+</span>
                )}
              </React.Fragment>
            ))}
            <span className="text-blue-400 mx-1">→</span>
            {transformations.map((transform, idx) => (
              <React.Fragment key={idx}>
                <span className="bg-purple-50 px-2 py-1 rounded border border-purple-200 text-xs">
                  {getTransformLabel(transform)}
                </span>
                {idx < transformations.length - 1 && (
                  <span className="text-purple-400">→</span>
                )}
              </React.Fragment>
            ))}
            <span className="text-blue-400 mx-1">→</span>
            <span className="font-semibold text-green-700">📊 Result</span>
          </div>
        </div>
      </div>

      {/* Helper Text */}
      <div className="mt-3 text-xs text-blue-600">
        💡 Lineage automatically tracked from your SQL query
      </div>
    </div>
  )
}

export default QueryLineageInfo
