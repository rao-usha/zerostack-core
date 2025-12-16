import axios from 'axios'

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default client

// API functions
export const uploadDataset = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await client.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const listDatasets = async () => {
  const response = await client.get('/api/datasets')
  return response.data
}

export const getDataset = async (datasetId: string) => {
  const response = await client.get(`/api/dataset/${datasetId}`)
  return response.data
}

export const generateSyntheticData = async (datasetId: string, numRows: number = 1000) => {
  const response = await client.post('/api/synthetic/generate', {
    dataset_id: datasetId,
    num_rows: numRows,
  })
  return response.data
}

export const buildPredictiveModel = async (
  datasetId: string,
  targetColumn: string,
  modelType: string = 'regression'
) => {
  const response = await client.post('/api/models/predictive', {
    dataset_id: datasetId,
    target_column: targetColumn,
    model_type: modelType,
  })
  return response.data
}

export const generateInsights = async (datasetId: string, context: string = 'general business') => {
  const response = await client.post('/api/insights/generate', {
    dataset_id: datasetId,
    context,
  })
  return response.data
}

export const chatQuery = async (query: string, datasetId?: string) => {
  const response = await client.post('/api/chat', {
    query,
    dataset_id: datasetId,
  })
  return response.data
}

export const getDataQuality = async (datasetId: string) => {
  const response = await client.get(`/api/quality/${datasetId}`)
  return response.data
}

export const getKnowledgeGaps = async (datasetId: string) => {
  const response = await client.get(`/api/knowledge-gaps/${datasetId}`)
  return response.data
}

// Context Engineering API
export const listContexts = async () => {
  const response = await client.get('/api/v1/contexts', {
    headers: {
      'X-Org-ID': 'demo',
    },
  })
  return response.data.contexts || []
}

export const getContext = async (contextId: string) => {
  const response = await client.get(`/api/v1/contexts/${contextId}`)
  return response.data
}

export const createContext = async (name: string, description?: string, datasetVersionIds: string[] = []) => {
  const response = await client.post(
    '/api/v1/contexts',
    {
      name,
      description,
      dataset_version_ids: datasetVersionIds,
      metadata: {},
    },
    {
      headers: {
        'X-Org-ID': 'demo',
      },
    }
  )
  return response.data
}

export const getContextLayers = async (contextId: string) => {
  const response = await client.get(`/api/v1/contexts/${contextId}/layers`)
  return response.data.layers || []
}

export const addContextLayer = async (
  contextId: string,
  kind: string,
  name: string,
  spec: any = {},
  enabled: boolean = true
) => {
  const response = await client.post(`/api/v1/contexts/${contextId}/layers`, {
    kind,
    name,
    spec,
    enabled,
  })
  return response.data
}

export const updateContextLayer = async (layerId: string, enabled?: boolean, spec?: any) => {
  const response = await client.put(`/api/v1/contexts/layers/${layerId}`, {
    enabled,
    spec,
  })
  return response.data
}

export const deleteContextLayer = async (layerId: string) => {
  const response = await client.delete(`/api/v1/contexts/layers/${layerId}`)
  return response.data
}

export const createContextVersion = async (contextId: string, message?: string) => {
  const response = await client.post(
    `/api/v1/contexts/${contextId}/version`,
    message ? { message } : {},
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  )
  return response.data
}

export const getContextVersions = async (contextId: string) => {
  const response = await client.get(`/api/v1/contexts/${contextId}/versions`)
  return response.data.versions || []
}

export const upsertContextDictionary = async (contextId: string, name: string, entries: Record<string, string>) => {
  const response = await client.post(`/api/v1/contexts/${contextId}/dictionary`, {
    name,
    entries,
  })
  return response.data
}

export const getContextDictionaries = async (contextId: string) => {
  const response = await client.get(`/api/v1/contexts/${contextId}/dictionaries`)
  return response.data.dictionaries || []
}

export const exportContextPack = async (contextId: string, versionId?: string) => {
  const url = versionId
    ? `/api/v1/contexts/${contextId}/export?version_id=${versionId}`
    : `/api/v1/contexts/${contextId}/export`
  const response = await client.get(url)
  return response.data
}

