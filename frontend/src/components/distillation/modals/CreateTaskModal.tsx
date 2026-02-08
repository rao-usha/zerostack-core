/**
 * Modal for creating new tasks.
 */
import { X, Loader2 } from 'lucide-react'
import { NewTask, Domain, Topic, AvailableModel } from '../../../types/distillation'

interface CreateTaskModalProps {
  open: boolean
  onClose: () => void
  newTask: NewTask
  setNewTask: (task: NewTask) => void
  handleCreateTask: () => void
  taskLoading: boolean
  domains: Domain[]
  topics: Topic[]
  availableModels: AvailableModel[]
  apiKeys: Record<string, boolean>
}

export default function CreateTaskModal({
  open,
  onClose,
  newTask,
  setNewTask,
  handleCreateTask,
  taskLoading,
  domains,
  topics,
  availableModels,
  apiKeys
}: CreateTaskModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto" style={{
        backgroundColor: 'rgba(30, 30, 40, 0.95)',
        border: '1px solid rgba(168, 216, 255, 0.3)'
      }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Create New Task</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Task Name *</label>
            <input
              type="text"
              value={newTask.name}
              onChange={e => setNewTask({ ...newTask, name: e.target.value })}
              placeholder="e.g., Insurance FAQ Generator"
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
            <input
              type="text"
              value={newTask.description}
              onChange={e => setNewTask({ ...newTask, description: e.target.value })}
              placeholder="Optional description..."
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            />
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Task Type</label>
            <select
              value={newTask.task_type}
              onChange={e => setNewTask({ ...newTask, task_type: e.target.value })}
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            >
              <option value="freeform">Freeform</option>
              <option value="qa">Q&A</option>
              <option value="summary">Summary</option>
              <option value="instruction">Instruction</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Prompt Template *</label>
            <textarea
              value={newTask.prompt_template}
              onChange={e => setNewTask({ ...newTask, prompt_template: e.target.value })}
              placeholder="Enter the prompt template. Use {{variable}} for dynamic values..."
              className="w-full px-3 py-2 rounded-lg font-mono text-sm"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
              rows={4}
            />
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>System Prompt</label>
            <textarea
              value={newTask.system_prompt}
              onChange={e => setNewTask({ ...newTask, system_prompt: e.target.value })}
              placeholder="Optional system prompt for the model..."
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
              rows={2}
            />
          </div>
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Target Models</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {newTask.target_models.map((model, idx) => (
                <span key={idx} className="px-2 py-1 rounded text-xs flex items-center space-x-1" style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  color: '#a8d8ff'
                }}>
                  <span>{model}</span>
                  <button
                    onClick={() => setNewTask({
                      ...newTask,
                      target_models: newTask.target_models.filter((_, i) => i !== idx)
                    })}
                    className="hover:text-red-400"
                  >×</button>
                </span>
              ))}
            </div>
            <select
              value=""
              onChange={e => {
                if (e.target.value && !newTask.target_models.includes(e.target.value)) {
                  setNewTask({
                    ...newTask,
                    target_models: [...newTask.target_models, e.target.value]
                  })
                }
              }}
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            >
              <option value="">+ Add model</option>
              {availableModels
                .filter(m => !newTask.target_models.includes(m.id) && apiKeys[m.provider])
                .map(m => (
                  <option key={m.id} value={m.id}>{m.provider}: {m.name}</option>
                ))
              }
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Domain</label>
              <select
                value={newTask.domain_id}
                onChange={e => setNewTask({ ...newTask, domain_id: e.target.value })}
                className="w-full px-3 py-2 rounded-lg"
                style={{
                  backgroundColor: 'rgba(20, 20, 30, 0.8)',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
              >
                <option value="">No domain</option>
                {domains.map(d => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Topic</label>
              <select
                value={newTask.topic_id}
                onChange={e => setNewTask({ ...newTask, topic_id: e.target.value })}
                className="w-full px-3 py-2 rounded-lg"
                style={{
                  backgroundColor: 'rgba(20, 20, 30, 0.8)',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
              >
                <option value="">No topic</option>
                {topics.map(t => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex space-x-3 pt-2">
            <button
              onClick={onClose}
              className="flex-1 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(100, 100, 100, 0.2)',
                border: '1px solid rgba(100, 100, 100, 0.4)',
                color: '#999'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleCreateTask}
              disabled={!newTask.name.trim() || !newTask.prompt_template.trim() || taskLoading}
              className="flex-1 py-2 rounded-lg disabled:opacity-50 flex items-center justify-center space-x-2"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.2)',
                border: '1px solid rgba(168, 216, 255, 0.4)',
                color: '#a8d8ff'
              }}
            >
              {taskLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Creating...</span>
                </>
              ) : (
                <span>Create Task</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
