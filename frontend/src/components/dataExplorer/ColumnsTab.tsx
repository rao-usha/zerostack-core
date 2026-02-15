/**
 * Columns tab with dictionary documentation.
 */
import { Book, Tag } from 'lucide-react'
import { Column } from '../../types/dataExplorer'
import { DictionaryEntry } from '../../api/client'

interface ColumnsTabProps {
  columns: Column[]
  dictionaryEntries: DictionaryEntry[]
  loadingDictionary: boolean
}

export default function ColumnsTab({
  columns,
  dictionaryEntries,
  loadingDictionary
}: ColumnsTabProps) {
  return (
    <div className="space-y-2">
      {columns.map((col) => {
        const dictEntry = dictionaryEntries.find(
          e => e.column_name.toLowerCase() === col.name.toLowerCase()
        )

        return (
          <div
            key={col.name}
            className="p-4 rounded-lg"
            style={{
              backgroundColor: dictEntry
                ? 'rgba(34, 197, 94, 0.05)'
                : 'rgba(168, 216, 255, 0.05)',
              border: dictEntry
                ? '1px solid rgba(34, 197, 94, 0.2)'
                : '1px solid rgba(168, 216, 255, 0.1)',
            }}
          >
            <div className="flex items-start justify-between mb-2">
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <h4 className="font-semibold" style={{ color: '#f0f0f5' }}>
                    {col.name}
                  </h4>
                  {dictEntry && (
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      fontSize: '0.625rem',
                      padding: '0.125rem 0.375rem',
                      backgroundColor: 'rgba(34, 197, 94, 0.15)',
                      color: '#22c55e',
                      borderRadius: '9999px'
                    }}>
                      <Book className="h-3 w-3" />
                      Documented
                    </span>
                  )}
                </div>
                <p className="text-sm" style={{ color: '#b0b8c0' }}>
                  {col.data_type}
                  {!col.is_nullable && ' • NOT NULL'}
                  {col.default && ` • Default: ${col.default}`}
                </p>
              </div>
              <span
                className="text-xs px-2 py-1 rounded"
                style={{ backgroundColor: 'rgba(196, 181, 253, 0.15)', color: '#c4b5fd' }}
              >
                {col.ordinal_position}
              </span>
            </div>

            {/* Dictionary Documentation */}
            {dictEntry && (
              <div style={{
                marginTop: '0.75rem',
                paddingTop: '0.75rem',
                borderTop: '1px solid rgba(168, 216, 255, 0.1)'
              }}>
                {dictEntry.business_name && dictEntry.business_name !== col.name && (
                  <div style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
                    <strong style={{ color: '#a8d8ff' }}>Business Name:</strong> {dictEntry.business_name}
                  </div>
                )}

                {dictEntry.business_description && (
                  <p style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem', lineHeight: '1.4' }}>
                    <strong style={{ color: '#a8d8ff' }}>Description:</strong> {dictEntry.business_description}
                  </p>
                )}

                {dictEntry.technical_description && (
                  <p style={{ fontSize: '0.8125rem', color: '#9ca3af', fontStyle: 'italic', marginBottom: '0.5rem' }}>
                    {dictEntry.technical_description}
                  </p>
                )}

                {dictEntry.examples && dictEntry.examples.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
                    <strong>Examples:</strong>{' '}
                    {dictEntry.examples.map((ex, i) => (
                      <code
                        key={i}
                        style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.1)',
                          padding: '0.125rem 0.375rem',
                          borderRadius: '0.25rem',
                          marginRight: '0.375rem'
                        }}
                      >
                        {ex}
                      </code>
                    ))}
                  </div>
                )}

                {dictEntry.tags && dictEntry.tags.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
                    {dictEntry.tags.map((tag, i) => (
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
            )}
          </div>
        )
      })}

      {/* No documentation notice */}
      {dictionaryEntries.length === 0 && !loadingDictionary && (
        <div style={{
          padding: '1.5rem',
          textAlign: 'center',
          backgroundColor: 'rgba(251, 191, 36, 0.05)',
          border: '1px solid rgba(251, 191, 36, 0.2)',
          borderRadius: '0.5rem',
          marginTop: '1rem'
        }}>
          <Book className="h-8 w-8 mx-auto mb-2" style={{ color: '#f59e0b' }} />
          <p style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
            This table doesn't have documentation yet
          </p>
          <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
            Run a Column Documentation analysis to add business descriptions
          </p>
        </div>
      )}
    </div>
  )
}
