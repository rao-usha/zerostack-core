import { ReactNode, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Upload,
  Sparkles,
  MessageCircle,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  Database,
  Layers,
  Table,
  Brain,
  Book,
  Activity,
  FlaskConical,
  FolderOpen,
  PlugZap,
  FileCode2,
  HardDrive,
  WifiOff,
  Settings,
  Network,
  FolderInput,
  Cpu,
  DollarSign,
  Package,
  Gauge,
  ScanLine
} from 'lucide-react'
import { LucideIcon } from 'lucide-react'
import { checkBackendHealth } from '../api/health'
import NavGroup from './NavGroup'

function HealthIndicator() {
  const [healthy, setHealthy] = useState(true)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const check = async () => {
      setChecking(true)
      const isHealthy = await checkBackendHealth()
      setHealthy(isHealthy)
      setChecking(false)
    }

    check()
    const interval = setInterval(check, 30000) // Check every 30s
    return () => clearInterval(interval)
  }, [])

  if (checking || healthy) return null

  return (
    <div
      style={{
        backgroundColor: 'rgba(239, 68, 68, 0.15)',
        borderBottom: '1px solid rgba(239, 68, 68, 0.5)',
        color: '#f87171',
        padding: '0.75rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.5rem',
        fontSize: '0.875rem'
      }}
    >
      <WifiOff size={16} />
      <span>Backend connection lost. Some features may not work.</span>
    </div>
  )
}

interface LayoutProps {
  children: ReactNode
}

interface NavItem {
  path: string
  icon: LucideIcon
  label: string
}

interface NavGroupConfig {
  type: 'group'
  label: string
  icon: LucideIcon
  storageKey: string
  defaultExpanded?: boolean
  items: NavItem[]
}

interface NavStandaloneItem {
  type: 'item'
  path: string
  icon: LucideIcon
  label: string
}

interface NavDivider {
  type: 'divider'
}

