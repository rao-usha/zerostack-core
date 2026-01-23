import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Database,
  Upload,
  MessageCircle,
  FileCode2,
  FolderOpen,
  Table,
  PlugZap,
  ArrowRight,
  Clock,
  HardDrive
} from 'lucide-react'
import { listDatasets, listFileAssets, getDataSources, listFileLocations } from '../api/client'

interface Stats {
  datasets: number
  files: number
  dataSources: number
  tables: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({ datasets: 0, files: 0, dataSources: 0, tables: 0 })
  const [recentDatasets, setRecentDatasets] = useState<any[]>([])
  const [recentFiles, setRecentFiles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [datasetsRes, filesRes, dataSourcesRes, locationsRes] = await Promise.allSettled([
        listDatasets(),
        listFileAssets(),
        getDataSources(),
        listFileLocations()
      ])

      const datasets = datasetsRes.status === 'fulfilled' ? datasetsRes.value : []
      const files = filesRes.status === 'fulfilled' ? filesRes.value : []
      const dataSources = dataSourcesRes.status === 'fulfilled' ? dataSourcesRes.value : []
      const locations = locationsRes.status === 'fulfilled' ? locationsRes.value : []

      // Calculate total tables from data sources
      const totalTables = dataSources.reduce((acc: number, ds: any) => acc + (ds.table_count || 0), 0)

      setStats({
        datasets: datasets.length,
        files: files.length,
        dataSources: locations.length,
        tables: totalTables
      })

      setRecentDatasets(datasets.slice(0, 5))
      setRecentFiles(files.slice(0, 5))
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    {
      icon: Upload,
      title: 'Upload Data',
      description: 'Import CSV, Excel, or Parquet files',
      link: '/upload',
    },
    {
      icon: MessageCircle,
      title: 'Chat with Data',
      description: 'Ask questions in natural language',
      link: '/chat',
    },
    {
      icon: FileCode2,
      title: 'SQL Notebook',
      description: 'Write and run SQL queries',
      link: '/notebooks',
    },
    {
      icon: Table,
      title: 'Explore Data',
      description: 'Browse tables and schemas',
      link: '/explorer',
    },
  ]

  const statCards = [
    { label: 'Datasets', value: stats.datasets, icon: HardDrive, color: '#a8d8ff' },
    { label: 'Files', value: stats.files, icon: FolderOpen, color: '#c4b5fd' },
    { label: 'Data Sources', value: stats.dataSources, icon: PlugZap, color: '#c7f5d4' },
    { label: 'Tables', value: stats.tables, icon: Database, color: '#ffc4e5' },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-left">
        <h1
          className="text-4xl font-bold"
          style={{
            background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 50%, #ffc4e5 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Welcome to zerostack
        </h1>
        <p className="mt-2" style={{ color: '#b0b8c0' }}>
          Your AI-native data platform
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <div
              key={stat.label}
              className="rounded-xl p-5 transition-all duration-300"
              style={{
                backgroundColor: '#1a1a24',
                border: `1px solid ${stat.color}25`
              }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide" style={{ color: stat.color }}>
                    {stat.label}
                  </p>
                  <p className="mt-1 text-2xl font-bold" style={{ color: '#f0f0f5' }}>
                    {loading ? '...' : stat.value.toLocaleString()}
                  </p>
                </div>
                <div className="p-2 rounded-lg" style={{ backgroundColor: `${stat.color}15` }}>
                  <Icon className="h-5 w-5" style={{ color: stat.color }} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold mb-4" style={{ color: '#f0f0f5' }}>
          Quick Actions
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon
            return (
              <Link
                key={action.title}
                to={action.link}
                className="rounded-xl p-5 transition-all duration-300 group hover:scale-[1.02]"
                style={{
                  backgroundColor: '#1a1a24',
                  border: '1px solid rgba(168, 216, 255, 0.15)'
                }}
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    border: '1px solid rgba(168, 216, 255, 0.2)'
                  }}
                >
                  <Icon className="h-5 w-5" style={{ color: '#a8d8ff' }} />
                </div>
                <h3 className="font-medium text-sm" style={{ color: '#f0f0f5' }}>
                  {action.title}
                </h3>
                <p className="text-xs mt-1" style={{ color: '#888' }}>
                  {action.description}
                </p>
                <div className="mt-3 flex items-center text-xs" style={{ color: '#a8d8ff' }}>
                  <span>Go</span>
                  <ArrowRight className="h-3 w-3 ml-1 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Datasets */}
        <div
          className="rounded-xl overflow-hidden"
          style={{
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(168, 216, 255, 0.12)'
          }}
        >
          <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.08)' }}>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" style={{ color: '#a8d8ff' }} />
              <h3 className="font-medium text-sm" style={{ color: '#f0f0f5' }}>Recent Datasets</h3>
            </div>
            <Link to="/datasets" className="text-xs" style={{ color: '#a8d8ff' }}>View all</Link>
          </div>
          <div className="p-2">
            {loading ? (
              <div className="px-4 py-8 text-center text-sm" style={{ color: '#888' }}>Loading...</div>
            ) : recentDatasets.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <p className="text-sm" style={{ color: '#888' }}>No datasets yet</p>
                <Link to="/upload" className="text-xs mt-2 inline-block" style={{ color: '#a8d8ff' }}>
                  Upload your first dataset
                </Link>
              </div>
            ) : (
              <div className="space-y-1">
                {recentDatasets.map((dataset) => (
                  <div
                    key={dataset.id}
                    className="px-3 py-2 rounded-lg flex items-center justify-between hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <HardDrive className="h-4 w-4 flex-shrink-0" style={{ color: '#666' }} />
                      <span className="text-sm truncate" style={{ color: '#f0f0f5' }}>
                        {dataset.filename || dataset.name}
                      </span>
                    </div>
                    <span className="text-xs flex-shrink-0 ml-2" style={{ color: '#666' }}>
                      {dataset.rows?.toLocaleString() || '?'} rows
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Files */}
        <div
          className="rounded-xl overflow-hidden"
          style={{
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(196, 181, 253, 0.12)'
          }}
        >
          <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(196, 181, 253, 0.08)' }}>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" style={{ color: '#c4b5fd' }} />
              <h3 className="font-medium text-sm" style={{ color: '#f0f0f5' }}>Recent Files</h3>
            </div>
            <Link to="/files/locations" className="text-xs" style={{ color: '#c4b5fd' }}>View all</Link>
          </div>
          <div className="p-2">
            {loading ? (
              <div className="px-4 py-8 text-center text-sm" style={{ color: '#888' }}>Loading...</div>
            ) : recentFiles.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <p className="text-sm" style={{ color: '#888' }}>No files yet</p>
                <Link to="/files/locations" className="text-xs mt-2 inline-block" style={{ color: '#c4b5fd' }}>
                  Connect a file location
                </Link>
              </div>
            ) : (
              <div className="space-y-1">
                {recentFiles.map((file) => (
                  <div
                    key={file.id}
                    className="px-3 py-2 rounded-lg flex items-center justify-between hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <FolderOpen className="h-4 w-4 flex-shrink-0" style={{ color: '#666' }} />
                      <span className="text-sm truncate" style={{ color: '#f0f0f5' }}>
                        {file.filename || file.name}
                      </span>
                    </div>
                    <span className="text-xs flex-shrink-0 ml-2 px-2 py-0.5 rounded" style={{
                      color: '#c4b5fd',
                      backgroundColor: 'rgba(196, 181, 253, 0.1)'
                    }}>
                      {file.file_type || 'file'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
