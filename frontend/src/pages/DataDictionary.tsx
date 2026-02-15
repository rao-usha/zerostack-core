/**
 * Data Dictionary page - AI-generated column documentation.
 * Refactored to use modular components.
 */
import {
  Book,
  Search,
  FileText,
  AlertCircle,
  Loader2
} from 'lucide-react'
import Toast from '../components/Toast'
import { useDataDictionary } from '../hooks/useDataDictionary'
import {
  SchemaSidebar,
  DictionaryTable,
  VersionHistoryModal,
  ApprovalModal
} from '../components/dataDictionary'

export default function DataDictionary() {
  const [state, actions] = useDataDictionary()

  const {
    databases,
    selectedDbId,
    schemas,
    expandedSchemas,
    tablesBySchema,
    loadingNav,
    loading,
    error,
    searchTerm,
    selectedTable,
    displayedEntries,
    documentedTables,
    totalTables,
    entries,
    editingEntry,
    editForm,
    versionNotes,
    saving,
    viewingVersions,
    versions,
    loadingVersions,
    toast,
    approvalModal,
    approvalNotes
  } = state

  const {
    setSelectedDbId,
    setSearchTerm,
    toggleSchema,
    selectTable,
    generateDocumentation,
    getTableDocStatus,
    startEditing,
    cancelEditing,
    saveEntry,
    setEditForm,
    setVersionNotes,
    addTag,
    removeTag,
    viewVersionHistory,
    activateVersion,
    closeVersionHistory,
    handleSubmitForApproval,
    handleApprove,
    handleReject,
    submitApprovalAction,
    cancelApprovalAction,
    setApprovalNotes,
    closeToast
  } = actions

  return (
    <div style={{ height: '100vh', overflow: 'hidden', backgroundColor: '#0a0a0f', color: '#f0f0f5', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)', padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
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

          {/* Database Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <select
              value={selectedDbId}
              onChange={(e) => setSelectedDbId(e.target.value)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#0f0f17',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontSize: '0.875rem',
                minWidth: '200px'
              }}
            >
              {databases.map(db => (
                <option key={db.id} value={db.id}>{db.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats */}
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1.5rem', fontSize: '0.875rem', color: '#9ca3af' }}>
          <span>{documentedTables.size} of {totalTables} tables documented</span>
          <span>{entries.filter(e => e.database_name === selectedDbId).length} columns</span>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Sidebar - Table Navigator */}
        <div style={{
          width: '320px',
          borderRight: '1px solid rgba(168, 216, 255, 0.2)',
          backgroundColor: '#0f0f17',
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          overflow: 'hidden'
        }}>
          <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
            <SchemaSidebar
              schemas={schemas}
              expandedSchemas={expandedSchemas}
              tablesBySchema={tablesBySchema}
              selectedTable={selectedTable}
              loading={loadingNav}
              onToggleSchema={toggleSchema}
              onSelectTable={selectTable}
              onGenerateDocumentation={generateDocumentation}
              getTableDocStatus={getTableDocStatus}
            />
          </div>
        </div>

        {/* Right Panel - Documentation Display */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Search Bar */}
          <div style={{ padding: '1.5rem 2rem', borderBottom: '1px solid rgba(168, 216, 255, 0.2)' }}>
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

          {/* Content Area */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>
            {loading && (
              <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                <p>Loading dictionary...</p>
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

            {!loading && !error && selectedTable && (
              <DictionaryTable
                selectedTable={selectedTable}
                entries={displayedEntries}
                editingEntry={editingEntry}
                editForm={editForm}
                versionNotes={versionNotes}
                saving={saving}
                onGenerateDocumentation={() => generateDocumentation(selectedTable.schema, selectedTable.table)}
                onStartEditing={startEditing}
                onCancelEditing={cancelEditing}
                onSaveEntry={saveEntry}
                onEditFormChange={setEditForm}
                onVersionNotesChange={setVersionNotes}
                onAddTag={addTag}
                onRemoveTag={removeTag}
                onViewVersionHistory={viewVersionHistory}
                onSubmitForApproval={handleSubmitForApproval}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            )}

            {!loading && !error && !selectedTable && (
              <div style={{ textAlign: 'center', padding: '4rem 2rem', color: '#9ca3af' }}>
                <Book className="h-16 w-16 mx-auto mb-4" style={{ color: '#4b5563' }} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: '500', marginBottom: '0.5rem', color: '#d1d5db' }}>
                  Select a Table
                </h3>
                <p style={{ fontSize: '0.875rem' }}>
                  Choose a table from the left sidebar to view its column documentation.
                </p>
                <div style={{ marginTop: '1.5rem', fontSize: '0.8125rem' }}>
                  <p style={{ marginBottom: '0.5rem' }}>Legend:</p>
                  <div style={{ display: 'inline-flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <FileText className="h-4 w-4" style={{ color: '#22c55e' }} />
                      <span>Documented table</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <AlertCircle className="h-4 w-4" style={{ color: '#f59e0b' }} />
                      <span>Undocumented table</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Version History Modal */}
      {viewingVersions && (
        <VersionHistoryModal
          entry={viewingVersions}
          versions={versions}
          loading={loadingVersions}
          saving={saving}
          onClose={closeVersionHistory}
          onActivateVersion={activateVersion}
        />
      )}

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={closeToast}
        />
      )}

      {/* Approval/Rejection Modal */}
      <ApprovalModal
        modal={approvalModal}
        notes={approvalNotes}
        saving={saving}
        onNotesChange={setApprovalNotes}
        onSubmit={submitApprovalAction}
        onCancel={cancelApprovalAction}
      />
    </div>
  )
}
