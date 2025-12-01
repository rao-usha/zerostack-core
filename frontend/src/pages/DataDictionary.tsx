import { useState, useEffect } from 'react'
import { Book, Search, Database, Table as TableIcon, Tag } from 'lucide-react'
import { fetchDictionaryEntries, DictionaryEntry } from '../api/client'

export default function DataDictionary() {
  const [entries, setEntries] = useState<DictionaryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSchema, setSelectedSchema] = useState<string>('')
  const [selectedTable, setSelectedTable] = useState<string>('')

  useEffect(() => {
    loadDictionary()
  }, [])

  const loadDictionary = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchDictionaryEntries()
      setEntries(data)
    } catch (err: any) {
      console.error('Failed to load dictionary:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to load data dictionary')
    } finally {
      setLoading(false)
    }
  }

  // Group entries by schema and table
  const groupedEntries = entries.reduce((acc, entry) => {
    const schemaKey = `${entry.database_name}.${entry.schema_name}`
    const tableKey = `${schemaKey}.${entry.table_name}`
    
    if (!acc[schemaKey]) {
      acc[schemaKey] = {}
    }
    if (!acc[schemaKey][tableKey]) {
      acc[schemaKey][tableKey] = []
    }
    acc[schemaKey][tableKey].push(entry)
    
    return acc
  }, {} as Record<string, Record<string, DictionaryEntry[]>>)

  // Get unique schemas and tables for filters
  const schemas = Array.from(new Set(entries.map(e => `${e.database_name}.${e.schema_name}`)))
  const tables = selectedSchema
    ? Array.from(new Set(
        entries
          .filter(e => `${e.database_name}.${e.schema_name}` === selectedSchema)
          .map(e => e.table_name)
      ))
    : []

  // Filter entries
  const filteredEntries = entries.filter(entry => {
    const matchesSearch =
      !searchTerm ||
      entry.column_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.business_description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesSchema = !selectedSchema || `${entry.database_name}.${entry.schema_name}` === selectedSchema
    const matchesTable = !selectedTable || entry.table_name === selectedTable
    
    return matchesSearch && matchesSchema && matchesTable
  })

  // Re-group filtered entries
  const filteredGrouped = filteredEntries.reduce((acc, entry) => {
    const schemaKey = `${entry.database_name}.${entry.schema_name}`
    const tableKey = `${schemaKey}.${entry.table_name}`
    
    if (!acc[schemaKey]) {
      acc[schemaKey] = {}
    }
    if (!acc[schemaKey][tableKey]) {
      acc[schemaKey][tableKey] = []
    }
    acc[schemaKey][tableKey].push(entry)
    
    return acc
  }, {} as Record<string, Record<string, DictionaryEntry[]>>)

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)', padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <Book className="h-8 w-8" style={{ color: '#a8d8ff' }} />
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f0f0f5' }}>
            Data Dictionary
          </h1>
        </div>
        <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
          AI-generated column documentation for your database tables
        </p>
      </div>

      {/* Controls */}
      <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid rgba(168, 216, 255, 0.2)' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Search */}
          <div style={{ flex: '1', minWidth: '300px' }}>
            <div style={{ position: 'relative' }}>
              <Search className="h-5 w-5" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#6b7280' }} />
              <input
                type="text"
                placeholder="Search columns, descriptions, tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem 0.5rem 2.5rem',
                  backgroundColor: '#0f0f17',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.5rem',
                  color: '#f0f0f5',
                  fontSize: '0.875rem'
                }}
              />
            </div>
          </div>

          {/* Schema Filter */}
          <select
            value={selectedSchema}
            onChange={(e) => {
              setSelectedSchema(e.target.value)
              setSelectedTable('')
            }}
            style={{
              padding: '0.5rem 0.75rem',
              backgroundColor: '#0f0f17',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              borderRadius: '0.5rem',
              color: '#f0f0f5',
              fontSize: '0.875rem'
            }}
          >
            <option value="">All Schemas</option>
            {schemas.map(schema => (
              <option key={schema} value={schema}>{schema}</option>
            ))}
          </select>

          {/* Table Filter */}
          {selectedSchema && (
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              style={{
                padding: '0.5rem 0.75rem',
                backgroundColor: '#0f0f17',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontSize: '0.875rem'
              }}
            >
              <option value="">All Tables</option>
              {tables.map(table => (
                <option key={table} value={table}>{table}</option>
              ))}
            </select>
          )}
        </div>

        {/* Stats */}
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1.5rem', fontSize: '0.875rem', color: '#9ca3af' }}>
          <span>{filteredEntries.length} columns</span>
          <span>{Object.keys(filteredGrouped).length} schemas</span>
          <span>{Object.values(filteredGrouped).flatMap(s => Object.keys(s)).length} tables</span>
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '2rem' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
            Loading dictionary...
          </div>
        )}

        {error && (
          <div style={{ 
            padding: '1rem', 
            backgroundColor: 'rgba(239, 68, 68, 0.1)', 
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '0.5rem',
            color: '#fca5a5'
          }}>
            {error}
          </div>
        )}

        {!loading && !error && filteredEntries.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
            <Book className="h-16 w-16 mx-auto mb-4" style={{ color: '#4b5563' }} />
            <p style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '0.5rem' }}>
              No data dictionary entries yet
            </p>
            <p style={{ fontSize: '0.875rem' }}>
              Run a "Column Documentation" analysis to generate your first dictionary entries.
            </p>
          </div>
        )}

        {!loading && !error && filteredEntries.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {Object.entries(filteredGrouped).map(([schemaKey, tables]) => (
              <div key={schemaKey}>
                {/* Schema Header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  <Database className="h-5 w-5" style={{ color: '#a8d8ff' }} />
                  <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#f0f0f5' }}>
                    {schemaKey}
                  </h2>
                </div>

                {/* Tables */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginLeft: '1.5rem' }}>
                  {Object.entries(tables).map(([tableKey, columns]) => (
                    <div key={tableKey}>
                      {/* Table Header */}
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '0.5rem', 
                        marginBottom: '0.75rem',
                        padding: '0.5rem',
                        backgroundColor: 'rgba(168, 216, 255, 0.05)',
                        borderRadius: '0.5rem'
                      }}>
                        <TableIcon className="h-4 w-4" style={{ color: '#60a5fa' }} />
                        <h3 style={{ fontSize: '1rem', fontWeight: '500', color: '#e5e7eb' }}>
                          {tableKey.split('.').pop()}
                        </h3>
                        <span style={{ 
                          fontSize: '0.75rem', 
                          color: '#9ca3af',
                          padding: '0.125rem 0.5rem',
                          backgroundColor: 'rgba(168, 216, 255, 0.1)',
                          borderRadius: '9999px'
                        }}>
                          {columns.length} columns
                        </span>
                      </div>

                      {/* Columns */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginLeft: '1.5rem' }}>
                        {columns.map(column => (
                          <div 
                            key={column.id}
                            style={{
                              padding: '1rem',
                              backgroundColor: '#0f0f17',
                              border: '1px solid rgba(168, 216, 255, 0.2)',
                              borderRadius: '0.5rem'
                            }}
                          >
                            {/* Column Name & Type */}
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.5rem' }}>
                              <code style={{ 
                                fontSize: '0.875rem', 
                                fontWeight: '600', 
                                color: '#a8d8ff',
                                fontFamily: 'monospace'
                              }}>
                                {column.column_name}
                              </code>
                              {column.data_type && (
                                <span style={{ 
                                  fontSize: '0.75rem', 
                                  color: '#9ca3af',
                                  fontFamily: 'monospace'
                                }}>
                                  : {column.data_type}
                                </span>
                              )}
                              <span style={{
                                fontSize: '0.625rem',
                                color: '#6b7280',
                                marginLeft: 'auto',
                                padding: '0.125rem 0.375rem',
                                backgroundColor: 'rgba(107, 114, 128, 0.2)',
                                borderRadius: '0.25rem'
                              }}>
                                {column.source}
                              </span>
                            </div>

                            {/* Business Name */}
                            {column.business_name && column.business_name !== column.column_name && (
                              <div style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
                                <strong>Business Name:</strong> {column.business_name}
                              </div>
                            )}

                            {/* Business Description */}
                            {column.business_description && (
                              <p style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
                                {column.business_description}
                              </p>
                            )}

                            {/* Technical Description */}
                            {column.technical_description && (
                              <p style={{ fontSize: '0.8125rem', color: '#9ca3af', fontStyle: 'italic', marginBottom: '0.5rem' }}>
                                {column.technical_description}
                              </p>
                            )}

                            {/* Examples */}
                            {column.examples && column.examples.length > 0 && (
                              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
                                <strong>Examples:</strong>{' '}
                                {column.examples.map((ex, i) => (
                                  <code 
                                    key={i} 
                                    style={{ 
                                      backgroundColor: 'rgba(168, 216, 255, 0.1)', 
                                      padding: '0.125rem 0.25rem',
                                      borderRadius: '0.25rem',
                                      marginRight: '0.25rem'
                                    }}
                                  >
                                    {ex}
                                  </code>
                                ))}
                              </div>
                            )}

                            {/* Tags */}
                            {column.tags && column.tags.length > 0 && (
                              <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
                                {column.tags.map((tag, i) => (
                                  <span
                                    key={i}
                                    style={{
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                      fontSize: '0.6875rem',
                                      padding: '0.125rem 0.5rem',
                                      backgroundColor: 'rgba(168, 216, 255, 0.15)',
                                      color: '#a8d8ff',
                                      borderRadius: '9999px'
                                    }}
                                  >
                                    <Tag className="h-3 w-3" />
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

