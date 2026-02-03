import { useState, useEffect } from 'react'
import {
  Settings as SettingsIcon,
  Brain,
  Cpu,
  Database,
  Key,
  ToggleLeft,
  CheckCircle,
  XCircle,
  RefreshCw,
  Eye,
  EyeOff,
  Save,
  Loader2,
  AlertTriangle,
  Download
} from 'lucide-react'
import {
  getSettingCategories,
  getSettingsByCategory,
  updateSetting,
  testSetting,
  seedSettingsFromEnv,
  SettingCategory,
  Setting,
  SettingTestResult
} from '../api/client'

// Category icon mapping
const categoryIcons: Record<string, typeof Brain> = {
  llm: Brain,
  compute: Cpu,
  storage: Database,
  oauth: Key,
  feature: ToggleLeft
}

// Category colors
const categoryColors: Record<string, string> = {
  llm: '#a8d8ff',
  compute: '#c4b5fd',
  storage: '#ffc4e5',
  oauth: '#ffd6a5',
  feature: '#a5ffc4'
}

export default function Settings() {
  const [categories, setCategories] = useState<SettingCategory[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [settings, setSettings] = useState<Setting[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [testing, setTesting] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, SettingTestResult>>({})
  const [editValues, setEditValues] = useState<Record<string, string>>({})
  const [showValues, setShowValues] = useState<Record<string, boolean>>({})
  const [seeding, setSeeding] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Load categories on mount
  useEffect(() => {
    loadCategories()
  }, [])

  // Load settings when category changes
  useEffect(() => {
    if (selectedCategory) {
      loadSettings(selectedCategory)
    }
  }, [selectedCategory])

  const loadCategories = async () => {
    try {
      setLoading(true)
      const data = await getSettingCategories()
      setCategories(data.categories)
      if (data.categories.length > 0 && !selectedCategory) {
        setSelectedCategory(data.categories[0].category)
      }
    } catch (error) {
      console.error('Failed to load categories:', error)
      setMessage({ type: 'error', text: 'Failed to load settings categories' })
    } finally {
      setLoading(false)
    }
  }

  const loadSettings = async (category: string) => {
    try {
      setLoading(true)
      const data = await getSettingsByCategory(category)
      setSettings(data.settings)
      // Initialize edit values with empty strings
      const initialValues: Record<string, string> = {}
      data.settings.forEach(s => {
        initialValues[s.key] = ''
      })
      setEditValues(initialValues)
    } catch (error) {
      console.error('Failed to load settings:', error)
      setMessage({ type: 'error', text: 'Failed to load settings' })
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (key: string) => {
    if (!selectedCategory || !editValues[key]) return

    try {
      setSaving(key)
      await updateSetting(selectedCategory, key, editValues[key])
      setMessage({ type: 'success', text: `${key} saved successfully` })
      // Reload settings to get updated state
      await loadSettings(selectedCategory)
      await loadCategories()
      // Clear edit value
      setEditValues(prev => ({ ...prev, [key]: '' }))
      // Clear any previous test result
      setTestResults(prev => {
        const newResults = { ...prev }
        delete newResults[key]
        return newResults
      })
    } catch (error) {
      console.error('Failed to save setting:', error)
      setMessage({ type: 'error', text: `Failed to save ${key}` })
    } finally {
      setSaving(null)
    }
  }

  const handleTest = async (key: string) => {
    if (!selectedCategory) return

    try {
      setTesting(key)
      const result = await testSetting(selectedCategory, key)
      setTestResults(prev => ({ ...prev, [key]: result }))
    } catch (error) {
      console.error('Failed to test setting:', error)
      setTestResults(prev => ({
        ...prev,
        [key]: { key, valid: false, message: 'Test failed' }
      }))
    } finally {
      setTesting(null)
    }
  }

  const handleSeedFromEnv = async () => {
    try {
      setSeeding(true)
      const result = await seedSettingsFromEnv(false)
      setMessage({
        type: 'success',
        text: `Seeded ${result.seeded_count} settings from environment`
      })
      // Reload everything
      await loadCategories()
      if (selectedCategory) {
        await loadSettings(selectedCategory)
      }
    } catch (error) {
      console.error('Failed to seed settings:', error)
      setMessage({ type: 'error', text: 'Failed to seed settings from environment' })
    } finally {
      setSeeding(false)
    }
  }

  const getSettingStatus = (setting: Setting): 'configured' | 'missing' | 'unknown' => {
    if (setting.has_value) return 'configured'
    return 'missing'
  }

  const currentCategory = categories.find(c => c.category === selectedCategory)
  const Icon = selectedCategory ? categoryIcons[selectedCategory] || SettingsIcon : SettingsIcon
  const color = selectedCategory ? categoryColors[selectedCategory] || '#a8d8ff' : '#a8d8ff'

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <div
            className="p-3 rounded-xl"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.15)',
              border: '1px solid rgba(168, 216, 255, 0.4)'
            }}
          >
            <SettingsIcon className="h-8 w-8" style={{ color: '#a8d8ff' }} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Settings</h1>
            <p className="text-dark-text-secondary mt-1">
              Manage API keys, integrations, and configuration
            </p>
          </div>
        </div>

        <button
          onClick={handleSeedFromEnv}
          disabled={seeding}
          className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors"
          style={{
            backgroundColor: 'rgba(168, 216, 255, 0.15)',
            border: '1px solid rgba(168, 216, 255, 0.4)',
            color: '#a8d8ff'
          }}
        >
          {seeding ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          Seed from .env
        </button>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
            message.type === 'success'
              ? 'bg-green-500/15 border border-green-500/40 text-green-400'
              : 'bg-red-500/15 border border-red-500/40 text-red-400'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="h-5 w-5" />
          ) : (
            <AlertTriangle className="h-5 w-5" />
          )}
          {message.text}
          <button
            onClick={() => setMessage(null)}
            className="ml-auto text-current opacity-70 hover:opacity-100"
          >
            &times;
          </button>
        </div>
      )}

      <div className="flex gap-6">
        {/* Category Sidebar */}
        <div className="w-64 flex-shrink-0">
          <div className="bg-dark-surface rounded-xl border border-dark-border">
            <div className="p-4 border-b border-dark-border">
              <h3 className="font-medium text-white">Categories</h3>
            </div>
            <div className="p-2">
              {categories.map(category => {
                const CatIcon = categoryIcons[category.category] || SettingsIcon
                const catColor = categoryColors[category.category] || '#a8d8ff'
                const isSelected = selectedCategory === category.category

                return (
                  <button
                    key={category.category}
                    onClick={() => setSelectedCategory(category.category)}
                    className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg transition-all text-left ${
                      isSelected ? '' : 'hover:bg-dark-hover'
                    }`}
                    style={
                      isSelected
                        ? {
                            backgroundColor: `${catColor}15`,
                            border: `1px solid ${catColor}40`
                          }
                        : {}
                    }
                  >
                    <CatIcon
                      className="h-5 w-5"
                      style={{ color: isSelected ? catColor : '#9ca3af' }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-white truncate">
                        {category.display_name}
                      </div>
                      <div className="text-xs text-dark-text-secondary">
                        {category.configured_count}/{category.total_settings} configured
                      </div>
                    </div>
                    {category.configured_count === category.total_settings &&
                      category.total_settings > 0 && (
                        <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0" />
                      )}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        <div className="flex-1">
          {loading ? (
            <div className="bg-dark-surface rounded-xl border border-dark-border p-8 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-dark-text-secondary" />
            </div>
          ) : selectedCategory && currentCategory ? (
            <div className="bg-dark-surface rounded-xl border border-dark-border">
              <div className="p-6 border-b border-dark-border">
                <div className="flex items-center gap-3">
                  <Icon className="h-6 w-6" style={{ color }} />
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {currentCategory.display_name}
                    </h2>
                    <p className="text-dark-text-secondary text-sm mt-1">
                      {currentCategory.description}
                    </p>
                  </div>
                </div>
              </div>

              <div className="divide-y divide-dark-border">
                {settings.map(setting => {
                  const status = getSettingStatus(setting)
                  const testResult = testResults[setting.key]

                  return (
                    <div key={setting.key} className="p-6">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium text-white">
                              {setting.display_name || setting.key}
                            </h4>
                            {status === 'configured' ? (
                              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 border border-green-500/40">
                                <CheckCircle className="h-3 w-3" />
                                Configured
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/40">
                                <AlertTriangle className="h-3 w-3" />
                                Not Set
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-dark-text-secondary mt-1">
                            {setting.description}
                          </p>
                          <code className="text-xs text-dark-text-secondary bg-dark-hover px-2 py-0.5 rounded mt-2 inline-block">
                            {setting.key}
                          </code>
                        </div>
                      </div>

                      {/* Current Value (if set) */}
                      {setting.has_value && (
                        <div className="mb-3">
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-dark-text-secondary">Current:</span>
                            <code className="bg-dark-hover px-2 py-1 rounded text-white font-mono">
                              {setting.value_masked}
                            </code>
                          </div>
                        </div>
                      )}

                      {/* Input */}
                      <div className="flex items-center gap-3">
                        <div className="flex-1 relative">
                          <input
                            type={
                              setting.is_secret && !showValues[setting.key]
                                ? 'password'
                                : 'text'
                            }
                            value={editValues[setting.key] || ''}
                            onChange={e =>
                              setEditValues(prev => ({
                                ...prev,
                                [setting.key]: e.target.value
                              }))
                            }
                            placeholder={
                              setting.has_value
                                ? 'Enter new value to update...'
                                : 'Enter value...'
                            }
                            className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg text-white placeholder-dark-text-secondary focus:outline-none focus:border-blue-500 font-mono text-sm"
                          />
                          {setting.is_secret && (
                            <button
                              onClick={() =>
                                setShowValues(prev => ({
                                  ...prev,
                                  [setting.key]: !prev[setting.key]
                                }))
                              }
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-text-secondary hover:text-white"
                            >
                              {showValues[setting.key] ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </button>
                          )}
                        </div>

                        <button
                          onClick={() => handleSave(setting.key)}
                          disabled={
                            !editValues[setting.key] || saving === setting.key
                          }
                          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-dark-hover disabled:text-dark-text-secondary text-white rounded-lg transition-colors"
                        >
                          {saving === setting.key ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Save className="h-4 w-4" />
                          )}
                          Save
                        </button>

                        {setting.has_value && (
                          <button
                            onClick={() => handleTest(setting.key)}
                            disabled={testing === setting.key}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors"
                            style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.15)',
                              border: '1px solid rgba(168, 216, 255, 0.4)',
                              color: '#a8d8ff'
                            }}
                          >
                            {testing === setting.key ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <RefreshCw className="h-4 w-4" />
                            )}
                            Test
                          </button>
                        )}
                      </div>

                      {/* Test Result */}
                      {testResult && (
                        <div
                          className={`mt-3 p-3 rounded-lg flex items-center gap-2 text-sm ${
                            testResult.valid
                              ? 'bg-green-500/15 border border-green-500/40 text-green-400'
                              : 'bg-red-500/15 border border-red-500/40 text-red-400'
                          }`}
                        >
                          {testResult.valid ? (
                            <CheckCircle className="h-4 w-4" />
                          ) : (
                            <XCircle className="h-4 w-4" />
                          )}
                          {testResult.message}
                        </div>
                      )}
                    </div>
                  )
                })}

                {settings.length === 0 && (
                  <div className="p-8 text-center text-dark-text-secondary">
                    No settings in this category
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-dark-surface rounded-xl border border-dark-border p-8 text-center text-dark-text-secondary">
              Select a category to view settings
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
