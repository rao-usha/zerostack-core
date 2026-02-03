import { useState, useEffect, useCallback, useRef } from 'react'

// ============================================================================
// TYPES
// ============================================================================
interface ForecastResult {
  job_id: string
  status: string
  name?: string  // User-provided name
  created_at?: string
  gpu_type?: string
  pod_name?: string
  mae?: number
  rmse?: number
  training_time_seconds?: number
  feature_importance?: string
  forecasts_preview?: string
}

interface GpuStatus {
  active: boolean
  name?: string
  gpu_type?: string
  cost_per_hour?: number
  balance?: number
}

interface ParsedForecast {
  item: string
  store: string
  value: number
}

interface ParsedFeature {
  name: string
  importance: number
}

interface RunConfig {
  name: string  // NEW: User-friendly name
  horizon: number
  limit: number
}

interface RunningJob {
  job_id: string
  name: string
  started_at: string
  progress: number
  status: 'starting' | 'running' | 'finishing'
}

// Saved forecast names (persist in localStorage)
const FORECAST_NAMES_KEY = 'nex_forecast_names'
const getForecastNames = (): Record<string, string> => {
  try {
    return JSON.parse(localStorage.getItem(FORECAST_NAMES_KEY) || '{}')
  } catch { return {} }
}
const saveForecastName = (jobId: string, name: string) => {
  const names = getForecastNames()
  names[jobId] = name
  localStorage.setItem(FORECAST_NAMES_KEY, JSON.stringify(names))
}

// ============================================================================
// HELP TOOLTIPS DATA
// ============================================================================
const METRIC_HELP: Record<string, { title: string; explanation: string; good: string }> = {
  mae: {
    title: 'Mean Absolute Error (MAE)',
    explanation: 'Average difference between predicted and actual values',
    good: 'Lower is better. MAE of 2 means predictions are off by ~2 units on average.'
  },
  rmse: {
    title: 'Root Mean Square Error (RMSE)',
    explanation: 'Similar to MAE but penalizes large errors more heavily',
    good: 'Lower is better. More sensitive to outliers than MAE.'
  },
  accuracy: {
    title: 'Model Accuracy',
    explanation: 'How close predictions are to actual values (inverse of error)',
    good: 'Higher is better. 95% means predictions are very close.'
  },
  training_time: {
    title: 'Training Time',
    explanation: 'How long it took to train the model on GPU',
    good: 'Faster is generally better, but quality matters more.'
  }
}

