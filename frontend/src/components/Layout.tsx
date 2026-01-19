import { ReactNode, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Upload,
  Sparkles,
  MessageCircle,
  CheckCircle2,
  AlertCircle,
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
  WifiOff
} from 'lucide-react'
import { checkBackendHealth } from '../api/health'

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

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/upload', icon: Upload, label: 'Upload Data' },
    { path: '/contexts', icon: Layers, label: 'Contexts' },
    { path: '/data-sources', icon: PlugZap, label: 'Data Sources' },
    { path: '/notebooks', icon: FileCode2, label: 'SQL Notebooks' },
    { path: '/datasets', icon: HardDrive, label: 'Datasets' },
    { path: '/explorer', icon: Table, label: 'Data Explorer' },
    { path: '/analysis', icon: Brain, label: 'Data Analysis' },
    { path: '/dictionary', icon: Book, label: 'Data Dictionary' },
    { path: '/files/locations', icon: FolderOpen, label: 'Files' },
    { path: '/model-development', icon: Activity, label: 'Model Development' },
    { path: '/distillation', icon: FlaskConical, label: 'Distillation' },
    { path: '/chat', icon: MessageCircle, label: 'Chat with Data' },
    { path: '/insights', icon: Sparkles, label: 'Insights' },
    { path: '/quality', icon: CheckCircle2, label: 'Data Quality' },
    { path: '/gaps', icon: AlertCircle, label: 'Knowledge Gaps' },
    { path: '/models', icon: TrendingUp, label: 'Predictive Models' },
    { path: '/synthetic', icon: Database, label: 'Synthetic Data' },
  ]

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
          
          <nav className="p-4 space-y-2 flex-1">
            {navItems.map((item) => {
              const Icon = item.icon
              // Special handling for Files menu - highlight on any /files/* route
              const isActive = item.path === '/files/locations' 
                ? location.pathname.startsWith('/files')
                : location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className="flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200"
                  style={isActive ? {
                    background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                    color: '#a8d8ff',
                    border: '1px solid rgba(168, 216, 255, 0.4)'
                  } : {
                    color: '#f0f0f5'
                  }}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              )
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

