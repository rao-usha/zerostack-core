/**
 * Dictionary entries table with header and empty state.
 */
import {
  Table as TableIcon,
  AlertCircle,
  Play
} from 'lucide-react'
import { DictionaryEntry, EditFormData, SelectedTable } from '../../types/dataDictionary'
import DictionaryEntryRow from './DictionaryEntryRow'

interface DictionaryTableProps {
  selectedTable: SelectedTable
  entries: DictionaryEntry[]
  editingEntry: number | null
  editForm: EditFormData
  versionNotes: string
  saving: boolean
  onGenerateDocumentation: () => void
  onStartEditing: (entry: DictionaryEntry) => void
  onCancelEditing: () => void
  onSaveEntry: (entryId: number) => void
  onEditFormChange: (form: EditFormData) => void
  onVersionNotesChange: (notes: string) => void
  onAddTag: (tag: string) => void
  onRemoveTag: (tag: string) => void
  onViewVersionHistory: (entry: DictionaryEntry) => void
  onSubmitForApproval: (entryId: number) => void
  onApprove: (entryId: number) => void
  onReject: (entryId: number) => void
}

export default function DictionaryTable({
  selectedTable,
  entries,
  editingEntry,
  editForm,
  versionNotes,
  saving,
  onGenerateDocumentation,
  onStartEditing,
  onCancelEditing,
  onSaveEntry,
  onEditFormChange,
  onVersionNotesChange,
  onAddTag,
  onRemoveTag,
  onViewVersionHistory,
  onSubmitForApproval,
  onApprove,
  onReject
}: DictionaryTableProps) {
  return (
    <>
      {/* Table Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <TableIcon className="h-6 w-6" style={{ color: '#a8d8ff' }} />
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#f0f0f5' }}>
                {selectedTable.schema}.{selectedTable.table}
              </h2>
            </div>
            <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
              {entries.length} columns documented
            </p>
          </div>

          {entries.length === 0 && (
            <button
              onClick={onGenerateDocumentation}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.625rem 1.25rem',
                backgroundColor: '#a8d8ff',
                color: '#0a0a0f',
                border: 'none',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              <Play className="h-4 w-4" />
              Generate Documentation
            </button>
          )}
        </div>

        {entries.length === 0 && (
          <div style={{
            padding: '2rem',
            textAlign: 'center',
            backgroundColor: 'rgba(168, 216, 255, 0.05)',
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.5rem'
          }}>
            <AlertCircle className="h-12 w-12 mx-auto mb-3" style={{ color: '#f59e0b' }} />
            <h3 style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '0.5rem', color: '#f0f0f5' }}>
              No Documentation Yet
            </h3>
            <p style={{ fontSize: '0.875rem', color: '#9ca3af', marginBottom: '1rem' }}>
              This table hasn't been documented yet. Run a Column Documentation analysis to generate AI-powered descriptions.
            </p>
          </div>
        )}
      </div>

      {/* Column Documentation */}
      {entries.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {entries.map(entry => (
            <DictionaryEntryRow
              key={entry.id}
              entry={entry}
              isEditing={editingEntry === entry.id}
              editForm={editForm}
              versionNotes={versionNotes}
              saving={saving}
              onStartEditing={() => onStartEditing(entry)}
              onCancelEditing={onCancelEditing}
              onSave={() => onSaveEntry(entry.id)}
              onEditFormChange={onEditFormChange}
              onVersionNotesChange={onVersionNotesChange}
              onAddTag={onAddTag}
              onRemoveTag={onRemoveTag}
              onViewVersionHistory={() => onViewVersionHistory(entry)}
              onSubmitForApproval={() => onSubmitForApproval(entry.id)}
              onApprove={() => onApprove(entry.id)}
              onReject={() => onReject(entry.id)}
            />
          ))}
        </div>
      )}
    </>
  )
}
