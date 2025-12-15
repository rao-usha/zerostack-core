import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, ArrowLeft, FileText, Rocket, BarChart3, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface Model {
  id: string
  name: string
  model_family: string
  recipe_id: string
  recipe_version_id: string
  status: string
  owner?: string
  created_at: string
  updated_at: string
}

interface MonitorSnapshot {
  id: string
  model_id: string
  captured_at: string
  performance_metrics_json: any
  drift_metrics_json: any
  data_freshness_json: any
  alerts_json: any
}

type TabType = 'overview' | 'deployments' | 'monitoring' | 'alerts'

export default function ModelDetail() {
  const { modelId } = useParams<{ modelId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [model, setModel] = useState<Model | null>(null)
  const [snapshots, setSnapshots] = useState<MonitorSnapshot[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadModel()
    loadMonitoring()
  }, [modelId])

  const loadModel = async () => {
    try {
      const response = await fetch(`/api/v1/ml-development/models/${modelId}`)
      if (response.ok) {
        const data = await response.json()
        setModel(data)
      }
    } catch (error) {
      console.error('Error loading model:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadMonitoring = async () => {
    try {
      const response = await fetch(`/api/v1/ml-development/models/${modelId}/monitoring`)
      if (response.ok) {
        const data = await response.json()
        setSnapshots(data)
      }
    } catch (error) {
      console.error('Error loading monitoring:', error)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#fbbf24',
      staging: '#3b82f6',
      production: '#10b981',
      retired: '#6b7280'
    }
    return colors[status] || '#9ca3af'
  }

  const prepareChartData = () => {
    return snapshots.map(snap => ({
      date: new Date(snap.captured_at).toLocaleDateString(),
      ...snap.performance_metrics_json
    })).reverse()
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', padding: '2rem' }}>
        <p style={{ textAlign: 'center', color: '#b3b3c4' }}>Loading model...</p>
      </div>
    )
  }

  if (!model) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', padding: '2rem' }}>
        <p style={{ textAlign: 'center', color: '#b3b3c4' }}>Model not found</p>
      </div>
    )
  }

  const chartData = prepareChartData()
  const latestSnapshot = snapshots.length > 0 ? snapshots[0] : null

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)', padding: '1.5rem 2rem' }}>
        <button
          onClick={() => navigate('/model-development')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'none',
            border: 'none',
            color: '#a8d8ff',
            cursor: 'pointer',
            marginBottom: '1rem',
            fontSize: '0.95rem'
          }}
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Model Library
        </button>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
              <Box className="h-8 w-8" style={{ color: '#a8d8ff' }} />
              <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f0f0f5' }}>
                {model.name}
              </h1>
              <span
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: `${getStatusColor(model.status)}20`,
                  color: getStatusColor(model.status),
                  borderRadius: '9999px',
                  fontSize: '0.875rem',
                  fontWeight: '600'
                }}
              >
                {model.status}
              </span>
            </div>
            <p style={{ color: '#b3b3c4', fontSize: '0.95rem' }}>
              {model.model_family} · {model.owner ? `Owner: ${model.owner}` : 'No owner'}
            </p>
          </div>
        </div>
      </div>

      <div style={{ padding: '2rem' }}>
        {/* Tabs */}
        <div style={{ 
          display: 'flex', 
          gap: '1rem', 
          borderBottom: '1px solid rgba(168, 216, 255, 0.2)',
          marginBottom: '2rem'
        }}>
          {[
            { id: 'overview', label: 'Overview', icon: FileText },
            { id: 'deployments', label: 'Deployments', icon: Rocket },
            { id: 'monitoring', label: 'Monitoring', icon: BarChart3 },
            { id: 'alerts', label: 'Alerts', icon: AlertTriangle }
          ].map(tab => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: activeTab === tab.id ? 'rgba(168, 216, 255, 0.1)' : 'transparent',
                  border: 'none',
                  borderBottom: activeTab === tab.id ? '2px solid #a8d8ff' : '2px solid transparent',
                  color: activeTab === tab.id ? '#a8d8ff' : '#b3b3c4',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s'
                }}
              >
                <Icon className="h-5 w-5" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div style={{ maxWidth: '800px' }}>
            <div style={{ 
              padding: '1.5rem', 
              backgroundColor: '#1a1a24', 
              border: '1px solid rgba(168, 216, 255, 0.2)',
              borderRadius: '0.75rem',
              marginBottom: '1.5rem'
            }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#a8d8ff' }}>
                Model Information
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Model Family</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{model.model_family}</p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Status</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{model.status}</p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Recipe ID</p>
                  <p 
                    style={{ color: '#a8d8ff', fontWeight: '600', cursor: 'pointer' }}
                    onClick={() => navigate(`/model-development/recipes/${model.recipe_id}`)}
                  >
                    {model.recipe_id}
                  </p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Recipe Version</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{model.recipe_version_id}</p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Created</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>
                    {new Date(model.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Last Updated</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>
                    {new Date(model.updated_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            {latestSnapshot && (
              <div style={{ 
                padding: '1.5rem', 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.75rem'
              }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#a8d8ff' }}>
                  Latest Performance Metrics
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  {Object.entries(latestSnapshot.performance_metrics_json).map(([key, value]) => (
                    <div key={key}>
                      <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                        {key.toUpperCase()}
                      </p>
                      <p style={{ color: '#f0f0f5', fontSize: '1.5rem', fontWeight: '700' }}>
                        {typeof value === 'number' ? value.toFixed(4) : value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'deployments' && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
            <Rocket className="h-16 w-16" style={{ margin: '0 auto 1rem', color: '#a8d8ff' }} />
            <p>Deployment endpoints and batch jobs will appear here</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              (Stubbed in v1)
            </p>
          </div>
        )}

        {activeTab === 'monitoring' && (
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#f0f0f5' }}>
              Performance Over Time
            </h3>

            {chartData.length > 0 ? (
              <div style={{ 
                padding: '2rem', 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.75rem',
                marginBottom: '2rem'
              }}>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(168, 216, 255, 0.1)" />
                    <XAxis dataKey="date" stroke="#b3b3c4" />
                    <YAxis stroke="#b3b3c4" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1a1a24', 
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                        borderRadius: '0.5rem'
                      }}
                    />
                    <Legend />
                    {Object.keys(chartData[0] || {}).filter(k => k !== 'date').map((key, idx) => (
                      <Line 
                        key={key}
                        type="monotone" 
                        dataKey={key} 
                        stroke={['#a8d8ff', '#c4b5fd', '#ffc4e5', '#10b981'][idx % 4]}
                        strokeWidth={2}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '3rem', 
                backgroundColor: '#1a1a24',
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.75rem',
                color: '#b3b3c4' 
              }}>
                <BarChart3 className="h-16 w-16" style={{ margin: '0 auto 1rem', color: '#a8d8ff' }} />
                <p>No monitoring data available yet</p>
              </div>
            )}

            {/* Additional monitoring metrics */}
            {latestSnapshot && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                <div style={{ 
                  padding: '1.5rem', 
                  backgroundColor: '#1a1a24', 
                  border: '1px solid rgba(168, 216, 255, 0.2)',
                  borderRadius: '0.75rem'
                }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#a8d8ff' }}>
                    Drift Metrics
                  </h4>
                  {Object.entries(latestSnapshot.drift_metrics_json).length > 0 ? (
                    Object.entries(latestSnapshot.drift_metrics_json).map(([key, value]) => (
                      <div key={key} style={{ marginBottom: '0.75rem' }}>
                        <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>{key}</p>
                        <p style={{ color: '#f0f0f5', fontWeight: '600' }}>
                          {typeof value === 'number' ? value.toFixed(4) : JSON.stringify(value)}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>No drift detected</p>
                  )}
                </div>

                <div style={{ 
                  padding: '1.5rem', 
                  backgroundColor: '#1a1a24', 
                  border: '1px solid rgba(168, 216, 255, 0.2)',
                  borderRadius: '0.75rem'
                }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '1rem', color: '#a8d8ff' }}>
                    Data Freshness
                  </h4>
                  {Object.entries(latestSnapshot.data_freshness_json).length > 0 ? (
                    Object.entries(latestSnapshot.data_freshness_json).map(([key, value]) => (
                      <div key={key} style={{ marginBottom: '0.75rem' }}>
                        <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>{key}</p>
                        <p style={{ color: '#f0f0f5', fontWeight: '600' }}>
                          {typeof value === 'string' ? new Date(value).toLocaleString() : JSON.stringify(value)}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>Data is fresh</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'alerts' && (
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#f0f0f5' }}>
              Model Alerts
            </h3>
            
            {latestSnapshot && latestSnapshot.alerts_json && Object.keys(latestSnapshot.alerts_json).length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {Object.entries(latestSnapshot.alerts_json).map(([key, alert]: [string, any]) => (
                  <div
                    key={key}
                    style={{
                      padding: '1.5rem',
                      backgroundColor: '#1a1a24',
                      border: `1px solid ${alert.severity === 'critical' ? 'rgba(239, 68, 68, 0.5)' : 'rgba(251, 191, 36, 0.5)'}`,
                      borderRadius: '0.75rem'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'start', gap: '1rem' }}>
                      <AlertTriangle 
                        className="h-6 w-6" 
                        style={{ color: alert.severity === 'critical' ? '#ef4444' : '#fbbf24', flexShrink: 0 }} 
                      />
                      <div style={{ flex: 1 }}>
                        <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5', marginBottom: '0.5rem' }}>
                          {alert.message || key}
                        </h4>
                        <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>
                          {alert.description || 'No description available'}
                        </p>
                      </div>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: alert.severity === 'critical' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(251, 191, 36, 0.2)',
                          color: alert.severity === 'critical' ? '#ef4444' : '#fbbf24',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}
                      >
                        {alert.severity || 'warning'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '3rem', 
                backgroundColor: '#1a1a24',
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.75rem',
                color: '#b3b3c4' 
              }}>
                <AlertTriangle className="h-16 w-16" style={{ margin: '0 auto 1rem', color: '#10b981' }} />
                <p>No active alerts</p>
                <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                  Model is operating within normal parameters
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}


