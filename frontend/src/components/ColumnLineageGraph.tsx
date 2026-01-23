/**
 * Column-Level Lineage Graph
 * 
 * Visualizes how individual columns transform through a query.
 * Shows source columns -> transformations -> target columns.
 */
import React, { useMemo } from 'react';

interface ColumnTransformation {
  source: string;
  target: string;
  type: string;
  function?: string;
  sql?: string;
  label: string;
}

interface ColumnLineageGraphProps {
  transformations: ColumnTransformation[];
  compact?: boolean;
}

const ColumnLineageGraph: React.FC<ColumnLineageGraphProps> = ({ transformations, compact = false }) => {
  // Group by transformation type for color coding
  const typeColors: Record<string, string> = {
    'DIRECT': 'bg-blue-100 border-blue-300 text-blue-800',
    'AGGREGATE': 'bg-purple-100 border-purple-300 text-purple-800',
    'FUNCTION': 'bg-green-100 border-green-300 text-green-800',
    'EXPRESSION': 'bg-orange-100 border-orange-300 text-orange-800',
    'CALCULATED': 'bg-yellow-100 border-yellow-300 text-yellow-800',
  };

  const typeIcons: Record<string, string> = {
    'DIRECT': '→',
    'AGGREGATE': '∑',
    'FUNCTION': 'ƒ',
    'EXPRESSION': '⚙',
    'CALCULATED': '📊',
  };

  // Group transformations by source table
  const grouped = useMemo(() => {
    const groups: Record<string, ColumnTransformation[]> = {};
    
    transformations.forEach(trans => {
      const table = trans.source.split('.')[0] || 'unknown';
      if (!groups[table]) {
        groups[table] = [];
      }
      groups[table].push(trans);
    });
    
    return groups;
  }, [transformations]);

  if (transformations.length === 0) {
    return (
      <div className="text-sm text-gray-500 italic">
        No column transformations detected
      </div>
    );
  }

  // Compact view - just list transformations
  if (compact) {
    return (
      <div className="flex flex-wrap gap-2">
        {transformations.slice(0, 5).map((trans, idx) => (
          <div
            key={idx}
            className={`px-2 py-1 rounded text-xs font-mono ${typeColors[trans.type] || 'bg-gray-100'}`}
            title={trans.sql || trans.label}
          >
            {trans.source} → {trans.target}
          </div>
        ))}
        {transformations.length > 5 && (
          <div className="px-2 py-1 text-xs text-gray-500">
            +{transformations.length - 5} more
          </div>
        )}
      </div>
    );
  }

  // Full view - visual graph
  return (
    <div className="bg-gradient-to-br from-gray-50 to-blue-50 border border-gray-200 rounded-lg p-6 shadow-sm">
      <h4 className="text-sm font-semibold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">🔗</span>
        Column-Level Lineage ({transformations.length} transformation{transformations.length !== 1 ? 's' : ''})
      </h4>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b border-gray-200">
        {Object.entries(typeColors).map(([type, colorClass]) => (
          <div key={type} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded border ${colorClass}`} />
            <span className="text-xs text-gray-600">
              {typeIcons[type]} {type}
            </span>
          </div>
        ))}
      </div>

      {/* Transformations grouped by source table */}
      <div className="space-y-6">
        {Object.entries(grouped).map(([table, trans]) => (
          <div key={table} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-xs font-medium text-gray-500 mb-3">
              Source: <span className="font-mono text-blue-600">{table}</span>
            </div>
            
            <div className="space-y-2">
              {trans.map((t, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  {/* Source Column */}
                  <div className="flex-shrink-0 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded font-mono text-sm">
                    {t.source.split('.')[1] || t.source}
                  </div>

                  {/* Transformation Badge */}
                  <div className={`flex-shrink-0 px-2 py-1 rounded text-xs font-medium border ${typeColors[t.type] || 'bg-gray-100'}`}>
                    <div className="flex items-center gap-1">
                      <span>{typeIcons[t.type]}</span>
                      <span>{t.function || t.type}</span>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="flex-shrink-0 text-gray-400">→</div>

                  {/* Target Column */}
                  <div className="flex-shrink-0 px-3 py-1.5 bg-green-50 border border-green-200 rounded font-mono text-sm">
                    {t.target}
                  </div>

                  {/* SQL Preview (if available) */}
                  {t.sql && t.type !== 'DIRECT' && (
                    <div className="flex-1 text-xs text-gray-500 font-mono truncate" title={t.sql}>
                      {t.sql.substring(0, 50)}{t.sql.length > 50 ? '...' : ''}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600">
        <div className="flex flex-wrap gap-4">
          <div>
            <span className="font-medium">Direct:</span> {transformations.filter(t => t.type === 'DIRECT').length}
          </div>
          <div>
            <span className="font-medium">Aggregations:</span> {transformations.filter(t => t.type === 'AGGREGATE').length}
          </div>
          <div>
            <span className="font-medium">Functions:</span> {transformations.filter(t => t.type === 'FUNCTION').length}
          </div>
          <div>
            <span className="font-medium">Expressions:</span> {transformations.filter(t => t.type === 'EXPRESSION').length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ColumnLineageGraph;
