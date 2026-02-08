/**
 * Sidebar navigation for Distillation Workbench.
 */
import {
  MessageSquare, List, Database, GitCompare, FileJson,
  ClipboardCheck, FolderOpen, BarChart3, LucideIcon
} from 'lucide-react'
import { ViewMode, Statistics, StructuredItem, Dataset } from '../../types/distillation'

interface NavItem {
  mode: ViewMode
  label: string
  icon: LucideIcon
}

const navItems: NavItem[] = [
  { mode: 'chat', label: 'Interactive Chat', icon: MessageSquare },
  { mode: 'tasks', label: 'Task Library', icon: List },
  { mode: 'bank', label: 'Response Bank', icon: Database },
  { mode: 'compare', label: 'Compare', icon: GitCompare },
  { mode: 'structure', label: 'Structure', icon: FileJson },
  { mode: 'review', label: 'Expert Review', icon: ClipboardCheck },
  { mode: 'datasets', label: 'Datasets', icon: FolderOpen },
  { mode: 'stats', label: 'Statistics', icon: BarChart3 },
]

interface SidebarProps {
  viewMode: ViewMode
  setViewMode: (mode: ViewMode) => void
  statistics: Statistics | null
  structuredItems: StructuredItem[]
  datasets: Dataset[]
}

export default function Sidebar({
  viewMode,
  setViewMode,
  statistics,
  structuredItems,
  datasets
}: SidebarProps) {
  return (
    <div
      className="lg:col-span-1 rounded-lg p-4"
      style={{
        backgroundColor: 'rgba(30, 30, 40, 0.8)',
        border: '1px solid rgba(168, 216, 255, 0.2)'
      }}
    >
      <h2 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>
        Workbench
      </h2>
      <div className="space-y-2">
        {navItems.map(({ mode, label, icon: Icon }) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all"
            style={
              viewMode === mode
                ? {
                    background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                    color: '#a8d8ff',
                    border: '1px solid rgba(168, 216, 255, 0.4)'
                  }
                : { color: '#f0f0f5' }
            }
          >
            <Icon className="h-5 w-5" />
            <span className="font-medium">{label}</span>
          </button>
        ))}
      </div>

      {/* Quick Stats */}
      {statistics && (
        <div className="mt-6 space-y-2">
          <h3 className="text-sm font-semibold" style={{ color: '#a8d8ff' }}>
            Quick Stats
          </h3>
          <div className="text-sm" style={{ color: '#b3d9ff' }}>
            <div className="flex justify-between">
              <span>Responses:</span>
              <span>{statistics.total_responses}</span>
            </div>
            <div className="flex justify-between">
              <span>Banked:</span>
              <span>{statistics.total_banked}</span>
            </div>
            <div className="flex justify-between">
              <span>Structured:</span>
              <span>{structuredItems.length}</span>
            </div>
            <div className="flex justify-between">
              <span>Datasets:</span>
              <span>{datasets.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