// ============================================================================
// MAIN COMPONENT  
// ============================================================================
export default function ForecastDashboard() {
  // State
  const [latestForecast, setLatestForecast] = useState<ForecastResult | null>(null)
  const [allForecasts, setAllForecasts] = useState<ForecastResult[]>([])
  const [gpuStatus, setGpuStatus] = useState<GpuStatus>({ active: false })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Running job state
  const [runningJob, setRunningJob] = useState<RunningJob | null>(null)
  const [runningElapsed, setRunningElapsed] = useState(0)
  const runningInterval = useRef<NodeJS.Timeout | null>(null)
  
  // Feature states
  const [showConfig, setShowConfig] = useState(false)
  const [compareJobA, setCompareJobA] = useState<string>('')
  const [compareJobB, setCompareJobB] = useState<string>('')
  const [compareDataA, setCompareDataA] = useState<ForecastResult | null>(null)
  const [compareDataB, setCompareDataB] = useState<ForecastResult | null>(null)
  const [runConfig, setRunConfig] = useState<RunConfig>({ 
    name: '', 
    horizon: 28, 
    limit: 1000 
  })
  const [activeView, setActiveView] = useState<'dashboard' | 'history' | 'compare' | 'help'>('dashboard')
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null)

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  const loadData = useCallback(async () => {
    try {
      const [jobsRes, podsRes, spendingRes, runsRes] = await Promise.all([
        fetch('/api/v1/ml-development/runpod/jobs').then(r => r.ok ? r.json() : { jobs: [] }),
        fetch('/api/v1/ml-development/runpod/pods').then(r => r.ok ? r.json() : { pods: [] }),
        fetch('/api/v1/ml-development/runpod/spending').then(r => r.ok ? r.json() : null),
        fetch('/api/v1/ml-development/runs?status=running').then(r => r.ok ? r.json() : { runs: [] })
      ])
      
      // Merge saved names into jobs
      const names = getForecastNames()
      const jobs = (jobsRes.jobs || []).map((j: ForecastResult) => ({
        ...j,
        name: names[j.job_id] || j.name
      }))
      setAllForecasts(jobs)
      
      // Check for running jobs
      const runningJobs = (runsRes.runs || []).filter((r: any) => r.status === 'running')
      if (runningJobs.length > 0 && !runningJob) {
        const rj = runningJobs[0]
        setRunningJob({
          job_id: rj.id,
          name: names[rj.id] || 'Running Forecast',
          started_at: rj.started_at || new Date().toISOString(),
          progress: 50,
          status: 'running'
        })
      } else if (runningJobs.length === 0 && runningJob) {
        // Job finished - notify and clear
        if (Notification.permission === 'granted') {
          new Notification('Forecast Complete! 🎉', {
            body: `Your forecast "${runningJob.name}" has finished.`,
            icon: '/favicon.ico'
          })
        }
        setRunningJob(null)
        setRunningElapsed(0)
      }
      
      // Get most recent completed job
      const completed = jobs.filter((j: ForecastResult) => j.status === 'completed')
      if (completed.length > 0) {
        const latestId = completed[0].job_id
        try {
          const details = await fetch(`/api/v1/ml-development/runpod/jobs/${latestId}`).then(r => r.json())
          setLatestForecast({ ...completed[0], ...details, name: names[latestId] || completed[0].name })
        } catch {
          setLatestForecast(completed[0])
        }
      }
      
      // GPU status
      const activePod = (podsRes.pods || []).find((p: any) => p.status === 'RUNNING')
      setGpuStatus({
        active: !!activePod,
        name: activePod?.name,
        gpu_type: activePod?.gpu_type,
        cost_per_hour: activePod?.cost_per_hour,
        balance: spendingRes?.client_balance
      })
      
    } catch (err) {
      setError('Failed to load forecast data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [runningJob])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, runningJob ? 5000 : 15000) // Faster refresh when job running
    return () => clearInterval(interval)
  }, [loadData, runningJob])

  // Running job elapsed timer
  useEffect(() => {
    if (runningJob) {
      runningInterval.current = setInterval(() => {
        setRunningElapsed(prev => prev + 1)
      }, 1000)
    } else {
      if (runningInterval.current) {
        clearInterval(runningInterval.current)
      }
    }
    return () => {
      if (runningInterval.current) clearInterval(runningInterval.current)
    }
  }, [runningJob])

  // Load comparison data
  useEffect(() => {
    const loadCompareData = async () => {
      const names = getForecastNames()
      if (compareJobA) {
        try {
          const data = await fetch(`/api/v1/ml-development/runpod/jobs/${compareJobA}`).then(r => r.json())
          setCompareDataA({ ...data, name: names[compareJobA] })
        } catch { setCompareDataA(null) }
      }
      if (compareJobB) {
        try {
          const data = await fetch(`/api/v1/ml-development/runpod/jobs/${compareJobB}`).then(r => r.json())
          setCompareDataB({ ...data, name: names[compareJobB] })
        } catch { setCompareDataB(null) }
      }
    }
    loadCompareData()
  }, [compareJobA, compareJobB])

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  // ============================================================================
  // ACTIONS
  // ============================================================================
  const runNewForecast = async (config: RunConfig) => {
    setError(null)
    setShowConfig(false)
    
    // Generate a job ID and save the name
    const tempJobId = `pending_${Date.now()}`
    const forecastName = config.name || `Forecast ${new Date().toLocaleDateString()}`
    
    // Set running state immediately
    setRunningJob({
      job_id: tempJobId,
      name: forecastName,
      started_at: new Date().toISOString(),
      progress: 10,
      status: 'starting'
    })
    setRunningElapsed(0)
    
    try {
      const response = await fetch('/api/v1/ml-development/runpod/forecast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ horizon: config.horizon, limit: config.limit })
      })
      
      if (!response.ok) throw new Error('Failed to start forecast')
      
      const result = await response.json()
      
      // Save the name for this job
      if (result.job_id) {
        saveForecastName(result.job_id, forecastName)
        setRunningJob(prev => prev ? { ...prev, job_id: result.job_id, status: 'running', progress: 30 } : null)
      }
      
      // Reset config name for next time
      setRunConfig(prev => ({ ...prev, name: '' }))
      
      // Refresh data
      setTimeout(loadData, 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to run forecast')
      setRunningJob(null)
    }
  }

  // Export functions
  const exportForecast = (forecast: ForecastResult | null) => {
    if (!forecast?.forecasts_preview) {
      setError('No forecast data to export')
      return
    }
    const blob = new Blob([forecast.forecasts_preview], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${forecast.name || forecast.job_id}_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const exportAllMetrics = () => {
    const completedJobs = allForecasts.filter(j => j.status === 'completed' && j.mae)
    if (completedJobs.length === 0) {
      setError('No metrics to export')
      return
    }
    const headers = ['Name', 'Job ID', 'Date', 'MAE', 'RMSE', 'Training Time (s)', 'GPU']
    const rows = completedJobs.map(j => [
      j.name || 'Unnamed',
      j.job_id,
      j.created_at || '',
      j.mae?.toFixed(4) || '',
      j.rmse?.toFixed(4) || '',
      j.training_time_seconds?.toFixed(1) || '',
      j.gpu_type || ''
    ])
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `all_forecasts_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // ============================================================================
  // HELPERS
  // ============================================================================
  const parseForecasts = (csv: string | undefined): ParsedForecast[] => {
    if (!csv) return []
    try {
      const lines = csv.trim().split('\n')
      const headers = lines[0].split(',')
      const itemIdx = headers.findIndex(h => h.includes('item_id'))
      const storeIdx = headers.findIndex(h => h.includes('store_id'))
      const valueIdx = headers.findIndex(h => h.includes('forecast'))
      return lines.slice(1, 15).map(line => {
        const cols = line.split(',')
        return { item: cols[itemIdx] || 'Unknown', store: cols[storeIdx] || '', value: parseFloat(cols[valueIdx]) || 0 }
      }).filter(f => f.value > 0)
    } catch { return [] }
  }

  const parseFeatures = (csv: string | undefined): ParsedFeature[] => {
    if (!csv) return []
    try {
      const lines = csv.trim().split('\n')
      return lines.slice(1, 8).map(line => {
        const [name, importance] = line.split(',')
        return { name, importance: parseFloat(importance) || 0 }
      }).filter(f => f.importance > 0)
    } catch { return [] }
  }

  const formatElapsed = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  const forecasts = parseForecasts(latestForecast?.forecasts_preview)
  const features = parseFeatures(latestForecast?.feature_importance)
  const maxForecast = Math.max(...forecasts.map(f => f.value), 1)
  const maxFeature = Math.max(...features.map(f => f.importance), 1)
  const completedForecasts = allForecasts.filter(j => j.status === 'completed' && j.mae)
    .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))

  // ============================================================================
  // TOOLTIP COMPONENT
  // ============================================================================
  const HelpTooltip = ({ metricKey, children }: { metricKey: string; children: React.ReactNode }) => {
    const help = METRIC_HELP[metricKey]
    if (!help) return <>{children}</>
    
    return (
      <div 
        style={{ position: 'relative', display: 'inline-block' }}
        onMouseEnter={() => setActiveTooltip(metricKey)}
        onMouseLeave={() => setActiveTooltip(null)}
      >
        {children}
        <span style={{ marginLeft: '4px', color: '#6b7280', cursor: 'help' }}>ⓘ</span>
        {activeTooltip === metricKey && (
          <div style={styles.tooltip}>
            <div style={styles.tooltipTitle}>{help.title}</div>
            <div style={styles.tooltipText}>{help.explanation}</div>
            <div style={styles.tooltipGood}>💡 {help.good}</div>
          </div>
        )}
      </div>
    )
  }

  // ============================================================================
  // RENDER
  // ============================================================================
  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingState}>
          <div style={styles.spinner} />
          <p>Loading your forecasts...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* ================================================================ */}
      {/* RUNNING JOB BANNER */}
      {/* ================================================================ */}
      {runningJob && (
        <div style={styles.runningBanner}>
          <div style={styles.runningContent}>
            <div style={styles.runningSpinner} />
            <div>
              <strong style={{ color: '#fbbf24' }}>Running: {runningJob.name}</strong>
              <span style={{ color: '#9ca3af', marginLeft: '12px' }}>
                {formatElapsed(runningElapsed)} elapsed
              </span>
            </div>
          </div>
          <div style={styles.runningProgress}>
            <div style={{ ...styles.runningProgressBar, width: `${Math.min(runningElapsed * 2, 95)}%` }} />
          </div>
        </div>
      )}

      {/* Header */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>📈 Forecast Center</h1>
          <p style={styles.subtitle}>
            Run, compare, and analyze your sales forecasts
          </p>
        </div>
        
        <div style={styles.headerActions}>
          {/* View Tabs */}
          <div style={styles.viewTabs}>
            {[
              { id: 'dashboard', label: '📊 Dashboard' },
              { id: 'history', label: '📋 History' },
              { id: 'compare', label: '⚖️ Compare' },
              { id: 'help', label: '❓ Help' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveView(tab.id as any)}
                style={{
                  ...styles.viewTab,
                  backgroundColor: activeView === tab.id ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                  color: activeView === tab.id ? '#60a5fa' : '#9ca3af'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* GPU Status */}
          <div style={{
            ...styles.gpuPill,
            backgroundColor: gpuStatus.active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(107, 114, 128, 0.15)',
            borderColor: gpuStatus.active ? 'rgba(16, 185, 129, 0.4)' : 'rgba(107, 114, 128, 0.4)'
          }}>
            <div style={{ ...styles.gpuDot, backgroundColor: gpuStatus.active ? '#10b981' : '#6b7280' }} />
            <span style={{ color: gpuStatus.active ? '#10b981' : '#9ca3af' }}>
              {gpuStatus.active ? gpuStatus.gpu_type : 'No GPU'}
            </span>
            {gpuStatus.balance !== undefined && (
              <span style={{ color: '#10b981', marginLeft: '8px' }}>${gpuStatus.balance.toFixed(2)}</span>
            )}
          </div>
          
          {/* Run Button */}
          <button 
            onClick={() => setShowConfig(true)}
            disabled={!!runningJob || !gpuStatus.active}
            style={{
              ...styles.primaryButton,
              opacity: (runningJob || !gpuStatus.active) ? 0.6 : 1,
              cursor: (runningJob || !gpuStatus.active) ? 'not-allowed' : 'pointer'
            }}
          >
            {runningJob ? '⏳ Running...' : '▶ New Forecast'}
          </button>
        </div>
      </header>

      {error && (
        <div style={styles.errorBanner}>
          {error}
          <button onClick={() => setError(null)} style={styles.errorClose}>×</button>
        </div>
      )}

      {/* Main Content */}
      <main style={styles.main}>
        {/* ================================================================ */}
        {/* DASHBOARD VIEW */}
        {/* ================================================================ */}
        {activeView === 'dashboard' && (
          <>
            {latestForecast ? (
              <>
                {/* Results Summary */}
                <section style={styles.summaryCard}>
                  <div style={styles.summaryHeader}>
                    <div>
                      <span style={styles.summaryLabel}>Latest Forecast</span>
                      <h2 style={styles.summaryTitle}>
                        {latestForecast.name || latestForecast.created_at 
                          ? new Date(latestForecast.created_at!).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
                          : 'Recent Forecast'
                        }
                      </h2>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button onClick={() => exportForecast(latestForecast)} style={styles.exportButton}>
                        📥 Export
                      </button>
                      <div style={styles.statusBadge}>✓ Complete</div>
                    </div>
                  </div>

                  {/* Metrics with Help Tooltips */}
                  <div style={styles.metricsGrid}>
                    <div style={styles.metricCard}>
                      <HelpTooltip metricKey="accuracy">
                        <span style={styles.metricLabel}>Model Accuracy</span>
                      </HelpTooltip>
                      <span style={{...styles.metricValue, color: '#10b981'}}>
                        {latestForecast.mae ? (100 - latestForecast.mae * 10).toFixed(1) : '—'}%
                      </span>
                      <span style={styles.metricUnit}>Based on MAE</span>
                    </div>
                    <div style={styles.metricCard}>
                      <HelpTooltip metricKey="mae">
                        <span style={styles.metricLabel}>MAE</span>
                      </HelpTooltip>
                      <span style={styles.metricValue}>{latestForecast.mae?.toFixed(3) || '—'}</span>
                      <span style={styles.metricUnit}>avg error per item</span>
                    </div>
                    <div style={styles.metricCard}>
                      <HelpTooltip metricKey="rmse">
                        <span style={styles.metricLabel}>RMSE</span>
                      </HelpTooltip>
                      <span style={styles.metricValue}>{latestForecast.rmse?.toFixed(3) || '—'}</span>
                      <span style={styles.metricUnit}>weighted error</span>
                    </div>
                    <div style={styles.metricCard}>
                      <HelpTooltip metricKey="training_time">
                        <span style={styles.metricLabel}>Training Time</span>
                      </HelpTooltip>
                      <span style={styles.metricValue}>
                        {latestForecast.training_time_seconds?.toFixed(1) || '—'}s
                      </span>
                      <span style={styles.metricUnit}>{latestForecast.gpu_type || 'GPU'}</span>
                    </div>
                  </div>
                </section>

                {/* Forecast Chart */}
                <section style={styles.chartSection}>
                  <h3 style={styles.sectionTitle}>📊 Predicted Sales by Item</h3>
                  <div style={styles.chartContainer}>
                    {forecasts.length > 0 ? (
                      <div style={styles.barChart}>
                        {forecasts.map((f, i) => (
                          <div key={i} style={styles.barGroup}>
                            <div style={styles.barWrapper}>
                              <div style={{ ...styles.bar, height: `${(f.value / maxForecast) * 100}%` }}>
                                <span style={styles.barValue}>{f.value.toFixed(0)}</span>
                              </div>
                            </div>
                            <span style={styles.barLabel}>{f.item.split('_').slice(-2).join('_')}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p style={styles.noData}>No forecast data available</p>
                    )}
                  </div>
                </section>

                {/* Insights */}
                <div style={styles.insightsGrid}>
                  <section style={styles.insightCard}>
                    <h3 style={styles.sectionTitle}>🎯 Key Drivers</h3>
                    <div style={styles.featureList}>
                      {features.length > 0 ? features.map((f, i) => (
                        <div key={i} style={styles.featureRow}>
                          <span style={styles.featureRank}>#{i + 1}</span>
                          <span style={styles.featureName}>{f.name}</span>
                          <div style={styles.featureBarContainer}>
                            <div style={{ ...styles.featureBar, width: `${(f.importance / maxFeature) * 100}%` }} />
                          </div>
                        </div>
                      )) : <p style={styles.noData}>No feature data</p>}
                    </div>
                    {features.length > 0 && (
                      <div style={styles.insightBox}>
                        <span>💡</span>
                        <p style={styles.insightText}>
                          <strong>{features[0]?.name}</strong> is the biggest predictor of sales.
                        </p>
                      </div>
                    )}
                  </section>

                  <section style={styles.insightCard}>
                    <h3 style={styles.sectionTitle}>⚡ Quick Actions</h3>
                    <div style={styles.actionsList}>
                      <button onClick={() => setShowConfig(true)} disabled={!gpuStatus.active} style={styles.actionButton}>
                        <span>🔄</span>
                        <div><strong>Run New Forecast</strong><span>Configure and run</span></div>
                      </button>
                      <button onClick={() => setActiveView('compare')} style={styles.actionButton}>
                        <span>⚖️</span>
                        <div><strong>Compare Forecasts</strong><span>Side-by-side analysis</span></div>
                      </button>
                      <button onClick={() => setActiveView('history')} style={styles.actionButton}>
                        <span>📋</span>
                        <div><strong>View History</strong><span>{completedForecasts.length} forecasts</span></div>
                      </button>
                      <button onClick={exportAllMetrics} style={styles.actionButton}>
                        <span>📥</span>
                        <div><strong>Export All</strong><span>Download as CSV</span></div>
                      </button>
                    </div>
                  </section>
                </div>
              </>
            ) : (
              /* Empty State */
              <section style={styles.emptyState}>
                <div style={styles.emptyIcon}>📊</div>
                <h2 style={styles.emptyTitle}>No Forecasts Yet</h2>
                <p style={styles.emptyText}>
                  Run your first forecast to predict future sales.
                  {!gpuStatus.active && ' Start a GPU pod on RunPod first.'}
                </p>
                <button 
                  onClick={gpuStatus.active ? () => setShowConfig(true) : () => window.open('https://runpod.io/console/pods', '_blank')}
                  style={styles.primaryButton}
                >
                  {gpuStatus.active ? '▶ Run First Forecast' : '🚀 Start GPU Pod'}
                </button>
              </section>
            )}
          </>
        )}

        {/* ================================================================ */}
        {/* HISTORY VIEW */}
        {/* ================================================================ */}
        {activeView === 'history' && (
          <section style={styles.historySection}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
              <div>
                <h2 style={styles.sectionTitle}>📋 Forecast History</h2>
                <p style={styles.sectionSubtitle}>{completedForecasts.length} completed forecasts</p>
              </div>
              <button onClick={exportAllMetrics} style={styles.exportButton}>📥 Export All</button>
            </div>

            {completedForecasts.length > 0 ? (
              <div style={styles.historyTable}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                      <th style={styles.tableHeader}>Name</th>
                      <th style={styles.tableHeader}>Date</th>
                      <th style={styles.tableHeader}>MAE</th>
                      <th style={styles.tableHeader}>RMSE</th>
                      <th style={styles.tableHeader}>Time</th>
                      <th style={styles.tableHeader}>GPU</th>
                      <th style={styles.tableHeader}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {completedForecasts.map((f, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={styles.tableCell}>
                          <strong style={{ color: '#f0f0f5' }}>{f.name || 'Unnamed'}</strong>
                        </td>
                        <td style={styles.tableCell}>
                          {f.created_at ? new Date(f.created_at).toLocaleDateString() : '—'}
                        </td>
                        <td style={styles.tableCell}>{f.mae?.toFixed(4) || '—'}</td>
                        <td style={styles.tableCell}>{f.rmse?.toFixed(4) || '—'}</td>
                        <td style={styles.tableCell}>{f.training_time_seconds?.toFixed(1)}s</td>
                        <td style={styles.tableCell}>{f.gpu_type || '—'}</td>
                        <td style={styles.tableCell}>
                          <button 
                            onClick={() => { setCompareJobA(f.job_id); setActiveView('compare'); }}
                            style={{ ...styles.smallButton, marginRight: '4px' }}
                          >
                            Compare
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={styles.emptyHistory}>
                <p>No completed forecasts yet. Run your first forecast to see history.</p>
              </div>
            )}
          </section>
        )}

        {/* ================================================================ */}
        {/* COMPARE VIEW */}
        {/* ================================================================ */}
        {activeView === 'compare' && (
          <section style={styles.compareSection}>
            <h2 style={styles.sectionTitle}>⚖️ Compare Forecasts</h2>
            <p style={styles.sectionSubtitle}>Select two forecasts to compare</p>

            <div style={styles.compareSelectors}>
              <div style={styles.compareSelector}>
                <label style={styles.compareSelectorLabel}>Forecast A</label>
                <select value={compareJobA} onChange={(e) => setCompareJobA(e.target.value)} style={styles.compareSelect}>
                  <option value="">Select...</option>
                  {completedForecasts.map(f => (
                    <option key={f.job_id} value={f.job_id}>
                      {f.name || f.created_at?.split('T')[0] || f.job_id.slice(0, 12)}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ fontSize: '24px', color: '#6b7280' }}>vs</div>
              <div style={styles.compareSelector}>
                <label style={styles.compareSelectorLabel}>Forecast B</label>
                <select value={compareJobB} onChange={(e) => setCompareJobB(e.target.value)} style={styles.compareSelect}>
                  <option value="">Select...</option>
                  {completedForecasts.map(f => (
                    <option key={f.job_id} value={f.job_id}>
                      {f.name || f.created_at?.split('T')[0] || f.job_id.slice(0, 12)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {compareDataA && compareDataB && (
              <div style={styles.compareResults}>
                <div style={styles.compareMetrics}>
                  {[
                    { key: 'mae', label: 'MAE', aVal: compareDataA.mae, bVal: compareDataB.mae, lowerBetter: true },
                    { key: 'rmse', label: 'RMSE', aVal: compareDataA.rmse, bVal: compareDataB.rmse, lowerBetter: true },
                    { key: 'time', label: 'Training Time', aVal: compareDataA.training_time_seconds, bVal: compareDataB.training_time_seconds, lowerBetter: true }
                  ].map(({ key, label, aVal, bVal, lowerBetter }) => {
                    const aWins = lowerBetter ? (aVal || 0) < (bVal || 0) : (aVal || 0) > (bVal || 0)
                    const bWins = lowerBetter ? (bVal || 0) < (aVal || 0) : (bVal || 0) > (aVal || 0)
                    return (
                      <div key={key} style={styles.compareMetricRow}>
                        <div style={styles.compareMetricLabel}>{label}</div>
                        <div style={{ ...styles.compareMetricValue, color: aWins ? '#10b981' : '#9ca3af' }}>
                          {typeof aVal === 'number' ? aVal.toFixed(4) : '—'}
                          {aWins && ' ✓'}
                        </div>
                        <div style={styles.compareMetricDiff}>
                          {aVal && bVal && `Δ ${Math.abs(aVal - bVal).toFixed(4)}`}
                        </div>
                        <div style={{ ...styles.compareMetricValue, color: bWins ? '#10b981' : '#9ca3af' }}>
                          {typeof bVal === 'number' ? bVal.toFixed(4) : '—'}
                          {bWins && ' ✓'}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {(!compareJobA || !compareJobB) && (
              <div style={styles.emptyCompare}>
                <p>Select two forecasts above to compare their results.</p>
              </div>
            )}
          </section>
        )}

        {/* ================================================================ */}
        {/* HELP VIEW */}
        {/* ================================================================ */}
        {activeView === 'help' && (
          <section style={styles.helpSection}>
            <h2 style={styles.sectionTitle}>❓ Understanding Your Forecasts</h2>
            
            <div style={styles.helpGrid}>
              {Object.entries(METRIC_HELP).map(([key, help]) => (
                <div key={key} style={styles.helpCard}>
                  <h3 style={styles.helpCardTitle}>{help.title}</h3>
                  <p style={styles.helpCardText}>{help.explanation}</p>
                  <div style={styles.helpCardTip}>
                    <span>💡</span> {help.good}
                  </div>
                </div>
              ))}
              
              <div style={styles.helpCard}>
                <h3 style={styles.helpCardTitle}>Feature Importance</h3>
                <p style={styles.helpCardText}>
                  Shows which factors most influence predictions. Higher bars = bigger impact on forecasts.
                </p>
                <div style={styles.helpCardTip}>
                  <span>💡</span> Use this to understand what drives your sales.
                </div>
              </div>
              
              <div style={styles.helpCard}>
                <h3 style={styles.helpCardTitle}>Forecast Horizon</h3>
                <p style={styles.helpCardText}>
                  How far into the future the model predicts. 28 days is typical for monthly planning.
                </p>
                <div style={styles.helpCardTip}>
                  <span>💡</span> Shorter horizons are usually more accurate.
                </div>
              </div>
            </div>

            <div style={styles.helpQuickStart}>
              <h3 style={styles.sectionTitle}>🚀 Quick Start Guide</h3>
              <ol style={styles.helpSteps}>
                <li><strong>Start a GPU</strong> - Make sure you have an active RunPod GPU</li>
                <li><strong>Click "New Forecast"</strong> - Configure your forecast settings</li>
                <li><strong>Name your forecast</strong> - Give it a memorable name like "Q1 Planning"</li>
                <li><strong>Wait for results</strong> - You'll be notified when it's done</li>
                <li><strong>Analyze & Compare</strong> - Review metrics and compare with past runs</li>
              </ol>
            </div>
          </section>
        )}
      </main>

      {/* ================================================================ */}
      {/* CONFIGURE & RUN MODAL */}
      {/* ================================================================ */}
      {showConfig && (
        <div style={styles.modalOverlay} onClick={() => setShowConfig(false)}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={{ margin: 0, color: '#f0f0f5' }}>▶ New Forecast</h2>
              <button onClick={() => setShowConfig(false)} style={styles.modalClose}>×</button>
            </div>
            
            <div style={styles.modalBody}>
              {/* Forecast Name - NEW! */}
              <div style={styles.configField}>
                <label style={styles.configLabel}>
                  Forecast Name
                  <span style={styles.configHint}>Give this forecast a memorable name</span>
                </label>
                <input
                  type="text"
                  value={runConfig.name}
                  onChange={e => setRunConfig(c => ({ ...c, name: e.target.value }))}
                  placeholder={`Forecast ${new Date().toLocaleDateString()}`}
                  style={styles.configTextInput}
                />
                <div style={styles.configPresets}>
                  {['Q1 Planning', 'Weekly Update', 'Test Run', 'Full Analysis'].map(name => (
                    <button
                      key={name}
                      onClick={() => setRunConfig(c => ({ ...c, name }))}
                      style={styles.configPreset}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Horizon */}
              <div style={styles.configField}>
                <label style={styles.configLabel}>
                  Forecast Horizon
                  <span style={styles.configHint}>Days into the future to predict</span>
                </label>
                <div style={styles.configInputGroup}>
                  <input
                    type="range" min="7" max="90" value={runConfig.horizon}
                    onChange={e => setRunConfig(c => ({ ...c, horizon: parseInt(e.target.value) }))}
                    style={styles.configSlider}
                  />
                  <input
                    type="number" value={runConfig.horizon}
                    onChange={e => setRunConfig(c => ({ ...c, horizon: parseInt(e.target.value) || 28 }))}
                    style={styles.configNumber}
                  />
                  <span style={styles.configUnit}>days</span>
                </div>
                <div style={styles.configPresets}>
                  {[7, 14, 28, 60, 90].map(d => (
                    <button
                      key={d}
                      onClick={() => setRunConfig(c => ({ ...c, horizon: d }))}
                      style={{ ...styles.configPreset, backgroundColor: runConfig.horizon === d ? 'rgba(59, 130, 246, 0.3)' : 'transparent' }}
                    >
                      {d}d
                    </button>
                  ))}
                </div>
              </div>

              {/* Data Size */}
              <div style={styles.configField}>
                <label style={styles.configLabel}>
                  Data Sample Size
                  <span style={styles.configHint}>More data = better accuracy, slower training</span>
                </label>
                <div style={styles.configInputGroup}>
                  <input
                    type="range" min="100" max="10000" step="100" value={runConfig.limit}
                    onChange={e => setRunConfig(c => ({ ...c, limit: parseInt(e.target.value) }))}
                    style={styles.configSlider}
                  />
                  <input
                    type="number" value={runConfig.limit}
                    onChange={e => setRunConfig(c => ({ ...c, limit: parseInt(e.target.value) || 1000 }))}
                    style={styles.configNumber}
                  />
                  <span style={styles.configUnit}>rows</span>
                </div>
                <div style={styles.configPresets}>
                  {[500, 1000, 2500, 5000, 10000].map(n => (
                    <button
                      key={n}
                      onClick={() => setRunConfig(c => ({ ...c, limit: n }))}
                      style={{ ...styles.configPreset, backgroundColor: runConfig.limit === n ? 'rgba(59, 130, 246, 0.3)' : 'transparent' }}
                    >
                      {n >= 1000 ? `${n/1000}k` : n}
                    </button>
                  ))}
                </div>
              </div>

              {/* Estimate */}
              <div style={styles.configEstimate}>
                <div style={styles.estimateRow}>
                  <span>Estimated time:</span>
                  <span>{Math.ceil(runConfig.limit / 500) * 10}s - {Math.ceil(runConfig.limit / 500) * 20}s</span>
                </div>
                <div style={styles.estimateRow}>
                  <span>GPU cost:</span>
                  <span>~${((gpuStatus.cost_per_hour || 0) / 60 * Math.ceil(runConfig.limit / 500) * 15 / 60).toFixed(3)}</span>
                </div>
              </div>
            </div>

            <div style={styles.modalFooter}>
              <button onClick={() => setShowConfig(false)} style={styles.modalCancel}>Cancel</button>
              <button onClick={() => runNewForecast(runConfig)} style={styles.modalSubmit}>
                ▶ Run Forecast
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={styles.footer}>
        <span>LightGBM • RunPod GPU</span>
      </footer>
    </div>
  )
}

// ============================================================================
// STYLES
// ============================================================================
const styles: Record<string, React.CSSProperties> = {
  container: { minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  
  // Running Banner
  runningBanner: { backgroundColor: 'rgba(251, 191, 36, 0.1)', borderBottom: '1px solid rgba(251, 191, 36, 0.3)', padding: '12px 32px' },
  runningContent: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' },
  runningSpinner: { width: '16px', height: '16px', border: '2px solid rgba(251, 191, 36, 0.3)', borderTop: '2px solid #fbbf24', borderRadius: '50%', animation: 'spin 1s linear infinite' },
  runningProgress: { height: '4px', backgroundColor: 'rgba(251, 191, 36, 0.2)', borderRadius: '2px', overflow: 'hidden' },
  runningProgressBar: { height: '100%', backgroundColor: '#fbbf24', transition: 'width 1s linear' },
  
  // Header
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 32px', borderBottom: '1px solid rgba(255,255,255,0.1)', flexWrap: 'wrap', gap: '16px' },
  title: { fontSize: '24px', fontWeight: '700', margin: 0 },
  subtitle: { fontSize: '13px', color: '#9ca3af', margin: '4px 0 0 0' },
  headerActions: { display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' },
  viewTabs: { display: 'flex', gap: '2px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '4px' },
  viewTab: { padding: '8px 14px', border: 'none', borderRadius: '6px', background: 'none', cursor: 'pointer', fontSize: '13px', transition: 'all 0.2s' },
  gpuPill: { display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', borderRadius: '20px', border: '1px solid', fontSize: '12px' },
  gpuDot: { width: '8px', height: '8px', borderRadius: '50%' },
  primaryButton: { padding: '10px 20px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '8px', color: '#fff', fontWeight: '600', fontSize: '14px', cursor: 'pointer' },
  exportButton: { padding: '8px 14px', backgroundColor: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#d1d5db', fontSize: '12px', cursor: 'pointer' },
  smallButton: { padding: '4px 10px', backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', borderRadius: '4px', color: '#60a5fa', fontSize: '11px', cursor: 'pointer' },
  
  // Main
  main: { padding: '24px 32px', maxWidth: '1400px', margin: '0 auto' },
  
  // Summary Card
  summaryCard: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', marginBottom: '20px', border: '1px solid rgba(255,255,255,0.1)' },
  summaryHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' },
  summaryLabel: { fontSize: '11px', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.5px' },
  summaryTitle: { fontSize: '20px', fontWeight: '600', margin: '4px 0 0 0' },
  statusBadge: { padding: '4px 10px', backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981', borderRadius: '12px', fontSize: '12px' },
  metricsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' },
  metricCard: { backgroundColor: '#1a1a24', borderRadius: '8px', padding: '14px' },
  metricLabel: { fontSize: '11px', color: '#9ca3af', display: 'block', marginBottom: '4px' },
  metricValue: { fontSize: '24px', fontWeight: '700', color: '#f0f0f5', display: 'block' },
  metricUnit: { fontSize: '11px', color: '#6b7280' },
  
  // Tooltip
  tooltip: { position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px', backgroundColor: '#1f1f2e', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px', padding: '12px', width: '250px', zIndex: 100, boxShadow: '0 4px 12px rgba(0,0,0,0.5)' },
  tooltipTitle: { fontWeight: '600', color: '#f0f0f5', marginBottom: '6px', fontSize: '13px' },
  tooltipText: { color: '#9ca3af', fontSize: '12px', marginBottom: '8px', lineHeight: '1.4' },
  tooltipGood: { color: '#10b981', fontSize: '11px', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '6px 8px', borderRadius: '4px' },
  
  // Chart
  chartSection: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', marginBottom: '20px', border: '1px solid rgba(255,255,255,0.1)' },
  sectionTitle: { fontSize: '16px', fontWeight: '600', margin: '0 0 4px 0', color: '#f0f0f5' },
  sectionSubtitle: { fontSize: '13px', color: '#6b7280', margin: 0 },
  chartContainer: { padding: '16px 0' },
  barChart: { display: 'flex', alignItems: 'flex-end', gap: '6px', height: '180px' },
  barGroup: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '35px' },
  barWrapper: { width: '100%', height: '140px', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' },
  bar: { width: '80%', background: 'linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%)', borderRadius: '3px 3px 0 0', minHeight: '4px', position: 'relative' },
  barValue: { position: 'absolute', top: '-18px', left: '50%', transform: 'translateX(-50%)', fontSize: '10px', color: '#9ca3af' },
  barLabel: { fontSize: '8px', color: '#6b7280', marginTop: '6px', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis' },
  
  // Insights
  insightsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '20px' },
  insightCard: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.1)' },
  featureList: { display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px' },
  featureRow: { display: 'flex', alignItems: 'center', gap: '10px' },
  featureRank: { fontSize: '10px', color: '#6b7280', width: '20px' },
  featureName: { fontSize: '12px', color: '#d1d5db', width: '90px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  featureBarContainer: { flex: 1, height: '6px', backgroundColor: '#1a1a24', borderRadius: '3px' },
  featureBar: { height: '100%', background: 'linear-gradient(90deg, #8b5cf6, #a78bfa)', borderRadius: '3px' },
  insightBox: { display: 'flex', gap: '10px', padding: '10px', backgroundColor: 'rgba(139, 92, 246, 0.1)', borderRadius: '6px', marginTop: '12px' },
  insightText: { fontSize: '12px', color: '#d1d5db', margin: 0 },
  actionsList: { display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' },
  actionButton: { display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#f0f0f5', cursor: 'pointer', textAlign: 'left', width: '100%' },
  
  // History
  historySection: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.1)' },
  historyTable: { backgroundColor: '#0f0f14', borderRadius: '6px', overflow: 'hidden' },
  tableHeader: { textAlign: 'left', padding: '10px 14px', fontSize: '11px', color: '#6b7280', fontWeight: '500' },
  tableCell: { padding: '10px 14px', fontSize: '12px', color: '#9ca3af' },
  emptyHistory: { textAlign: 'center', padding: '40px', color: '#6b7280' },
  
  // Compare
  compareSection: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.1)' },
  compareSelectors: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '20px', margin: '24px 0', flexWrap: 'wrap' },
  compareSelector: { flex: 1, minWidth: '200px', maxWidth: '350px' },
  compareSelectorLabel: { display: 'block', fontSize: '11px', color: '#6b7280', marginBottom: '6px' },
  compareSelect: { width: '100%', padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '13px' },
  compareResults: { marginTop: '24px' },
  compareMetrics: { backgroundColor: '#0f0f14', borderRadius: '8px', padding: '20px' },
  compareMetricRow: { display: 'grid', gridTemplateColumns: '100px 1fr 80px 1fr', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' },
  compareMetricLabel: { fontSize: '12px', color: '#6b7280' },
  compareMetricValue: { fontSize: '16px', fontWeight: '600', textAlign: 'center' },
  compareMetricDiff: { fontSize: '11px', color: '#6b7280', textAlign: 'center' },
  emptyCompare: { textAlign: 'center', padding: '40px', color: '#6b7280' },
  
  // Help
  helpSection: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.1)' },
  helpGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginTop: '20px' },
  helpCard: { backgroundColor: '#0f0f14', borderRadius: '8px', padding: '16px' },
  helpCardTitle: { fontSize: '14px', fontWeight: '600', color: '#f0f0f5', margin: '0 0 8px 0' },
  helpCardText: { fontSize: '13px', color: '#9ca3af', margin: '0 0 12px 0', lineHeight: '1.5' },
  helpCardTip: { fontSize: '12px', color: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '8px 10px', borderRadius: '4px', display: 'flex', gap: '6px' },
  helpQuickStart: { marginTop: '24px', backgroundColor: '#0f0f14', borderRadius: '8px', padding: '20px' },
  helpSteps: { margin: '16px 0 0 0', paddingLeft: '20px', color: '#d1d5db', fontSize: '13px', lineHeight: '2' },
  
  // Modal
  modalOverlay: { position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { backgroundColor: '#12121a', borderRadius: '12px', width: '90%', maxWidth: '480px', border: '1px solid rgba(255,255,255,0.1)' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  modalClose: { background: 'none', border: 'none', color: '#6b7280', fontSize: '20px', cursor: 'pointer' },
  modalBody: { padding: '20px' },
  modalFooter: { display: 'flex', justifyContent: 'flex-end', gap: '10px', padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.1)' },
  modalCancel: { padding: '8px 16px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', cursor: 'pointer' },
  modalSubmit: { padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: '600', cursor: 'pointer' },
  
  // Config
  configField: { marginBottom: '20px' },
  configLabel: { display: 'block', fontSize: '13px', fontWeight: '500', color: '#f0f0f5', marginBottom: '6px' },
  configHint: { display: 'block', fontSize: '11px', color: '#6b7280', fontWeight: '400' },
  configTextInput: { width: '100%', padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '14px', marginTop: '8px' },
  configInputGroup: { display: 'flex', alignItems: 'center', gap: '10px', marginTop: '8px' },
  configSlider: { flex: 1, accentColor: '#3b82f6' },
  configNumber: { width: '70px', padding: '6px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '4px', color: '#f0f0f5', textAlign: 'center' },
  configUnit: { fontSize: '12px', color: '#6b7280', width: '40px' },
  configPresets: { display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' },
  configPreset: { padding: '4px 10px', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '4px', color: '#9ca3af', background: 'none', cursor: 'pointer', fontSize: '11px' },
  configEstimate: { backgroundColor: '#0f0f14', borderRadius: '6px', padding: '12px' },
  estimateRow: { display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#9ca3af', marginBottom: '6px' },
  
  // Empty
  emptyState: { textAlign: 'center', padding: '60px 32px', backgroundColor: '#12121a', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.2)' },
  emptyIcon: { fontSize: '48px', marginBottom: '12px' },
  emptyTitle: { fontSize: '20px', fontWeight: '600', margin: '0 0 8px 0' },
  emptyText: { fontSize: '13px', color: '#9ca3af', margin: '0 0 20px 0', maxWidth: '360px', marginLeft: 'auto', marginRight: 'auto' },
  
  // Footer
  footer: { padding: '12px 32px', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '11px', color: '#6b7280', textAlign: 'center' },
  
  // Loading
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' },
  spinner: { width: '32px', height: '32px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' },
  
  // Error
  errorBanner: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 32px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontSize: '13px' },
  errorClose: { background: 'none', border: 'none', color: '#ef4444', fontSize: '18px', cursor: 'pointer' },
  
  noData: { color: '#6b7280', textAlign: 'center', padding: '24px', fontSize: '13px' }
}
