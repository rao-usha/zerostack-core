import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { BookOpen, ArrowLeft, Save, Copy, CheckCircle, Edit, FileText, GitBranch, Beaker, Github, ExternalLink, Star } from 'lucide-react'

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

export default function RecipeDetail() {
  const { recipeId } = useParams<{ recipeId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [versions, setVersions] = useState<RecipeVersion[]>([])
  const [selectedVersion, setSelectedVersion] = useState<RecipeVersion | null>(null)
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [manifestText, setManifestText] = useState('')
  const [saving, setSaving] = useState(false)

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
      alert('Error saving manifest. Please check JSON syntax.')
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
                borderRadius: '0.75rem'
              }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', color: '#a8d8ff' }}>
                  Manifest Summary
                </h3>
                <p style={{ color: '#b3b3c4', fontSize: '0.95rem', lineHeight: '1.6' }}>
                  {selectedVersion.manifest_json.metadata.description || 'No description available'}
                </p>
              </div>
            )}
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
    </div>
  )
}


