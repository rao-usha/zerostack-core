import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  Database, 
  Sparkles, 
  TrendingUp, 
  CheckCircle2,
  AlertCircle,
  Upload,
  MessageCircle
} from 'lucide-react'
import { listDatasets } from '../api/client'

export default function Dashboard() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const data = await listDatasets()
      setDatasets(data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    } finally {
      setLoading(false)
    }
  }

  const features = [
    {
      icon: Upload,
      title: 'Data Upload',
      description: 'Upload your datasets and start analyzing',
      link: '/upload',
      color: 'bg-blue-500',
    },
    {
      icon: Sparkles,
      title: 'AI Insights',
      description: 'Get strategic insights automatically',
      link: '/insights',
      color: 'bg-purple-500',
    },
    {
      icon: TrendingUp,
      title: 'Predictive Models',
      description: 'Build and deploy ML models',
      link: '/models',
      color: 'bg-green-500',
    },
    {
      icon: Database,
      title: 'Synthetic Data',
      description: 'Generate synthetic data from samples',
      link: '/synthetic',
      color: 'bg-orange-500',
    },
    {
      icon: CheckCircle2,
      title: 'Data Quality',
      description: 'Assess and improve data quality',
      link: '/quality',
      color: 'bg-teal-500',
    },
    {
      icon: AlertCircle,
      title: 'Knowledge Gaps',
      description: 'Identify gaps in your data',
      link: '/gaps',
      color: 'bg-red-500',
    },
    {
      icon: MessageCircle,
      title: 'AI Chat',
      description: 'Ask questions about your data',
      link: '/chat',
      color: 'bg-indigo-500',
    },
  ]

  return (
    <div className="space-y-8">
      <div className="text-left">
        <h1 
          className="text-5xl font-bold"
          style={{
            background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 50%, #ffc4e5 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            textAlign: 'left'
          }}
        >
          Dashboard
        </h1>
        <p className="mt-2" style={{ color: '#b0b8c0', textAlign: 'left' }}>Welcome to NEX.AI - Your AI-native data platform</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="rounded-xl p-6 transition-all duration-300" style={{ 
          backgroundColor: '#1a1a24', 
          border: '1px solid rgba(168, 216, 255, 0.15)' 
        }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium" style={{ color: '#b3d9ff' }}>Total Datasets</p>
              <p className="mt-2 text-3xl font-bold" style={{
                background: 'linear-gradient(90deg, #a8d8ff, #c4f4f4)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                {loading ? '...' : datasets.length}
              </p>
            </div>
            <div className="p-3 rounded-lg" style={{ 
              backgroundColor: 'rgba(168, 216, 255, 0.08)', 
              border: '1px solid rgba(168, 216, 255, 0.15)' 
            }}>
              <Database className="h-8 w-8" style={{ color: '#a8d8ff' }} />
            </div>
          </div>
        </div>

        <div className="rounded-xl p-6 transition-all duration-300" style={{ 
          backgroundColor: '#1a1a24', 
          border: '1px solid rgba(196, 181, 253, 0.15)' 
        }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium" style={{ color: '#d4c5ff' }}>Features Available</p>
              <p className="mt-2 text-3xl font-bold" style={{
                background: 'linear-gradient(90deg, #c4b5fd, #ffc4e5)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>7</p>
            </div>
            <div className="p-3 rounded-lg" style={{ 
              backgroundColor: 'rgba(196, 181, 253, 0.08)', 
              border: '1px solid rgba(196, 181, 253, 0.15)' 
            }}>
              <Sparkles className="h-8 w-8" style={{ color: '#c4b5fd' }} />
            </div>
          </div>
        </div>

        <div className="rounded-xl p-6 transition-all duration-300" style={{ 
          backgroundColor: '#1a1a24', 
          border: '1px solid rgba(199, 245, 212, 0.15)' 
        }}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium" style={{ color: '#c7f5d4' }}>AI-Powered</p>
              <p className="mt-2 text-3xl font-bold" style={{
                background: 'linear-gradient(90deg, #c7f5d4, #c4f4f4)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>100%</p>
            </div>
            <div className="p-3 rounded-lg" style={{ 
              backgroundColor: 'rgba(199, 245, 212, 0.08)', 
              border: '1px solid rgba(199, 245, 212, 0.15)' 
            }}>
              <TrendingUp className="h-8 w-8" style={{ color: '#c7f5d4' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div>
        <h2 
          className="text-3xl font-bold mb-6"
          style={{
            background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}
        >
          Platform Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <Link
                key={feature.title}
                to={feature.link}
                className="rounded-xl transition-all duration-300 p-6 group"
                style={{ 
                  backgroundColor: '#1a1a24', 
                  border: '1px solid rgba(168, 216, 255, 0.12)' 
                }}
              >
                <div 
                  className="w-14 h-14 rounded-lg flex items-center justify-center mb-4 transition-all"
                  style={{ 
                    backgroundColor: 'rgba(168, 216, 255, 0.06)', 
                    border: '1px solid rgba(168, 216, 255, 0.12)' 
                  }}
                >
                  <Icon className="h-7 w-7" style={{ color: '#a8d8ff' }} />
                </div>
                <h3 
                  className="text-lg font-semibold"
                  style={{
                    background: 'linear-gradient(90deg, #a8d8ff, #c4b5fd)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}
                >
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm" style={{ color: '#b0b8c0' }}>{feature.description}</p>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Recent Datasets */}
      {datasets.length > 0 && (
        <div>
          <h2 
            className="text-3xl font-bold mb-6"
            style={{
              background: 'linear-gradient(90deg, #c7f5d4 0%, #c4f4f4 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}
          >
            Recent Datasets
          </h2>
          <div 
            className="rounded-xl overflow-hidden" 
            style={{ 
              backgroundColor: '#1a1a24', 
              border: '1px solid rgba(168, 216, 255, 0.12)' 
            }}
          >
            <table className="min-w-full">
              <thead style={{ backgroundColor: '#13131a' }}>
                <tr style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.08)' }}>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: '#a8d8ff' }}>Filename</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: '#a8d8ff' }}>Rows</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: '#a8d8ff' }}>Columns</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider" style={{ color: '#a8d8ff' }}>Uploaded</th>
                </tr>
              </thead>
              <tbody style={{ backgroundColor: '#1a1a24' }}>
                {datasets.slice(0, 5).map((dataset, index) => (
                  <tr 
                    key={dataset.id} 
                    className="transition-colors"
                    style={{ 
                      borderBottom: index !== datasets.slice(0, 5).length - 1 ? '1px solid rgba(168, 216, 255, 0.08)' : 'none'
                    }}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium" style={{ color: '#f0f0f5' }}>
                      {dataset.filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: '#b0b8c0' }}>
                      {dataset.rows}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: '#b0b8c0' }}>
                      {dataset.columns}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm" style={{ color: '#b0b8c0' }}>
                      {new Date(dataset.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

