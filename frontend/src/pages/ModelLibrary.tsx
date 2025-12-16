import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, Search, Filter, Plus, BookOpen, Box, PlayCircle, BarChart3, CheckCircle2 } from 'lucide-react'

interface Recipe {
  id: string
  name: string
  model_family: string
  level: string
  status: string
  tags: string[]
  created_at: string
  updated_at: string
}

interface Model {
  id: string
  name: string
  model_family: string
  status: string
  owner: string
  created_at: string
}

interface Run {
  id: string
  run_type: string
  status: string
  started_at: string
  recipe_id: string
  model_id?: string
}

interface EvaluationPack {
  id: string
  name: string
  model_family: string
  status: string
  tags: string[]
  created_at: string
  updated_at: string
}

type TabType = 'recipes' | 'models' | 'runs' | 'evaluation-packs' | 'monitoring'

export default function ModelLibrary() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('recipes')
  const [searchTerm, setSearchTerm] = useState('')
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [evaluationPacks, setEvaluationPacks] = useState<EvaluationPack[]>([])
  const [loading, setLoading] = useState(false)
  
  // Filters
  const [familyFilter, setFamilyFilter] = useState<string>('all')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    loadData()
  }, [activeTab, familyFilter, levelFilter, statusFilter])

  const loadData = async () => {
    setLoading(true)
    try {
      const apiPrefix = '/api/v1'
      
      if (activeTab === 'recipes') {
        const params = new URLSearchParams()
        if (familyFilter !== 'all') params.append('model_family', familyFilter)
        if (levelFilter !== 'all') params.append('level', levelFilter)
        if (statusFilter !== 'all') params.append('status', statusFilter)
        
        const response = await fetch(`${apiPrefix}/ml-development/recipes?${params}`)
        const data = await response.json()
        setRecipes(data.recipes || [])
      } else if (activeTab === 'models') {
        const params = new URLSearchParams()
        if (familyFilter !== 'all') params.append('model_family', familyFilter)
        if (statusFilter !== 'all') params.append('status', statusFilter)
        
        const response = await fetch(`${apiPrefix}/ml-development/models?${params}`)
        const data = await response.json()
        setModels(data.models || [])
      } else if (activeTab === 'runs') {
        const params = new URLSearchParams()
        if (statusFilter !== 'all') params.append('status', statusFilter)
        
        const response = await fetch(`${apiPrefix}/ml-development/runs?${params}`)
        const data = await response.json()
        setRuns(data.runs || [])
      } else if (activeTab === 'evaluation-packs') {
        const params = new URLSearchParams()
        if (familyFilter !== 'all') params.append('model_family', familyFilter)
        if (statusFilter !== 'all') params.append('status', statusFilter)
        
        const response = await fetch(`${apiPrefix}/evaluation-packs?${params}`)
        const data = await response.json()
        setEvaluationPacks(data.packs || [])
      }
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredRecipes = recipes.filter(r => 
    r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.model_family.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredModels = models.filter(m =>
    m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.model_family.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredRuns = runs.filter(r =>
    r.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.run_type.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredEvaluationPacks = evaluationPacks.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.model_family.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getFamilyLabel = (family: string) => {
    const labels: Record<string, string> = {
      pricing: 'Pricing',
      next_best_action: 'Next Best Action',
      location_scoring: 'Location Scoring',
      forecasting: 'Forecasting'
    }
    return labels[family] || family
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: '#fbbf24',
      approved: '#10b981',
      archived: '#6b7280',
      staging: '#3b82f6',
      production: '#10b981',
      retired: '#6b7280',
      queued: '#9ca3af',
      running: '#3b82f6',
      succeeded: '#10b981',
      failed: '#ef4444'
    }
    return colors[status] || '#9ca3af'
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)', padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <Activity className="h-8 w-8" style={{ color: '#a8d8ff' }} />
              <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f0f0f5' }}>
                Model Development
              </h1>
            </div>
            <p style={{ color: '#b3b3c4', fontSize: '0.95rem' }}>
              ML model recipes, registered models, training runs, and monitoring
            </p>
          </div>
          
          <button
            onClick={() => navigate('/model-development/chat')}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'linear-gradient(135deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              borderRadius: '0.5rem',
              color: '#a8d8ff',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Plus className="h-5 w-5" />
            Build with Chat
          </button>
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
            { id: 'recipes', label: 'Recipes', icon: BookOpen },
            { id: 'models', label: 'Models', icon: Box },
            { id: 'runs', label: 'Runs', icon: PlayCircle },
            { id: 'evaluation-packs', label: 'Evaluation Packs', icon: CheckCircle2 },
            { id: 'monitoring', label: 'Monitoring', icon: BarChart3 }
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

        {/* Search and Filters */}
        <div style={{ 
          display: 'flex', 
          gap: '1rem', 
          marginBottom: '2rem',
          flexWrap: 'wrap'
        }}>
          <div style={{ flex: '1', minWidth: '300px', position: 'relative' }}>
            <Search 
              className="h-5 w-5" 
              style={{ 
                position: 'absolute', 
                left: '1rem', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: '#b3b3c4'
              }} 
            />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 1rem 0.75rem 3rem',
                backgroundColor: '#1a1a24',
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontSize: '0.95rem'
              }}
            />
          </div>

          <select
            value={familyFilter}
            onChange={(e) => setFamilyFilter(e.target.value)}
            style={{
              padding: '0.75rem 1rem',
              backgroundColor: '#1a1a24',
              border: '1px solid rgba(168, 216, 255, 0.2)',
              borderRadius: '0.5rem',
              color: '#f0f0f5',
              fontSize: '0.95rem',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Families</option>
            <option value="pricing">Pricing</option>
            <option value="next_best_action">Next Best Action</option>
            <option value="location_scoring">Location Scoring</option>
            <option value="forecasting">Forecasting</option>
          </select>

          {activeTab === 'recipes' && (
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              style={{
                padding: '0.75rem 1rem',
                backgroundColor: '#1a1a24',
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontSize: '0.95rem',
                cursor: 'pointer'
              }}
            >
              <option value="all">All Levels</option>
              <option value="baseline">Baseline</option>
              <option value="industry">Industry</option>
              <option value="client">Client</option>
            </select>
          )}

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '0.75rem 1rem',
              backgroundColor: '#1a1a24',
              border: '1px solid rgba(168, 216, 255, 0.2)',
              borderRadius: '0.5rem',
              color: '#f0f0f5',
              fontSize: '0.95rem',
              cursor: 'pointer'
            }}
          >
            <option value="all">All Statuses</option>
            {activeTab === 'recipes' ? (
              <>
                <option value="draft">Draft</option>
                <option value="approved">Approved</option>
                <option value="archived">Archived</option>
              </>
            ) : activeTab === 'models' ? (
              <>
                <option value="draft">Draft</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
                <option value="retired">Retired</option>
              </>
            ) : (
              <>
                <option value="queued">Queued</option>
                <option value="running">Running</option>
                <option value="succeeded">Succeeded</option>
                <option value="failed">Failed</option>
              </>
            )}
          </select>
        </div>

        {/* Content */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
            Loading...
          </div>
        ) : (
          <>
            {/* Recipes Tab */}
            {activeTab === 'recipes' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                {filteredRecipes.map(recipe => (
                  <div
                    key={recipe.id}
                    onClick={() => navigate(`/model-development/recipes/${recipe.id}`)}
                    style={{
                      padding: '1.5rem',
                      backgroundColor: '#1a1a24',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.5)'
                      e.currentTarget.style.transform = 'translateY(-2px)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.2)'
                      e.currentTarget.style.transform = 'translateY(0)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5' }}>
                        {recipe.name}
                      </h3>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: `${getStatusColor(recipe.status)}20`,
                          color: getStatusColor(recipe.status),
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}
                      >
                        {recipe.status}
                      </span>
                    </div>
                    
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: 'rgba(168, 216, 255, 0.15)',
                          color: '#a8d8ff',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem',
                          marginRight: '0.5rem'
                        }}
                      >
                        {getFamilyLabel(recipe.model_family)}
                      </span>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: 'rgba(196, 181, 253, 0.15)',
                          color: '#c4b5fd',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem'
                        }}
                      >
                        {recipe.level}
                      </span>
                    </div>

                    {recipe.tags && recipe.tags.length > 0 && (
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {recipe.tags.map((tag, idx) => (
                          <span
                            key={idx}
                            style={{
                              padding: '0.125rem 0.5rem',
                              backgroundColor: 'rgba(255, 255, 255, 0.05)',
                              color: '#b3b3c4',
                              borderRadius: '0.25rem',
                              fontSize: '0.75rem'
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                
                {filteredRecipes.length === 0 && (
                  <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
                    No recipes found. Create one to get started!
                  </div>
                )}
              </div>
            )}

            {/* Models Tab */}
            {activeTab === 'models' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                {filteredModels.map(model => (
                  <div
                    key={model.id}
                    onClick={() => navigate(`/model-development/models/${model.id}`)}
                    style={{
                      padding: '1.5rem',
                      backgroundColor: '#1a1a24',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.5)'
                      e.currentTarget.style.transform = 'translateY(-2px)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.2)'
                      e.currentTarget.style.transform = 'translateY(0)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5' }}>
                        {model.name}
                      </h3>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: `${getStatusColor(model.status)}20`,
                          color: getStatusColor(model.status),
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}
                      >
                        {model.status}
                      </span>
                    </div>
                    
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: 'rgba(168, 216, 255, 0.15)',
                          color: '#a8d8ff',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem'
                        }}
                      >
                        {getFamilyLabel(model.model_family)}
                      </span>
                    </div>

                    {model.owner && (
                      <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>
                        Owner: {model.owner}
                      </p>
                    )}
                  </div>
                ))}
                
                {filteredModels.length === 0 && (
                  <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
                    No models found. Register a model from an approved recipe!
                  </div>
                )}
              </div>
            )}

            {/* Runs Tab */}
            {activeTab === 'runs' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                {filteredRuns.map(run => (
                  <div
                    key={run.id}
                    onClick={() => navigate(`/model-development/runs/${run.id}`)}
                    style={{
                      padding: '1.5rem',
                      backgroundColor: '#1a1a24',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.5)'
                      e.currentTarget.style.transform = 'translateY(-2px)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.2)'
                      e.currentTarget.style.transform = 'translateY(0)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5' }}>
                        {run.id}
                      </h3>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: `${getStatusColor(run.status)}20`,
                          color: getStatusColor(run.status),
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}
                      >
                        {run.status}
                      </span>
                    </div>
                    
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: 'rgba(168, 216, 255, 0.15)',
                          color: '#a8d8ff',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem'
                        }}
                      >
                        {run.run_type}
                      </span>
                    </div>

                    <p style={{ color: '#b3b3c4', fontSize: '0.875rem' }}>
                      Started: {run.started_at ? new Date(run.started_at).toLocaleString() : 'Not started'}
                    </p>
                  </div>
                ))}
                
                {filteredRuns.length === 0 && (
                  <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
                    No runs found. Create a run from a recipe or model!
                  </div>
                )}
              </div>
            )}

            {/* Evaluation Packs Tab */}
            {activeTab === 'evaluation-packs' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                {filteredEvaluationPacks.map(pack => (
                  <div
                    key={pack.id}
                    onClick={() => navigate(`/model-development/evaluation-packs/${pack.id}`)}
                    style={{
                      padding: '1.5rem',
                      backgroundColor: '#1a1a24',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      borderRadius: '0.75rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.5)'
                      e.currentTarget.style.transform = 'translateY(-2px)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.2)'
                      e.currentTarget.style.transform = 'translateY(0)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5' }}>
                        {pack.name}
                      </h3>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: `${getStatusColor(pack.status)}20`,
                          color: getStatusColor(pack.status),
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}
                      >
                        {pack.status}
                      </span>
                    </div>
                    
                    <div style={{ marginBottom: '0.75rem' }}>
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: 'rgba(168, 216, 255, 0.15)',
                          color: '#a8d8ff',
                          borderRadius: '0.375rem',
                          fontSize: '0.875rem'
                        }}
                      >
                        {getFamilyLabel(pack.model_family)}
                      </span>
                    </div>

                    {pack.tags && pack.tags.length > 0 && (
                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
                        {pack.tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            style={{
                              padding: '0.25rem 0.5rem',
                              backgroundColor: 'rgba(139, 92, 246, 0.1)',
                              border: '1px solid rgba(139, 92, 246, 0.3)',
                              borderRadius: '0.25rem',
                              fontSize: '0.75rem',
                              color: '#b3b3c4'
                            }}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                
                {filteredEvaluationPacks.length === 0 && (
                  <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
                    No evaluation packs found. Create a standard evaluation pack!
                  </div>
                )}
              </div>
            )}

            {/* Monitoring Tab */}
            {activeTab === 'monitoring' && (
              <div style={{ textAlign: 'center', padding: '3rem', color: '#b3b3c4' }}>
                <BarChart3 className="h-16 w-16" style={{ margin: '0 auto 1rem', color: '#a8d8ff' }} />
                <p>Select a model to view its monitoring dashboard</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}


