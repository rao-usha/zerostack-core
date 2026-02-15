/**
 * Version History Modal for Data Dictionary entries.
 */
import { X as XIcon, Loader2, History, Check } from 'lucide-react'
import { DictionaryEntry } from '../../types/dataDictionary'
import { renderStateBadge } from './utils'

interface VersionHistoryModalProps {
  entry: DictionaryEntry
  versions: DictionaryEntry[]
  loading: boolean
  saving: boolean
  onClose: () => void
  onActivateVersion: (versionId: number) => void
}

export default function VersionHistoryModal({
  entry,
  versions,
  loading,
  saving,
  onClose,
  onActivateVersion
}: VersionHistoryModalProps) {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: '#0f0f17',
        border: '1px solid rgba(168, 216, 255, 0.3)',
        borderRadius: '0.75rem',
        padding: '2rem',
        maxWidth: '800px',
        width: '90%',
        maxHeight: '80vh',
        overflow: 'auto'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#f0f0f5', marginBottom: '0.25rem' }}>
              Version History
            </h2>
            <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
              {entry.schema_name}.{entry.table_name}.{entry.column_name}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '0.375rem',
              color: '#ef4444',
              cursor: 'pointer'
            }}
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Version List */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" style={{ color: '#a8d8ff' }} />
            <p style={{ color: '#9ca3af' }}>Loading versions...</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {versions.map(version => (
              <div
                key={version.id}
                style={{
                  padding: '1rem',
                  backgroundColor: version.is_active ? 'rgba(34, 197, 94, 0.1)' : 'rgba(168, 216, 255, 0.05)',
                  border: version.is_active ? '2px solid #22c55e' : '1px solid rgba(168, 216, 255, 0.2)',
                  borderRadius: '0.5rem'
                }}
              >
                {/* Version Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{
                      fontSize: '1rem',
                      fontWeight: '600',
                      color: version.is_active ? '#22c55e' : '#a8d8ff'
                    }}>
                      Version {version.version_number}
                    </span>
                    {renderStateBadge(version.state)}
                    {version.is_active && (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        fontSize: '0.75rem',
                        padding: '0.25rem 0.5rem',
                        backgroundColor: 'rgba(34, 197, 94, 0.2)',
                        color: '#22c55e',
                        borderRadius: '9999px'
                      }}>
                        <Check className="h-3 w-3" />
                        Active
                      </span>
                    )}
                    <span style={{
                      fontSize: '0.75rem',
                      color: '#6b7280',
                      padding: '0.125rem 0.375rem',
                      backgroundColor: 'rgba(107, 114, 128, 0.2)',
                      borderRadius: '0.25rem'
                    }}>
                      {version.source}
                    </span>
                  </div>
                  {!version.is_active && version.state === 'published' && (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
                      <button
                        onClick={() => onActivateVersion(version.id)}
                        disabled={saving}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          padding: '0.375rem 0.75rem',
                          backgroundColor: 'rgba(168, 216, 255, 0.1)',
                          border: '1px solid rgba(168, 216, 255, 0.3)',
                          borderRadius: '0.375rem',
                          color: '#a8d8ff',
                          fontSize: '0.75rem',
                          cursor: saving ? 'wait' : 'pointer',
                          opacity: saving ? 0.5 : 1
                        }}
                        title="Create a new draft version with this content"
                      >
                        <History className="h-3 w-3" />
                        {saving ? 'Creating...' : 'Rollback to This Version'}
                      </button>
                      <span style={{ fontSize: '0.7rem', color: '#6b7280', fontStyle: 'italic' }}>
                        Creates new draft for approval
                      </span>
                    </div>
                  )}
                </div>

                {/* Version Notes */}
                {version.version_notes && (
                  <p style={{ fontSize: '0.875rem', color: '#d1d5db', fontStyle: 'italic', marginBottom: '0.75rem' }}>
                    {version.version_notes}
                  </p>
                )}

                {/* Content */}
                <div style={{ fontSize: '0.875rem', color: '#d1d5db' }}>
                  {version.business_name && (
                    <div style={{ marginBottom: '0.5rem' }}>
                      <strong style={{ color: '#a8d8ff' }}>Business Name:</strong> {version.business_name}
                    </div>
                  )}
                  {version.business_description && (
                    <div style={{ marginBottom: '0.5rem' }}>
                      <strong style={{ color: '#a8d8ff' }}>Description:</strong> {version.business_description}
                    </div>
                  )}
                  {version.technical_description && (
                    <div style={{ marginBottom: '0.5rem', fontStyle: 'italic', color: '#9ca3af' }}>
                      {version.technical_description}
                    </div>
                  )}
                  {version.tags && version.tags.length > 0 && (
                    <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                      {version.tags.map((tag, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: '0.6875rem',
                            padding: '0.125rem 0.5rem',
                            backgroundColor: 'rgba(168, 216, 255, 0.15)',
                            color: '#a8d8ff',
                            borderRadius: '9999px'
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Metadata */}
                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(168, 216, 255, 0.1)', fontSize: '0.75rem', color: '#6b7280' }}>
                  Created: {new Date(version.created_at).toLocaleString()} • Updated: {new Date(version.updated_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
