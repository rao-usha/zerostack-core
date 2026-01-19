import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Package, Tag, Calendar, Activity, AlertCircle } from 'lucide-react'

interface EvaluationPack {
  id: string
  name: string
  model_family: string
  status: string
  tags: string[]
  created_at: string
  updated_at: string
}

export default function EvaluationPackDetail() {
  const { packId } = useParams<{ packId: string }>()
  const navigate = useNavigate()
  const [pack, setPack] = useState<EvaluationPack | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPack()
  }, [packId])

  const loadPack = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`/api/v1/evaluation-packs/${packId}`)
      
      if (!response.ok) {
        throw new Error(`Failed to load pack: ${response.statusText}`)
      }
      
      const data = await response.json()
      setPack(data)
    } catch (err: any) {
      console.error('Error loading evaluation pack:', err)
      setError(err.message || 'Failed to load evaluation pack')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'ready':
        return '#22c55e'
      case 'draft':
        return '#f59e0b'
      case 'archived':
        return '#6b7280'
      default:
        return '#a8d8ff'
    }
  }

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0a0a0f',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <Activity className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff', margin: '0 auto' }} />
          <p style={{ marginTop: '1rem', color: '#b3b3c4' }}>Loading evaluation pack...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0a0a0f',
        padding: '2rem'
      }}>
        <div style={{
          maxWidth: '48rem',
          margin: '0 auto',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '0.75rem',
          padding: '1.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <AlertCircle className="h-6 w-6" style={{ color: '#ef4444' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#ef4444' }}>
              Error Loading Evaluation Pack
            </h2>
          </div>
          <p style={{ color: '#fca5a5', marginBottom: '1.5rem' }}>{error}</p>
          <button
            onClick={() => navigate('/model-development')}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'rgba(168, 216, 255, 0.15)',
              color: '#a8d8ff',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            ← Back to Model Library
          </button>
        </div>
      </div>
    )
  }

  if (!pack) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#0a0a0f',
        padding: '2rem'
      }}>
        <div style={{ maxWidth: '48rem', margin: '0 auto', textAlign: 'center' }}>
          <p style={{ color: '#b3b3c4' }}>Evaluation pack not found</p>
          <button
            onClick={() => navigate('/model-development')}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: 'rgba(168, 216, 255, 0.15)',
              color: '#a8d8ff',
              border: 'none',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            ← Back to Model Library
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0a0f',
      padding: '2rem'
    }}>
      <div style={{ maxWidth: '80rem', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <button
            onClick={() => navigate('/model-development')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              backgroundColor: 'transparent',
              color: '#a8d8ff',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              marginBottom: '1.5rem',
              fontWeight: '500',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.1)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
            }}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Model Library
          </button>

          <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Package className="h-8 w-8" style={{ color: '#a8d8ff' }} />
              <h1 style={{ fontSize: '2rem', fontWeight: '700', color: '#f0f0f5' }}>
                {pack.name}
              </h1>
            </div>
            
            <span
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: `${getStatusColor(pack.status)}20`,
                color: getStatusColor(pack.status),
                borderRadius: '9999px',
                fontSize: '0.875rem',
                fontWeight: '600',
                whiteSpace: 'nowrap'
              }}
            >
              {pack.status}
            </span>
          </div>

          {/* Metadata */}
          <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', color: '#b3b3c4', fontSize: '0.875rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Tag className="h-4 w-4" />
              <span>{pack.model_family || 'No family'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Calendar className="h-4 w-4" />
              <span>Created {new Date(pack.created_at).toLocaleDateString()}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Calendar className="h-4 w-4" />
              <span>Updated {new Date(pack.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Tags */}
        {pack.tags && pack.tags.length > 0 ? (
          <div style={{
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.75rem',
            padding: '1.5rem'
          }}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#b3b3c4', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
              Tags
            </h3>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {pack.tags.map((tag, idx) => (
                <span
                  key={idx}
                  style={{
                    padding: '0.375rem 0.75rem',
                    backgroundColor: 'rgba(168, 216, 255, 0.15)',
                    color: '#a8d8ff',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem'
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div style={{
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.75rem',
            padding: '1.5rem',
            textAlign: 'center',
            color: '#b3b3c4'
          }}>
            <Tag className="h-12 w-12" style={{ margin: '0 auto', marginBottom: '1rem', opacity: 0.5 }} />
            <p>No tags defined for this evaluation pack</p>
          </div>
        )}
      </div>
    </div>
  )
}

