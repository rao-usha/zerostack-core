import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Toast from '../components/Toast'
import { BookOpen, ArrowLeft, Save, Copy, CheckCircle, Edit, FileText, GitBranch, Beaker, Github, ExternalLink, Star, Database, ArrowRight, PlayCircle, X, Cloud, Monitor } from 'lucide-react'
import LiveRunStatus from '../components/LiveRunStatus'

interface Recipe {
  id: string
  name: string
  model_family: string
  level: string
  status: string
  parent_id?: string
  tags: string[]
  created_at: string
  updated_at: string
}

interface RecipeVersion {
  version_id: string
  recipe_id: string
  version_number: string
  manifest_json: any
  created_by?: string
  created_at: string
  change_note?: string
}

type TabType = 'overview' | 'manifest' | 'versions' | 'synthetic' | 'reference'

// Helper function to get M5 data source info
const getM5DataSource = (modelFamily: string) => {
  if (modelFamily === 'forecasting') {
    return {
      name: 'M5 Forecasting - Walmart Retail Sales',
      description: 'Daily sales data with prices, events, and calendar features',
      tables: ['m5_sales', 'm5_calendar', 'm5_items', 'm5_prices'],
      grain: 'item_store_day',
      target: 'sales',
      dateRange: '2011-01-29 to 2016-06-19 (1,969 days)',
      rows: '60M+',
      features: ['historical_sales', 'price', 'day_of_week', 'is_weekend', 'is_event_day', 'is_snap_day'],
      queryExample: `SELECT 
  c.date, s.sales, p.sell_price,
  c.weekday, c.event_name_1
FROM m5_sales s
JOIN m5_calendar c ON s.d = c.d
LEFT JOIN m5_prices p ON s.item_id = p.item_id 
  AND s.store_id = p.store_id 
  AND c.wm_yr_wk = p.wm_yr_wk
WHERE s.item_store_id = 'FOODS_1_001_CA_1'
ORDER BY c.date`
    }
  } else if (modelFamily === 'pricing') {
    return {
      name: 'M5 Price Elasticity Data',
      description: 'Price-demand relationships for elasticity modeling',
      tables: ['m5_prices', 'm5_sales', 'm5_calendar'],
      grain: 'item_store_week',
      target: 'demand_response',
      dateRange: '2011-01-29 to 2016-06-19',
      rows: '60M+',
      features: ['price', 'price_change', 'demand', 'events', 'seasonality'],
      queryExample: `SELECT 
  p.wm_yr_wk, p.item_id, p.sell_price,
  AVG(s.sales) as avg_daily_sales
FROM m5_prices p
JOIN m5_sales s ON p.item_id = s.item_id 
  AND p.store_id = s.store_id
JOIN m5_calendar c ON s.d = c.d 
  AND c.wm_yr_wk = p.wm_yr_wk
GROUP BY p.wm_yr_wk, p.item_id, p.sell_price`
    }
  }
  return null
}

