/**
 * Query Lineage View Component
 * 
 * Displays automatic lineage information extracted from SQL queries.
 * Shows source tables, transformations, and columns used.
 */
import React from 'react';

interface TableRef {
  schema?: string;
  table: string;
  alias?: string;
  full_name: string;
}

interface ColumnRef {
  table?: string;
  column: string;
}

interface Transformations {
  join_type?: string;
  has_aggregation: boolean;
  has_filter: boolean;
}

interface QueryLineageInfo {
  query_type: string;
  source_tables: TableRef[];
  target_table?: TableRef;
  columns_used: ColumnRef[];
  transformations: Transformations;
  ctes: Record<string, string[]>;
}

interface QueryLineageViewProps {
  lineageInfo: QueryLineageInfo;
  compact?: boolean;
}

const QueryLineageView: React.FC<QueryLineageViewProps> = ({ lineageInfo, compact = false }) => {
  if (!lineageInfo || !lineageInfo.source_tables || lineageInfo.source_tables.length === 0) {
    return null;
  }

  // Compact view - single line summary
  if (compact) {
    const tableNames = lineageInfo.source_tables.map(t => t.full_name).join(', ');
    const transforms = [];
    if (lineageInfo.transformations?.join_type) {
      transforms.push(lineageInfo.transformations.join_type + ' JOIN');
    }
    if (lineageInfo.transformations?.has_aggregation) {
      transforms.push('AGGREGATE');
    }
    if (lineageInfo.transformations?.has_filter) {
      transforms.push('FILTER');
    }

    return (
      <div className="text-sm text-gray-600 bg-blue-50 p-2 rounded border border-blue-200">
        <span className="font-medium">📊 Lineage:</span> {tableNames}
        {transforms.length > 0 && (
          <span className="ml-2 text-gray-500">
            ({transforms.join(', ')})
          </span>
        )}
      </div>
    );
  }

  // Full view - detailed breakdown
  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 shadow-sm">
      <h4 className="text-sm font-semibold text-gray-800 mb-3 flex items-center">
        <span className="mr-2">🔍</span>
        Query Lineage Analysis
      </h4>

      {/* Source Tables */}
      <div className="mb-3">
        <div className="text-xs font-medium text-gray-600 mb-1">Source Tables:</div>
        <div className="flex flex-wrap gap-2">
          {lineageInfo.source_tables.map((table, idx) => (
            <div
              key={idx}
              className="bg-white px-3 py-1.5 rounded-full border border-blue-300 text-sm flex items-center gap-1"
            >
              <span className="font-mono text-blue-700">{table.full_name}</span>
              {table.alias && (
                <span className="text-gray-500 text-xs">({table.alias})</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Target Table (for INSERT/CREATE) */}
      {lineageInfo.target_table && (
        <div className="mb-3">
          <div className="text-xs font-medium text-gray-600 mb-1">Target Table:</div>
          <div className="bg-green-100 border border-green-300 px-3 py-1.5 rounded-full inline-block">
            <span className="font-mono text-green-800">{lineageInfo.target_table.full_name}</span>
          </div>
        </div>
      )}

      {/* Transformations */}
      {(lineageInfo.transformations?.join_type ||
        lineageInfo.transformations?.has_aggregation ||
        lineageInfo.transformations?.has_filter) && (
        <div className="mb-3">
          <div className="text-xs font-medium text-gray-600 mb-1">Transformations:</div>
          <div className="flex flex-wrap gap-2">
            {lineageInfo.transformations.join_type && (
              <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
                {lineageInfo.transformations.join_type} JOIN
              </span>
            )}
            {lineageInfo.transformations.has_aggregation && (
              <span className="bg-orange-100 text-orange-700 px-2 py-1 rounded text-xs font-medium">
                AGGREGATE
              </span>
            )}
            {lineageInfo.transformations.has_filter && (
              <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-medium">
                FILTER
              </span>
            )}
          </div>
        </div>
      )}

      {/* Columns Used */}
      {lineageInfo.columns_used && lineageInfo.columns_used.length > 0 && (
        <div>
          <div className="text-xs font-medium text-gray-600 mb-1">
            Columns Used: ({lineageInfo.columns_used.length})
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto">
            {lineageInfo.columns_used.slice(0, 10).map((col, idx) => (
              <span
                key={idx}
                className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs font-mono"
              >
                {col.table ? `${col.table}.${col.column}` : col.column}
              </span>
            ))}
            {lineageInfo.columns_used.length > 10 && (
              <span className="text-xs text-gray-500 px-2 py-0.5">
                +{lineageInfo.columns_used.length - 10} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Data Flow Diagram (simplified) */}
      <div className="mt-4 pt-3 border-t border-blue-200">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center gap-2">
            {lineageInfo.source_tables.map((table, idx) => (
              <React.Fragment key={idx}>
                <div className="px-2 py-1 bg-blue-100 rounded border border-blue-300">
                  {table.table}
                </div>
                {idx < lineageInfo.source_tables.length - 1 && (
                  <span className="text-gray-400">+</span>
                )}
              </React.Fragment>
            ))}
          </div>
          <span className="text-gray-400 mx-2">→</span>
          <div className="px-2 py-1 bg-green-100 rounded border border-green-300">
            {lineageInfo.target_table?.table || 'Result'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryLineageView;
