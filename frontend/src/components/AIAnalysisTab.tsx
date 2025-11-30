import { useState, useEffect } from 'react'
import { 
  Brain, 
  Play, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  Save,
  Trash2,
  Calendar,
  Tag,
  TrendingUp,
  AlertTriangle,
  BarChart3,
  Shield
} from 'lucide-react'
import { runAIAnalysis, listAnalyses, deleteAnalysis, updateAnalysis } from '../api/client'

interface Table {
  schema: string
  name: string
  type: string
  row_estimate?: number
}

interface AnalysisResult {
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

interface SavedAnalysis {
  id: string
  name: string
  description?: string
  analysis_result: AnalysisResult
  saved_at: string
  tags: string[]
}

interface AIAnalysisTabProps {
  selectedDbId: string
  availableTables: Table[]
  selectedTableFromTree?: Table
}

export default function AIAnalysisTab({ selectedDbId, availableTables, selectedTableFromTree }: AIAnalysisTabProps) {
  const [selectedTables, setSelectedTables] = useState<Table[]>([])
  const [analysisTypes, setAnalysisTypes] = useState<string[]>(['eda', 'anomaly'])
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('gpt-4-turbo-preview')
  const [context, setContext] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState('')
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [viewMode, setViewMode] = useState<'new' | 'history'>('new')

  useEffect(() => {
    if (selectedTableFromTree) {
      // Auto-add the selected table from the tree
      if (!selectedTables.find(t => t.schema === selectedTableFromTree.schema && t.name === selectedTableFromTree.name)) {
        setSelectedTables([selectedTableFromTree])
      }
    }
  }, [selectedTableFromTree])

  useEffect(() => {
    if (viewMode === 'history') {
      loadHistory()
    }
  }, [viewMode, selectedDbId])

  const loadHistory = async () => {
    setLoadingHistory(true)
    try {
      const analyses = await listAnalyses(selectedDbId)
      setSavedAnalyses(analyses)
    } catch (err: any) {
      console.error('Failed to load history:', err)
    } finally {
      setLoadingHistory(false)
    }
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

  const runAnalysis = async () => {
    if (selectedTables.length === 0) {
      setError('Please select at least one table')
      return
    }
    if (analysisTypes.length === 0) {
      setError('Please select at least one analysis type')
      return
    }

    setRunning(true)
    setError('')
    setResult(null)

    try {
      const response = await runAIAnalysis({
        tables: selectedTables.map(t => ({ schema: t.schema, table: t.name })),
        analysis_types: analysisTypes,
        provider,
        model,
        db_id: selectedDbId,
        context: context || undefined
      })

      if (response.status === 'completed' && response.result) {
        setResult(response.result)
      } else {
        setError(response.error || 'Analysis failed')
      }
    } catch (err: any) {
      // Always ensure we set a string error message
      let errorMessage = 'Failed to run analysis'
      
      try {
        // Handle validation errors (422)
        if (err.response?.status === 422 && err.response?.data?.detail) {
          const detail = err.response.data.detail
          if (Array.isArray(detail)) {
            // Pydantic validation errors
            const errorMessages = detail.map((e: any) => 
              `${Array.isArray(e.loc) ? e.loc.join('.') : 'field'}: ${e.msg || 'validation error'}`
            ).join(', ')
            errorMessage = `Validation error: ${errorMessages}`
          } else if (typeof detail === 'string') {
            errorMessage = detail
          } else if (typeof detail === 'object') {
            errorMessage = JSON.stringify(detail)
          }
        } else if (err.response?.data?.detail) {
          const detail = err.response.data.detail
          errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail)
        } else if (err.message) {
          errorMessage = String(err.message)
        }
      } catch (parseError) {
        console.error('Error parsing error message:', parseError)
        errorMessage = 'An unexpected error occurred'
      }
      
      setError(errorMessage)
    } finally {
      setRunning(false)
    }
  }

  const handleDeleteAnalysis = async (id: string) => {
    try {
      await deleteAnalysis(id)
      setSavedAnalyses(savedAnalyses.filter(a => a.id !== id))
    } catch (err: any) {
      console.error('Failed to delete analysis:', err)
    }
  }

  const modelOptions = {
    openai: ['gpt-4-turbo-preview', 'gpt-4', 'gpt-3.5-turbo'],
    anthropic: ['claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet'],
    google: ['gemini-pro', 'gemini-ultra'],
    xai: ['grok-1', 'grok-2']
  }

  const analysisTypeOptions = [
    { value: 'eda', label: 'Exploratory Data Analysis', icon: BarChart3 },
    { value: 'anomaly', label: 'Anomaly Detection', icon: AlertTriangle },
    { value: 'correlation', label: 'Correlation Analysis', icon: TrendingUp },
    { value: 'quality', label: 'Data Quality Assessment', icon: Shield },
    { value: 'trends', label: 'Trend Analysis', icon: TrendingUp },
    { value: 'patterns', label: 'Pattern Discovery', icon: Brain }
  ]

  if (viewMode === 'history') {
    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Analysis History</h3>
          <button
            onClick={() => setViewMode('new')}
            className="px-4 py-2 text-sm rounded-lg hover:bg-gray-100"
            style={{ borderColor: '#a8d8ff', borderWidth: 1 }}
          >
            New Analysis
          </button>
        </div>

        {loadingHistory ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#a8d8ff' }} />
          </div>
        ) : savedAnalyses.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Brain className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No saved analyses yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {savedAnalyses.map(analysis => (
              <div
                key={analysis.id}
                className="p-4 rounded-lg border hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => {
                  setResult(analysis.analysis_result)
                  setViewMode('new')
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium mb-1">{analysis.name}</h4>
                    {analysis.description && (
                      <p className="text-sm text-gray-600 mb-2">{analysis.description}</p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(analysis.saved_at).toLocaleDateString()}
                      </span>
                      <span>{analysis.analysis_result.tables.length} table(s)</span>
                      <span className="px-2 py-0.5 rounded" style={{ backgroundColor: '#e8f4ff', color: '#0066cc' }}>
                        {analysis.analysis_result.provider}
                      </span>
                    </div>
                    {analysis.tags && analysis.tags.length > 0 && (
                      <div className="flex items-center gap-2 mt-2">
                        {analysis.tags.map(tag => (
                          <span key={tag} className="px-2 py-0.5 text-xs rounded bg-gray-100">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteAnalysis(analysis.id)
                    }}
                    className="p-2 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="h-4 w-4 text-red-600" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Brain className="h-6 w-6" style={{ color: '#0066cc' }} />
          <h3 className="text-lg font-semibold">AI-Powered Analysis</h3>
        </div>
        <button
          onClick={() => setViewMode('history')}
          className="px-4 py-2 text-sm rounded-lg hover:bg-gray-100"
          style={{ borderColor: '#a8d8ff', borderWidth: 1 }}
        >
          View History
        </button>
      </div>

      {/* Configuration Panel */}
      {!result && (
        <div className="space-y-6">
          {/* Table Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Select Tables ({selectedTables.length} selected)
            </label>
            <div className="border rounded-lg p-4 max-h-48 overflow-y-auto">
              {availableTables.length === 0 ? (
                <p className="text-sm text-gray-500">No tables available</p>
              ) : (
                <div className="space-y-2">
                  {availableTables.map(table => (
                    <label
                      key={`${table.schema}.${table.name}`}
                      className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedTables.some(t => t.schema === table.schema && t.name === table.name)}
                        onChange={() => toggleTable(table)}
                        className="rounded"
                      />
                      <span className="text-sm">
                        {table.schema}.{table.name}
                        {table.row_estimate && (
                          <span className="text-gray-500 ml-2">
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
          <div>
            <label className="block text-sm font-medium mb-2">
              Analysis Types
            </label>
            <div className="grid grid-cols-2 gap-3">
              {analysisTypeOptions.map(({ value, label, icon: Icon }) => (
                <label
                  key={value}
                  className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                    analysisTypes.includes(value)
                      ? 'border-blue-500 bg-blue-50 text-gray-900'
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={analysisTypes.includes(value)}
                    onChange={() => toggleAnalysisType(value)}
                    className="rounded"
                  />
                  <Icon className={`h-4 w-4 ${analysisTypes.includes(value) ? 'text-blue-600' : 'text-gray-600'}`} />
                  <span className="text-sm font-medium">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Model Configuration */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">LLM Provider</label>
              <select
                value={provider}
                onChange={(e) => {
                  setProvider(e.target.value)
                  setModel(modelOptions[e.target.value as keyof typeof modelOptions][0])
                }}
                className="w-full p-2 border rounded-lg"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google</option>
                <option value="xai">xAI</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full p-2 border rounded-lg"
              >
                {modelOptions[provider as keyof typeof modelOptions].map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Context */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Business Context (optional)
            </label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="E.g., 'This is e-commerce data for an online retail store...'"
              className="w-full p-3 border rounded-lg"
              rows={3}
            />
          </div>

          {/* Run Button */}
          <button
            onClick={runAnalysis}
            disabled={running || selectedTables.length === 0}
            className="w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundColor: running || selectedTables.length === 0 ? '#cccccc' : '#0066cc',
              color: 'white'
            }}
          >
            {running ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Play className="h-5 w-5" />
                Run Analysis
              </>
            )}
          </button>

          {error && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-red-800">{error}</span>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <h4 className="font-semibold">Analysis Complete</h4>
            </div>
            <button
              onClick={() => setResult(null)}
              className="px-4 py-2 text-sm rounded-lg hover:bg-gray-100"
              style={{ borderColor: '#a8d8ff', borderWidth: 1 }}
            >
              New Analysis
            </button>
          </div>

          {/* Summary */}
          <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
            <h5 className="font-medium mb-2">Executive Summary</h5>
            <p className="text-sm whitespace-pre-wrap">{result.summary}</p>
            <div className="mt-3 flex items-center gap-4 text-xs text-gray-600">
              <span>{result.tables.length} table(s) analyzed</span>
              <span>{result.provider} / {result.model}</span>
              {result.metadata?.execution_time_seconds && (
                <span>{result.metadata.execution_time_seconds}s execution time</span>
              )}
            </div>
          </div>

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div>
              <h5 className="font-medium mb-3">Recommendations</h5>
              <div className="space-y-2">
                {result.recommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200">
                    <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Insights */}
          <div>
            <h5 className="font-medium mb-3">Detailed Insights</h5>
            <div className="space-y-4">
              {Object.entries(result.insights).map(([key, value]: [string, any]) => (
                <div key={key} className="p-4 rounded-lg border">
                  <h6 className="font-medium mb-2 capitalize">{key.replace(/_/g, ' ')}</h6>
                  <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(value, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

