/**
 * Modal for creating new review queues.
 */
import { X } from 'lucide-react'
import { NewQueue } from '../../../types/distillation'

interface CreateQueueModalProps {
  open: boolean
  onClose: () => void
  newQueue: NewQueue
  setNewQueue: (queue: NewQueue) => void
  handleCreateQueue: () => void
}

export default function CreateQueueModal({
  open,
  onClose,
  newQueue,
  setNewQueue,
  handleCreateQueue
}: CreateQueueModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="rounded-lg p-6 w-full max-w-md" style={{
        backgroundColor: 'rgba(30, 30, 40, 0.95)',
        border: '1px solid rgba(168, 216, 255, 0.3)'
      }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Create Review Queue</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Name</label>
            <input
              type="text"
              value={newQueue.name}
              onChange={e => setNewQueue({ ...newQueue, name: e.target.value })}
              placeholder="e.g., Insurance Q&A Review"
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            />
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Description</label>
            <textarea
              value={newQueue.description}
              onChange={e => setNewQueue({ ...newQueue, description: e.target.value })}
              placeholder="Optional description..."
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
            onClick={handleCreateQueue}
            disabled={!newQueue.name}
            className="w-full py-2 rounded-lg disabled:opacity-50"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.2)',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              color: '#a8d8ff'
            }}
          >
            Create Queue
          </button>
        </div>
      </div>
    </div>
  )
}
