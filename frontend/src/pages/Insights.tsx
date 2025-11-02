import { useState, useEffect } from 'react'
import { Sparkles, TrendingUp, TrendingDown, AlertTriangle, Lightbulb, Target, Activity, BarChart3, PieChart } from 'lucide-react'
import { generateInsights, listDatasets } from '../api/client'
import { useLocation } from 'react-router-dom'
import {
  LineChart, Line, BarChart, Bar, PieChart as RePieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart
} from 'recharts'

export default function Insights() {
  const location = useLocation()
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [insights, setInsights] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState('general business')

  useEffect(() => {
    loadDatasets()
    if (location.state?.datasetId) {
      setSelectedDataset(location.state.datasetId)
    }
  }, [location])

  const loadDatasets = async () => {
    try {
      const data = await listDatasets()
      setDatasets(data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    }
  }

  const handleGenerateInsights = async () => {
    if (!selectedDataset) return

    setLoading(true)
    try {
      const result = await generateInsights(selectedDataset, context)
      setInsights(result)
    } catch (error: any) {
      console.error('Failed to generate insights:', error)
      alert(error.response?.data?.detail || 'Failed to generate insights')
    } finally {
      setLoading(false)
    }
  }

  const COLORS = ['#a8d8ff', '#c4b5fd', '#ffc4e5', '#c7f5d4', '#fde68a', '#fed7aa']

  return (
    <div className="space-y-6">
      {/* Header */}
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
          Executive Insights
        </h1>
        <p className="mt-2" style={{ color: '#b0b8c0', textAlign: 'left' }}>Strategic intelligence for data-driven decision making</p>
      </div>

      {/* Controls */}
      <div 
        className="rounded-xl p-6"
        style={{ 
          backgroundColor: '#1a1a24', 
          border: '1px solid rgba(168, 216, 255, 0.12)' 
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
              Select Dataset
            </label>
            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="w-full px-4 py-2 rounded-lg focus:ring-2"
              style={{
                backgroundColor: '#1a1a24',
                color: '#f0f0f5',
                border: '1px solid rgba(168, 216, 255, 0.15)'
              }}
            >
              <option value="">Select a dataset...</option>
              {datasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.filename} ({dataset.rows} rows)
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
              Business Context
            </label>
            <input
              type="text"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="e.g., retail, healthcare, finance"
              className="w-full px-4 py-2 rounded-lg focus:ring-2"
              style={{
                backgroundColor: '#1a1a24',
                color: '#f0f0f5',
                border: '1px solid rgba(168, 216, 255, 0.15)'
              }}
            />
          </div>
        </div>
        <button
          onClick={handleGenerateInsights}
          disabled={!selectedDataset || loading}
          className="mt-4 px-6 py-3 rounded-lg font-medium transition-all disabled:opacity-50"
          style={{
            background: 'linear-gradient(90deg, #a8d8ff, #c4b5fd)',
            color: '#0a0a0f'
          }}
        >
          {loading ? 'Analyzing Data...' : 'Generate Executive Report'}
        </button>
      </div>

      {/* Insights Display */}
      {insights && (
        <div className="space-y-6">
          {/* Performance Score */}
          {insights.performance_score && (
            <div 
              className="rounded-xl p-6"
              style={{ 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.12)' 
              }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>Overall Performance</h2>
                  <p className="mt-1" style={{ color: '#b0b8c0' }}>Business health score: {insights.performance_score.health}</p>
                </div>
                <div className="text-center">
                  <div 
                    className="text-6xl font-bold"
                    style={{
                      background: 'linear-gradient(135deg, #a8d8ff, #c7f5d4)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text'
                    }}
                  >
                    {insights.performance_score.overall_score.toFixed(0)}
                  </div>
                  <div className="text-sm" style={{ color: '#b0b8c0' }}>out of 100</div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div className="text-center p-4 rounded-lg" style={{ backgroundColor: 'rgba(168, 216, 255, 0.08)' }}>
                  <div className="text-sm font-medium" style={{ color: '#a8d8ff' }}>Data Quality</div>
                  <div className="text-3xl font-bold mt-2" style={{ color: '#f0f0f5' }}>
                    {insights.performance_score.data_quality.toFixed(0)}%
                  </div>
                </div>
                <div className="text-center p-4 rounded-lg" style={{ backgroundColor: 'rgba(196, 181, 253, 0.08)' }}>
                  <div className="text-sm font-medium" style={{ color: '#c4b5fd' }}>Consistency</div>
                  <div className="text-3xl font-bold mt-2" style={{ color: '#f0f0f5' }}>
                    {insights.performance_score.consistency.toFixed(0)}%
                  </div>
                </div>
                <div className="text-center p-4 rounded-lg" style={{ backgroundColor: 'rgba(199, 245, 212, 0.08)' }}>
                  <div className="text-sm font-medium" style={{ color: '#c7f5d4' }}>Growth</div>
                  <div className="text-3xl font-bold mt-2" style={{ color: '#f0f0f5' }}>
                    {insights.performance_score.growth.toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Executive KPIs */}
          {insights.executive_kpis && insights.executive_kpis.length > 0 && (
            <div>
              <h2 
                className="text-3xl font-bold mb-4"
                style={{
                  background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text'
                }}
              >
                Key Performance Indicators
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {insights.executive_kpis.map((kpi: any, index: number) => (
                  <div 
                    key={index}
                    className="rounded-xl p-6"
                    style={{ 
                      backgroundColor: '#1a1a24', 
                      border: '1px solid rgba(168, 216, 255, 0.12)' 
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium" style={{ color: '#b0b8c0' }}>{kpi.name}</p>
                        <p className="text-3xl font-bold mt-2" style={{ color: '#f0f0f5' }}>
                          {kpi.value.toFixed(2)}
                        </p>
                      </div>
                      <div className={`p-2 rounded-lg`} style={{ 
                        backgroundColor: kpi.trend_direction === 'up' ? 'rgba(199, 245, 212, 0.15)' : 'rgba(255, 196, 229, 0.15)'
                      }}>
                        {kpi.trend_direction === 'up' ? (
                          <TrendingUp className="h-5 w-5" style={{ color: '#c7f5d4' }} />
                        ) : (
                          <TrendingDown className="h-5 w-5" style={{ color: '#ffc4e5' }} />
                        )}
                      </div>
                    </div>
                    <div className="mt-3 flex items-center space-x-2">
                      <span 
                        className="text-sm font-medium"
                        style={{ color: kpi.trend_direction === 'up' ? '#c7f5d4' : '#ffc4e5' }}
                      >
                        {kpi.trend > 0 ? '+' : ''}{kpi.trend.toFixed(1)}%
                      </span>
                      <span className="text-xs" style={{ color: '#b0b8c0' }}>vs baseline</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trend Visualization */}
          {insights.trend_data && insights.trend_data.length > 0 && (
            <div 
              className="rounded-xl p-6"
              style={{ 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.12)' 
              }}
            >
              <div className="flex items-center space-x-3 mb-6">
                <Activity className="h-6 w-6" style={{ color: '#a8d8ff' }} />
                <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>Performance Trends</h2>
              </div>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={insights.trend_data}>
                  <defs>
                    <linearGradient id="colorGradient1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a8d8ff" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#a8d8ff" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorGradient2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#c4b5fd" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#c4b5fd" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(168, 216, 255, 0.1)" />
                  <XAxis 
                    dataKey="index" 
                    stroke="#b0b8c0"
                    style={{ fontSize: '12px' }}
                  />
                  <YAxis 
                    stroke="#b0b8c0"
                    style={{ fontSize: '12px' }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1a1a24', 
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '8px',
                      color: '#f0f0f5'
                    }}
                  />
                  <Legend wrapperStyle={{ color: '#f0f0f5' }} />
                  {Object.keys(insights.trend_data[0]).filter(key => key !== 'index').slice(0, 3).map((key, index) => (
                    <Area
                      key={key}
                      type="monotone"
                      dataKey={key}
                      stroke={COLORS[index]}
                      strokeWidth={2}
                      fill={`url(#colorGradient${index + 1})`}
                    />
                  ))}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Growth Metrics */}
          {insights.growth_metrics && Object.keys(insights.growth_metrics).length > 0 && (
            <div 
              className="rounded-xl p-6"
              style={{ 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.12)' 
              }}
            >
              <div className="flex items-center space-x-3 mb-6">
                <TrendingUp className="h-6 w-6" style={{ color: '#c7f5d4' }} />
                <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>Growth Analysis</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(insights.growth_metrics).map(([metric, data]: [string, any]) => (
                  <div 
                    key={metric}
                    className="p-6 rounded-xl"
                    style={{ 
                      backgroundColor: 'rgba(168, 216, 255, 0.05)', 
                      border: '1px solid rgba(168, 216, 255, 0.12)' 
                    }}
                  >
                    <h3 className="text-lg font-semibold" style={{ color: '#f0f0f5' }}>{metric}</h3>
                    <div className="mt-4 space-y-3">
                      <div>
                        <div className="text-sm" style={{ color: '#b0b8c0' }}>Growth Rate</div>
                        <div 
                          className="text-2xl font-bold"
                          style={{ color: data.growth_rate > 0 ? '#c7f5d4' : '#ffc4e5' }}
                        >
                          {data.growth_rate > 0 ? '+' : ''}{data.growth_rate.toFixed(1)}%
                        </div>
                      </div>
                      <div>
                        <div className="text-sm" style={{ color: '#b0b8c0' }}>CAGR</div>
                        <div className="text-xl font-bold" style={{ color: '#a8d8ff' }}>
                          {data.cagr.toFixed(1)}%
                        </div>
                      </div>
                      <div className="pt-2 border-t" style={{ borderColor: 'rgba(168, 216, 255, 0.12)' }}>
                        <span 
                          className="text-sm font-medium px-3 py-1 rounded-full"
                          style={{ 
                            backgroundColor: data.momentum === 'accelerating' ? 'rgba(199, 245, 212, 0.2)' : 'rgba(255, 196, 229, 0.2)',
                            color: data.momentum === 'accelerating' ? '#c7f5d4' : '#ffc4e5'
                          }}
                        >
                          {data.momentum}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Indicators */}
          {insights.risk_indicators && insights.risk_indicators.length > 0 && (
            <div 
              className="rounded-xl p-6"
              style={{ 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.12)' 
              }}
            >
              <div className="flex items-center space-x-3 mb-6">
                <AlertTriangle className="h-6 w-6" style={{ color: '#fed7aa' }} />
                <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>Risk Assessment</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {insights.risk_indicators.map((risk: any, index: number) => (
                  <div 
                    key={index}
                    className="p-4 rounded-lg"
                    style={{ 
                      backgroundColor: 'rgba(168, 216, 255, 0.05)', 
                      border: '1px solid rgba(168, 216, 255, 0.12)' 
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium" style={{ color: '#f0f0f5' }}>{risk.metric}</p>
                        <p className="text-sm mt-1" style={{ color: '#b0b8c0' }}>
                          Volatility: {risk.volatility.toFixed(1)}%
                        </p>
                        <p className="text-sm" style={{ color: '#b0b8c0' }}>
                          Outliers: {risk.outlier_percentage.toFixed(1)}%
                        </p>
                      </div>
                      <span 
                        className="px-2 py-1 rounded text-xs font-medium"
                        style={{
                          backgroundColor: 
                            risk.risk_level === 'low' ? 'rgba(199, 245, 212, 0.2)' :
                            risk.risk_level === 'medium' ? 'rgba(254, 230, 138, 0.2)' :
                            'rgba(254, 215, 170, 0.2)',
                          color: 
                            risk.risk_level === 'low' ? '#c7f5d4' :
                            risk.risk_level === 'medium' ? '#fde68a' :
                            '#fed7aa'
                        }}
                      >
                        {risk.risk_level.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Distribution Charts */}
          {insights.distribution_data && Object.keys(insights.distribution_data).length > 0 && (
            <div 
              className="rounded-xl p-6"
              style={{ 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.12)' 
              }}
            >
              <div className="flex items-center space-x-3 mb-6">
                <BarChart3 className="h-6 w-6" style={{ color: '#c4b5fd' }} />
                <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>Distribution Analysis</h2>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(insights.distribution_data).slice(0, 2).map(([metric, data]: [string, any]) => (
                  <div key={metric}>
                    <h3 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>{metric}</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(168, 216, 255, 0.1)" />
                        <XAxis 
                          dataKey="range" 
                          stroke="#b0b8c0"
                          style={{ fontSize: '10px' }}
                          angle={-45}
                          textAnchor="end"
                          height={80}
                        />
                        <YAxis 
                          stroke="#b0b8c0"
                          style={{ fontSize: '12px' }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#1a1a24', 
                            border: '1px solid rgba(168, 216, 255, 0.2)',
                            borderRadius: '8px',
                            color: '#f0f0f5'
                          }}
                        />
                        <Bar dataKey="count" fill="#a8d8ff" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Strategic Recommendations */}
          {insights.recommendations && insights.recommendations.length > 0 && (
            <div 
              className="rounded-xl p-6"
              style={{ 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.12)' 
              }}
            >
              <div className="flex items-center space-x-3 mb-6">
                <Lightbulb className="h-6 w-6" style={{ color: '#fde68a' }} />
                <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>Strategic Recommendations</h2>
              </div>
              <div className="space-y-3">
                {insights.recommendations.map((rec: string, index: number) => (
                  <div 
                    key={index}
                    className="flex items-start space-x-3 p-4 rounded-lg"
                    style={{ 
                      backgroundColor: 'rgba(168, 216, 255, 0.05)', 
                      border: '1px solid rgba(168, 216, 255, 0.12)' 
                    }}
                  >
                    <div 
                      className="mt-1 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: 'rgba(168, 216, 255, 0.2)' }}
                    >
                      <span className="text-sm font-bold" style={{ color: '#a8d8ff' }}>{index + 1}</span>
                    </div>
                    <p style={{ color: '#f0f0f5' }}>{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          <div 
            className="rounded-xl p-6"
            style={{ 
              backgroundColor: '#1a1a24', 
              border: '1px solid rgba(168, 216, 255, 0.12)' 
            }}
          >
            <div className="flex items-center space-x-3 mb-4">
              <Sparkles className="h-6 w-6" style={{ color: '#ffc4e5' }} />
              <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>Executive Summary</h2>
            </div>
            <p className="text-lg leading-relaxed" style={{ color: '#b0b8c0' }}>{insights.summary}</p>
          </div>
        </div>
      )}

      {!insights && !loading && (
        <div 
          className="text-center py-16 rounded-xl"
          style={{ 
            backgroundColor: '#1a1a24', 
            border: '1px solid rgba(168, 216, 255, 0.12)' 
          }}
        >
          <Target className="h-16 w-16 mx-auto mb-4" style={{ color: '#a8d8ff', opacity: 0.5 }} />
          <p className="text-xl" style={{ color: '#b0b8c0' }}>
            Select a dataset and generate insights to view executive dashboard
          </p>
        </div>
      )}
    </div>
  )
}
