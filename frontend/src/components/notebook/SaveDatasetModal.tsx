/**
 * Save as Dataset modal component.
 */
import { styles } from './styles'

interface SaveDatasetModalProps {
  datasetName: string
  onNameChange: (name: string) => void
  onSave: () => void
  onClose: () => void
}

export default function SaveDatasetModal({
  datasetName,
  onNameChange,
  onSave,
  onClose
}: SaveDatasetModalProps) {
  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modal} onClick={e => e.stopPropagation()}>
        <h3 style={{ margin: '0 0 16px 0', color: '#f0f0f5' }}>💾 Save as Dataset</h3>
        <input
          type="text"
          value={datasetName}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Dataset name"
          style={styles.modalInput}
          autoFocus
        />
        <div style={styles.modalActions}>
          <button onClick={onClose} style={styles.modalCancel}>Cancel</button>
          <button onClick={onSave} style={styles.modalSubmit}>Save</button>
        </div>
      </div>
    </div>
  )
}
