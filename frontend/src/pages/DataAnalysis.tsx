import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import {
  Brain,
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Clock,
  Database,
  Trash2,
  Eye,
  X,
  RefreshCw,
  Filter,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  Shield,
  Book,
  Sparkles
} from 'lucide-react'
import {
  getExplorerDatabases,
  getExplorerSchemas,
  getExplorerTables,
  createAnalysisJob,
  listAnalysisJobs,
  getAnalysisJob,
  cancelAnalysisJob,
  deleteAnalysisJob,
  getJobStatus,
  getAvailableModels,
  checkApiKeys,
  fetchPromptRecipes,
  createPromptRecipe,
  clonePromptRecipe
} from '../api/client'
import PromptLibrary from '../components/PromptLibrary'

interface Job {
  id: string
  name: string
  description?: string
  status: string
  progress: number
  current_stage?: string
  tables: Array<{ schema: string; table: string }>
  analysis_types: string[]
  provider: string
  model: string
  db_id: string
  created_at: string
  started_at?: string
  completed_at?: string
  cancelled_at?: string
  result_id?: string
  error_message?: string
  tags: string[]
  job_metadata?: any
}

interface JobWithResult {
  job: Job
  result?: {
    analysis_id: string
    tables: Array<{ schema: string; table: string }>
    analysis_types: string[]
    provider: string
    model: string
    insights: any
    summary: string
    recommendations: string[]
    metadata: any
    created_at: string
  }
}

interface Database {
  id: string
  name: string
  description: string
  host: string
  port: number
}

interface Table {
  schema: string
  name: string
  type: string
  row_estimate?: number
}

