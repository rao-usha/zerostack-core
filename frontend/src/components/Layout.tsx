import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Upload, 
  Sparkles, 
  MessageCircle, 
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Database
} from 'lucide-react'
import FloatingChat from './FloatingChat'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/upload', icon: Upload, label: 'Upload Data' },
    { path: '/insights', icon: Sparkles, label: 'Insights' },
    { path: '/quality', icon: CheckCircle2, label: 'Data Quality' },
    { path: '/gaps', icon: AlertCircle, label: 'Knowledge Gaps' },
    { path: '/models', icon: TrendingUp, label: 'Predictive Models' },
    { path: '/synthetic', icon: Database, label: 'Synthetic Data' },
  ]

  return (
    <div className="min-h-screen bg-dark-bg">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-dark-surface shadow-2xl min-h-screen border-r border-dark-border flex flex-col">
          {/* NEX.AI Logo */}
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
                  NEX.AI
                </h1>
                <p className="text-xs" style={{ color: '#b3d9ff' }}>AI Native Data Platform</p>
              </div>
            </div>
          </div>
          
          <nav className="p-4 space-y-2 flex-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
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
        <main className="flex-1 p-8 bg-dark-bg mr-96 min-h-screen">
          {children}
        </main>

        {/* Fixed Right Chat Sidebar */}
        <FloatingChat />
      </div>
    </div>
  )
}

