/**
 * Notebook header with title, connection selector, and actions.
 */
import { Notebook, DataConnection } from '../../types/notebook'
import { styles } from './styles'

interface NotebookHeaderProps {
  notebook: Notebook
  connections: DataConnection[]
  editingName: boolean
  onNavigateBack: () => void
  onEditName: () => void
  onUpdateName: (name: string) => void
  onUpdateConnection: (connectionId: string) => void
  onResetSession: () => void
  onRunAll: () => void
}

export default function NotebookHeader({
  notebook,
  connections,
  editingName,
  onNavigateBack,
  onEditName,
  onUpdateName,
  onUpdateConnection,
  onResetSession,
  onRunAll
}: NotebookHeaderProps) {
  return (
    <header style={styles.header}>
      <div style={styles.headerLeft}>
        <button onClick={onNavigateBack} style={styles.backLink}>←</button>
        {editingName ? (
          <input
            type="text"
            defaultValue={notebook.name}
            autoFocus
            onBlur={(e) => onUpdateName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onUpdateName((e.target as HTMLInputElement).value)}
            style={styles.nameInput}
          />
        ) : (
          <h1 style={styles.title} onClick={onEditName}>
            📓 {notebook.name}
          </h1>
        )}
      </div>

      <div style={styles.headerActions}>
        <select
          value={notebook.default_connection_id || ''}
          onChange={(e) => onUpdateConnection(e.target.value)}
          style={styles.connectionSelect}
        >
          <option value="">Select connection...</option>
          {connections.map(c => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.database})
            </option>
          ))}
        </select>

        <button onClick={onResetSession} style={styles.resetButton} title="Reset Python session">
          🔄 Reset
        </button>

        <button onClick={onRunAll} style={styles.runAllButton}>
          ▶ Run All
        </button>
      </div>
    </header>
  )
}
