import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '@/api/client'

// ============================================================================
// TYPES
// ============================================================================
interface Recipe {
  id: string
  name: string
  model_family: string
  level: string
  status: string
}

interface Dataset {
  id: string
  name: string
  source_type: string
  row_count?: number
}

interface Run {
  id: string
  status: string
  started_at?: string
  finished_at?: string
  recipe_id?: string
  compute_target?: string
  gpu_type?: string
  runtime_seconds?: number
  metrics_json?: Record<string, any>
  actual_cost_usd?: number
}

interface Job {
  job_id: string
  status: string
  gpu_type?: string
  pod_name?: string
  mae?: number
  rmse?: number
  training_time_seconds?: number
  started_at?: string
}

interface GpuPod {
  id: string
  name: string
  status: string
  gpu_type: string
  cost_per_hour: number
}

// ============================================================================
// WORKBENCH COMPONENT
// ============================================================================
export default function MLWorkbench() {
  const navigate = useNavigate()
  
  // Data state
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [pods, setPods] = useState<GpuPod[]>([])
  const [spending, setSpending] = useState<any>(null)
  
  // UI state
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null)
  const [selectedRun, setSelectedRun] = useState<Run | null>(null)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [activePanel, setActivePanel] = useState<'recipe' | 'run' | 'job'>('recipe')
  const [consoleMessages, setConsoleMessages] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  
  // Refs
  const consoleRef = useRef<HTMLDivElement>(null)

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  const log = useCallback((msg: string) => {
    const timestamp = new Date().toLocaleTimeString()
    setConsoleMessages(prev => [...prev.slice(-50), `[${timestamp}] ${msg}`])
  }, [])

  const loadAllData = useCallback(async () => {
    try {
      log('Loading workspace data...')

      const [recipesRes, datasetsRes, runsRes, jobsRes, podsRes, spendingRes] = await Promise.all([
        client.get('/api/v1/ml-development/recipes').then(r => r.data).catch(() => ({ recipes: [] })),
        client.get('/api/v1/highlighted-datasets').then(r => r.data).catch(() => ({ datasets: [] })),
        client.get('/api/v1/ml-development/runs').then(r => r.data).catch(() => ({ runs: [] })),
        client.get('/api/v1/ml-development/runpod/jobs').then(r => r.data).catch(() => ({ jobs: [] })),
        client.get('/api/v1/ml-development/runpod/pods').then(r => r.data).catch(() => ({ pods: [] })),
        client.get('/api/v1/ml-development/runpod/spending').then(r => r.data).catch(() => null)
      ])

      setRecipes(recipesRes.recipes || [])
      setDatasets(datasetsRes.datasets || [])
      setRuns(runsRes.runs || [])
      setJobs(jobsRes.jobs || [])
      setPods(podsRes.pods || [])
      setSpending(spendingRes)

      log(`Loaded: ${recipesRes.recipes?.length || 0} recipes, ${runsRes.runs?.length || 0} runs, ${jobsRes.jobs?.length || 0} jobs`)
    } catch (error) {
      log(`Error loading data: ${error}`)
    } finally {
      setLoading(false)
    }
  }, [log])

  useEffect(() => {
    loadAllData()
    // Refresh every 10 seconds
    const interval = setInterval(loadAllData, 10000)
    return () => clearInterval(interval)
  }, [loadAllData])

  // Auto-scroll console
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight
    }
  }, [consoleMessages])

  // ============================================================================
  // KEYBOARD SHORTCUTS
  // ============================================================================
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in input
      if ((e.target as HTMLElement).tagName === 'INPUT') return
      
      switch (e.key) {
        case '1': setActivePanel('recipe'); break
        case '2': setActivePanel('run'); break
        case '3': setActivePanel('job'); break
        case 'r': if (e.ctrlKey) { e.preventDefault(); loadAllData(); } break
        case 'Escape': setSelectedRecipe(null); setSelectedRun(null); setSelectedJob(null); break
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [loadAllData])

  // ============================================================================
  // ACTIONS
  // ============================================================================
  const runForecast = async () => {
    log('Starting forecast job...')
    try {
      const response = await client.post('/api/v1/ml-development/runpod/forecast', {
        horizon: 28,
        limit: 1000
      })
      log(`Job submitted: ${response.data.job_id || 'Unknown'}`)
      setTimeout(loadAllData, 2000)
    } catch (error) {
      log(`Failed to start job: ${error}`)
    }
  }

  // ============================================================================
  // HELPERS
  // ============================================================================
  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      running: '#fbbf24', queued: '#f59e0b', succeeded: '#10b981', 
      completed: '#10b981', failed: '#ef4444', RUNNING: '#10b981',
      active: '#10b981', draft: '#6b7280', published: '#3b82f6'
    }
    return colors[status] || '#6b7280'
  }

  const formatTime = (seconds?: number) => {
    if (!seconds) return '-'
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`
  }

  const activePod = pods.find(p => p.status === 'RUNNING')

  // ============================================================================
  // RENDER
  // ============================================================================
  return (
    <div style={{
      height: '100vh',
      display: 'grid',
      gridTemplateRows: 'auto 1fr auto',
      gridTemplateColumns: '220px 1fr 320px',
      backgroundColor: '#0a0a0f',
      color: '#e0e0e5',
      fontFamily: "'SF Mono', 'Consolas', monospace",
      fontSize: '12px'
    }}>
      
      {/* ================================================================== */}
      {/* TOP BAR - GPU Status & Quick Actions */}
      {/* ================================================================== */}
      <div style={{
        gridColumn: '1 / -1',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 12px',
        backgroundColor: '#12121a',
        borderBottom: '1px solid #2a2a3a'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ color: '#a8d8ff', fontWeight: 'bold', fontSize: '14px' }}>ML WORKBENCH</span>
          <span style={{ color: '#6b7280' }}>|</span>
          
          {/* GPU Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              backgroundColor: activePod ? '#10b981' : '#6b7280',
              animation: activePod ? 'pulse 2s infinite' : 'none'
            }} />
            <span style={{ color: activePod ? '#10b981' : '#6b7280' }}>
              {activePod ? `${activePod.name} (${activePod.gpu_type})` : 'No GPU'}
            </span>
            {activePod && (
              <span style={{ color: '#fbbf24' }}>${activePod.cost_per_hour?.toFixed(2)}/hr</span>
            )}
          </div>
          
          {spending && (
            <>
              <span style={{ color: '#6b7280' }}>|</span>
              <span style={{ color: '#10b981' }}>BAL: ${spending.client_balance?.toFixed(2)}</span>
            </>
          )}
        </div>
        
        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={runForecast} style={buttonStyle}>
            ▶ RUN FORECAST
          </button>
          <button onClick={loadAllData} style={buttonStyle}>
            ↻ REFRESH
          </button>
          <button onClick={() => navigate('/model-development')} style={{...buttonStyle, backgroundColor: 'transparent', border: '1px solid #3a3a4a'}}>
            ← OLD VIEW
          </button>
        </div>
      </div>

      {/* ================================================================== */}
      {/* LEFT SIDEBAR - Navigation Tree */}
      {/* ================================================================== */}
      <div style={{
        backgroundColor: '#0f0f14',
        borderRight: '1px solid #2a2a3a',
        overflow: 'auto'
      }}>
        {/* Recipes Section */}
        <SidebarSection title="RECIPES" count={recipes.length} hotkey="1">
          {recipes.slice(0, 10).map(recipe => (
            <SidebarItem
              key={recipe.id}
              label={recipe.name}
              sublabel={recipe.model_family}
              status={recipe.status}
              selected={selectedRecipe?.id === recipe.id}
              onClick={() => { setSelectedRecipe(recipe); setActivePanel('recipe'); }}
            />
          ))}
        </SidebarSection>

        {/* Datasets Section */}
        <SidebarSection title="DATASETS" count={datasets.length}>
          {datasets.slice(0, 8).map(ds => (
            <SidebarItem
              key={ds.id}
              label={ds.name}
              sublabel={ds.source_type}
              onClick={() => log(`Selected dataset: ${ds.name}`)}
            />
          ))}
        </SidebarSection>

        {/* Active Jobs */}
        <SidebarSection title="GPU JOBS" count={jobs.length} hotkey="3">
          {jobs.slice(0, 6).map(job => (
            <SidebarItem
              key={job.job_id}
              label={job.job_id?.slice(0, 12) || 'Unknown'}
              sublabel={job.gpu_type || 'GPU'}
              status={job.status}
              selected={selectedJob?.job_id === job.job_id}
              onClick={() => { setSelectedJob(job); setActivePanel('job'); }}
            />
          ))}
        </SidebarSection>
      </div>

      {/* ================================================================== */}
      {/* MAIN WORKSPACE - Center Panel */}
      {/* ================================================================== */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Panel Tabs */}
        <div style={{
          display: 'flex',
          gap: '2px',
          padding: '4px 8px',
          backgroundColor: '#12121a',
          borderBottom: '1px solid #2a2a3a'
        }}>
          {[
            { id: 'recipe', label: 'RECIPE', hotkey: '1' },
            { id: 'run', label: 'RUNS', hotkey: '2' },
            { id: 'job', label: 'JOB DETAILS', hotkey: '3' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActivePanel(tab.id as any)}
              style={{
                padding: '6px 12px',
                backgroundColor: activePanel === tab.id ? '#1a1a24' : 'transparent',
                border: 'none',
                borderBottom: activePanel === tab.id ? '2px solid #a8d8ff' : '2px solid transparent',
                color: activePanel === tab.id ? '#a8d8ff' : '#6b7280',
                cursor: 'pointer',
                fontSize: '11px',
                fontFamily: 'inherit'
              }}
            >
              {tab.label} <span style={{ color: '#4a4a5a', fontSize: '10px' }}>[{tab.hotkey}]</span>
            </button>
          ))}
        </div>

        {/* Panel Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
          {activePanel === 'recipe' && (
            <RecipePanel recipe={selectedRecipe} runs={runs.filter(r => r.recipe_id === selectedRecipe?.id)} />
          )}
          {activePanel === 'run' && (
            <RunsPanel 
              runs={runs} 
              selectedRun={selectedRun}
              onSelectRun={setSelectedRun}
            />
          )}
          {activePanel === 'job' && (
            <JobPanel job={selectedJob} />
          )}
        </div>
      </div>

      {/* ================================================================== */}
      {/* RIGHT SIDEBAR - Live Stats & Results */}
      {/* ================================================================== */}
      <div style={{
        backgroundColor: '#0f0f14',
        borderLeft: '1px solid #2a2a3a',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Stats Grid */}
        <div style={{ padding: '8px', borderBottom: '1px solid #2a2a3a' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <StatCard label="RECIPES" value={recipes.length} color="#3b82f6" />
            <StatCard label="RUNS" value={runs.length} color="#8b5cf6" />
            <StatCard label="COMPLETED" value={runs.filter(r => r.status === 'succeeded').length} color="#10b981" />
            <StatCard label="RUNNING" value={runs.filter(r => r.status === 'running').length} color="#fbbf24" />
          </div>
        </div>

        {/* Recent Activity */}
        <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
          <div style={{ color: '#6b7280', fontSize: '10px', marginBottom: '8px' }}>RECENT RUNS</div>
          {runs.slice(0, 8).map(run => (
            <div 
              key={run.id}
              onClick={() => { setSelectedRun(run); setActivePanel('run'); }}
              style={{
                padding: '8px',
                marginBottom: '4px',
                backgroundColor: selectedRun?.id === run.id ? '#1a1a2e' : '#12121a',
                borderRadius: '4px',
                cursor: 'pointer',
                borderLeft: `3px solid ${getStatusColor(run.status)}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#e0e0e5', fontWeight: 500 }}>{run.id.slice(0, 8)}</span>
                <span style={{ color: getStatusColor(run.status), fontSize: '10px' }}>{run.status.toUpperCase()}</span>
              </div>
              {run.metrics_json?.mae && (
                <div style={{ color: '#6b7280', fontSize: '10px', marginTop: '2px' }}>
                  MAE: {Number(run.metrics_json.mae).toFixed(4)}
                </div>
              )}
              {run.runtime_seconds && (
                <div style={{ color: '#6b7280', fontSize: '10px' }}>
                  ⏱ {formatTime(run.runtime_seconds)}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* GPU Jobs Quick View */}
        <div style={{ borderTop: '1px solid #2a2a3a', padding: '8px' }}>
          <div style={{ color: '#6b7280', fontSize: '10px', marginBottom: '8px' }}>GPU JOBS</div>
          {jobs.slice(0, 3).map(job => (
            <div 
              key={job.job_id}
              style={{
                padding: '6px',
                marginBottom: '4px',
                backgroundColor: '#12121a',
                borderRadius: '4px',
                fontSize: '10px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#a8d8ff' }}>{job.job_id?.slice(0, 10)}</span>
                <span style={{ color: getStatusColor(job.status) }}>{job.status}</span>
              </div>
              {job.mae && <span style={{ color: '#10b981' }}>MAE: {job.mae.toFixed(4)}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* ================================================================== */}
      {/* BOTTOM CONSOLE - Activity Log */}
      {/* ================================================================== */}
      <div 
        ref={consoleRef}
        style={{
          gridColumn: '1 / -1',
          backgroundColor: '#08080c',
          borderTop: '1px solid #2a2a3a',
          padding: '4px 8px',
          height: '80px',
          overflow: 'auto',
          fontFamily: "'SF Mono', monospace",
          fontSize: '10px'
        }}
      >
        <div style={{ color: '#4a4a5a', marginBottom: '4px' }}>
          CONSOLE — Keyboard: [1] Recipe [2] Runs [3] Jobs [Ctrl+R] Refresh [Esc] Clear
        </div>
        {consoleMessages.map((msg, i) => (
          <div key={i} style={{ color: '#8b8b9b' }}>{msg}</div>
        ))}
        {loading && <div style={{ color: '#fbbf24' }}>Loading...</div>}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

const buttonStyle: React.CSSProperties = {
  padding: '4px 12px',
  backgroundColor: '#2563eb',
  border: 'none',
  borderRadius: '4px',
  color: '#fff',
  fontSize: '10px',
  fontWeight: 'bold',
  cursor: 'pointer',
  fontFamily: 'inherit'
}

function SidebarSection({ title, count, hotkey, children }: { 
  title: string
  count: number
  hotkey?: string
  children: React.ReactNode 
}) {
  const [collapsed, setCollapsed] = useState(false)
  
  return (
    <div style={{ borderBottom: '1px solid #1a1a24' }}>
      <div 
        onClick={() => setCollapsed(!collapsed)}
        style={{
          padding: '8px 10px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          backgroundColor: '#12121a'
        }}
      >
        <span style={{ color: '#8b8b9b', fontSize: '10px', fontWeight: 'bold' }}>
          {collapsed ? '▸' : '▾'} {title}
          {hotkey && <span style={{ color: '#4a4a5a' }}> [{hotkey}]</span>}
        </span>
        <span style={{ 
          backgroundColor: '#2a2a3a', 
          padding: '1px 6px', 
          borderRadius: '8px',
          color: '#6b7280',
          fontSize: '9px'
        }}>
          {count}
        </span>
      </div>
      {!collapsed && <div>{children}</div>}
    </div>
  )
}

function SidebarItem({ label, sublabel, status, selected, onClick }: {
  label: string
  sublabel?: string
  status?: string
  selected?: boolean
  onClick?: () => void
}) {
  const statusColors: Record<string, string> = {
    running: '#fbbf24', succeeded: '#10b981', completed: '#10b981',
    failed: '#ef4444', active: '#10b981', draft: '#6b7280', published: '#3b82f6'
  }
  
  return (
    <div 
      onClick={onClick}
      style={{
        padding: '6px 10px 6px 16px',
        cursor: 'pointer',
        backgroundColor: selected ? '#1a1a2e' : 'transparent',
        borderLeft: selected ? '2px solid #a8d8ff' : '2px solid transparent'
      }}
    >
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{ 
          color: selected ? '#a8d8ff' : '#c0c0c5',
          fontSize: '11px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          maxWidth: '140px'
        }}>
          {label}
        </span>
        {status && (
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: statusColors[status] || '#6b7280'
          }} />
        )}
      </div>
      {sublabel && (
        <div style={{ color: '#5a5a6a', fontSize: '9px' }}>{sublabel}</div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{
      backgroundColor: '#12121a',
      padding: '8px',
      borderRadius: '4px',
      borderLeft: `3px solid ${color}`
    }}>
      <div style={{ color: '#6b7280', fontSize: '9px' }}>{label}</div>
      <div style={{ color, fontSize: '18px', fontWeight: 'bold' }}>{value}</div>
    </div>
  )
}

function RecipePanel({ recipe, runs }: { recipe: Recipe | null; runs: Run[] }) {
  if (!recipe) {
    return (
      <div style={{ color: '#6b7280', padding: '20px', textAlign: 'center' }}>
        Select a recipe from the sidebar to view details
      </div>
    )
  }

  return (
    <div>
      <div style={{ 
        padding: '12px', 
        backgroundColor: '#12121a', 
        borderRadius: '6px',
        marginBottom: '12px'
      }}>
        <h2 style={{ color: '#a8d8ff', margin: '0 0 8px 0', fontSize: '16px' }}>{recipe.name}</h2>
        <div style={{ display: 'flex', gap: '16px', color: '#8b8b9b', fontSize: '11px' }}>
          <span>Family: <span style={{ color: '#c0c0c5' }}>{recipe.model_family}</span></span>
          <span>Level: <span style={{ color: '#c0c0c5' }}>{recipe.level}</span></span>
          <span>Status: <span style={{ color: recipe.status === 'published' ? '#10b981' : '#6b7280' }}>{recipe.status}</span></span>
        </div>
      </div>

      {/* Associated Runs */}
      <div style={{ color: '#6b7280', fontSize: '10px', marginBottom: '8px' }}>
        RUNS FOR THIS RECIPE ({runs.length})
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '8px' }}>
        {runs.map(run => (
          <div key={run.id} style={{
            padding: '10px',
            backgroundColor: '#12121a',
            borderRadius: '4px',
            borderLeft: `3px solid ${run.status === 'succeeded' ? '#10b981' : run.status === 'running' ? '#fbbf24' : '#6b7280'}`
          }}>
            <div style={{ color: '#c0c0c5', fontWeight: 500 }}>{run.id.slice(0, 12)}</div>
            <div style={{ color: '#6b7280', fontSize: '10px', marginTop: '4px' }}>
              {run.status} • {run.gpu_type || 'local'}
            </div>
            {run.metrics_json?.mae && (
              <div style={{ color: '#10b981', fontSize: '11px', marginTop: '4px' }}>
                MAE: {Number(run.metrics_json.mae).toFixed(4)}
              </div>
            )}
          </div>
        ))}
        {runs.length === 0 && (
          <div style={{ color: '#5a5a6a', fontSize: '11px' }}>No runs yet</div>
        )}
      </div>
    </div>
  )
}

function RunsPanel({ runs, selectedRun, onSelectRun }: { 
  runs: Run[]
  selectedRun: Run | null
  onSelectRun: (run: Run) => void 
}) {
  return (
    <div style={{ display: 'flex', gap: '12px', height: '100%' }}>
      {/* Runs List */}
      <div style={{ width: '300px', overflow: 'auto' }}>
        <div style={{ color: '#6b7280', fontSize: '10px', marginBottom: '8px' }}>
          ALL RUNS ({runs.length})
        </div>
        {runs.map(run => (
          <div 
            key={run.id}
            onClick={() => onSelectRun(run)}
            style={{
              padding: '10px',
              marginBottom: '4px',
              backgroundColor: selectedRun?.id === run.id ? '#1a1a2e' : '#12121a',
              borderRadius: '4px',
              cursor: 'pointer',
              borderLeft: `3px solid ${run.status === 'succeeded' ? '#10b981' : run.status === 'running' ? '#fbbf24' : '#6b7280'}`
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#c0c0c5' }}>{run.id.slice(0, 16)}</span>
              <span style={{ 
                color: run.status === 'succeeded' ? '#10b981' : run.status === 'running' ? '#fbbf24' : '#6b7280',
                fontSize: '10px'
              }}>
                {run.status}
              </span>
            </div>
            <div style={{ color: '#5a5a6a', fontSize: '10px', marginTop: '2px' }}>
              {run.compute_target || 'local'} • {run.gpu_type || '-'}
            </div>
          </div>
        ))}
      </div>

      {/* Run Details */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {selectedRun ? (
          <div style={{ backgroundColor: '#12121a', borderRadius: '6px', padding: '12px' }}>
            <h3 style={{ color: '#a8d8ff', margin: '0 0 12px 0', fontSize: '14px' }}>
              Run: {selectedRun.id}
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <div style={{ color: '#6b7280', fontSize: '10px' }}>STATUS</div>
                <div style={{ color: '#c0c0c5' }}>{selectedRun.status}</div>
              </div>
              <div>
                <div style={{ color: '#6b7280', fontSize: '10px' }}>COMPUTE</div>
                <div style={{ color: '#c0c0c5' }}>{selectedRun.compute_target || 'local'}</div>
              </div>
              <div>
                <div style={{ color: '#6b7280', fontSize: '10px' }}>GPU</div>
                <div style={{ color: '#c0c0c5' }}>{selectedRun.gpu_type || '-'}</div>
              </div>
              <div>
                <div style={{ color: '#6b7280', fontSize: '10px' }}>RUNTIME</div>
                <div style={{ color: '#c0c0c5' }}>
                  {selectedRun.runtime_seconds ? `${selectedRun.runtime_seconds.toFixed(1)}s` : '-'}
                </div>
              </div>
              {selectedRun.actual_cost_usd && (
                <div>
                  <div style={{ color: '#6b7280', fontSize: '10px' }}>COST</div>
                  <div style={{ color: '#10b981' }}>${selectedRun.actual_cost_usd.toFixed(4)}</div>
                </div>
              )}
            </div>

            {/* Metrics */}
            {selectedRun.metrics_json && Object.keys(selectedRun.metrics_json).length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ color: '#6b7280', fontSize: '10px', marginBottom: '8px' }}>METRICS</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  {Object.entries(selectedRun.metrics_json).map(([key, value]) => (
                    <div key={key} style={{ 
                      backgroundColor: '#0f0f14', 
                      padding: '8px', 
                      borderRadius: '4px' 
                    }}>
                      <div style={{ color: '#6b7280', fontSize: '9px', textTransform: 'uppercase' }}>{key}</div>
                      <div style={{ color: '#a8d8ff', fontSize: '14px', fontWeight: 'bold' }}>
                        {typeof value === 'number' ? value.toFixed(4) : String(value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ color: '#6b7280', padding: '20px', textAlign: 'center' }}>
            Select a run to view details
          </div>
        )}
      </div>
    </div>
  )
}

function JobPanel({ job }: { job: Job | null }) {
  const [details, setDetails] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (job?.job_id) {
      setLoading(true)
      client.get(`/api/v1/ml-development/runpod/jobs/${job.job_id}`)
        .then(r => setDetails(r.data))
        .catch(console.error)
        .finally(() => setLoading(false))
    }
  }, [job?.job_id])

  if (!job) {
    return (
      <div style={{ color: '#6b7280', padding: '20px', textAlign: 'center' }}>
        Select a GPU job from the sidebar to view details
      </div>
    )
  }

  return (
    <div>
      <div style={{ 
        padding: '12px', 
        backgroundColor: '#12121a', 
        borderRadius: '6px',
        marginBottom: '12px'
      }}>
        <h3 style={{ color: '#a8d8ff', margin: '0 0 8px 0', fontSize: '14px' }}>
          Job: {job.job_id}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
          <div>
            <div style={{ color: '#6b7280', fontSize: '10px' }}>STATUS</div>
            <div style={{ color: job.status === 'completed' ? '#10b981' : '#fbbf24' }}>{job.status}</div>
          </div>
          <div>
            <div style={{ color: '#6b7280', fontSize: '10px' }}>GPU</div>
            <div style={{ color: '#c0c0c5' }}>{job.gpu_type || '-'}</div>
          </div>
          <div>
            <div style={{ color: '#6b7280', fontSize: '10px' }}>POD</div>
            <div style={{ color: '#c0c0c5' }}>{job.pod_name || '-'}</div>
          </div>
          <div>
            <div style={{ color: '#6b7280', fontSize: '10px' }}>TRAINING TIME</div>
            <div style={{ color: '#c0c0c5' }}>
              {job.training_time_seconds ? `${job.training_time_seconds.toFixed(1)}s` : '-'}
            </div>
          </div>
        </div>
      </div>

      {loading && <div style={{ color: '#fbbf24' }}>Loading job details...</div>}

      {/* Metrics */}
      {details?.mae && (
        <div style={{ marginBottom: '12px' }}>
          <div style={{ color: '#6b7280', fontSize: '10px', marginBottom: '8px' }}>METRICS</div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ 
              padding: '12px 20px', 
              backgroundColor: '#12121a', 
              borderRadius: '6px',
              borderLeft: '3px solid #3b82f6'
            }}>
              <div style={{ color: '#6b7280', fontSize: '10px' }}>MAE</div>
              <div style={{ color: '#3b82f6', fontSize: '24px', fontWeight: 'bold' }}>
                {details.mae.toFixed(4)}
              </div>
            </div>
            {details.rmse && (
              <div style={{ 
                padding: '12px 20px', 
                backgroundColor: '#12121a', 
                borderRadius: '6px',
                borderLeft: '3px solid #8b5cf6'
              }}>
                <div style={{ color: '#6b7280', fontSize: '10px' }}>RMSE</div>
                <div style={{ color: '#8b5cf6', fontSize: '24px', fontWeight: 'bold' }}>
                  {details.rmse.toFixed(4)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Feature Importance Chart */}
      {details?.feature_importance && (
        <div style={{ marginBottom: '12px' }}>
          <div style={{ color: '#6b7280', fontSize: '10px', marginBottom: '8px' }}>FEATURE IMPORTANCE</div>
          <div style={{ backgroundColor: '#12121a', borderRadius: '6px', padding: '12px' }}>
            {(() => {
              const lines = details.feature_importance.trim().split('\n')
              const data = lines.slice(1).map((line: string) => {
                const [feature, importance] = line.split(',')
                return { feature, importance: parseFloat(importance) }
              }).filter((d: any) => !isNaN(d.importance)).slice(0, 8)
              
              const maxImportance = Math.max(...data.map((d: any) => d.importance))
              
              return data.map((item: any, i: number) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ color: '#8b8b9b', width: '100px', fontSize: '10px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.feature}
                  </span>
                  <div style={{ flex: 1, height: '16px', backgroundColor: '#1a1a24', borderRadius: '2px' }}>
                    <div 
                      style={{
                        height: '100%',
                        width: `${(item.importance / maxImportance) * 100}%`,
                        background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                        borderRadius: '2px'
                      }}
                    />
                  </div>
                  <span style={{ color: '#6b7280', fontSize: '10px', width: '50px', textAlign: 'right' }}>
                    {item.importance.toFixed(0)}
                  </span>
                </div>
              ))
            })()}
          </div>
        </div>
      )}
    </div>
  )
}
