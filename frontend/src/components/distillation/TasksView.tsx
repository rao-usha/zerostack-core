/**
 * Task Library view for Distillation Workbench.
 * Displays and manages automated knowledge extraction tasks.
 */
import { Plus, Play } from 'lucide-react'
import { Task } from '../../types/distillation'

interface TasksViewProps {
  tasks: Task[]
  setCreateTaskOpen: (open: boolean) => void
}

export default function TasksView({ tasks, setCreateTaskOpen }: TasksViewProps) {
  return (
    <div className="rounded-lg p-6" style={{
      backgroundColor: 'rgba(30, 30, 40, 0.8)',
      border: '1px solid rgba(168, 216, 255, 0.2)'
    }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>Task Library</h2>
        <button
          onClick={() => setCreateTaskOpen(true)}
          className="px-3 py-2 rounded-lg flex items-center space-x-2 hover:bg-opacity-25 transition-all"
          style={{
            backgroundColor: 'rgba(168, 216, 255, 0.15)',
            border: '1px solid rgba(168, 216, 255, 0.4)',
            color: '#a8d8ff'
          }}
        >
          <Plus className="h-4 w-4" /><span>New Task</span>
        </button>
      </div>

      {tasks.length === 0 ? (
        <p style={{ color: '#b3d9ff' }}>No tasks created yet. Create a task to automate knowledge extraction.</p>
      ) : (
        <div className="space-y-3">
          {tasks.map(task => (
            <div key={task.id} className="p-4 rounded-lg flex items-center justify-between" style={{
              backgroundColor: 'rgba(20, 20, 30, 0.6)',
              border: '1px solid rgba(168, 216, 255, 0.1)'
            }}>
              <div>
                <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{task.name}</h3>
                <p className="text-sm mt-1" style={{ color: '#b3d9ff' }}>{task.description || `Type: ${task.task_type}`}</p>
                <div className="flex items-center space-x-2 mt-2">
                  {task.target_models.map(model => (
                    <span key={model} className="px-2 py-0.5 rounded text-xs" style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.1)',
                      color: '#a8d8ff'
                    }}>{model}</span>
                  ))}
                </div>
              </div>
              <button className="p-2 rounded hover:bg-white/10" style={{ color: '#10b981' }}>
                <Play className="h-5 w-5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
