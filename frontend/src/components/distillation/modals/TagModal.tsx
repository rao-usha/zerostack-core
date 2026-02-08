/**
 * Tag modal for adding tags to responses.
 */
import { X } from 'lucide-react'
import { TagItem } from '../../../types/distillation'

interface TagModalProps {
  open: boolean
  onClose: () => void
  tags: TagItem[]
  newTagName: string
  setNewTagName: (name: string) => void
  handleAddTags: () => void
}

export default function TagModal({
  open,
  onClose,
  tags,
  newTagName,
  setNewTagName,
  handleAddTags
}: TagModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="rounded-lg p-6 w-full max-w-md" style={{
        backgroundColor: 'rgba(30, 30, 40, 0.95)',
        border: '1px solid rgba(168, 216, 255, 0.3)'
      }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Add Tags</h3>
          <button onClick={() => { onClose(); setNewTagName('') }} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex space-x-2 mb-4">
          <input
            type="text"
            value={newTagName}
            onChange={e => setNewTagName(e.target.value)}
            placeholder="Enter tag name..."
            className="flex-1 px-3 py-2 rounded-lg"
            style={{
              backgroundColor: 'rgba(20, 20, 30, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              color: '#f0f0f5'
            }}
            onKeyPress={e => e.key === 'Enter' && handleAddTags()}
          />
          <button
            onClick={handleAddTags}
            disabled={!newTagName.trim()}
            className="px-4 py-2 rounded-lg disabled:opacity-50"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.2)',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              color: '#a8d8ff'
            }}
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {tags.map(tag => (
            <button
              key={tag.id}
              onClick={() => setNewTagName(tag.name)}
              className="px-2 py-1 rounded text-xs"
              style={{ backgroundColor: tag.color || 'rgba(168, 216, 255, 0.1)', color: '#f0f0f5' }}
            >
              {tag.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
