/**
 * Schema and table navigation sidebar.
 */
import {
  Database,
  Table2,
  ChevronRight,
  ChevronDown
} from 'lucide-react'
import { Schema, Table } from '../../types/dataExplorer'

interface SchemaSidebarProps {
  schemas: Schema[]
  expandedSchemas: Set<string>
  tablesBySchema: Record<string, Table[]>
  selectedTable: Table | null
  onToggleSchema: (schemaName: string) => void
  onSelectTable: (table: Table) => void
}

export default function SchemaSidebar({
  schemas,
  expandedSchemas,
  tablesBySchema,
  selectedTable,
  onToggleSchema,
  onSelectTable
}: SchemaSidebarProps) {
  return (
    <div
      className="w-80 flex-shrink-0 rounded-xl p-4 overflow-y-auto"
      style={{
        backgroundColor: '#1a1a24',
        border: '1px solid rgba(168, 216, 255, 0.15)',
        maxHeight: '700px',
        width: '320px'
      }}
    >
      <div className="flex items-center space-x-2 mb-4 pb-3 border-b" style={{ borderColor: 'rgba(168, 216, 255, 0.15)' }}>
        <Database className="h-5 w-5" style={{ color: '#a8d8ff' }} />
        <h2 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Schemas & Tables</h2>
      </div>

      <div className="space-y-1">
        {schemas.map((schema) => (
          <div key={schema.name}>
            <button
              onClick={() => onToggleSchema(schema.name)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors hover:bg-opacity-80"
              style={{
                backgroundColor: expandedSchemas.has(schema.name) ? 'rgba(168, 216, 255, 0.1)' : 'transparent',
                color: '#f0f0f5'
              }}
            >
              <div className="flex items-center space-x-2">
                {expandedSchemas.has(schema.name) ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                <span className="font-medium">{schema.name}</span>
              </div>
              {schema.table_count !== undefined && (
                <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.15)', color: '#a8d8ff' }}>
                  {schema.table_count}
                </span>
              )}
            </button>

            {expandedSchemas.has(schema.name) && tablesBySchema[schema.name] && (
              <div className="ml-6 mt-1 space-y-1">
                {tablesBySchema[schema.name].map((table) => (
                  <button
                    key={`${table.schema}.${table.name}`}
                    onClick={() => onSelectTable(table)}
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left"
                    style={{
                      backgroundColor: selectedTable?.name === table.name && selectedTable?.schema === table.schema
                        ? 'rgba(196, 181, 253, 0.15)'
                        : 'transparent',
                      color: '#f0f0f5'
                    }}
                  >
                    <div className="flex items-center space-x-2">
                      <Table2 className="h-4 w-4" style={{ color: '#c4b5fd' }} />
                      <span className="text-sm">{table.name}</span>
                    </div>
                    {table.row_estimate !== null && table.row_estimate !== undefined && (
                      <span className="text-xs" style={{ color: '#8090a0' }}>
                        ~{table.row_estimate.toLocaleString()}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
