/**
 * Add cell buttons component.
 */
import { styles } from './styles'

interface AddCellButtonsProps {
  onAddSQL: () => void
  onAddPython: () => void
  onAddMarkdown: () => void
  isEmptyState?: boolean
}

export default function AddCellButtons({
  onAddSQL,
  onAddPython,
  onAddMarkdown,
  isEmptyState = false
}: AddCellButtonsProps) {
  const containerStyle = isEmptyState ? styles.addCellButtons : styles.addCellRow

  return (
    <div style={containerStyle}>
      <button onClick={onAddSQL} style={styles.addCellBtn}>
        ⚡ SQL
      </button>
      <button
        onClick={onAddPython}
        style={{
          ...styles.addCellBtn,
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          borderColor: 'rgba(16, 185, 129, 0.4)',
          color: '#10b981'
        }}
      >
        🐍 Python
      </button>
      <button
        onClick={onAddMarkdown}
        style={{
          ...styles.addCellBtn,
          backgroundColor: 'transparent',
          border: '1px solid rgba(255,255,255,0.2)',
          color: '#9ca3af'
        }}
      >
        📝 Markdown
      </button>
    </div>
  )
}