export default function DataAnalysis() {
  const location = useLocation()
  const navigationState = location.state as {
    preselectedTables?: Array<{ schema: string; name: string }>
    preselectedAction?: string
    dbId?: string
  } | null

  const [activeTab, setActiveTab] = useState<'jobs' | 'prompts'>('jobs')
  const [view, setView] = useState<'new' | 'list' | 'detail'>('list')
  const [selectedDb, setSelectedDb] = useState(navigationState?.dbId || 'default')
  const [databases, setDatabases] = useState<Database[]>([])
  const [tables, setTables] = useState<Table[]>([])
  const [selectedTables, setSelectedTables] = useState<Table[]>([])
  
  // New analysis config
  const [jobName, setJobName] = useState('')
  const [analysisTypes, setAnalysisTypes] = useState<string[]>(
    navigationState?.preselectedAction ? [navigationState.preselectedAction] : ['profiling', 'quality']
  )
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('gpt-4o')
  const [context, setContext] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  
  // Prompt recipes
  const [recipes, setRecipes] = useState<any[]>([])
  const [selectedRecipeId, setSelectedRecipeId] = useState<number | undefined>(undefined)
  const [loadingRecipes, setLoadingRecipes] = useState(false)
  
  // Jobs list
  const [jobs, setJobs] = useState<Job[]>([])
  const [filteredJobs, setFilteredJobs] = useState<Job[]>([])
  const [loadingJobs, setLoadingJobs] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'created' | 'name' | 'status'>('created')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  
  // Job detail
  const [selectedJob, setSelectedJob] = useState<JobWithResult | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  
  // Delete confirmation
  const [deleteConfirmJob, setDeleteConfirmJob] = useState<string | null>(null)
  
  // Auto-refresh running jobs
  const [autoRefresh, setAutoRefresh] = useState(true)
  
  // Re-run with edited prompt
  const [showPromptEditor, setShowPromptEditor] = useState(false)
  const [editedSystemMessage, setEditedSystemMessage] = useState('')
  const [editedUserMessage, setEditedUserMessage] = useState('')
  const [saveAsNewRecipe, setSaveAsNewRecipe] = useState(false)
  const [newRecipeName, setNewRecipeName] = useState('')
  
  // Available models from providers
  const [availableModels, setAvailableModels] = useState<Record<string, string[]>>({})
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({})
  const [loadingModels, setLoadingModels] = useState(true)

  useEffect(() => {
    loadDatabases()
    loadJobs()
    loadAvailableModels()
  }, [])

  useEffect(() => {
    if (selectedDb) {
      loadTables()
    }
  }, [selectedDb])

  // Handle preselected tables from navigation (e.g., from Data Dictionary)
  useEffect(() => {
    if (navigationState?.preselectedTables && tables.length > 0) {
      // Switch to new analysis view
      setView('new')
      
      // Match preselected tables with loaded tables
      const matchedTables = navigationState.preselectedTables
        .map(pt => tables.find(t => t.schema === pt.schema && t.name === pt.name))
        .filter((t): t is Table => t !== undefined)
      
      if (matchedTables.length > 0) {
        setSelectedTables(matchedTables)
        
        // Set a default job name
        if (matchedTables.length === 1) {
          setJobName(`Document ${matchedTables[0].schema}.${matchedTables[0].name}`)
        } else {
          setJobName(`Document ${matchedTables.length} tables`)
        }
      }
      
      // Clear the navigation state to prevent re-triggering
      window.history.replaceState({}, document.title)
    }
  }, [tables, navigationState])

  // Load recipes when analysis types change
  useEffect(() => {
    if (analysisTypes.length > 0) {
      // Load recipes for the first selected analysis type (as a starting point)
      loadRecipes(analysisTypes[0])
    }
  }, [analysisTypes])

  useEffect(() => {
    filterAndSortJobs()
  }, [jobs, statusFilter, searchQuery, sortBy, sortOrder])

  // Auto-refresh every 5 seconds if there are running jobs
  useEffect(() => {
    if (!autoRefresh) return
    
    const hasRunning = jobs.some(j => j.status === 'pending' || j.status === 'running')
    if (!hasRunning) return
    
    const interval = setInterval(() => {
      loadJobs(true) // Silent refresh
    }, 5000)
    
    return () => clearInterval(interval)
  }, [jobs, autoRefresh])

  const loadDatabases = async () => {
    try {
      const dbs = await getExplorerDatabases()
      setDatabases(dbs)
    } catch (error) {
      console.error('Failed to load databases:', error)
    }
  }

  const loadAvailableModels = async () => {
    setLoadingModels(true)
    try {
      const [modelsData, keysData] = await Promise.all([
        getAvailableModels(),
        checkApiKeys()
      ])
      
      // Build models map
      const modelsMap: Record<string, string[]> = {}
      for (const providerData of modelsData.providers) {
        modelsMap[providerData.provider] = providerData.models
      }
      
      setAvailableModels(modelsMap)
      setApiKeys(keysData)
      
      // Set default provider/model to first available
      const firstProvider = modelsData.providers.find(p => p.has_api_key && p.models.length > 0)
      if (firstProvider && firstProvider.models.length > 0) {
        setProvider(firstProvider.provider)
        setModel(firstProvider.models[0])
      }
    } catch (error) {
      console.error('Failed to load models:', error)
      // Fallback to defaults
      setAvailableModels({
        openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-4'],
        anthropic: ['claude-3-5-sonnet-20241022'],
        google: ['gemini-2.0-flash-exp'],
        xai: ['grok-beta']
      })
    } finally {
      setLoadingModels(false)
    }
  }

  const loadTables = async () => {
    try {
      const schemas = await getExplorerSchemas(selectedDb)
      const allTables: Table[] = []
      
      for (const schema of schemas) {
        const schemaTables = await getExplorerTables(schema.name, selectedDb)
        allTables.push(...schemaTables)
      }
      
      setTables(allTables)
    } catch (error) {
      console.error('Failed to load tables:', error)
    }
  }

  const loadRecipes = async (actionType?: string) => {
    setLoadingRecipes(true)
    try {
      const recipesList = await fetchPromptRecipes(actionType)
      setRecipes(recipesList)
    } catch (error) {
      console.error('Failed to load recipes:', error)
      setRecipes([])
    } finally {
      setLoadingRecipes(false)
    }
  }

  const loadJobs = async (silent = false) => {
    if (!silent) setLoadingJobs(true)
    try {
      const jobsList = await listAnalysisJobs({ db_id: selectedDb, limit: 100 })
      setJobs(jobsList)
    } catch (error) {
      console.error('Failed to load jobs:', error)
    } finally {
      if (!silent) setLoadingJobs(false)
    }
  }

  const filterAndSortJobs = () => {
    let filtered = jobs
    
    // Status filter
    if (statusFilter === 'all') {
      filtered = jobs
    } else if (statusFilter === 'active') {
      filtered = jobs.filter(j => j.status === 'pending' || j.status === 'running')
    } else {
      filtered = jobs.filter(j => j.status === statusFilter)
    }
    
    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(j => 
        j.name.toLowerCase().includes(query) ||
        j.description?.toLowerCase().includes(query) ||
        j.tables.some(t => `${t.schema}.${t.table}`.toLowerCase().includes(query))
      )
    }
    
    // Sort
    filtered = [...filtered].sort((a, b) => {
      let comparison = 0
      
      if (sortBy === 'created') {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      } else if (sortBy === 'name') {
        comparison = a.name.localeCompare(b.name)
      } else if (sortBy === 'status') {
        comparison = a.status.localeCompare(b.status)
      }
      
      return sortOrder === 'asc' ? comparison : -comparison
    })
    
    setFilteredJobs(filtered)
  }

  const toggleTable = (table: Table) => {
    const exists = selectedTables.find(t => t.schema === table.schema && t.name === table.name)
    if (exists) {
      setSelectedTables(selectedTables.filter(t => !(t.schema === table.schema && t.name === table.name)))
    } else {
      setSelectedTables([...selectedTables, table])
    }
  }

  const toggleAnalysisType = (type: string) => {
    if (analysisTypes.includes(type)) {
      setAnalysisTypes(analysisTypes.filter(t => t !== type))
    } else {
      setAnalysisTypes([...analysisTypes, type])
    }
  }

  const startAnalysis = async () => {
    if (!jobName.trim()) {
      alert('Please enter a job name')
      return
    }
    if (selectedTables.length === 0) {
      alert('Please select at least one table')
      return
    }
    if (!apiKeys[provider]) {
      const envVarMap: Record<string, string> = {
        openai: 'OPENAI_API_KEY',
        anthropic: 'ANTHROPIC_API_KEY',
        google: 'GOOGLE_API_KEY or GEMINI_API_KEY',
        xai: 'X_AI_API_KEY'
      }
      alert(`No API key configured for ${provider}. Please add ${envVarMap[provider]} to your environment.`)
      return
    }
    if (!availableModels[provider] || availableModels[provider].length === 0) {
      alert(`No models available for ${provider}. Please check your API key configuration.`)
      return
    }

    setSubmitting(true)
    try {
      await createAnalysisJob({
        name: jobName,
        tables: selectedTables.map(t => ({ schema: t.schema, table: t.name })),
        analysis_types: analysisTypes,
        provider,
        model,
        db_id: selectedDb,
        context: context || undefined,
        tags,
        prompt_recipe_id: selectedRecipeId || undefined
      })

      // Reset form and switch to list view
      setJobName('')
      setSelectedTables([])
      setContext('')
      setTags([])
      setView('list')
      loadJobs()
      
      // Show notification
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Analysis Started', {
          body: `Job "${jobName}" is now running`,
          icon: '/favicon.ico'
        })
      }
    } catch (error: any) {
      console.error('Failed to start analysis:', error)
      alert('Failed to start analysis: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSubmitting(false)
    }
  }

  const viewJobDetail = async (jobId: string) => {
    setLoadingDetail(true)
    try {
      const jobDetail = await getAnalysisJob(jobId)
      setSelectedJob(jobDetail)
      setView('detail')
    } catch (error) {
      console.error('Failed to load job:', error)
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleCancelJob = async (jobId: string) => {
    try {
      await cancelAnalysisJob(jobId)
      loadJobs()
    } catch (error) {
      console.error('Failed to cancel job:', error)
    }
  }

  const handleDeleteJob = async (jobId: string) => {
    try {
      await deleteAnalysisJob(jobId)
      setJobs(jobs.filter(j => j.id !== jobId))
      setDeleteConfirmJob(null)
      if (selectedJob?.job.id === jobId) {
        setView('list')
        setSelectedJob(null)
      }
    } catch (error) {
      console.error('Failed to delete job:', error)
      alert('Failed to delete job: ' + (error as any).message)
    }
  }

  const handleRerunWithEditedPrompt = async () => {
    if (!selectedJob) return
    
    setSubmitting(true)
    try {
      let recipeIdToUse: number | undefined = undefined
      
      // If user wants to save as new recipe, create it first
      if (saveAsNewRecipe && newRecipeName) {
        const newRecipe = await createPromptRecipe({
          name: newRecipeName,
          action_type: selectedJob.job.analysis_types[0],
          default_provider: selectedJob.job.provider,
          default_model: selectedJob.job.model,
          system_message: editedSystemMessage,
          user_template: editedUserMessage,
          recipe_metadata: {
            version: '1.0',
            created_from_job: selectedJob.job.id,
            created_at: new Date().toISOString()
          }
        })
        recipeIdToUse = newRecipe.id
      }
      
      // Create new job with edited prompts
      await createAnalysisJob({
        name: `${selectedJob.job.name} (re-run)`,
        tables: selectedJob.job.tables,
        analysis_types: selectedJob.job.analysis_types,
        provider: selectedJob.job.provider,
        model: selectedJob.job.model,
        db_id: selectedJob.job.db_id,
        context: undefined,
        tags: [...selectedJob.job.tags, 're-run'],
        prompt_recipe_id: recipeIdToUse
      })
      
      // Close modal and refresh jobs list
      setShowPromptEditor(false)
      setSaveAsNewRecipe(false)
      await loadJobs()
      setView('list')
    } catch (error) {
      console.error('Failed to re-run job:', error)
      alert('Failed to re-run job: ' + (error as any).message)
    } finally {
      setSubmitting(false)
    }
  }

  // Model options are now loaded dynamically from availableModels state

  const analysisTypeOptions = [
    { value: 'profiling', label: 'Data Profiling', icon: BarChart3, description: 'Structural and statistical properties of data' },
    { value: 'quality', label: 'Data Quality Checks', icon: Shield, description: 'Missing data, duplicates, invalid values, violations' },
    { value: 'anomaly', label: 'Outlier & Anomaly Detection', icon: AlertTriangle, description: 'Unusual values, distribution shifts, temporal anomalies' },
    { value: 'relationships', label: 'Relationship Analysis', icon: TrendingUp, description: 'Correlations and associations between columns' },
    { value: 'trends', label: 'Trend & Time-Series Analysis', icon: TrendingUp, description: 'Temporal behavior, trends, seasonality, cycles' },
    { value: 'patterns', label: 'Pattern Discovery', icon: Brain, description: 'Higher-order patterns, clusters, segments, groups' },
    { value: 'column_documentation', label: 'Column Documentation', icon: Book, description: 'Generate data dictionary with business descriptions' }
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="h-5 w-5 text-gray-500" />
      case 'running': return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
      case 'completed': return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'failed': return <XCircle className="h-5 w-5 text-red-500" />
      case 'cancelled': return <AlertCircle className="h-5 w-5 text-orange-500" />
      default: return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-800'
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'cancelled': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0a0a0f' }}>
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="h-8 w-8" style={{ color: '#a8d8ff' }} />
            <h1 className="text-3xl font-bold" style={{ color: '#f0f0f5' }}>
              Data Analysis
            </h1>
          </div>
          <p style={{ color: '#b0b8c0' }}>
            AI-powered analysis with MCP integration for deep data exploration
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 mb-6 border-b" style={{ borderColor: 'rgba(168, 216, 255, 0.2)' }}>
          <button
            onClick={() => setActiveTab('jobs')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'jobs' ? '' : 'border-transparent'
            }`}
            style={{
              color: activeTab === 'jobs' ? '#a8d8ff' : '#7a8a99',
              borderColor: activeTab === 'jobs' ? '#a8d8ff' : 'transparent'
            }}
          >
            Analysis Jobs
          </button>
          <button
            onClick={() => setActiveTab('prompts')}
            className={`px-6 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'prompts' ? '' : 'border-transparent'
            }`}
            style={{
              color: activeTab === 'prompts' ? '#a8d8ff' : '#7a8a99',
              borderColor: activeTab === 'prompts' ? '#a8d8ff' : 'transparent'
            }}
          >
            Prompt Library
          </button>
        </div>

        {/* Jobs Tab Content */}
        {activeTab === 'jobs' && (
          <>
            {/* Action Buttons */}
            <div className="flex items-center gap-4 mb-6">
              <button
                onClick={() => setView('new')}
                className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                  view === 'new' ? 'text-white' : ''
                }`}
                style={{
                  backgroundColor: view === 'new' ? '#0066cc' : 'rgba(168, 216, 255, 0.1)',
                  color: view === 'new' ? 'white' : '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.3)'
                }}
              >
                <Play className="h-4 w-4 inline mr-2" />
                New Analysis
              </button>
              <button
                onClick={() => { setView('list'); loadJobs(); }}
                className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                  view === 'list' ? 'text-white' : ''
                }`}
                style={{
                  backgroundColor: view === 'list' ? '#0066cc' : 'rgba(168, 216, 255, 0.1)',
                  color: view === 'list' ? 'white' : '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.3)'
                }}
              >
                Analysis Jobs ({jobs.length})
              </button>
              <div className="flex-1" />
              <label className="flex items-center gap-2" style={{ color: '#b0b8c0' }}>
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                Auto-refresh
              </label>
            </div>

        {/* New Analysis View */}
        {view === 'new' && (
          <div className="space-y-6">
            <div className="p-6 rounded-xl" style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}>
              <h3 className="text-xl font-semibold mb-6" style={{ color: '#f0f0f5' }}>
                Configure New Analysis
              </h3>

              {/* Job Name */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Analysis Name *
                </label>
                <input
                  type="text"
                  value={jobName}
                  onChange={(e) => setJobName(e.target.value)}
                  placeholder="E.g., Q4 Sales Analysis"
                  className="w-full p-3 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
              </div>

              {/* Database Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Database
                </label>
                <select
                  value={selectedDb}
                  onChange={(e) => setSelectedDb(e.target.value)}
                  className="w-full p-3 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                >
                  {databases.map(db => (
                    <option key={db.id} value={db.id}>{db.name} ({db.host}:{db.port})</option>
                  ))}
                </select>
              </div>

              {/* Table Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Select Tables ({selectedTables.length} selected) *
                </label>
                <div 
                  className="p-4 rounded-lg max-h-64 overflow-y-auto"
                  style={{
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)'
                  }}
                >
                  {tables.length === 0 ? (
                    <p className="text-sm" style={{ color: '#b0b8c0' }}>No tables available</p>
                  ) : (
                    <div className="space-y-2">
                      {tables.map(table => (
                        <label
                          key={`${table.schema}.${table.name}`}
                          className="flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-opacity-50"
                          style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)' }}
                        >
                          <input
                            type="checkbox"
                            checked={selectedTables.some(t => t.schema === table.schema && t.name === table.name)}
                            onChange={() => toggleTable(table)}
                            className="rounded"
                          />
                          <span className="text-sm" style={{ color: '#f0f0f5' }}>
                            {table.schema}.{table.name}
                            {table.row_estimate && (
                              <span style={{ color: '#b0b8c0' }} className="ml-2">
                                (~{table.row_estimate.toLocaleString()} rows)
                              </span>
                            )}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Analysis Types */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Analysis Types
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {analysisTypeOptions.map(({ value, label, icon: Icon }) => (
                    <label
                      key={value}
                      className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors"
                      style={{
                        backgroundColor: analysisTypes.includes(value) 
                          ? 'rgba(168, 216, 255, 0.15)' 
                          : 'rgba(168, 216, 255, 0.05)',
                        border: `1px solid ${analysisTypes.includes(value) ? '#a8d8ff' : 'rgba(168, 216, 255, 0.2)'}`,
                        color: analysisTypes.includes(value) ? '#a8d8ff' : '#b0b8c0'
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={analysisTypes.includes(value)}
                        onChange={() => toggleAnalysisType(value)}
                        className="rounded"
                      />
                      <Icon className="h-4 w-4" />
                      <span className="text-sm font-medium">{label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Prompt Recipe (Optional) */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Prompt Recipe (Optional) {loadingRecipes && '(Loading...)'}
                </label>
                <select
                  value={selectedRecipeId ?? ''}
                  onChange={(e) => setSelectedRecipeId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full p-3 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                  disabled={loadingRecipes}
                >
                  <option value="">Use default prompt templates</option>
                  {recipes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
                <div className="flex items-center justify-between mt-1">
                  <p className="text-xs" style={{ color: '#7a8a99' }}>
                    Select a custom prompt recipe to override the default analysis prompts
                  </p>
                  <button
                    type="button"
                    onClick={() => setActiveTab('prompts')}
                    className="text-xs underline hover:no-underline transition-colors"
                    style={{ color: '#a8d8ff' }}
                  >
                    Manage Recipes →
                  </button>
                </div>
              </div>

              {/* Model Selection */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                    Provider {loadingModels && '(Loading...)'}
                  </label>
                  <select
                    value={provider}
                    onChange={(e) => {
                      const newProvider = e.target.value
                      setProvider(newProvider)
                      const models = availableModels[newProvider] || []
                      if (models.length > 0) {
                        setModel(models[0])
                      }
                    }}
                    className="w-full p-3 rounded-lg"
                    style={{
                      backgroundColor: '#0f0f17',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                    disabled={loadingModels}
                  >
                    {Object.keys(availableModels).map(p => (
                      <option key={p} value={p}>
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                        {!apiKeys[p] && ' (No API Key)'}
                        {apiKeys[p] && availableModels[p].length === 0 && ' (No Models)'}
                      </option>
                    ))}
                  </select>
                  
                  {/* API Key Warning */}
                  {!apiKeys[provider] && (
                    <p className="text-xs mt-1 text-amber-400 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      No API key configured for {provider}
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                    Model
                  </label>
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full p-3 rounded-lg"
                    style={{
                      backgroundColor: '#0f0f17',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                    disabled={loadingModels || !availableModels[provider] || availableModels[provider].length === 0}
                  >
                    {availableModels[provider]?.length > 0 ? (
                      availableModels[provider].map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))
                    ) : (
                      <option value="">No models available</option>
                    )}
                  </select>
                  
                  {/* Model count */}
                  {availableModels[provider]?.length > 0 && (
                    <p className="text-xs mt-1" style={{ color: '#b0b8c0' }}>
                      {availableModels[provider].length} model(s) available
                    </p>
                  )}
                </div>
              </div>

              {/* Context */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Business Context (optional)
                </label>
                <textarea
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="Provide context about your business domain or what you're trying to discover..."
                  className="w-full p-3 rounded-lg"
                  rows={3}
                  style={{
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
              </div>

              {/* Start Button */}
              <button
                onClick={startAnalysis}
                disabled={submitting || !jobName.trim() || selectedTables.length === 0}
                className="w-full py-4 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                style={{
                  backgroundColor: submitting || !jobName.trim() || selectedTables.length === 0 ? '#333' : '#0066cc',
                  color: 'white'
                }}
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Starting Analysis...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    Start Analysis
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Jobs List View */}
        {view === 'list' && (
          <div>
            {/* Search and Filters */}
            <div className="mb-6 space-y-4">
              {/* Search Bar */}
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name, description, or table..."
                  className="w-full p-3 pl-10 rounded-lg"
                  style={{
                    backgroundColor: '#1a1a24',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
                <Filter className="h-5 w-5 absolute left-3 top-3.5" style={{ color: '#a8d8ff' }} />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-3 p-0.5 hover:bg-opacity-80"
                  >
                    <X className="h-5 w-5" style={{ color: '#b0b8c0' }} />
                  </button>
                )}
              </div>
              
              {/* Status Filters and Sort */}
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex gap-2">
                  {['all', 'active', 'running', 'completed', 'failed'].map(filter => (
                    <button
                      key={filter}
                      onClick={() => setStatusFilter(filter)}
                      className={`px-3 py-1.5 text-sm rounded-lg transition-colors capitalize ${
                        statusFilter === filter ? 'text-white' : ''
                      }`}
                      style={{
                        backgroundColor: statusFilter === filter 
                          ? '#0066cc' 
                          : 'rgba(168, 216, 255, 0.1)',
                        color: statusFilter === filter ? 'white' : '#b0b8c0',
                        border: '1px solid rgba(168, 216, 255, 0.2)'
                      }}
                    >
                      {filter} ({filter === 'all' ? jobs.length : 
                        filter === 'active' ? jobs.filter(j => j.status === 'pending' || j.status === 'running').length :
                        jobs.filter(j => j.status === filter).length})
                    </button>
                  ))}
                </div>
                
                {/* Sort */}
                <div className="flex items-center gap-2 ml-auto">
                  <span className="text-sm" style={{ color: '#b0b8c0' }}>Sort:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="px-3 py-1.5 text-sm rounded-lg"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.1)',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      color: '#f0f0f5'
                    }}
                  >
                    <option value="created">Created</option>
                    <option value="name">Name</option>
                    <option value="status">Status</option>
                  </select>
                  <button
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                    className="p-1.5 rounded-lg hover:bg-opacity-80"
                    style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}
                    title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
                  >
                    {sortOrder === 'asc' ? '↑' : '↓'}
                  </button>
                  <button
                    onClick={() => loadJobs()}
                    className="p-1.5 rounded-lg hover:bg-opacity-80"
                    style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}
                    title="Refresh"
                  >
                    <RefreshCw className="h-4 w-4" style={{ color: '#a8d8ff' }} />
                  </button>
                </div>
              </div>
              
              {/* Results count */}
              <div className="text-sm" style={{ color: '#b0b8c0' }}>
                Showing {filteredJobs.length} of {jobs.length} jobs
              </div>
            </div>

            {/* Jobs Grid */}
            {loadingJobs ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff' }} />
              </div>
            ) : filteredJobs.length === 0 ? (
              <div 
                className="p-12 text-center rounded-xl"
                style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}
              >
                <Brain className="h-16 w-16 mx-auto mb-4 opacity-50" style={{ color: '#a8d8ff' }} />
                <h3 className="text-xl font-semibold mb-2" style={{ color: '#f0f0f5' }}>
                  No analyses found
                </h3>
                <p style={{ color: '#b0b8c0' }}>
                  Click "New Analysis" to start your first data analysis
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {filteredJobs.map(job => (
                  <div
                    key={job.id}
                    className="p-6 rounded-xl hover:shadow-lg transition-shadow cursor-pointer"
                    style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}
                    onClick={() => viewJobDetail(job.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getStatusIcon(job.status)}
                          <h4 className="text-lg font-semibold" style={{ color: '#f0f0f5' }}>
                            {job.name}
                          </h4>
                          <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>

                        {job.description && (
                          <p className="text-sm mb-3" style={{ color: '#b0b8c0' }}>
                            {job.description}
                          </p>
                        )}

                        <div className="flex items-center gap-4 text-sm mb-3" style={{ color: '#b0b8c0' }}>
                          <span className="flex items-center gap-1">
                            <Database className="h-4 w-4" />
                            {job.tables.length} table(s)
                          </span>
                          <span>{job.provider} / {job.model}</span>
                          <span>{new Date(job.created_at).toLocaleString()}</span>
                        </div>

                        {/* Progress Bar */}
                        {job.status === 'running' && (
                          <div className="mb-2">
                            <div className="flex items-center justify-between text-xs mb-1" style={{ color: '#b0b8c0' }}>
                              <span>{job.current_stage}</span>
                              <span>{job.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-2">
                              <div
                                className="h-2 rounded-full transition-all duration-500"
                                style={{
                                  width: `${job.progress}%`,
                                  backgroundColor: '#0066cc'
                                }}
                              />
                            </div>
                          </div>
                        )}

                        {job.error_message && (
                          <div className="mt-2 p-3 rounded bg-red-900 bg-opacity-20 border border-red-500 border-opacity-30">
                            <p className="text-sm text-red-400">{job.error_message}</p>
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 ml-4">
                        {(job.status === 'pending' || job.status === 'running') && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCancelJob(job.id)
                            }}
                            className="p-2 rounded hover:bg-opacity-80"
                            style={{ backgroundColor: 'rgba(255, 100, 100, 0.2)' }}
                          >
                            <X className="h-4 w-4 text-red-400" />
                          </button>
                        )}
                        {job.status === 'completed' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              viewJobDetail(job.id)
                            }}
                            className="p-2 rounded hover:bg-opacity-80"
                            style={{ backgroundColor: 'rgba(168, 216, 255, 0.2)' }}
                          >
                            <Eye className="h-4 w-4" style={{ color: '#a8d8ff' }} />
                          </button>
                        )}
                        {['completed', 'failed', 'cancelled'].includes(job.status) && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setDeleteConfirmJob(job.id)
                            }}
                            className="p-2 rounded hover:bg-opacity-80"
                            style={{ backgroundColor: 'rgba(255, 100, 100, 0.2)' }}
                            title="Delete job"
                          >
                            <Trash2 className="h-4 w-4 text-red-400" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Job Detail View */}
        {view === 'detail' && selectedJob && (
          <div className="space-y-6">
            <button
              onClick={() => { setView('list'); setSelectedJob(null); }}
              className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-opacity-80"
              style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)', color: '#a8d8ff' }}
            >
              ← Back to List
            </button>

            {/* Job Info */}
            <div className="p-6 rounded-xl" style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getStatusIcon(selectedJob.job.status)}
                  <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>
                    {selectedJob.job.name}
                  </h2>
                  <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(selectedJob.job.status)}`}>
                    {selectedJob.job.status}
                  </span>
                </div>
                
                {/* Re-run with different prompt button */}
                {(selectedJob.job.status === 'completed' || selectedJob.job.status === 'failed') && (
                  <button
                    onClick={async () => {
                      // Fetch full job details to get metadata with prompts
                      const fullJob = await getAnalysisJob(selectedJob.job.id)
                      const metadata = fullJob.job_metadata || {}
                      const analysisType = selectedJob.job.analysis_types[0]
                      
                      // Get prompts from metadata (stored per analysis type)
                      const systemMsg = metadata[`${analysisType}_system_message`] || 'System message not found'
                      const userMsg = metadata[`${analysisType}_user_message`] || 'User message not found'
                      
                      setEditedSystemMessage(systemMsg)
                      setEditedUserMessage(userMsg)
                      setNewRecipeName(`${analysisType} - Custom from ${selectedJob.job.name}`)
                      setShowPromptEditor(true)
                    }}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.15)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#a8d8ff'
                    }}
                  >
                    <RefreshCw className="h-4 w-4" />
                    Re-run with Different Prompt
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm" style={{ color: '#b0b8c0' }}>
                <div>
                  <strong style={{ color: '#a8d8ff' }}>Database:</strong> {selectedJob.job.db_id}
                </div>
                <div>
                  <strong style={{ color: '#a8d8ff' }}>Model:</strong> {selectedJob.job.provider} / {selectedJob.job.model}
                </div>
                <div>
                  <strong style={{ color: '#a8d8ff' }}>Tables:</strong> {selectedJob.job.tables.length}
                </div>
                <div>
                  <strong style={{ color: '#a8d8ff' }}>Analysis Types:</strong> {selectedJob.job.analysis_types.join(', ')}
                </div>
                <div>
                  <strong style={{ color: '#a8d8ff' }}>Created:</strong> {new Date(selectedJob.job.created_at).toLocaleString()}
                </div>
                {selectedJob.job.completed_at && (
                  <div>
                    <strong style={{ color: '#a8d8ff' }}>Completed:</strong> {new Date(selectedJob.job.completed_at).toLocaleString()}
                  </div>
                )}
              </div>
            </div>

            {/* Results */}
            {selectedJob.result && (
              <div className="space-y-6">
                {/* AI-Enhanced Executive Summary - Prominent Display */}
                <div 
                  className="p-8 rounded-xl relative overflow-hidden" 
                  style={{ 
                    background: 'linear-gradient(135deg, rgba(168, 216, 255, 0.15) 0%, rgba(168, 216, 255, 0.05) 100%)',
                    border: '2px solid rgba(168, 216, 255, 0.3)',
                    boxShadow: '0 4px 20px rgba(168, 216, 255, 0.1)'
                  }}
                >
                  {/* Decorative corner accent */}
                  <div 
                    style={{
                      position: 'absolute',
                      top: 0,
                      right: 0,
                      width: '150px',
                      height: '150px',
                      background: 'radial-gradient(circle at top right, rgba(168, 216, 255, 0.2), transparent 70%)',
                      pointerEvents: 'none'
                    }}
                  />
                  
                  <div style={{ position: 'relative', zIndex: 1 }}>
                    <div className="flex items-center gap-3 mb-4">
                      <div 
                        className="flex items-center justify-center rounded-lg"
                        style={{
                          width: '48px',
                          height: '48px',
                          background: 'rgba(168, 216, 255, 0.2)',
                          border: '1px solid rgba(168, 216, 255, 0.3)'
                        }}
                      >
                        <Sparkles className="h-6 w-6" style={{ color: '#a8d8ff' }} />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold" style={{ color: '#a8d8ff' }}>
                          AI-Enhanced Executive Summary
                        </h3>
                        <p className="text-sm" style={{ color: '#9ca3af' }}>
                          Key findings synthesized by AI
                        </p>
                      </div>
                    </div>
                    
                    <p 
                      className="text-lg leading-relaxed" 
                      style={{ 
                        color: '#f0f0f5',
                        lineHeight: '1.8'
                      }}
                    >
                      {selectedJob.result.summary}
                    </p>
                  </div>
                </div>

                {/* Recommendations */}
                {selectedJob.result.recommendations && selectedJob.result.recommendations.length > 0 && (
                  <div className="p-6 rounded-xl" style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}>
                    <h3 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>
                      Recommendations
                    </h3>
                    <div className="space-y-3">
                      {selectedJob.result.recommendations.map((rec, i) => (
                        <div key={i} className="flex items-start gap-3 p-4 rounded-lg" style={{ backgroundColor: 'rgba(255, 200, 100, 0.1)', border: '1px solid rgba(255, 200, 100, 0.3)' }}>
                          <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                          <span style={{ color: '#f0f0f5' }}>{rec}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Detailed Insights */}
                <div className="p-6 rounded-xl" style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}>
                  <h3 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>
                    Detailed Insights
                  </h3>
                  
                  {/* Show parsing error prominently if present */}
                  {selectedJob.result.insights.parse_error && (
                    <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: 'rgba(255, 100, 100, 0.1)', border: '1px solid rgba(255, 100, 100, 0.3)' }}>
                      <h4 className="font-medium mb-2 text-red-400 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
                        JSON Parsing Failed
                      </h4>
                      <p className="text-sm text-red-300 mb-3">
                        {selectedJob.result.insights.parse_error}
                      </p>
                      
                      {/* Show raw response if available */}
                      {selectedJob.result.insights.raw_response && (
                        <details className="mt-3">
                          <summary className="cursor-pointer text-sm font-medium text-red-300 hover:text-red-200 mb-2">
                            Show Raw LLM Response
                          </summary>
                          <div className="mt-2 p-3 rounded text-xs overflow-auto max-h-96" style={{ backgroundColor: '#0a0a0f', color: '#f0f0f5' }}>
                            <pre className="whitespace-pre-wrap">{selectedJob.result.insights.raw_response}</pre>
                          </div>
                        </details>
                      )}
                    </div>
                  )}
                  
                  <div className="space-y-4">
                    {Object.entries(selectedJob.result.insights)
                      .filter(([key]) => !['parse_error', 'raw_response'].includes(key))
                      .map(([key, value]: [string, any]) => (
                        <div key={key} className="p-4 rounded-lg" style={{ backgroundColor: '#0f0f17', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                          <h4 className="font-medium mb-2 capitalize" style={{ color: '#a8d8ff' }}>
                            {key.replace(/_/g, ' ')}
                          </h4>
                          
                          {/* Better rendering for different data types */}
                          {typeof value === 'string' ? (
                            <p style={{ color: '#f0f0f5' }}>{value}</p>
                          ) : Array.isArray(value) ? (
                            <ul className="list-disc list-inside space-y-1">
                              {value.map((item, i) => (
                                <li key={i} className="text-sm" style={{ color: '#b0b8c0' }}>
                                  {typeof item === 'string' ? item : JSON.stringify(item)}
                                </li>
                              ))}
                            </ul>
                          ) : typeof value === 'object' && value !== null ? (
                            <pre className="text-xs overflow-x-auto p-3 rounded" style={{ backgroundColor: '#0a0a0f', color: '#b0b8c0' }}>
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          ) : (
                            <span style={{ color: '#b0b8c0' }}>{String(value)}</span>
                          )}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}

            {selectedJob.job.error_message && (
              <div className="p-6 rounded-xl" style={{ backgroundColor: 'rgba(255, 50, 50, 0.1)', border: '1px solid rgba(255, 50, 50, 0.3)' }}>
                <h3 className="text-lg font-semibold mb-3 text-red-400">Error</h3>
                <p style={{ color: '#f0f0f5' }}>{selectedJob.job.error_message}</p>
              </div>
            )}
        </div>
      )}
          </>
        )}

        {/* Prompts Tab Content */}
        {activeTab === 'prompts' && (
          <PromptLibrary />
        )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmJob && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setDeleteConfirmJob(null)}
        >
          <div 
            className="p-6 rounded-xl max-w-md w-full mx-4"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.3)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="h-6 w-6 text-amber-400" />
              <h3 className="text-lg font-semibold" style={{ color: '#f0f0f5' }}>
                Delete Analysis Job
              </h3>
            </div>
            
            <p className="mb-6" style={{ color: '#b0b8c0' }}>
              Are you sure you want to delete this analysis job? This action cannot be undone.
            </p>
            
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirmJob(null)}
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
                onClick={() => handleDeleteJob(deleteConfirmJob)}
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

      {/* Prompt Editor Modal */}
      {showPromptEditor && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowPromptEditor(false)}
        >
          <div 
            className="p-6 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-auto"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.3)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Brain className="h-6 w-6" style={{ color: '#a8d8ff' }} />
                <h3 className="text-xl font-semibold" style={{ color: '#f0f0f5' }}>
                  Edit Prompt & Re-run Analysis
                </h3>
              </div>
              <button onClick={() => setShowPromptEditor(false)}>
                <X className="h-5 w-5" style={{ color: '#b0b8c0' }} />
              </button>
            </div>
            
            <p className="mb-6 text-sm" style={{ color: '#b0b8c0' }}>
              Edit the system and user prompts below, then re-run the analysis with the new configuration.
            </p>

            {/* System Message */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                System Message
              </label>
              <textarea
                value={editedSystemMessage}
                onChange={(e) => setEditedSystemMessage(e.target.value)}
                rows={8}
                className="w-full p-3 rounded-lg font-mono text-sm"
                style={{
                  backgroundColor: '#0f0f17',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
                placeholder="System message defines the AI's role and constraints..."
              />
            </div>

            {/* User Template */}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                User Message Template
              </label>
              <textarea
                value={editedUserMessage}
                onChange={(e) => setEditedUserMessage(e.target.value)}
                rows={12}
                className="w-full p-3 rounded-lg font-mono text-sm"
                style={{
                  backgroundColor: '#0f0f17',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
                placeholder="User message template (use {{schema_summary}} and {{sample_rows}} placeholders)..."
              />
              <p className="text-xs mt-1" style={{ color: '#7a8a99' }}>
                Use <code className="px-1 py-0.5 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>
                  {'{'}{'{'} schema_summary {'}'}{'}'}
                </code> and <code className="px-1 py-0.5 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>
                  {'{'}{'{'} sample_rows {'}'}{'}'}
                </code> as placeholders
              </p>
            </div>

            {/* Save as New Recipe Option */}
            <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.2)' }}>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={saveAsNewRecipe}
                  onChange={(e) => setSaveAsNewRecipe(e.target.checked)}
                  className="rounded"
                />
                <span className="font-medium" style={{ color: '#a8d8ff' }}>
                  Save as new prompt recipe
                </span>
              </label>
              
              {saveAsNewRecipe && (
                <div className="mt-3">
                  <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                    Recipe Name
                  </label>
                  <input
                    type="text"
                    value={newRecipeName}
                    onChange={(e) => setNewRecipeName(e.target.value)}
                    className="w-full p-3 rounded-lg"
                    style={{
                      backgroundColor: '#0f0f17',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                    placeholder="e.g., Custom Data Profiling v2"
                  />
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowPromptEditor(false)}
                className="px-4 py-2 rounded-lg font-medium transition-colors"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.1)',
                  color: '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.3)'
                }}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                onClick={handleRerunWithEditedPrompt}
                disabled={submitting || !editedSystemMessage || !editedUserMessage || (saveAsNewRecipe && !newRecipeName)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: '#a8d8ff',
                  color: '#0a0a0f'
                }}
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Re-run Analysis
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}

