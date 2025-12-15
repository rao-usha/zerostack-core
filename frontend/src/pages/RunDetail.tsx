import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { PlayCircle, ArrowLeft, FileText, BarChart3, Package, Terminal } from 'lucide-react'

interface Run {
  id: string
  model_id?: string
  recipe_id: string
  recipe_version_id: string
  run_type: string
  status: string
  started_at?: string
  finished_at?: string
  metrics_json: any
  artifacts_json: any
  logs_text?: string
}

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [run, setRun] = useState<Run | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRun()
  }, [runId])

  const loadRun = async () => {
    try {
      const response = await fetch(`/api/v1/ml-development/runs/${runId}`)
      if (response.ok) {
        const data = await response.json()
        setRun(data)
      }
    } catch (error) {
      console.error('Error loading run:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      queued: '#9ca3af',
      running: '#3b82f6',
      succeeded: '#10b981',
      failed: '#ef4444'
    }
    return colors[status] || '#9ca3af'
  }

  const getDuration = () => {
    if (!run?.started_at || !run?.finished_at) return 'N/A'
    const start = new Date(run.started_at).getTime()
    const end = new Date(run.finished_at).getTime()
    const durationMs = end - start
    const minutes = Math.floor(durationMs / 60000)
    const seconds = Math.floor((durationMs % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', padding: '2rem' }}>
        <p style={{ textAlign: 'center', color: '#b3b3c4' }}>Loading run...</p>
      </div>
    )
  }

  if (!run) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', padding: '2rem' }}>
        <p style={{ textAlign: 'center', color: '#b3b3c4' }}>Run not found</p>
      </div>
    )
  }

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
              <PlayCircle className="h-8 w-8" style={{ color: '#a8d8ff' }} />
              <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f0f0f5' }}>
                Run {run.id}
              </h1>
              <span
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: `${getStatusColor(run.status)}20`,
                  color: getStatusColor(run.status),
                  borderRadius: '9999px',
                  fontSize: '0.875rem',
                  fontWeight: '600'
                }}
              >
                {run.status}
              </span>
            </div>
            <p style={{ color: '#b3b3c4', fontSize: '0.95rem' }}>
              {run.run_type} run
            </p>
          </div>
        </div>
      </div>

      <div style={{ padding: '2rem', maxWidth: '1200px' }}>
        {/* Run Summary */}
        <div style={{ 
          padding: '1.5rem', 
          backgroundColor: '#1a1a24', 
          border: '1px solid rgba(168, 216, 255, 0.2)',
          borderRadius: '0.75rem',
          marginBottom: '2rem'
        }}>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '600', 
            marginBottom: '1.5rem', 
            color: '#a8d8ff',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <FileText className="h-5 w-5" />
            Run Summary
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
            <div>
              <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Run Type</p>
              <p style={{ color: '#f0f0f5', fontWeight: '600', fontSize: '1.125rem' }}>{run.run_type}</p>
            </div>
            <div>
              <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Status</p>
              <p style={{ color: getStatusColor(run.status), fontWeight: '600', fontSize: '1.125rem' }}>{run.status}</p>
            </div>
            <div>
              <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Duration</p>
              <p style={{ color: '#f0f0f5', fontWeight: '600', fontSize: '1.125rem' }}>{getDuration()}</p>
            </div>
            <div>
              <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Recipe</p>
              <p 
                style={{ color: '#a8d8ff', fontWeight: '600', fontSize: '1.125rem', cursor: 'pointer' }}
                onClick={() => navigate(`/model-development/recipes/${run.recipe_id}`)}
              >
                {run.recipe_id}
              </p>
            </div>
            {run.model_id && (
              <div>
                <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Model</p>
                <p 
                  style={{ color: '#a8d8ff', fontWeight: '600', fontSize: '1.125rem', cursor: 'pointer' }}
                  onClick={() => navigate(`/model-development/models/${run.model_id}`)}
                >
                  {run.model_id}
                </p>
              </div>
            )}
            {run.started_at && (
              <div>
                <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Started At</p>
                <p style={{ color: '#f0f0f5', fontWeight: '600', fontSize: '1.125rem' }}>
                  {new Date(run.started_at).toLocaleString()}
                </p>
              </div>
            )}
            {run.finished_at && (
              <div>
                <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Finished At</p>
                <p style={{ color: '#f0f0f5', fontWeight: '600', fontSize: '1.125rem' }}>
                  {new Date(run.finished_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Metrics */}
        {Object.keys(run.metrics_json).length > 0 && (
          <div style={{ 
            padding: '1.5rem', 
            backgroundColor: '#1a1a24', 
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.75rem',
            marginBottom: '2rem'
          }}>
            <h3 style={{ 
              fontSize: '1.125rem', 
              fontWeight: '600', 
              marginBottom: '1.5rem', 
              color: '#a8d8ff',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <BarChart3 className="h-5 w-5" />
              Performance Metrics
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
              {Object.entries(run.metrics_json).map(([key, value]) => (
                <div key={key}>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                    {key.toUpperCase()}
                  </p>
                  <p style={{ color: '#f0f0f5', fontSize: '2rem', fontWeight: '700' }}>
                    {typeof value === 'number' ? value.toFixed(4) : JSON.stringify(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Artifacts */}
        {Object.keys(run.artifacts_json).length > 0 && (
          <div style={{ 
            padding: '1.5rem', 
            backgroundColor: '#1a1a24', 
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.75rem',
            marginBottom: '2rem'
          }}>
            <h3 style={{ 
              fontSize: '1.125rem', 
              fontWeight: '600', 
              marginBottom: '1.5rem', 
              color: '#a8d8ff',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <Package className="h-5 w-5" />
              Artifacts
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {Object.entries(run.artifacts_json).map(([key, value]) => (
                <div 
                  key={key}
                  style={{
                    padding: '1rem',
                    backgroundColor: 'rgba(168, 216, 255, 0.05)',
                    border: '1px solid rgba(168, 216, 255, 0.1)',
                    borderRadius: '0.5rem'
                  }}
                >
                  <p style={{ color: '#a8d8ff', fontSize: '0.95rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                    {key}
                  </p>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', fontFamily: 'monospace' }}>
                    {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Logs */}
        {run.logs_text && (
          <div style={{ 
            padding: '1.5rem', 
            backgroundColor: '#1a1a24', 
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.75rem'
          }}>
            <h3 style={{ 
              fontSize: '1.125rem', 
              fontWeight: '600', 
              marginBottom: '1.5rem', 
              color: '#a8d8ff',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <Terminal className="h-5 w-5" />
              Run Logs
            </h3>
            <pre 
              style={{ 
                backgroundColor: '#0a0a0f', 
                padding: '1rem', 
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontSize: '0.875rem',
                fontFamily: 'monospace',
                overflowX: 'auto',
                maxHeight: '400px',
                overflowY: 'auto'
              }}
            >
              {run.logs_text}
            </pre>
          </div>
        )}

        {/* Empty states */}
        {Object.keys(run.metrics_json).length === 0 && 
         Object.keys(run.artifacts_json).length === 0 && 
         !run.logs_text && (
          <div style={{ 
            textAlign: 'center', 
            padding: '3rem', 
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.75rem',
            color: '#b3b3c4' 
          }}>
            <PlayCircle className="h-16 w-16" style={{ margin: '0 auto 1rem', color: '#a8d8ff' }} />
            <p>No metrics, artifacts, or logs available yet</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
              {run.status === 'queued' && 'Run is queued and will start soon'}
              {run.status === 'running' && 'Run is in progress'}
              {run.status === 'succeeded' && 'Run completed but no outputs were recorded'}
              {run.status === 'failed' && 'Run failed before producing outputs'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}


