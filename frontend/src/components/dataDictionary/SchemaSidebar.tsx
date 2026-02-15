/**
 * Schema/Table navigation sidebar for Data Dictionary.
 */
import {
  Database,
  ChevronRight,
  ChevronDown,
  FileText,
  AlertCircle,
  Play,
  Loader2
} from 'lucide-react'
import { Schema, Table, SelectedTable } from '../../types/dataDictionary'

interface SchemaSidebarProps {
  schemas: Schema[]
  expandedSchemas: Set<string>
  tablesBySchema: Record<string, Table[]>
  selectedTable: SelectedTable | null
  loading: boolean
  onToggleSchema: (schemaName: string) => void
  onSelectTable: (schema: string, table: string) => void
  onGenerateDocumentation: (schema: string, table: string) => void
  getTableDocStatus: (schema: string, table: string) => { hasDoc: boolean; columnCount: number }
}

export default function SchemaSidebar({
  schemas,
  expandedSchemas,
  tablesBySchema,
  selectedTable,
  loading,
  onToggleSchema,
  onSelectTable,
  onGenerateDocumentation,
  getTableDocStatus
}: SchemaSidebarProps) {
  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>
        <Loader2 className="h-6 w-6 animate-spin mx-auto" />
        <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>Loading tables...</p>
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem' }}>
      {schemas.map(schema => {
        const isExpanded = expandedSchemas.has(schema.name)
        const tables = tablesBySchema[schema.name] || []

        return (
          <div key={schema.name} style={{ marginBottom: '0.5rem' }}>
            {/* Schema Header */}
            <button
              onClick={() => onToggleSchema(schema.name)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 0.75rem',
                backgroundColor: 'transparent',
                border: 'none',
                color: '#a8d8ff',
                cursor: 'pointer',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.1)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              <Database className="h-4 w-4" />
              <span style={{ flex: 1, textAlign: 'left' }}>{schema.name}</span>
              <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                {tables.length || schema.table_count || 0}
              </span>
            </button>

            {/* Tables List */}
            {isExpanded && (
              <div style={{ marginLeft: '1.5rem' }}>
                {tables.length === 0 ? (
                  <div style={{ padding: '0.5rem 0.75rem', fontSize: '0.8125rem', color: '#6b7280' }}>
                    <Loader2 className="h-3 w-3 inline-block mr-2 animate-spin" />
                    Loading...
                  </div>
                ) : (
                  tables.map(table => {
                    const docStatus = getTableDocStatus(schema.name, table.name)
                    const isSelected = selectedTable?.schema === schema.name && selectedTable?.table === table.name

                    return (
                      <div
                        key={`${schema.name}.${table.name}`}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          padding: '0.5rem 0.75rem',
                          backgroundColor: isSelected ? 'rgba(168, 216, 255, 0.15)' : 'transparent',
                          borderRadius: '0.375rem',
                          borderLeft: isSelected ? '2px solid #a8d8ff' : '2px solid transparent',
                          cursor: 'pointer'
                        }}
                        onClick={() => onSelectTable(schema.name, table.name)}
                        onMouseEnter={(e) => {
                          if (!isSelected) e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.05)'
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent'
                        }}
                      >
                        {docStatus.hasDoc ? (
                          <FileText className="h-4 w-4" style={{ color: '#22c55e' }} />
                        ) : (
                          <AlertCircle className="h-4 w-4" style={{ color: '#f59e0b' }} />
                        )}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            fontSize: '0.8125rem',
                            color: isSelected ? '#a8d8ff' : '#d1d5db',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {table.name}
                          </div>
                          {docStatus.hasDoc && (
                            <div style={{ fontSize: '0.6875rem', color: '#6b7280' }}>
                              {docStatus.columnCount} columns
                            </div>
                          )}
                        </div>
                        {!docStatus.hasDoc && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onGenerateDocumentation(schema.name, table.name)
                            }}
                            style={{
                              padding: '0.25rem',
                              backgroundColor: 'rgba(168, 216, 255, 0.1)',
                              border: '1px solid rgba(168, 216, 255, 0.3)',
                              borderRadius: '0.25rem',
                              color: '#a8d8ff',
                              cursor: 'pointer'
                            }}
                            title="Generate AI documentation"
                          >
                            <Play className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    )
                  })
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