type NavStructureItem = NavGroupConfig | NavStandaloneItem | NavDivider

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const navStructure: NavStructureItem[] = [
    // Dashboard (standalone - always visible)
    { type: 'item', path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { type: 'divider' },

    // Data group
    {
      type: 'group',
      label: 'Data',
      icon: FolderInput,
      storageKey: 'data',
      defaultExpanded: true,
      items: [
        { path: '/upload', icon: Upload, label: 'Upload Data' },
        { path: '/data-ingestion', icon: ScanLine, label: 'PE Due Diligence' },
        { path: '/data-sources', icon: PlugZap, label: 'Data Sources' },
        { path: '/datasets', icon: HardDrive, label: 'Datasets' },
        { path: '/files/locations', icon: FolderOpen, label: 'Files' },
        { path: '/explorer', icon: Table, label: 'Data Explorer' },
      ]
    },
    { type: 'divider' },

    // Analysis & Documentation group
    {
      type: 'group',
      label: 'Analysis & Docs',
      icon: Brain,
      storageKey: 'analysis',
      defaultExpanded: false,
      items: [
        { path: '/analysis', icon: Brain, label: 'Data Analysis' },
        { path: '/dictionary', icon: Book, label: 'Data Dictionary' },
        { path: '/quality', icon: CheckCircle2, label: 'Data Quality' },
        { path: '/gaps', icon: AlertCircle, label: 'Knowledge Gaps' },
      ]
    },
    { type: 'divider' },

    // Development group
    {
      type: 'group',
      label: 'Development',
      icon: FileCode2,
      storageKey: 'development',
      defaultExpanded: false,
      items: [
        { path: '/notebooks', icon: FileCode2, label: 'SQL Notebooks' },
        { path: '/contexts', icon: Layers, label: 'Contexts' },
        { path: '/ontology', icon: Network, label: 'Ontology' },
      ]
    },
    { type: 'divider' },

    // AI & Models group
    {
      type: 'group',
      label: 'AI & Models',
      icon: Cpu,
      storageKey: 'ai-models',
      defaultExpanded: false,
      items: [
        { path: '/model-development', icon: Activity, label: 'Model Development' },
        { path: '/model-development/registry', icon: Package, label: 'Model Registry' },
        { path: '/model-development/monitoring', icon: Gauge, label: 'Model Monitoring' },
        { path: '/model-development/drift', icon: AlertTriangle, label: 'Drift Detection' },
        { path: '/model-development/costs', icon: DollarSign, label: 'Cost Analytics' },
        { path: '/distillation', icon: FlaskConical, label: 'Distillation' },
        { path: '/models', icon: TrendingUp, label: 'Predictive Models' },
        { path: '/synthetic', icon: Database, label: 'Synthetic Data' },
        { path: '/insights', icon: Sparkles, label: 'Insights' },
      ]
    },
    { type: 'divider' },

    // Chat with Data (standalone)
    { type: 'item', path: '/chat', icon: MessageCircle, label: 'Chat with Data' },
    { type: 'divider' },

    // Settings (standalone - bottom)
    { type: 'item', path: '/settings', icon: Settings, label: 'Settings' },
  ]

  // Helper to check if a path is active
  const isPathActive = (path: string) => {
    if (path === '/files/locations') {
      return location.pathname.startsWith('/files')
    }
    return location.pathname === path
  }

  // Helper to check if any item in a group is active
  const isGroupActive = (items: NavItem[]) => {
    return items.some(item => isPathActive(item.path))
  }

  // Render a single nav item
  const renderNavItem = (item: NavItem, indent: boolean = false) => {
    const Icon = item.icon
    const isActive = isPathActive(item.path)
    return (
      <Link
        key={item.path}
        to={item.path}
        className={`flex items-center space-x-3 px-4 py-2.5 rounded-lg transition-all duration-200 ${indent ? 'text-sm' : ''}`}
        style={isActive ? {
          background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
          color: '#a8d8ff',
          border: '1px solid rgba(168, 216, 255, 0.4)'
        } : {
          color: '#f0f0f5'
        }}
      >
        <Icon className={indent ? 'h-4 w-4' : 'h-5 w-5'} />
        <span className="font-medium">{item.label}</span>
      </Link>
    )
  }

  return (
    <div className="min-h-screen bg-dark-bg">
      <HealthIndicator />
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-dark-surface shadow-2xl min-h-screen border-r border-dark-border flex flex-col">
          {/* zerostack Logo */}
          <div className="p-6 border-b border-dark-border">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg" style={{
                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                border: '1px solid rgba(168, 216, 255, 0.4)'
              }}>
                <Database className="h-6 w-6" style={{ color: '#a8d8ff' }} />
              </div>
              <div>
                <h1 className="text-2xl font-bold" style={{
                  background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 50%, #ffc4e5 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text'
                }}>
                  zerostack
                </h1>
                <p className="text-xs" style={{ color: '#b3d9ff' }}>AI Native Data Platform</p>
              </div>
            </div>
          </div>
          
          <nav className="p-4 space-y-1 flex-1 overflow-y-auto">
            {navStructure.map((entry, index) => {
              if (entry.type === 'divider') {
                return (
                  <div
                    key={`divider-${index}`}
                    className="my-2 border-t border-dark-border/50"
                  />
                )
              }

              if (entry.type === 'item') {
                return renderNavItem(entry, false)
              }

              if (entry.type === 'group') {
                const groupActive = isGroupActive(entry.items)
                return (
                  <NavGroup
                    key={entry.storageKey}
                    title={entry.label}
                    icon={entry.icon}
                    storageKey={entry.storageKey}
                    defaultExpanded={entry.defaultExpanded}
                    isActive={groupActive}
                  >
                    {entry.items.map(item => renderNavItem(item, true))}
                  </NavGroup>
                )
              }

              return null
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8 bg-dark-bg min-h-screen">
          {children}
        </main>
      </div>
    </div>
  )
}