// Document API
export const uploadContextDocument = async (
  contextId: string,
  file: File,
  name?: string,
  autoSummarize: boolean = true
) => {
  const formData = new FormData()
  formData.append('file', file)
  if (name) formData.append('name', name)
  formData.append('auto_summarize', autoSummarize.toString())

  const response = await client.post(`/api/v1/contexts/${contextId}/documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getContextDocuments = async (contextId: string) => {
  const response = await client.get(`/api/v1/contexts/${contextId}/documents`)
  return response.data.documents || []
}

export const summarizeDocument = async (documentId: string, style: string = 'concise') => {
  const response = await client.post(`/api/v1/contexts/documents/${documentId}/summarize?style=${style}`)
  return response.data
}

export const deleteContextDocument = async (documentId: string) => {
  const response = await client.delete(`/api/v1/contexts/documents/${documentId}`)
  return response.data
}

// Data Explorer API
export const getExplorerDatabases = async () => {
  const response = await client.get('/api/v1/data-explorer/databases')
  return response.data
}

export const getExplorerHealth = async (dbId: string = 'default') => {
  const response = await client.get(`/api/v1/data-explorer/health?db_id=${dbId}`)
  return response.data
}

export const getExplorerSchemas = async (dbId: string = 'default') => {
  const response = await client.get(`/api/v1/data-explorer/schemas?db_id=${dbId}`)
  return response.data
}

export const getExplorerTables = async (schema: string = 'public', dbId: string = 'default') => {
  const response = await client.get(`/api/v1/data-explorer/tables?schema=${schema}&db_id=${dbId}`)
  return response.data
}

export const getExplorerTableColumns = async (schema: string, table: string, dbId: string = 'default') => {
  const response = await client.get(`/api/v1/data-explorer/tables/${schema}/${table}/columns?db_id=${dbId}`)
  return response.data
}

export const getExplorerTableRows = async (
  schema: string,
  table: string,
  page: number = 1,
  pageSize: number = 50,
  dbId: string = 'default'
) => {
  const response = await client.get(
    `/api/v1/data-explorer/tables/${schema}/${table}/rows?page=${page}&page_size=${pageSize}&db_id=${dbId}`
  )
  return response.data
}

export const getExplorerTableSummary = async (schema: string, table: string, dbId: string = 'default') => {
  const response = await client.get(`/api/v1/data-explorer/tables/${schema}/${table}/summary?db_id=${dbId}`)
  return response.data
}

export const executeExplorerQuery = async (
  sql: string,
  page: number = 1,
  pageSize: number = 100,
  dbId: string = 'default'
) => {
  const response = await client.post(`/api/v1/data-explorer/query?db_id=${dbId}`, {
    sql,
    page,
    page_size: pageSize,
  })
  return response.data
}

// NEX Collector API (localhost:8080)
const collectorClient = axios.create({
  baseURL: (import.meta as any).env?.VITE_COLLECTOR_API_URL || 'http://localhost:8080',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health check
export const checkCollectorHealth = async () => {
  const response = await collectorClient.get('/healthz')
  return response.data
}

// Context Docs API
export const listCollectorContexts = async () => {
  const response = await collectorClient.get('/v1/contexts/variants')
  return response.data || []
}

export const getCollectorContext = async (contextId: string) => {
  const response = await collectorClient.get(`/v1/contexts/${contextId}`)
  return response.data
}

export const getCollectorVariant = async (variantId: string) => {
  const response = await collectorClient.get(`/v1/contexts/variants/${variantId}`)
  return response.data
}

// Datasets API
export const listCollectorDatasets = async () => {
  const response = await collectorClient.get('/v1/datasets')
  return response.data || []
}

export const getCollectorDataset = async (datasetId: string) => {
  const response = await collectorClient.get(`/v1/datasets/${datasetId}`)
  return response.data
}

// Explorer API - query all tables
export const listExplorerTables = async () => {
  const response = await collectorClient.get('/v1/explorer/tables')
  return response.data.tables || []
}

export const queryTable = async (tableName: string, limit: number = 100, offset: number = 0) => {
  const response = await collectorClient.get(`/v1/explorer/tables/${tableName}`, {
    params: { limit, offset }
  })
  return response.data
}

export const getTableCount = async (tableName: string) => {
  const response = await collectorClient.get(`/v1/explorer/tables/${tableName}/count`)
  return response.data
}

// Distillation API
export const distillExamples = async (
  variantIds: string[],
  exampleType: 'instruction' | 'qa' | 'task',
  quotaPerVariant: number = 10,
  rules: Record<string, any> = {}
) => {
  const response = await collectorClient.post('/v1/datasets/distill/examples', {
    variant_ids: variantIds,
    example_type: exampleType,
    quota_per_variant: quotaPerVariant,
    rules
  })
  return response.data
}

export const buildDistilledDataset = async (
  name: string,
  version: string,
  kind: 'train' | 'eval' | 'synthetic' | 'finetune_pack',
  variantIds: string[],
  filters: Record<string, any> = {}
) => {
  const response = await collectorClient.post('/v1/datasets/distill/build', {
    name,
    version,
    kind,
    variant_ids: variantIds,
    filters
  })
  return response.data
}

// =====================================================================
// Chat API functions
// =====================================================================

export const createConversation = async (data: {
  title?: string
  provider: string
  model: string
  connection_id?: string
}) => {
  const response = await client.post('/api/v1/chat/conversations', data)
  return response.data
}

export const listConversations = async (skip: number = 0, limit: number = 50, provider?: string) => {
  const response = await client.get('/api/v1/chat/conversations', {
    params: { skip, limit, provider }
  })
  return response.data
}

export const getConversation = async (conversationId: string) => {
  const response = await client.get(`/api/v1/chat/conversations/${conversationId}`)
  return response.data
}

export const updateConversation = async (conversationId: string, data: {
  title?: string
  metadata?: any
}) => {
  const response = await client.patch(`/api/v1/chat/conversations/${conversationId}`, data)
  return response.data
}

export const deleteConversation = async (conversationId: string) => {
  const response = await client.delete(`/api/v1/chat/conversations/${conversationId}`)
  return response.data
}

export const sendMessage = async (conversationId: string, data: {
  content: string
  provider?: string
  model?: string
  connection_id?: string
  stream?: boolean
}) => {
  const response = await client.post(`/api/v1/chat/conversations/${conversationId}/messages`, data)
  
  // If streaming, return URL for EventSource
  if (data.stream) {
    const url = `${API_BASE_URL}/api/v1/chat/conversations/${conversationId}/messages`
    return { url, ...response.data }
  }
  
  return response.data
}

// AI Analysis API
export const runAIAnalysis = async (request: {
  tables: Array<{ schema: string; table: string }>
  analysis_types: string[]
  provider: string
  model: string
  db_id?: string
  context?: string
}) => {
  const response = await client.post('/api/v1/data-explorer/analyze', request)
  return response.data
}

export const listAnalyses = async (dbId?: string, limit: number = 50) => {
  const params = new URLSearchParams()
  if (dbId) params.append('db_id', dbId)
  params.append('limit', limit.toString())
  
  const response = await client.get(`/api/v1/data-explorer/analyses?${params}`)
  return response.data
}

export const getAnalysis = async (analysisId: string) => {
  const response = await client.get(`/api/v1/data-explorer/analyses/${analysisId}`)
  return response.data
}

export const deleteAnalysis = async (analysisId: string) => {
  const response = await client.delete(`/api/v1/data-explorer/analyses/${analysisId}`)
  return response.data
}

export const updateAnalysis = async (
  analysisId: string,
  data: {
    name?: string
    description?: string
    tags?: string[]
  }
) => {
  const response = await client.patch(`/api/v1/data-explorer/analyses/${analysisId}`, data)
  return response.data
}

// Data Analysis Jobs API
export const createAnalysisJob = async (data: {
  name: string
  tables: Array<{ schema: string; table: string }>
  analysis_types: string[]
  provider: string
  model: string
  db_id?: string
  context?: string
  tags?: string[]
}) => {
  const response = await client.post('/api/v1/data-analysis/jobs', data)
  return response.data
}

export const listAnalysisJobs = async (params?: {
  db_id?: string
  status?: string
  limit?: number
}) => {
  const queryParams = new URLSearchParams()
  if (params?.db_id) queryParams.append('db_id', params.db_id)
  if (params?.status) queryParams.append('status', params.status)
  if (params?.limit) queryParams.append('limit', params.limit.toString())
  
  const response = await client.get(`/api/v1/data-analysis/jobs?${queryParams}`)
  return response.data
}

export const getAnalysisJob = async (jobId: string) => {
  const response = await client.get(`/api/v1/data-analysis/jobs/${jobId}`)
  return response.data
}

export const getJobStatus = async (jobId: string) => {
  const response = await client.get(`/api/v1/data-analysis/jobs/${jobId}/status`)
  return response.data
}

export const cancelAnalysisJob = async (jobId: string) => {
  const response = await client.post(`/api/v1/data-analysis/jobs/${jobId}/cancel`)
  return response.data
}

export const deleteAnalysisJob = async (jobId: string) => {
  const response = await client.delete(`/api/v1/data-analysis/jobs/${jobId}`)
  return response.data
}

// AI Models API
export const getAvailableModels = async () => {
  const response = await client.get('/api/v1/ai-models/available')
  return response.data
}

export const checkApiKeys = async () => {
  const response = await client.get('/api/v1/ai-models/check-keys')
  return response.data
}

// Prompt Recipes API
export const fetchPromptRecipes = async (actionType?: string) => {
  const params = actionType ? `?action_type=${encodeURIComponent(actionType)}` : ''
  const response = await client.get(`/api/v1/data-explorer/prompt-recipes${params}`)
  return response.data
}

export const createPromptRecipe = async (recipe: {
  name: string
  action_type: string
  default_provider?: string
  default_model?: string
  system_message: string
  user_template: string
  metadata?: any
}) => {
  const response = await client.post('/api/v1/data-explorer/prompt-recipes/', recipe)
  return response.data
}

export const getPromptRecipe = async (recipeId: number) => {
  const response = await client.get(`/api/v1/data-explorer/prompt-recipes/${recipeId}`)
  return response.data
}

export const updatePromptRecipe = async (recipeId: number, updates: any) => {
  const response = await client.patch(`/api/v1/data-explorer/prompt-recipes/${recipeId}`, updates)
  return response.data
}

export const clonePromptRecipe = async (recipeId: number) => {
  const response = await client.post(`/api/v1/data-explorer/prompt-recipes/${recipeId}/clone`)
  return response.data
}

export const deletePromptRecipe = async (recipeId: number, force: boolean = false) => {
  const params = force ? '?force=true' : ''
  const response = await client.delete(`/api/v1/data-explorer/prompt-recipes/${recipeId}${params}`)
  return response.data
}

// Data Dictionary API
export interface DictionaryEntry {
  id: number
  database_name: string
  schema_name: string
  table_name: string
  column_name: string
  version_number: number
  is_active: boolean
  version_notes?: string
  business_name?: string
  business_description?: string
  technical_description?: string
  data_type?: string
  examples?: string[]
  tags?: string[]
  source: string
  created_at: string
  updated_at: string
}

export const fetchDictionaryEntries = async (
  databaseName?: string,
  schemaName?: string,
  tableName?: string
): Promise<DictionaryEntry[]> => {
  const params = new URLSearchParams()
  if (databaseName) params.append('database_name', databaseName)
  if (schemaName) params.append('schema_name', schemaName)
  if (tableName) params.append('table_name', tableName)
  
  const queryString = params.toString()
  const url = queryString 
    ? `/api/v1/data-dictionary?${queryString}` 
    : '/api/v1/data-dictionary'
  
  const response = await client.get(url)
  return response.data
}

export const getDictionaryEntry = async (entryId: number): Promise<DictionaryEntry> => {
  const response = await client.get(`/api/v1/data-dictionary/${entryId}`)
  return response.data
}

export const updateDictionaryEntry = async (
  entryId: number,
  update: {
    business_name?: string
    business_description?: string
    technical_description?: string
    tags?: string[]
    create_new_version?: boolean
    version_notes?: string
  }
): Promise<DictionaryEntry> => {
  const response = await client.patch(`/api/v1/data-dictionary/${entryId}`, update)
  return response.data
}

export const getColumnVersions = async (
  databaseName: string,
  schemaName: string,
  tableName: string,
  columnName: string
): Promise<DictionaryEntry[]> => {
  const response = await client.get(
    `/api/v1/data-dictionary/versions/${databaseName}/${schemaName}/${tableName}/${columnName}`
  )
  return response.data
}

export const activateDictionaryVersion = async (entryId: number): Promise<DictionaryEntry> => {
  const response = await client.post(`/api/v1/data-dictionary/activate/${entryId}`)
  return response.data
}

