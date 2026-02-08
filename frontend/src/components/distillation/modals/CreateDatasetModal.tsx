/**
 * Modal for creating new datasets.
 */
import { X } from 'lucide-react'
import { NewDataset } from '../../../types/distillation'

interface CreateDatasetModalProps {
  open: boolean
  onClose: () => void
  newDataset: NewDataset
  setNewDataset: (dataset: NewDataset) => void
  handleCreateDataset: () => void
}

export default function CreateDatasetModal({
  open,
  onClose,
  newDataset,
  setNewDataset,
  handleCreateDataset
}: CreateDatasetModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="rounded-lg p-6 w-full max-w-md" style={{
        backgroundColor: 'rgba(30, 30, 40, 0.95)',
        border: '1px solid rgba(168, 216, 255, 0.3)'
      }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Create Dataset</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Name</label>
            <input
              type="text"
              value={newDataset.name}
              onChange={e => setNewDataset({ ...newDataset, name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            />
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Version</label>
            <input
              type="text"
              value={newDataset.version}
              onChange={e => setNewDataset({ ...newDataset, version: e.target.value })}
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            />
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Type</label>
            <select
              value={newDataset.dataset_type}
              onChange={e => setNewDataset({ ...newDataset, dataset_type: e.target.value })}
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            >
              <option value="training">Training</option>
              <option value="evaluation">Evaluation</option>
              <option value="benchmark">Benchmark</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Description</label>
            <textarea
              value={newDataset.description}
              onChange={e => setNewDataset({ ...newDataset, description: e.target.value })}
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
              rows={3}
            />
          </div>
          <button
            onClick={handleCreateDataset}
            disabled={!newDataset.name || !newDataset.version}
            className="w-full py-2 rounded-lg disabled:opacity-50"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.2)',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              color: '#a8d8ff'
            }}
          >
            Create Dataset
          </button>
        </div>
      </div>
    </div>
  )
}
