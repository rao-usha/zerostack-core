/**
 * Notebook page - SQL and Python cells with execution.
 * Refactored to use modular components.
 */
import { useParams } from 'react-router-dom'
import Toast from '../components/Toast'
import { useNotebook } from '../hooks/useNotebook'
import {
  NotebookHeader,
  NotebookCell,
  VariablesSidebar,
  SaveDatasetModal,
  AddCellButtons,
  styles
} from '../components/notebook'

export default function NotebookPage() {
  const { notebookId } = useParams<{ notebookId: string }>()
  const [state, actions] = useNotebook(notebookId)

  const {
    notebook,
    connections,
    loading,
    error,
    executingCell,
    cellResults,
    editingName,
    showSaveDataset,
    datasetName,
    sessionVariables,
    toast,
    newCellRef
  } = state

  const {
    addCell,
    updateCell,
    deleteCell,
    executeCell,
    executeAllCells,
    resetSession,
    saveAsDataset,
    updateNotebookName,
    updateDefaultConnection,
    setEditingName,
    setShowSaveDataset,
    setDatasetName,
    setError,
    setToast,
    navigateBack
  } = actions

  // Loading state
  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingState}>
          <div style={styles.spinner} />
          <p>Loading notebook...</p>
        </div>
      </div>
    )
  }

  // Not found state
  if (!notebook) {
    return (
      <div style={styles.container}>
        <div style={styles.errorState}>
          <p>Notebook not found</p>
          <button onClick={navigateBack} style={styles.backButton}>
            ← Back to Notebooks
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <NotebookHeader
        notebook={notebook}
        connections={connections}
        editingName={editingName}
        onNavigateBack={navigateBack}
        onEditName={() => setEditingName(true)}
        onUpdateName={updateNotebookName}
        onUpdateConnection={updateDefaultConnection}
        onResetSession={resetSession}
        onRunAll={executeAllCells}
      />

      {/* Error Banner */}
      {error && (
        <div style={styles.errorBanner}>
          {error}
          <button onClick={() => setError(null)} style={styles.errorClose}>×</button>
        </div>
      )}

      {/* Cells */}
      <main style={styles.main}>
        {notebook.cells.length === 0 ? (
          <div style={styles.emptyState}>
            <p>No cells yet. Add your first cell to start.</p>
            <AddCellButtons
              onAddSQL={() => addCell('sql')}
              onAddPython={() => addCell('python')}
              onAddMarkdown={() => addCell('markdown')}
              isEmptyState
            />
          </div>
        ) : (
          <>
            {notebook.cells.map((cell, index) => (
              <NotebookCell
                key={cell.id}
                cell={cell}
                index={index}
                isExecuting={executingCell === cell.id}
                hasConnection={!!notebook.default_connection_id}
                result={cellResults[cell.id]}
                isLastCell={index === notebook.cells.length - 1}
                newCellRef={newCellRef}
                onUpdateContent={(content) => updateCell(cell.id, content)}
                onExecute={() => executeCell(cell)}
                onDelete={() => deleteCell(cell.id)}
                onSaveAsDataset={() => {
                  setShowSaveDataset(cell.id)
                  setDatasetName(`Dataset from Cell ${index + 1}`)
                }}
              />
            ))}

            {/* Add Cell Buttons */}
            <AddCellButtons
              onAddSQL={() => addCell('sql')}
              onAddPython={() => addCell('python')}
              onAddMarkdown={() => addCell('markdown')}
            />
          </>
        )}
      </main>

      {/* Variables Sidebar */}
      <VariablesSidebar variables={sessionVariables} />

      {/* Save Dataset Modal */}
      {showSaveDataset && (
        <SaveDatasetModal
          datasetName={datasetName}
          onNameChange={setDatasetName}
          onSave={() => saveAsDataset(showSaveDataset)}
          onClose={() => setShowSaveDataset(null)}
        />
      )}

      {/* Keyboard Shortcuts */}
      <div style={styles.shortcuts}>
        <span>Ctrl+Enter to run cell</span>
      </div>

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
