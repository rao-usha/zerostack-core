/**
 * Individual dictionary entry row with view and edit modes.
 */
import {
  Tag,
  Edit2,
  Save,
  X as XIcon,
  History,
  Play,
  Check
} from 'lucide-react'
import { DictionaryEntry, EditFormData } from '../../types/dataDictionary'
import { renderStateBadge } from './utils'

interface DictionaryEntryRowProps {
  entry: DictionaryEntry
  isEditing: boolean
  editForm: EditFormData
  versionNotes: string
  saving: boolean
  onStartEditing: () => void
  onCancelEditing: () => void
  onSave: () => void
  onEditFormChange: (form: EditFormData) => void
  onVersionNotesChange: (notes: string) => void
  onAddTag: (tag: string) => void
  onRemoveTag: (tag: string) => void
  onViewVersionHistory: () => void
  onSubmitForApproval: () => void
  onApprove: () => void
  onReject: () => void
}

export default function DictionaryEntryRow({
  entry,
  isEditing,
  editForm,
  versionNotes,
  saving,
  onStartEditing,
  onCancelEditing,
  onSave,
  onEditFormChange,
  onVersionNotesChange,
  onAddTag,
  onRemoveTag,
  onViewVersionHistory,
  onSubmitForApproval,
  onApprove,
  onReject
}: DictionaryEntryRowProps) {
  return (
    <div
      style={{
        padding: '1rem',
        backgroundColor: '#0f0f17',
        border: isEditing ? '1px solid rgba(168, 216, 255, 0.5)' : '1px solid rgba(168, 216, 255, 0.2)',
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
          {entry.column_name}
        </code>
        {entry.data_type && (
          <span style={{
            fontSize: '0.75rem',
            color: '#9ca3af',
            fontFamily: 'monospace'
          }}>
            : {entry.data_type}
          </span>
        )}
        <span style={{
          fontSize: '0.625rem',
          color: '#6b7280',
          padding: '0.125rem 0.375rem',
          backgroundColor: 'rgba(107, 114, 128, 0.2)',
          borderRadius: '0.25rem'
        }}>
          {entry.source}
        </span>
        {renderStateBadge(entry.state)}

        {/* Action Buttons */}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          {!isEditing ? (
            <>
              <button
                onClick={onViewVersionHistory}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  padding: '0.25rem 0.5rem',
                  backgroundColor: 'rgba(139, 92, 246, 0.1)',
                  border: '1px solid rgba(139, 92, 246, 0.3)',
                  borderRadius: '0.375rem',
                  color: '#a78bfa',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
                title={entry.is_active ? "View version history (This is the active/published version)" : "View version history (Draft - not yet published)"}
              >
                <History className="h-3 w-3" />
                v{entry.version_number} {entry.is_active ? '(Active)' : entry.state === 'draft' ? '(Draft)' : ''}
              </button>
              {(entry.state === 'draft' || entry.state === 'published') && (
                <button
                  onClick={onStartEditing}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    padding: '0.25rem 0.5rem',
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    borderRadius: '0.375rem',
                    color: '#a8d8ff',
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                  title={entry.state === 'published' ? 'Edit (creates new draft version)' : 'Edit entry'}
                >
                  <Edit2 className="h-3 w-3" />
                  Edit
                </button>
              )}
              {entry.state === 'draft' && (
                <button
                  onClick={onSubmitForApproval}
                  disabled={saving}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    padding: '0.25rem 0.5rem',
                    backgroundColor: 'rgba(251, 191, 36, 0.1)',
                    border: '1px solid rgba(251, 191, 36, 0.3)',
                    borderRadius: '0.375rem',
                    color: '#fbbf24',
                    fontSize: '0.75rem',
                    cursor: saving ? 'wait' : 'pointer',
                    opacity: saving ? 0.5 : 1
                  }}
                  title="Submit for approval"
                >
                  <Play className="h-3 w-3" />
                  Submit
                </button>
              )}
              {entry.state === 'pending_approval' && (
                <>
                  <button
                    onClick={onApprove}
                    disabled={saving}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      padding: '0.25rem 0.5rem',
                      backgroundColor: 'rgba(34, 197, 94, 0.1)',
                      border: '1px solid rgba(34, 197, 94, 0.3)',
                      borderRadius: '0.375rem',
                      color: '#22c55e',
                      fontSize: '0.75rem',
                      cursor: saving ? 'wait' : 'pointer',
                      opacity: saving ? 0.5 : 1
                    }}
                    title="Approve and publish"
                  >
                    <Check className="h-3 w-3" />
                    Approve
                  </button>
                  <button
                    onClick={onReject}
                    disabled={saving}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      padding: '0.25rem 0.5rem',
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      borderRadius: '0.375rem',
                      color: '#ef4444',
                      fontSize: '0.75rem',
                      cursor: saving ? 'wait' : 'pointer',
                      opacity: saving ? 0.5 : 1
                    }}
                    title="Reject and return to draft"
                  >
                    <XIcon className="h-3 w-3" />
                    Reject
                  </button>
                </>
              )}
            </>
          ) : (
            <>
              <button
                onClick={onSave}
                disabled={saving}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  padding: '0.25rem 0.5rem',
                  backgroundColor: '#22c55e',
                  border: 'none',
                  borderRadius: '0.375rem',
                  color: '#fff',
                  fontSize: '0.75rem',
                  cursor: saving ? 'wait' : 'pointer',
                  opacity: saving ? 0.5 : 1
                }}
                title={entry.state === 'published' ? 'Save (creates new draft version)' : 'Save changes'}
              >
                <Save className="h-3 w-3" />
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button
                onClick={onCancelEditing}
                disabled={saving}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                  padding: '0.25rem 0.5rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '0.375rem',
                  color: '#ef4444',
                  fontSize: '0.75rem',
                  cursor: saving ? 'not-allowed' : 'pointer'
                }}
              >
                <XIcon className="h-3 w-3" />
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      {isEditing ? (
        /* Edit Form */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.75rem' }}>
          {/* Version Notes */}
          <div style={{
            padding: '0.75rem',
            backgroundColor: 'rgba(139, 92, 246, 0.05)',
            border: '1px solid rgba(139, 92, 246, 0.2)',
            borderRadius: '0.375rem'
          }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#a78bfa', marginBottom: '0.25rem', fontWeight: '500' }}>
              Version Notes (optional)
            </label>
            <input
              type="text"
              value={versionNotes}
              onChange={(e) => onVersionNotesChange(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: '#0a0a0f',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                borderRadius: '0.375rem',
                color: '#f0f0f5',
                fontSize: '0.875rem'
              }}
              placeholder="What changed? (used when saving as new version)"
            />
            <p style={{ fontSize: '0.6875rem', color: '#9ca3af', marginTop: '0.375rem', lineHeight: '1.3' }}>
              Click "New Version" to preserve current version and create a new one
            </p>
          </div>

          {/* Business Name */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
              Business Name
            </label>
            <input
              type="text"
              value={editForm.business_name || ''}
              onChange={(e) => onEditFormChange({ ...editForm, business_name: e.target.value })}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: '#0a0a0f',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.375rem',
                color: '#f0f0f5',
                fontSize: '0.875rem'
              }}
            />
          </div>

          {/* Business Description */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
              Business Description
            </label>
            <textarea
              value={editForm.business_description || ''}
              onChange={(e) => onEditFormChange({ ...editForm, business_description: e.target.value })}
              rows={3}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: '#0a0a0f',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.375rem',
                color: '#f0f0f5',
                fontSize: '0.875rem',
                resize: 'vertical'
              }}
            />
          </div>

          {/* Technical Description */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
              Technical Description
            </label>
            <textarea
              value={editForm.technical_description || ''}
              onChange={(e) => onEditFormChange({ ...editForm, technical_description: e.target.value })}
              rows={2}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: '#0a0a0f',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.375rem',
                color: '#f0f0f5',
                fontSize: '0.875rem',
                fontStyle: 'italic',
                resize: 'vertical'
              }}
            />
          </div>

          {/* Tags */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
              Tags
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', marginBottom: '0.5rem' }}>
              {editForm.tags?.map((tag, i) => (
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
                  <button
                    onClick={() => onRemoveTag(tag)}
                    style={{
                      display: 'inline-flex',
                      border: 'none',
                      background: 'none',
                      color: '#a8d8ff',
                      cursor: 'pointer',
                      padding: 0,
                      marginLeft: '0.125rem'
                    }}
                  >
                    <XIcon className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                placeholder="Add tag (e.g., PII, metric)"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    onAddTag((e.target as HTMLInputElement).value);
                    (e.target as HTMLInputElement).value = ''
                  }
                }}
                style={{
                  flex: 1,
                  padding: '0.375rem 0.5rem',
                  backgroundColor: '#0a0a0f',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.375rem',
                  color: '#f0f0f5',
                  fontSize: '0.75rem'
                }}
              />
            </div>
          </div>
        </div>
      ) : (
        /* View Mode */
        <>
          {/* Business Name */}
          {entry.business_name && entry.business_name !== entry.column_name && (
            <div style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
              <strong>Business Name:</strong> {entry.business_name}
            </div>
          )}

          {/* Business Description */}
          {entry.business_description && (
            <p style={{ fontSize: '0.875rem', color: '#d1d5db', marginBottom: '0.5rem' }}>
              {entry.business_description}
            </p>
          )}

          {/* Technical Description */}
          {entry.technical_description && (
            <p style={{ fontSize: '0.8125rem', color: '#9ca3af', fontStyle: 'italic', marginBottom: '0.5rem' }}>
              {entry.technical_description}
            </p>
          )}

          {/* Examples */}
          {entry.examples && entry.examples.length > 0 && (
            <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.5rem' }}>
              <strong>Examples:</strong>{' '}
              {entry.examples.map((ex, i) => (
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
          {entry.tags && entry.tags.length > 0 && (
            <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
              {entry.tags.map((tag, i) => (
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
        </>
      )}
    </div>
  )
}
