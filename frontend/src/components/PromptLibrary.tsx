import { useState, useEffect } from 'react'
import {
  Brain,
  Plus,
  Edit,
  Copy,
  Trash2,
  Star,
  AlertCircle,
  CheckCircle2,
  X
} from 'lucide-react'
import {
  fetchPromptRecipes,
  deletePromptRecipe,
  clonePromptRecipe,
  updatePromptRecipe
} from '../api/client'
import RecipeEditor from './RecipeEditor'

interface Recipe {
  id: number
  name: string
  action_type: string
  default_provider?: string
  default_model?: string
  system_message: string
  user_template: string
  recipe_metadata?: any
  created_at: string
  updated_at: string
}

export default function PromptLibrary() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<'list' | 'edit'>('list')
  const [editingRecipe, setEditingRecipe] = useState<Recipe | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const actionTypeLabels: Record<string, string> = {
    profiling: 'Data Profiling',
    quality: 'Data Quality Checks',
    anomaly: 'Outlier & Anomaly Detection',
    relationships: 'Relationship Analysis',
    trends: 'Trend & Time-Series Analysis',
    patterns: 'Pattern Discovery'
  }

  useEffect(() => {
    loadRecipes()
  }, [])

  const loadRecipes = async () => {
    setLoading(true)
    try {
      const data = await fetchPromptRecipes()
      setRecipes(data)
    } catch (error) {
      console.error('Failed to load recipes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (recipeId: number, isSystem: boolean) => {
    try {
      await deletePromptRecipe(recipeId, isSystem)
      setRecipes(recipes.filter(r => r.id !== recipeId))
      setDeleteConfirm(null)
    } catch (error: any) {
      console.error('Failed to delete recipe:', error)
      if (error.response?.status === 400) {
        alert('Cannot delete seed recipe. Use force delete if necessary.')
      } else {
        alert('Failed to delete recipe: ' + error.message)
      }
    }
  }

  const handleClone = async (recipeId: number) => {
    try {
      const cloned = await clonePromptRecipe(recipeId)
      setRecipes([...recipes, cloned])
    } catch (error) {
      console.error('Failed to clone recipe:', error)
      alert('Failed to clone recipe')
    }
  }

  const handleSetDefault = async (recipe: Recipe) => {
    try {
      const updatedMetadata = {
        ...(recipe.recipe_metadata || {}),
        is_default: true
      }
      
      await updatePromptRecipe(recipe.id, {
        recipe_metadata: updatedMetadata
      })
      
      // Reload all recipes to reflect changes
      await loadRecipes()
    } catch (error) {
      console.error('Failed to set default:', error)
      alert('Failed to set as default')
    }
  }

  const handleSaveRecipe = async () => {
    await loadRecipes()
    setView('list')
    setEditingRecipe(null)
  }

  // Group recipes by action_type
  const groupedRecipes = recipes.reduce((acc, recipe) => {
    if (!acc[recipe.action_type]) {
      acc[recipe.action_type] = []
    }
    acc[recipe.action_type].push(recipe)
    return acc
  }, {} as Record<string, Recipe[]>)

  if (view === 'edit') {
    return (
      <RecipeEditor
        recipe={editingRecipe || undefined}
        onSave={handleSaveRecipe}
        onCancel={() => {
          setView('list')
          setEditingRecipe(null)
        }}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>
            Prompt Library
          </h2>
          <p className="text-sm mt-1" style={{ color: '#b0b8c0' }}>
            Manage and customize analysis prompt recipes
          </p>
        </div>
        <button
          onClick={() => {
            setEditingRecipe(null)
            setView('edit')
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors"
          style={{
            backgroundColor: '#a8d8ff',
            color: '#0a0a0f'
          }}
        >
          <Plus className="h-4 w-4" />
          New Recipe
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12" style={{ color: '#b0b8c0' }}>
          Loading recipes...
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(groupedRecipes).map(([actionType, actionRecipes]) => (
            <div key={actionType}>
              <h3 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>
                {actionTypeLabels[actionType] || actionType}
              </h3>
              
              <div className="grid grid-cols-1 gap-4">
                {actionRecipes.map(recipe => {
                  const isDefault = recipe.recipe_metadata?.is_default === true
                  const isSystem = recipe.recipe_metadata?.source === 'seed'
                  
                  return (
                    <div
                      key={recipe.id}
                      className="p-4 rounded-lg"
                      style={{
                        backgroundColor: '#1a1a24',
                        border: `1px solid ${isDefault ? '#a8d8ff' : 'rgba(168, 216, 255, 0.15)'}`
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-medium" style={{ color: '#f0f0f5' }}>
                              {recipe.name}
                            </h4>
                            {isDefault && (
                              <span className="flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium" style={{ backgroundColor: 'rgba(168, 216, 255, 0.2)', color: '#a8d8ff' }}>
                                <Star className="h-3 w-3 fill-current" />
                                Default
                              </span>
                            )}
                            {isSystem && (
                              <span className="px-2 py-0.5 rounded text-xs font-medium" style={{ backgroundColor: 'rgba(100, 150, 255, 0.2)', color: '#7ea8ff' }}>
                                System
                              </span>
                            )}
                          </div>
                          
                          {recipe.default_provider && (
                            <p className="text-sm" style={{ color: '#b0b8c0' }}>
                              Default: {recipe.default_provider} / {recipe.default_model}
                            </p>
                          )}
                          
                          <p className="text-xs mt-2" style={{ color: '#7a8a99' }}>
                            Updated: {new Date(recipe.updated_at).toLocaleDateString()}
                          </p>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          {!isDefault && (
                            <button
                              onClick={() => handleSetDefault(recipe)}
                              className="p-2 rounded transition-colors"
                              style={{
                                backgroundColor: 'rgba(168, 216, 255, 0.1)',
                                color: '#a8d8ff'
                              }}
                              title="Set as default"
                            >
                              <Star className="h-4 w-4" />
                            </button>
                          )}
                          
                          <button
                            onClick={() => {
                              setEditingRecipe(recipe)
                              setView('edit')
                            }}
                            className="p-2 rounded transition-colors"
                            style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.1)',
                              color: '#a8d8ff'
                            }}
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          
                          <button
                            onClick={() => handleClone(recipe.id)}
                            className="p-2 rounded transition-colors"
                            style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.1)',
                              color: '#a8d8ff'
                            }}
                            title="Clone"
                          >
                            <Copy className="h-4 w-4" />
                          </button>
                          
                          <button
                            onClick={() => setDeleteConfirm(recipe.id)}
                            className="p-2 rounded transition-colors"
                            style={{
                              backgroundColor: 'rgba(255, 100, 100, 0.1)',
                              color: '#ff6b6b'
                            }}
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setDeleteConfirm(null)}
        >
          <div 
            className="p-6 rounded-xl max-w-md w-full mx-4"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.3)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="h-6 w-6 text-amber-400" />
              <h3 className="text-lg font-semibold" style={{ color: '#f0f0f5' }}>
                Delete Recipe
              </h3>
            </div>
            
            <p className="mb-6" style={{ color: '#b0b8c0' }}>
              Are you sure you want to delete this recipe? This action cannot be undone.
            </p>
            
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 rounded-lg font-medium transition-colors"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.1)',
                  color: '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.3)'
                }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const recipe = recipes.find(r => r.id === deleteConfirm)
                  handleDelete(deleteConfirm, recipe?.recipe_metadata?.source === 'seed')
                }}
                className="px-4 py-2 rounded-lg font-medium transition-colors"
                style={{
                  backgroundColor: '#dc2626',
                  color: 'white'
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

