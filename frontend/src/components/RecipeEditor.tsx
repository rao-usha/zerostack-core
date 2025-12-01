import { useState, useEffect } from 'react'
import { Save, X, AlertCircle } from 'lucide-react'
import { createPromptRecipe, updatePromptRecipe } from '../api/client'

interface Recipe {
  id: number
  name: string
  action_type: string
  default_provider?: string
  default_model?: string
  system_message: string
  user_template: string
  recipe_metadata?: any
}

interface RecipeEditorProps {
  recipe?: Recipe
  onSave: () => void
  onCancel: () => void
}

export default function RecipeEditor({ recipe, onSave, onCancel }: RecipeEditorProps) {
  const [name, setName] = useState('')
  const [actionType, setActionType] = useState('profiling')
  const [defaultProvider, setDefaultProvider] = useState('')
  const [defaultModel, setDefaultModel] = useState('')
  const [systemMessage, setSystemMessage] = useState('')
  const [userTemplate, setUserTemplate] = useState('')
  const [isDefault, setIsDefault] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const actionTypes = [
    { value: 'profiling', label: 'Data Profiling' },
    { value: 'quality', label: 'Data Quality Checks' },
    { value: 'anomaly', label: 'Outlier & Anomaly Detection' },
    { value: 'relationships', label: 'Relationship Analysis' },
    { value: 'trends', label: 'Trend & Time-Series Analysis' },
    { value: 'patterns', label: 'Pattern Discovery' }
  ]

  const providers = [
    { value: '', label: '(None)' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'google', label: 'Google' },
    { value: 'xai', label: 'xAI' }
  ]

  useEffect(() => {
    if (recipe) {
      setName(recipe.name)
      setActionType(recipe.action_type)
      setDefaultProvider(recipe.default_provider || '')
      setDefaultModel(recipe.default_model || '')
      setSystemMessage(recipe.system_message)
      setUserTemplate(recipe.user_template)
      setIsDefault(recipe.recipe_metadata?.is_default === true)
    }
  }, [recipe])

  const handleSave = async () => {
    setError('')
    
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    
    if (!systemMessage.trim()) {
      setError('System message is required')
      return
    }
    
    if (!userTemplate.trim()) {
      setError('User template is required')
      return
    }

    setSaving(true)
    try {
      const metadata = {
        source: 'user',
        is_default: isDefault
      }

      if (recipe) {
        // Update existing
        await updatePromptRecipe(recipe.id, {
          name: name.trim(),
          default_provider: defaultProvider || undefined,
          default_model: defaultModel || undefined,
          system_message: systemMessage,
          user_template: userTemplate,
          recipe_metadata: metadata
        })
      } else {
        // Create new
        await createPromptRecipe({
          name: name.trim(),
          action_type: actionType,
          default_provider: defaultProvider || undefined,
          default_model: defaultModel || undefined,
          system_message: systemMessage,
          user_template: userTemplate,
          recipe_metadata: metadata
        })
      }

      onSave()
    } catch (error: any) {
      console.error('Failed to save recipe:', error)
      setError(error.response?.data?.detail || error.message || 'Failed to save recipe')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>
            {recipe ? 'Edit Recipe' : 'New Recipe'}
          </h2>
          <p className="text-sm mt-1" style={{ color: '#b0b8c0' }}>
            {recipe ? 'Update prompt recipe settings' : 'Create a new prompt recipe'}
          </p>
        </div>
        <button
          onClick={onCancel}
          className="p-2 rounded transition-colors"
          style={{
            backgroundColor: 'rgba(168, 216, 255, 0.1)',
            color: '#a8d8ff'
          }}
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg flex items-start gap-3" style={{ backgroundColor: 'rgba(255, 100, 100, 0.1)', border: '1px solid rgba(255, 100, 100, 0.3)' }}>
          <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      <div className="space-y-6">
        {/* Basic Settings */}
        <div className="p-6 rounded-xl space-y-4" style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}>
          <h3 className="font-semibold mb-4" style={{ color: '#a8d8ff' }}>Basic Settings</h3>
          
          {/* Name */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
              Recipe Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full p-3 rounded-lg"
              style={{
                backgroundColor: '#0f0f17',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
              placeholder="e.g., Data Profiling - Healthcare v1"
            />
          </div>

          {/* Action Type */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
              Analysis Action Type *
            </label>
            <select
              value={actionType}
              onChange={(e) => setActionType(e.target.value)}
              disabled={!!recipe}
              className="w-full p-3 rounded-lg"
              style={{
                backgroundColor: '#0f0f17',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            >
              {actionTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            {recipe && (
              <p className="text-xs mt-1" style={{ color: '#7a8a99' }}>
                Action type cannot be changed after creation
              </p>
            )}
          </div>

          {/* Default Provider & Model */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                Default Provider (Optional)
              </label>
              <select
                value={defaultProvider}
                onChange={(e) => setDefaultProvider(e.target.value)}
                className="w-full p-3 rounded-lg"
                style={{
                  backgroundColor: '#0f0f17',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
              >
                {providers.map(provider => (
                  <option key={provider.value} value={provider.value}>
                    {provider.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                Default Model (Optional)
              </label>
              <input
                type="text"
                value={defaultModel}
                onChange={(e) => setDefaultModel(e.target.value)}
                className="w-full p-3 rounded-lg"
                style={{
                  backgroundColor: '#0f0f17',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
                placeholder="e.g., gpt-4o"
              />
            </div>
          </div>

          {/* Make Default Checkbox */}
          <div className="pt-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
                className="rounded"
              />
              <span className="font-medium" style={{ color: '#a8d8ff' }}>
                Make default recipe for this action type
              </span>
            </label>
            <p className="text-xs mt-1 ml-7" style={{ color: '#7a8a99' }}>
              This recipe will be automatically selected when creating new analysis jobs
            </p>
          </div>
        </div>

        {/* Prompt Content */}
        <div className="p-6 rounded-xl space-y-4" style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}>
          <h3 className="font-semibold mb-4" style={{ color: '#a8d8ff' }}>Prompt Content</h3>
          
          {/* System Message */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
              System Message *
            </label>
            <textarea
              value={systemMessage}
              onChange={(e) => setSystemMessage(e.target.value)}
              rows={10}
              className="w-full p-3 rounded-lg font-mono text-sm"
              style={{
                backgroundColor: '#0f0f17',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
              placeholder="Define the AI's role, constraints, and output requirements..."
            />
            <p className="text-xs mt-1" style={{ color: '#7a8a99' }}>
              Sets the AI's role and behavior for this analysis type
            </p>
          </div>

          {/* User Template */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
              User Message Template *
            </label>
            <textarea
              value={userTemplate}
              onChange={(e) => setUserTemplate(e.target.value)}
              rows={15}
              className="w-full p-3 rounded-lg font-mono text-sm"
              style={{
                backgroundColor: '#0f0f17',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
              placeholder="Instructions and context for the analysis. Use {{schema_summary}} and {{sample_rows}} as placeholders..."
            />
            <p className="text-xs mt-1" style={{ color: '#7a8a99' }}>
              Available placeholders: <code className="px-1 py-0.5 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>
                {'{'}{'{'} schema_summary {'}'}{'}'}
              </code> and <code className="px-1 py-0.5 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>
                {'{'}{'{'} sample_rows {'}'}{'}'}
              </code>
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={saving}
            className="px-6 py-3 rounded-lg font-medium transition-colors"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.1)',
              color: '#a8d8ff',
              border: '1px solid rgba(168, 216, 255, 0.3)'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !name.trim() || !systemMessage.trim() || !userTemplate.trim()}
            className="flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundColor: '#a8d8ff',
              color: '#0a0a0f'
            }}
          >
            {saving ? (
              <>Saving...</>
            ) : (
              <>
                <Save className="h-4 w-4" />
                {recipe ? 'Update Recipe' : 'Create Recipe'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