export default function RecipeDetail() {
  const { recipeId } = useParams<{ recipeId: string }>()
  const navigate = useNavigate()
  const [toast, setToast] = useState<{
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
  } | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [versions, setVersions] = useState<RecipeVersion[]>([])
  const [selectedVersion, setSelectedVersion] = useState<RecipeVersion | null>(null)
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [manifestText, setManifestText] = useState('')
  const [saving, setSaving] = useState(false)
  
  // Run Recipe Modal State
  const [showRunModal, setShowRunModal] = useState(false)
  const [runParams, setRunParams] = useState<Record<string, any>>({})
  const [computeTarget, setComputeTarget] = useState<'local' | 'runpod'>('runpod')
  const [creatingRun, setCreatingRun] = useState(false)
  const [runError, setRunError] = useState<string | null>(null)
  const [availableGpus, setAvailableGpus] = useState<any[]>([])
  const [runningPods, setRunningPods] = useState<any[]>([])
  const [selectedPod, setSelectedPod] = useState<string>('')
  const [loadingGpus, setLoadingGpus] = useState(false)
  const [spending, setSpending] = useState<any>(null)
  
  // Live run tracking
  const [activeRunId, setActiveRunId] = useState<string | null>(null)

  useEffect(() => {
    loadRecipe()
    loadVersions()
  }, [recipeId])

  useEffect(() => {
    if (selectedVersion) {
      setManifestText(JSON.stringify(selectedVersion.manifest_json, null, 2))
    }
  }, [selectedVersion])

  const loadRecipe = async () => {
    try {
      const response = await fetch(`/api/v1/ml-development/recipes/${recipeId}`)
      if (response.ok) {
        const data = await response.json()
        setRecipe(data)
      }
    } catch (error) {
      console.error('Error loading recipe:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadVersions = async () => {
    try {
      const response = await fetch(`/api/v1/ml-development/recipes/${recipeId}/versions`)
      if (response.ok) {
        const data = await response.json()
        setVersions(data)
        if (data.length > 0) {
          setSelectedVersion(data[0])
        }
      }
    } catch (error) {
      console.error('Error loading versions:', error)
    }
  }

  const saveNewVersion = async () => {
    setSaving(true)
    try {
      const manifestJson = JSON.parse(manifestText)
      const response = await fetch(`/api/v1/ml-development/recipes/${recipeId}/versions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipe_id: recipeId,
          manifest_json: manifestJson,
          change_note: 'Manual edit',
          created_by: 'user'
        })
      })
      
      if (response.ok) {
        await loadVersions()
        setEditMode(false)
      }
    } catch (error) {
      console.error('Error saving version:', error)
      setToast({ message: 'Error saving manifest. Please check JSON syntax.', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  const approveRecipe = async () => {
    try {
      const response = await fetch(`/api/v1/ml-development/recipes/${recipeId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'approved' })
      })
      if (response.ok) {
        await loadRecipe()
      }
    } catch (error) {
      console.error('Error approving recipe:', error)
    }
  }

  const cloneRecipe = async () => {
    const newName = prompt('Enter name for cloned recipe:', `${recipe?.name} (copy)`)
    if (!newName) return
    
    try {
      const response = await fetch(`/api/v1/ml-development/recipes/${recipeId}/clone?name=${encodeURIComponent(newName)}`, {
        method: 'POST'
      })
      if (response.ok) {
        const data = await response.json()
        navigate(`/model-development/recipes/${data.id}`)
      }
    } catch (error) {
      console.error('Error cloning recipe:', error)
    }
  }

  const openRunModal = async () => {
    // Set default parameters based on recipe family
    const defaultParams: Record<string, any> = {}
    if (recipe?.model_family === 'forecasting') {
      defaultParams.horizon = 28
      defaultParams.n_estimators = 100
    } else if (recipe?.model_family === 'pricing') {
      defaultParams.features = ['price', 'demand']
    }
    setRunParams(defaultParams)
    setRunError(null)
    setShowRunModal(true)
    
    // Fetch available GPUs, running pods, and spending info
    setLoadingGpus(true)
    try {
      const [gpuResponse, podResponse, spendingResponse] = await Promise.all([
        fetch('/api/v1/ml-development/runpod/gpus').then(r => r.ok ? r.json() : { gpus: [] }),
        fetch('/api/v1/ml-development/runpod/pods').then(r => r.ok ? r.json() : { pods: [] }),
        fetch('/api/v1/ml-development/runpod/spending').then(r => r.ok ? r.json() : null)
      ])
      setAvailableGpus(gpuResponse.gpus || [])
      setRunningPods(podResponse.pods || [])
      setSpending(spendingResponse)
      // Auto-select a running pod if available
      const activePods = (podResponse.pods || []).filter((p: any) => p.status === 'RUNNING')
      if (activePods.length > 0) {
        setSelectedPod(activePods[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch RunPod data:', error)
    } finally {
      setLoadingGpus(false)
    }
  }

  const createRun = async () => {
    if (!selectedVersion) return
    
    // Check if using RunPod but no running pod selected
    if (computeTarget === 'runpod') {
      const activePods = runningPods.filter(p => p.status === 'RUNNING')
      if (activePods.length === 0) {
        setRunError('No running pods available. Start a pod on RunPod or use Local compute.')
        return
      }
      if (!selectedPod) {
        setRunError('Please select a running pod to use.')
        return
      }
    }
    
    setCreatingRun(true)
    setRunError(null)
    
    try {
      const response = await fetch('/api/v1/ml-development/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipe_id: recipeId,
          recipe_version_id: selectedVersion.version_id,
          run_type: 'train',
          compute_target: computeTarget,
          parameters: {
            ...runParams,
            ...(selectedPod ? { pod_id: selectedPod } : {})
          }
        })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to create run')
      }
      
      const run = await response.json()
      setShowRunModal(false)
      // Show live status tracker instead of navigating away
      setActiveRunId(run.id)
    } catch (error: any) {
      console.error('Error creating run:', error)
      setRunError(error.message || 'Failed to create run')
    } finally {
      setCreatingRun(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#fbbf24',
      approved: '#10b981',
      archived: '#6b7280'
    }
    return colors[status] || '#9ca3af'
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', padding: '2rem' }}>
        <p style={{ textAlign: 'center', color: '#b3b3c4' }}>Loading recipe...</p>
      </div>
    )
  }

  if (!recipe) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', padding: '2rem' }}>
        <p style={{ textAlign: 'center', color: '#b3b3c4' }}>Recipe not found</p>
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
              <BookOpen className="h-8 w-8" style={{ color: '#a8d8ff' }} />
              <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f0f0f5' }}>
                {recipe.name}
              </h1>
              <span
                style={{
                  padding: '0.25rem 0.75rem',
                  backgroundColor: `${getStatusColor(recipe.status)}20`,
                  color: getStatusColor(recipe.status),
                  borderRadius: '9999px',
                  fontSize: '0.875rem',
                  fontWeight: '600'
                }}
              >
                {recipe.status}
              </span>
            </div>
            <p style={{ color: '#b3b3c4', fontSize: '0.95rem' }}>
              {recipe.model_family} · {recipe.level} level
            </p>
          </div>

          <div style={{ display: 'flex', gap: '1rem' }}>
            {/* Run Recipe Button - Primary Action */}
            <button
              onClick={openRunModal}
              disabled={!selectedVersion}
              style={{
                padding: '0.75rem 1.5rem',
                background: 'linear-gradient(135deg, #a8d8ff, #c4b5fd)',
                border: 'none',
                borderRadius: '0.5rem',
                color: '#0a0a0f',
                fontWeight: '700',
                cursor: selectedVersion ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                opacity: selectedVersion ? 1 : 0.5
              }}
            >
              <PlayCircle className="h-5 w-5" />
              Run Recipe
            </button>

            {recipe.status === 'draft' && (
              <button
                onClick={approveRecipe}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  borderRadius: '0.5rem',
                  color: '#10b981',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <CheckCircle className="h-5 w-5" />
                Approve Recipe
              </button>
            )}
            
            <button
              onClick={cloneRecipe}
              style={{
                padding: '0.75rem 1.5rem',
                background: 'rgba(168, 216, 255, 0.1)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.5rem',
                color: '#a8d8ff',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <Copy className="h-5 w-5" />
              Clone Recipe
            </button>
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
            { id: 'manifest', label: 'Manifest Editor', icon: Edit },
            { id: 'versions', label: 'Versions', icon: GitBranch },
            { id: 'reference', label: 'Reference Repos', icon: Github },
            { id: 'synthetic', label: 'Synthetic Example', icon: Beaker }
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
        {activeTab === 'overview' && selectedVersion && (
          <div style={{ maxWidth: '800px' }}>
            <div style={{ 
              padding: '1.5rem', 
              backgroundColor: '#1a1a24', 
              border: '1px solid rgba(168, 216, 255, 0.2)',
              borderRadius: '0.75rem',
              marginBottom: '1.5rem'
            }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#a8d8ff' }}>
                Recipe Metadata
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Model Family</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{recipe.model_family}</p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Level</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{recipe.level}</p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Status</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{recipe.status}</p>
                </div>
                <div>
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Current Version</p>
                  <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{selectedVersion.version_number}</p>
                </div>
              </div>
            </div>

            {selectedVersion.manifest_json.metadata && (
              <div style={{ 
                padding: '1.5rem', 
                backgroundColor: '#1a1a24', 
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.75rem',
                marginBottom: '1.5rem'
              }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#a8d8ff' }}>
                  Manifest Summary
                </h3>
                <p style={{ color: '#b3b3c4', fontSize: '0.95rem', lineHeight: '1.6' }}>
                  {selectedVersion.manifest_json.metadata.description || 'No description available'}
                </p>
              </div>
            )}

            {/* Data Source Section */}
            {(() => {
              const dataSource = getM5DataSource(recipe.model_family)
              if (!dataSource) return null

              return (
                <div style={{ 
                  padding: '1.5rem', 
                  backgroundColor: '#1a1a24', 
                  border: '1px solid rgba(168, 216, 255, 0.2)',
                  borderRadius: '0.75rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                    <Database className="h-5 w-5" style={{ color: '#a8d8ff' }} />
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#a8d8ff' }}>
                      Data Source
                    </h3>
                  </div>

                  {/* Dataset Name */}
                  <div style={{ marginBottom: '1.5rem' }}>
                    <p style={{ fontSize: '1rem', fontWeight: '600', color: '#f0f0f5', marginBottom: '0.5rem' }}>
                      {dataSource.name}
                    </p>
                    <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>
                      {dataSource.description}
                    </p>
                  </div>

                  {/* Tables */}
                  <div style={{ marginBottom: '1rem' }}>
                    <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                      <strong>Tables:</strong>
                    </p>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {dataSource.tables.map(table => (
                        <span key={table} style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: 'rgba(168, 216, 255, 0.15)',
                          color: '#a8d8ff',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem',
                          fontFamily: 'monospace'
                        }}>
                          {table}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Data Specs */}
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
                    gap: '1rem',
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    backgroundColor: 'rgba(168, 216, 255, 0.05)',
                    borderRadius: '0.5rem'
                  }}>
                    <div>
                      <p style={{ color: '#b3b3c4', fontSize: '0.75rem', marginBottom: '0.25rem' }}>GRAIN</p>
                      <p style={{ color: '#f0f0f5', fontSize: '0.875rem', fontWeight: '600' }}>{dataSource.grain}</p>
                    </div>
                    <div>
                      <p style={{ color: '#b3b3c4', fontSize: '0.75rem', marginBottom: '0.25rem' }}>TARGET</p>
                      <p style={{ color: '#f0f0f5', fontSize: '0.875rem', fontWeight: '600' }}>{dataSource.target}</p>
                    </div>
                    <div>
                      <p style={{ color: '#b3b3c4', fontSize: '0.75rem', marginBottom: '0.25rem' }}>DATE RANGE</p>
                      <p style={{ color: '#f0f0f5', fontSize: '0.875rem', fontWeight: '600' }}>{dataSource.dateRange}</p>
                    </div>
                    <div>
                      <p style={{ color: '#b3b3c4', fontSize: '0.75rem', marginBottom: '0.25rem' }}>VOLUME</p>
                      <p style={{ color: '#f0f0f5', fontSize: '0.875rem', fontWeight: '600' }}>{dataSource.rows} rows</p>
                    </div>
                  </div>

                  {/* Key Features */}
                  <div style={{ marginBottom: '1.5rem' }}>
                    <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                      <strong>Key Features:</strong>
                    </p>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {dataSource.features.map(feature => (
                        <span key={feature} style={{
                          padding: '0.25rem 0.5rem',
                          backgroundColor: 'rgba(139, 92, 246, 0.1)',
                          border: '1px solid rgba(139, 92, 246, 0.3)',
                          borderRadius: '0.25rem',
                          fontSize: '0.75rem',
                          color: '#b3b3c4'
                        }}>
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => navigate('/data-explorer', { 
                        state: { 
                          prefilledQuery: dataSource.queryExample,
                          datasetName: 'M5 Forecasting'
                        }
                      })}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: '#a8d8ff',
                        color: '#0a0a0f',
                        border: 'none',
                        borderRadius: '0.375rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#8ec5ff'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#a8d8ff'
                      }}
                    >
                      <Database className="h-4 w-4" />
                      Explore M5 Data
                      <ArrowRight className="h-4 w-4" />
                    </button>

                    <button
                      onClick={() => window.open('https://www.kaggle.com/competitions/m5-forecasting-accuracy', '_blank')}
                      style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: 'rgba(168, 216, 255, 0.1)',
                        color: '#a8d8ff',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                        borderRadius: '0.375rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem'
                      }}
                    >
                      <ExternalLink className="h-4 w-4" />
                      M5 Competition
                    </button>
                  </div>

                  {/* Info Note */}
                  <div style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: '0.375rem'
                  }}>
                    <p style={{ color: '#b3b3c4', fontSize: '0.75rem', lineHeight: '1.4' }}>
                      💡 <strong>M5 Dataset:</strong> This recipe is designed to work with the M5 Forecasting dataset 
                      from Kaggle. Click "Explore M5 Data" to query the full dataset or view the schema.
                    </p>
                  </div>
                </div>
              )
            })()}
          </div>
        )}

        {activeTab === 'manifest' && selectedVersion && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <p style={{ color: '#b3b3c4', fontSize: '0.95rem' }}>
                Editing version: {selectedVersion.version_number}
              </p>
              <div style={{ display: 'flex', gap: '1rem' }}>
                {editMode && (
                  <>
                    <button
                      onClick={() => setEditMode(false)}
                      style={{
                        padding: '0.5rem 1rem',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        borderRadius: '0.375rem',
                        color: '#ef4444',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={saveNewVersion}
                      disabled={saving}
                      style={{
                        padding: '0.5rem 1rem',
                        background: 'rgba(168, 216, 255, 0.1)',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                        borderRadius: '0.375rem',
                        color: '#a8d8ff',
                        cursor: saving ? 'not-allowed' : 'pointer',
                        opacity: saving ? 0.5 : 1,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}
                    >
                      <Save className="h-4 w-4" />
                      {saving ? 'Saving...' : 'Save as New Version'}
                    </button>
                  </>
                )}
                {!editMode && (
                  <button
                    onClick={() => setEditMode(true)}
                    style={{
                      padding: '0.5rem 1rem',
                      background: 'rgba(168, 216, 255, 0.1)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      borderRadius: '0.375rem',
                      color: '#a8d8ff',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}
                  >
                    <Edit className="h-4 w-4" />
                    Edit Manifest
                  </button>
                )}
              </div>
            </div>

            <textarea
              value={manifestText}
              onChange={(e) => setManifestText(e.target.value)}
              disabled={!editMode}
              style={{
                width: '100%',
                minHeight: '600px',
                padding: '1rem',
                backgroundColor: '#1a1a24',
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                lineHeight: '1.5',
                resize: 'vertical',
                opacity: editMode ? 1 : 0.7
              }}
            />
          </div>
        )}

        {activeTab === 'versions' && (
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#f0f0f5' }}>
              Version History
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {versions.map((version, idx) => (
                <div
                  key={version.version_id}
                  onClick={() => {
                    setSelectedVersion(version)
                    setActiveTab('manifest')
                  }}
                  style={{
                    padding: '1.5rem',
                    backgroundColor: '#1a1a24',
                    border: selectedVersion?.version_id === version.version_id 
                      ? '1px solid rgba(168, 216, 255, 0.5)' 
                      : '1px solid rgba(168, 216, 255, 0.2)',
                    borderRadius: '0.75rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.5)'}
                  onMouseLeave={(e) => {
                    if (selectedVersion?.version_id !== version.version_id) {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.2)'
                    }
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                        <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5' }}>
                          Version {version.version_number}
                        </h4>
                        {idx === 0 && (
                          <span
                            style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: 'rgba(168, 216, 255, 0.15)',
                              color: '#a8d8ff',
                              borderRadius: '0.25rem',
                              fontSize: '0.75rem',
                              fontWeight: '600'
                            }}
                          >
                            LATEST
                          </span>
                        )}
                      </div>
                      <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                        {version.change_note || 'No change note'}
                      </p>
                      <p style={{ color: '#9ca3af', fontSize: '0.8rem' }}>
                        Created {new Date(version.created_at).toLocaleString()}
                        {version.created_by && ` by ${version.created_by}`}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'reference' && selectedVersion && (
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem', color: '#f0f0f5' }}>
              Reference Implementations
            </h3>
            <p style={{ color: '#b3b3c4', marginBottom: '2rem', fontSize: '0.95rem' }}>
              Example repositories and implementations for {recipe?.model_family} models
            </p>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
              {selectedVersion.manifest_json.reference_repos?.map((repo: any, idx: number) => (
                <div
                  key={idx}
                  style={{
                    padding: '1.5rem',
                    backgroundColor: '#1a1a24',
                    border: '1px solid rgba(168, 216, 255, 0.2)',
                    borderRadius: '0.75rem',
                    transition: 'all 0.2s',
                    cursor: 'pointer'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.4)'
                    e.currentTarget.style.transform = 'translateY(-2px)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.2)'
                    e.currentTarget.style.transform = 'translateY(0)'
                  }}
                  onClick={() => window.open(repo.url, '_blank')}
                >
                  <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <Github className="h-5 w-5" style={{ color: '#a8d8ff' }} />
                      <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5', margin: 0 }}>
                        {repo.name}
                      </h4>
                    </div>
                    <ExternalLink className="h-4 w-4" style={{ color: '#b3b3c4' }} />
                  </div>
                  
                  <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '1rem', lineHeight: '1.5' }}>
                    {repo.description}
                  </p>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                    {repo.stars && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fbbf24' }}>
                        <Star className="h-4 w-4" />
                        <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>{repo.stars}</span>
                      </div>
                    )}
                    {repo.language && (
                      <span style={{
                        padding: '0.25rem 0.75rem',
                        background: 'rgba(168, 216, 255, 0.1)',
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        color: '#a8d8ff',
                        fontWeight: '600'
                      }}>
                        {repo.language}
                      </span>
                    )}
                    {repo.framework && (
                      <span style={{
                        padding: '0.25rem 0.75rem',
                        background: 'rgba(139, 92, 246, 0.1)',
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        color: '#a78bfa',
                        fontWeight: '600'
                      }}>
                        {repo.framework}
                      </span>
                    )}
                  </div>
                  
                  {repo.tags && repo.tags.length > 0 && (
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                      {repo.tags.map((tag: string, tagIdx: number) => (
                        <span
                          key={tagIdx}
                          style={{
                            padding: '0.25rem 0.5rem',
                            background: 'rgba(139, 92, 246, 0.05)',
                            border: '1px solid rgba(139, 92, 246, 0.2)',
                            borderRadius: '0.25rem',
                            fontSize: '0.75rem',
                            color: '#9ca3af'
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              
              {(!selectedVersion.manifest_json.reference_repos || selectedVersion.manifest_json.reference_repos.length === 0) && (
                <div style={{ 
                  gridColumn: '1 / -1',
                  textAlign: 'center', 
                  padding: '3rem', 
                  color: '#b3b3c4',
                  backgroundColor: '#1a1a24',
                  border: '1px solid rgba(168, 216, 255, 0.1)',
                  borderRadius: '0.75rem'
                }}>
                  <Github className="h-16 w-16" style={{ margin: '0 auto 1rem', color: '#a8d8ff', opacity: 0.5 }} />
                  <p>No reference repositories configured for this recipe yet</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'synthetic' && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
            <Beaker className="h-16 w-16" style={{ margin: '0 auto 1rem', color: '#a8d8ff' }} />
            <p>Synthetic examples for testing recipes will appear here</p>
          </div>
        )}
      </div>

      {/* Run Recipe Modal */}
      {showRunModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50
        }}>
          <div style={{
            backgroundColor: '#1a1a24',
            borderRadius: '1rem',
            border: '1px solid rgba(168, 216, 255, 0.3)',
            width: '100%',
            maxWidth: '500px',
            maxHeight: '90vh',
            overflow: 'auto'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '1.5rem',
              borderBottom: '1px solid rgba(168, 216, 255, 0.2)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <PlayCircle className="h-6 w-6" style={{ color: '#a8d8ff' }} />
                <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f0f0f5', margin: 0 }}>
                  Run Recipe
                </h2>
              </div>
              <button
                onClick={() => setShowRunModal(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#b3b3c4',
                  cursor: 'pointer',
                  padding: '0.5rem'
                }}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem' }}>
              {/* Recipe Info */}
              <div style={{
                padding: '1rem',
                backgroundColor: 'rgba(168, 216, 255, 0.05)',
                borderRadius: '0.5rem',
                marginBottom: '1.5rem'
              }}>
                <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Recipe</p>
                <p style={{ color: '#f0f0f5', fontWeight: '600' }}>{recipe?.name}</p>
                <p style={{ color: '#b3b3c4', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                  Version: {selectedVersion?.version_number}
                </p>
              </div>

              {/* Compute Target */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', color: '#f0f0f5', fontWeight: '600', marginBottom: '0.75rem' }}>
                  Compute Target
                </label>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button
                    onClick={() => setComputeTarget('runpod')}
                    style={{
                      flex: 1,
                      padding: '1rem',
                      backgroundColor: computeTarget === 'runpod' ? 'rgba(168, 216, 255, 0.15)' : 'transparent',
                      border: computeTarget === 'runpod' 
                        ? '2px solid #a8d8ff' 
                        : '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}
                  >
                    <Cloud className="h-6 w-6" style={{ color: computeTarget === 'runpod' ? '#a8d8ff' : '#b3b3c4' }} />
                    <span style={{ color: computeTarget === 'runpod' ? '#a8d8ff' : '#b3b3c4', fontWeight: '600' }}>
                      RunPod GPU
                    </span>
                    <span style={{ color: '#9ca3af', fontSize: '0.75rem' }}>
                      ~$0.20/hr
                    </span>
                  </button>
                  <button
                    onClick={() => setComputeTarget('local')}
                    style={{
                      flex: 1,
                      padding: '1rem',
                      backgroundColor: computeTarget === 'local' ? 'rgba(168, 216, 255, 0.15)' : 'transparent',
                      border: computeTarget === 'local' 
                        ? '2px solid #a8d8ff' 
                        : '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}
                  >
                    <Monitor className="h-6 w-6" style={{ color: computeTarget === 'local' ? '#a8d8ff' : '#b3b3c4' }} />
                    <span style={{ color: computeTarget === 'local' ? '#a8d8ff' : '#b3b3c4', fontWeight: '600' }}>
                      Local
                    </span>
                    <span style={{ color: '#9ca3af', fontSize: '0.75rem' }}>
                      Free
                    </span>
                  </button>
                </div>
              </div>

              {/* Parameters */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', color: '#f0f0f5', fontWeight: '600', marginBottom: '0.75rem' }}>
                  Parameters
                </label>
                {recipe?.model_family === 'forecasting' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                        Forecast Horizon (days)
                      </label>
                      <input
                        type="number"
                        value={runParams.horizon || 28}
                        onChange={(e) => setRunParams({ ...runParams, horizon: parseInt(e.target.value) })}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          backgroundColor: '#0a0a0f',
                          border: '1px solid rgba(168, 216, 255, 0.2)',
                          borderRadius: '0.375rem',
                          color: '#f0f0f5',
                          fontSize: '0.95rem'
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                        Number of Estimators
                      </label>
                      <input
                        type="number"
                        value={runParams.n_estimators || 100}
                        onChange={(e) => setRunParams({ ...runParams, n_estimators: parseInt(e.target.value) })}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          backgroundColor: '#0a0a0f',
                          border: '1px solid rgba(168, 216, 255, 0.2)',
                          borderRadius: '0.375rem',
                          color: '#f0f0f5',
                          fontSize: '0.95rem'
                        }}
                      />
                    </div>
                  </div>
                )}
                {recipe?.model_family !== 'forecasting' && (
                  <textarea
                    value={JSON.stringify(runParams, null, 2)}
                    onChange={(e) => {
                      try {
                        setRunParams(JSON.parse(e.target.value))
                      } catch {}
                    }}
                    style={{
                      width: '100%',
                      minHeight: '100px',
                      padding: '0.75rem',
                      backgroundColor: '#0a0a0f',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.375rem',
                      color: '#f0f0f5',
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      resize: 'vertical'
                    }}
                  />
                )}
              </div>

              {/* Error Message */}
              {runError && (
                <div style={{
                  padding: '1rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '0.5rem',
                  marginBottom: '1.5rem'
                }}>
                  <p style={{ color: '#ef4444', fontSize: '0.875rem', margin: 0 }}>
                    {runError}
                  </p>
                </div>
              )}

              {/* RunPod Dashboard */}
              {computeTarget === 'runpod' && (
                <div style={{ marginBottom: '1.5rem' }}>
                  {loadingGpus ? (
                    <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>Loading RunPod data...</p>
                  ) : (
                    <>
                      {/* Account Balance & Jobs Link */}
                      {spending && (
                        <div style={{
                          padding: '1rem',
                          backgroundColor: 'rgba(16, 185, 129, 0.1)',
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                          borderRadius: '0.5rem',
                          marginBottom: '1rem'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <p style={{ color: '#10b981', fontSize: '0.75rem', margin: 0, marginBottom: '0.25rem' }}>
                                💰 RunPod Balance
                              </p>
                              <p style={{ color: '#f0f0f5', fontSize: '1.25rem', fontWeight: '700', margin: 0 }}>
                                ${spending.client_balance?.toFixed(2) || '0.00'}
                              </p>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <p style={{ color: '#b3b3c4', fontSize: '0.75rem', margin: 0 }}>
                                Current: ${spending.spend_per_hour?.toFixed(2) || '0'}/hr
                              </p>
                              <p style={{ color: '#b3b3c4', fontSize: '0.75rem', margin: 0 }}>
                                Limit: ${spending.spend_limit || 'None'}
                              </p>
                            </div>
                          </div>
                          <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(16, 185, 129, 0.2)' }}>
                            <a
                              href="/model-development/runpod-jobs"
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{
                                color: '#10b981',
                                fontSize: '0.875rem',
                                textDecoration: 'none',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                              }}
                            >
                              📊 View Previous Jobs & Results →
                            </a>
                          </div>
                        </div>
                      )}

                      {/* Your Running Pods */}
                      <label style={{ display: 'block', color: '#f0f0f5', fontWeight: '600', marginBottom: '0.75rem' }}>
                        Your Running Pods
                      </label>
                      {runningPods.filter(p => p.status === 'RUNNING').length > 0 ? (
                        <div style={{ marginBottom: '1rem' }}>
                          {runningPods.filter(p => p.status === 'RUNNING').map((pod) => (
                            <div
                              key={pod.id}
                              onClick={() => setSelectedPod(pod.id)}
                              style={{
                                padding: '0.75rem 1rem',
                                backgroundColor: selectedPod === pod.id ? 'rgba(16, 185, 129, 0.2)' : 'rgba(168, 216, 255, 0.05)',
                                border: selectedPod === pod.id ? '2px solid #10b981' : '1px solid rgba(168, 216, 255, 0.2)',
                                borderRadius: '0.5rem',
                                marginBottom: '0.5rem',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                  <p style={{ color: '#f0f0f5', fontWeight: '600', margin: 0, fontSize: '0.9rem' }}>
                                    {pod.name}
                                  </p>
                                  <p style={{ color: '#b3b3c4', fontSize: '0.75rem', margin: 0, marginTop: '0.25rem' }}>
                                    {pod.gpu_type} • {Math.round((pod.uptime_seconds || 0) / 3600)}h uptime
                                  </p>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                  <span style={{
                                    padding: '0.25rem 0.5rem',
                                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                                    color: '#10b981',
                                    borderRadius: '0.25rem',
                                    fontSize: '0.7rem',
                                    fontWeight: '600'
                                  }}>
                                    RUNNING
                                  </span>
                                  <p style={{ color: '#fbbf24', fontSize: '0.75rem', margin: 0, marginTop: '0.25rem' }}>
                                    ${pod.cost_per_hour?.toFixed(2)}/hr
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                          <p style={{ color: '#10b981', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                            ✓ Jobs will be sent to selected pod
                          </p>
                        </div>
                      ) : (
                        <div style={{
                          padding: '1rem',
                          backgroundColor: 'rgba(251, 191, 36, 0.1)',
                          border: '1px solid rgba(251, 191, 36, 0.3)',
                          borderRadius: '0.5rem',
                          marginBottom: '1rem'
                        }}>
                          <p style={{ color: '#fbbf24', fontSize: '0.875rem', margin: 0 }}>
                            ⚠️ No running pods. Add RUNPOD_POD_ID to .env or start a pod on RunPod.
                          </p>
                        </div>
                      )}

                      {/* Stopped Pods */}
                      {runningPods.filter(p => p.status !== 'RUNNING').length > 0 && (
                        <div style={{ marginBottom: '1rem' }}>
                          <p style={{ color: '#b3b3c4', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
                            Stopped pods ({runningPods.filter(p => p.status !== 'RUNNING').length}):
                          </p>
                          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                            {runningPods.filter(p => p.status !== 'RUNNING').slice(0, 5).map((pod) => (
                              <span key={pod.id} style={{
                                padding: '0.25rem 0.5rem',
                                backgroundColor: 'rgba(168, 216, 255, 0.05)',
                                border: '1px solid rgba(168, 216, 255, 0.1)',
                                borderRadius: '0.25rem',
                                fontSize: '0.7rem',
                                color: '#6b7280'
                              }}>
                                {pod.name.slice(0, 20)}...
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Available GPUs (collapsed by default) */}
                      <details style={{ marginTop: '1rem' }}>
                        <summary style={{ 
                          color: '#b3b3c4', 
                          fontSize: '0.75rem', 
                          cursor: 'pointer',
                          marginBottom: '0.5rem'
                        }}>
                          📊 Available GPU Types ({availableGpus.length})
                        </summary>
                        <div style={{ 
                          maxHeight: '200px', 
                          overflowY: 'auto', 
                          marginTop: '0.5rem',
                          padding: '0.5rem',
                          backgroundColor: 'rgba(0,0,0,0.2)',
                          borderRadius: '0.375rem'
                        }}>
                          <table style={{ width: '100%', fontSize: '0.7rem', color: '#b3b3c4' }}>
                            <thead>
                              <tr style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.1)' }}>
                                <th style={{ textAlign: 'left', padding: '0.25rem' }}>GPU</th>
                                <th style={{ textAlign: 'right', padding: '0.25rem' }}>VRAM</th>
                                <th style={{ textAlign: 'right', padding: '0.25rem' }}>$/hr</th>
                              </tr>
                            </thead>
                            <tbody>
                              {availableGpus.slice(0, 15).map((gpu) => (
                                <tr key={gpu.id} style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.05)' }}>
                                  <td style={{ padding: '0.25rem' }}>{gpu.name}</td>
                                  <td style={{ textAlign: 'right', padding: '0.25rem' }}>{gpu.memory_gb}GB</td>
                                  <td style={{ textAlign: 'right', padding: '0.25rem', color: '#fbbf24' }}>
                                    ${gpu.hourly_rate_usd?.toFixed(2) || '?'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '1.5rem',
              borderTop: '1px solid rgba(168, 216, 255, 0.2)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '1rem'
            }}>
              <button
                onClick={() => setShowRunModal(false)}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: 'transparent',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.5rem',
                  color: '#b3b3c4',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={createRun}
                disabled={creatingRun}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: 'linear-gradient(135deg, #a8d8ff, #c4b5fd)',
                  border: 'none',
                  borderRadius: '0.5rem',
                  color: '#0a0a0f',
                  fontWeight: '700',
                  cursor: creatingRun ? 'not-allowed' : 'pointer',
                  opacity: creatingRun ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <PlayCircle className="h-5 w-5" />
                {creatingRun ? 'Creating Run...' : 'Create Run'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Live Run Status Tracker */}
      {activeRunId && (
        <LiveRunStatus
          runId={activeRunId}
          onComplete={() => {
            // Keep showing for 10 seconds after completion, then auto-hide
            setTimeout(() => {
              setActiveRunId(null)
            }, 10000)
          }}
          onClose={() => setActiveRunId(null)}
        />
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}


