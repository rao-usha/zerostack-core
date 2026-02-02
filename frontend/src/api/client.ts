import axios from 'axios'

// Always use empty string for baseURL - this makes requests relative to page origin
// Vite proxy will handle forwarding /api/* requests to the backend
// DO NOT use import.meta.env.VITE_API_URL - it must be empty for proxy to work
const client = axios.create({
  baseURL: '',  // Empty string = relative URLs = works with Vite proxy
  headers: {
    'Content-Type': 'application/json',
  },
})

// Ensure baseURL stays empty - guard against any accidental modification
if (client.defaults.baseURL !== '') {
  console.error('[ERROR] axios baseURL was modified! Resetting to empty string.')
  client.defaults.baseURL = ''
}

// Debug interceptor to verify requests use correct URLs
client.interceptors.request.use((config) => {
  // Force relative URLs by ensuring baseURL is empty
  if (config.baseURL && config.baseURL !== '') {
    console.warn('[WARN] Request had non-empty baseURL, clearing it:', config.baseURL)
    config.baseURL = ''
  }

  console.log('[DEBUG] Request URL:', config.url)
  console.log('[DEBUG] Page origin:', window.location.origin)
  return config
})

export default client

// ========================================
// Lineage API
// ========================================

export const getLineage = async (entityType: string, entityId: string, params?: {
  direction?: 'upstream' | 'downstream' | 'both'
  maxDepth?: number
  includeColumns?: boolean
}) => {
  const response = await client.get(`/api/v1/lineage/${entityType}/${entityId}`, { params })
  return response.data
}

export const getLineageSummary = async (entityType: string, entityId: string) => {
  const response = await client.get(`/api/v1/lineage/${entityType}/${entityId}/summary`)
  return response.data
}

export const getUpstreamLineage = async (entityType: string, entityId: string, maxDepth?: number) => {
  const response = await client.get(`/api/v1/lineage/${entityType}/${entityId}/upstream`, {
    params: { max_depth: maxDepth }
  })
  return response.data
}

export const getDownstreamLineage = async (entityType: string, entityId: string, maxDepth?: number) => {
  const response = await client.get(`/api/v1/lineage/${entityType}/${entityId}/downstream`, {
    params: { max_depth: maxDepth }
  })
  return response.data
}

export const analyzeImpact = async (entityType: string, entityId: string) => {
  const response = await client.get(`/api/v1/lineage/${entityType}/${entityId}/impact`)
  return response.data
}

// Advanced Lineage API functions
export const parseColumnLineage = async (sql: string) => {
  const response = await client.post('/api/v1/lineage/parse-sql/column-level', { sql })
  return response.data
}

export const analyzeMLQuery = async (sql: string) => {
  const response = await client.post('/api/v1/lineage/analyze-ml-query', { sql })
  return response.data
}

export const discoverPipelines = async (minStages: number = 3, timeWindowHours?: number) => {
  const response = await client.get('/api/v1/lineage/pipelines', {
    params: { min_stages: minStages, time_window_hours: timeWindowHours }
  })
  return response.data
}

export const findQueryChains = async (tableName: string, maxDepth: number = 10, timeWindowHours?: number) => {
  const response = await client.get(`/api/v1/lineage/query-chains/${tableName}`, {
    params: { max_depth: maxDepth, time_window_hours: timeWindowHours }
  })
  return response.data
}

export const trackLineage = async (data: {
  source_type: string
  source_id: string
  source_name: string
  target_type: string
  target_id: string
  target_name: string
  edge_type: string
  transform_sql?: string
  transform_config?: any
  source_row_count?: number
  target_row_count?: number
}) => {
  const response = await client.post('/api/v1/lineage/track', data)
  return response.data
}

// ========================================
// Datasets API (File Upload)
// ========================================

export interface UploadedDataset {
  id: string
  name: string
  description?: string
  status: 'active' | 'processing' | 'error' | 'archived'
  source_type: 'upload' | 'notebook' | 'connection' | 'synthetic'
  schema: { columns: Array<{ name: string; dtype: string; nullable: boolean; stats?: any }> }
  row_count?: number
  column_count?: number
  size_bytes?: number
  storage_uri?: string
  storage_format: string
  current_version_number: number
  tags: string[]
  org_id: string
  created_at: string
  updated_at: string
}

export interface DatasetVersion {
  id: string
  dataset_id: string
  version_number: number
  sha256: string
  storage_uri: string
  storage_format: string
  original_filename?: string
  row_count?: number
  column_count?: number
  size_bytes?: number
  schema: any
  quality_profile: any
  created_at: string
  notes?: string
}

export interface DatasetUploadResponse {
  dataset: UploadedDataset
  version: DatasetVersion
  message: string
}

export const uploadDatasetFile = async (
  file: File,
  name: string,
  description?: string,
  tags?: string,
  orgId: string = 'default',
  onProgress?: (progress: number) => void
): Promise<DatasetUploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', name)
  if (description) formData.append('description', description)
  if (tags) formData.append('tags', tags)
  formData.append('org_id', orgId)

  const response = await client.post('/api/v1/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress ? (e) => onProgress(Math.round((e.loaded * 100) / (e.total || 1))) : undefined,
  })
  return response.data
}

export const listUploadedDatasets = async (params?: {
  status?: string
  source_type?: string
  org_id?: string
  search?: string
  page?: number
  page_size?: number
}): Promise<{ items: UploadedDataset[]; total: number; page: number; page_size: number }> => {
  const response = await client.get('/api/v1/datasets', { params })
  return response.data
}

export const getUploadedDataset = async (datasetId: string): Promise<UploadedDataset> => {
  const response = await client.get(`/api/v1/datasets/${datasetId}`)
  return response.data
}

export const updateUploadedDataset = async (
  datasetId: string,
  data: { name?: string; description?: string; tags?: string[]; status?: string }
): Promise<UploadedDataset> => {
  const response = await client.patch(`/api/v1/datasets/${datasetId}`, data)
  return response.data
}

export const deleteUploadedDataset = async (datasetId: string, deleteStorage: boolean = true): Promise<void> => {
  await client.delete(`/api/v1/datasets/${datasetId}`, { params: { delete_storage: deleteStorage } })
}

export const listDatasetVersions = async (datasetId: string): Promise<{ items: DatasetVersion[]; total: number }> => {
  const response = await client.get(`/api/v1/datasets/${datasetId}/versions`)
  return response.data
}

export const uploadNewVersion = async (
  datasetId: string,
  file: File,
  notes?: string
): Promise<DatasetVersion> => {
  const formData = new FormData()
  formData.append('file', file)
  if (notes) formData.append('notes', notes)

  const response = await client.post(`/api/v1/datasets/${datasetId}/versions`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const previewUploadedDataset = async (
  datasetId: string,
  version?: number,
  limit: number = 100
): Promise<{ columns: string[]; rows: any[]; total_rows: number; preview_rows: number }> => {
  const response = await client.get(`/api/v1/datasets/${datasetId}/preview`, {
    params: { version, limit },
  })
  return response.data
}

export const getDatasetDownloadUrl = async (
  datasetId: string,
  version?: number,
  format: 'csv' | 'parquet' = 'csv',
  expiresIn: number = 3600
): Promise<{ download_url: string; expires_in: number; format: string }> => {
  const response = await client.get(`/api/v1/datasets/${datasetId}/download`, {
    params: { version, format, expires_in: expiresIn },
  })
  return response.data
}

// Legacy API functions (kept for backward compatibility)
export const uploadDataset = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await client.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
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
  state: string  // "draft", "pending_approval", "published"
  version_notes?: string
  business_name?: string
  business_description?: string
  technical_description?: string
  data_type?: string
  examples?: string[]
  tags?: string[]
  source: string
  data_source?: string
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
    ? `/api/v1/data-dictionary/?${queryString}`
    : '/api/v1/data-dictionary/'

  // Use native fetch to bypass any axios configuration issues
  console.log('[fetchDictionaryEntries] Fetching URL:', url)
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  return response.json()
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

// Workflow actions
export const submitForApproval = async (entryId: number): Promise<DictionaryEntry> => {
  const response = await client.post(`/api/v1/data-dictionary/${entryId}/submit-for-approval`)
  return response.data
}

export const approveEntry = async (entryId: number, notes?: string): Promise<DictionaryEntry> => {
  const response = await client.post(`/api/v1/data-dictionary/${entryId}/approve`, { notes })
  return response.data
}

export const rejectEntry = async (entryId: number, notes?: string): Promise<DictionaryEntry> => {
  const response = await client.post(`/api/v1/data-dictionary/${entryId}/reject`, { notes })
  return response.data
}

export const publishEntry = async (entryId: number, notes?: string): Promise<DictionaryEntry> => {
  const response = await client.post(`/api/v1/data-dictionary/${entryId}/publish`, { notes })
  return response.data
}

// ==================== Data Source Summary API ====================

export interface DataSourceSummary {
  source_name: string
  table_count: number
  column_count: number
  documented_columns: number
  documentation_percentage: number
  schemas: string[]
  sample_tables: string[]
  last_updated?: string
  description?: string
}

export const getDataSources = async (databaseName?: string): Promise<DataSourceSummary[]> => {
  const params = databaseName ? { database_name: databaseName } : {}
  const response = await client.get('/api/v1/data-dictionary/sources', { params })
  return response.data
}

export const quickAnalyzeSource = async (sourceName: string, databaseName?: string) => {
  const params = databaseName ? { database_name: databaseName } : {}
  const response = await client.post(
    `/api/v1/data-dictionary/sources/${encodeURIComponent(sourceName)}/quick-analysis`,
    {},
    { params }
  )
  return response.data
}

export const recategorizeDataSources = async (databaseName?: string) => {
  const params = databaseName ? { database_name: databaseName } : {}
  const response = await client.post(
    '/api/v1/data-dictionary/recategorize',
    {},
    { params }
  )
  return response.data
}

// ==================== Dictionary Semantics API ====================

export interface DecisionContext {
  primary_decisions?: string[]
  secondary_decisions?: string[]
  consumers?: Array<{ role: string; team?: string; system?: string }>
  decision_frequency?: string
  downside_if_wrong?: string
  notes?: string
}

export interface SemanticGuarantees {
  invariants?: string[]
  temporal_behavior?: {
    freshness?: string
    backfill_expected?: boolean
    late_arriving_data?: boolean
  }
  aggregation_rules?: {
    allowed?: string[]
    forbidden?: string[]
  }
  known_failure_modes?: string[]
  pii?: {
    contains_pii?: boolean
    pii_types?: string[]
  }
  notes?: string
}

export interface ValidationState {
  confidence_score?: number
  confidence_sources?: string[]
  last_validated_at?: string
  validated_by?: string[]
  upstream_sources?: string[]
  downstream_usage?: string[]
  notes?: string
}

export interface DictionarySemantics {
  entry_id: string
  decision_context: DecisionContext
  semantic_guarantees: SemanticGuarantees
  validation_state: ValidationState
  updated_at: string
}

export interface DictionaryGrain {
  id: string
  entry_id: string
  entity: string
  primary_key?: string[]
  time_grain?: string
  natural_key?: string[]
  notes?: string
  created_at: string
  updated_at: string
}

export interface DictionaryRelationship {
  id: string
  relationship_kind: string
  status: string
  left_entry_id: string
  right_entry_id: string
  left_ref?: any
  right_ref?: any
  relationship_type: string
  cardinality?: string
  match_rate_sample?: number
  left_null_rate?: number
  right_unique?: boolean
  suggested_join_sql?: string
  grain_compatibility?: any
  semantic_definition?: any
  confidence_score?: number
  created_by?: string
  created_at: string
  updated_at: string
}

export interface InferenceJob {
  id: string
  connection_id: string
  schema_name?: string
  status: string
  progress: number
  current_stage?: string
  relationships_found: number
  tables_scanned: number
  error_message?: string
  result_summary?: any
  created_at: string
  started_at?: string
  completed_at?: string
}

// Semantics
export const getSemantics = async (entryId: string): Promise<DictionarySemantics> => {
  const response = await client.get(`/api/v1/data-dictionary/entries/${entryId}/semantics`)
  return response.data
}

export const updateSemantics = async (
  entryId: string,
  data: {
    decision_context?: DecisionContext
    semantic_guarantees?: SemanticGuarantees
    validation_state?: ValidationState
    create_version?: boolean
  }
): Promise<DictionarySemantics> => {
  const response = await client.put(`/api/v1/data-dictionary/entries/${entryId}/semantics`, data)
  return response.data
}

// Grain
export const getGrain = async (entryId: string): Promise<DictionaryGrain | null> => {
  const response = await client.get(`/api/v1/data-dictionary/entries/${entryId}/grain`)
  return response.data
}

export const updateGrain = async (
  entryId: string,
  data: {
    entity: string
    primary_key?: string[]
    time_grain?: string
    natural_key?: string[]
    notes?: string
  }
): Promise<DictionaryGrain> => {
  const response = await client.put(`/api/v1/data-dictionary/entries/${entryId}/grain`, data)
  return response.data
}

// Relationships
export const listRelationships = async (params: {
  entry_id?: string
  database?: string
  schema?: string
  table?: string
  status?: string
  relationship_kind?: string
  limit?: number
  offset?: number
}): Promise<{ results: DictionaryRelationship[]; total: number; limit: number; offset: number }> => {
  const response = await client.get('/api/v1/data-dictionary/relationships', { params })
  return response.data
}

export const createRelationship = async (data: {
  relationship_kind: string
  left_entry_id: string
  right_entry_id: string
  relationship_type: string
  status?: string
  cardinality?: string
  left_ref?: any
  right_ref?: any
  grain_compatibility?: any
  semantic_definition?: any
  confidence_score?: number
  created_by?: string
}): Promise<DictionaryRelationship> => {
  const response = await client.post('/api/v1/data-dictionary/relationships', data)
  return response.data
}

export const updateRelationship = async (
  relationshipId: string,
  data: {
    cardinality?: string
    grain_compatibility?: any
    semantic_definition?: any
    confidence_score?: number
    suggested_join_sql?: string
    relationship_type?: string
  }
): Promise<DictionaryRelationship> => {
  const response = await client.patch(`/api/v1/data-dictionary/relationships/${relationshipId}`, data)
  return response.data
}

export const updateRelationshipStatus = async (
  relationshipId: string,
  status: string
): Promise<DictionaryRelationship> => {
  const response = await client.patch(`/api/v1/data-dictionary/relationships/${relationshipId}/status`, { status })
  return response.data
}

export const deleteRelationship = async (relationshipId: string, force: boolean = false): Promise<void> => {
  await client.delete(`/api/v1/data-dictionary/relationships/${relationshipId}`, { params: { force } })
}

// Inference
export const startInferenceJob = async (data: {
  connection_id?: string
  schema?: string
  include_tables?: string[]
  exclude_tables?: string[]
  max_samples?: number
}): Promise<InferenceJob> => {
  const response = await client.post('/api/v1/data-dictionary/relationships/infer', data)
  return response.data
}

export const getInferenceJob = async (jobId: string): Promise<InferenceJob> => {
  const response = await client.get(`/api/v1/data-dictionary/relationships/infer/${jobId}`)
  return response.data
}

// Context Blob
export const getContextBlob = async (
  entryId: string,
  includeRelationships: boolean = true,
  maxRelationships: number = 10
): Promise<any> => {
  const response = await client.get(`/api/v1/data-dictionary/entries/${entryId}/context-blob`, {
    params: { include_relationships: includeRelationships, max_relationships: maxRelationships }
  })
  return response.data
}

// --- Files API ---

export interface FileLocation {
  id: string
  name: string
  type: string
  local_path: string | null
  is_active: boolean
  last_scanned_at: string | null
  created_at: string
  updated_at: string
  file_count: number
}

export interface FileAsset {
  id: string
  location_id: string
  location_name: string
  relative_path: string
  file_name: string
  ext: string
  mime_type: string | null
  last_seen_at: string
  created_at: string
  latest_version: FileVersion | null
  version_count: number
  has_changes: boolean
}

export interface FileVersion {
  id: string
  file_asset_id: string
  detected_at: string
  modified_at: string
  size_bytes: number
  content_hash: string
  row_count_estimate: number | null
  table_count: number
}

export interface ColumnSchema {
  name: string
  data_type: string
  nullable: boolean
  example_values: string[] | null
}

export interface FileTable {
  id: string
  file_version_id: string
  table_name: string
  row_count: number
  column_count: number
  schema: ColumnSchema[]
  sample_data: any[][] | null
  is_published: boolean
  published_dataset_id: string | null
  created_at: string
}

export interface FileAssetDetail {
  asset: FileAsset
  versions: FileVersion[]
  latest_tables: FileTable[]
}

// File Locations
export const createFileLocation = async (
  name: string,
  type: 'local' | 'gdrive',
  local_path?: string,
  gdrive_folder_id?: string,
  gdrive_include_shared_drives?: boolean,
  external_account_id?: string
) => {
  const response = await client.post('/api/files/locations', {
    name,
    type,
    local_path,
    gdrive_folder_id,
    gdrive_include_shared_drives,
    external_account_id,
  })
  return response.data as FileLocation
}

export const listFileLocations = async () => {
  const response = await client.get('/api/files/locations')
  return response.data as FileLocation[]
}

export const getFileLocation = async (locationId: string) => {
  const response = await client.get(`/api/files/locations/${locationId}`)
  return response.data as FileLocation
}

export const updateFileLocation = async (
  locationId: string, 
  updates: { name?: string; local_path?: string; is_active?: boolean }
) => {
  const response = await client.patch(`/api/files/locations/${locationId}`, updates)
  return response.data as FileLocation
}

export const deleteFileLocation = async (locationId: string) => {
  await client.delete(`/api/files/locations/${locationId}`)
}

export const scanFileLocation = async (locationId: string) => {
  const response = await client.post(`/api/files/locations/${locationId}/scan`)
  return response.data
}

// File Assets
export const listFileAssets = async (locationId?: string) => {
  const params = locationId ? { location_id: locationId } : {}
  const response = await client.get('/api/files/assets', { params })
  return response.data as FileAsset[]
}

export const getFileAssetDetail = async (assetId: string) => {
  const response = await client.get(`/api/files/assets/${assetId}`)
  return response.data as FileAssetDetail
}

// Table Preview
export const previewFileTable = async (
  tableId: string,
  limit: number = 100,
  offset: number = 0
) => {
  const response = await client.post('/api/files/tables/preview', {
    table_id: tableId,
    limit,
    offset
  })
  return response.data
}

// Publish Table
export const publishFileTable = async (
  tableId: string,
  datasetName?: string,
  description?: string
) => {
  const response = await client.post(`/api/files/tables/${tableId}/publish`, {
    table_id: tableId,
    dataset_name: datasetName,
    description
  })
  return response.data
}

// Google Drive OAuth
export interface ExternalAccount {
  id: string
  provider: string
  account_email: string
  scopes: string[]
  token_expiry: string | null
  created_at: string
}

export const getGDriveAuthUrl = async () => {
  const response = await client.get('/api/files/gdrive/auth/url')
  return response.data as { auth_url: string; state: string }
}

export const listGDriveAccounts = async () => {
  const response = await client.get('/api/files/gdrive/accounts')
  return response.data as ExternalAccount[]
}

// ========================================
// Settings API
// ========================================

export interface SettingCategory {
  category: string
  display_name: string
  description: string
  icon?: string
  total_settings: number
  configured_count: number
}

export interface Setting {
  id: string | null
  category: string
  key: string
  value_masked: string | null
  is_secret: boolean
  description: string | null
  display_name: string | null
  has_value: boolean
  updated_at: string | null
  updated_by: string | null
}

export interface SettingTestResult {
  key: string
  valid: boolean
  message: string
  details?: Record<string, any>
}

// List all setting categories
export const getSettingCategories = async (): Promise<{ categories: SettingCategory[] }> => {
  const response = await client.get('/api/v1/settings')
  return response.data
}

// List settings in a category
export const getSettingsByCategory = async (category: string): Promise<{ settings: Setting[]; total: number }> => {
  const response = await client.get(`/api/v1/settings/${category}`)
  return response.data
}

// Get a single setting
export const getSetting = async (category: string, key: string): Promise<Setting> => {
  const response = await client.get(`/api/v1/settings/${category}/${key}`)
  return response.data
}

// Update a setting
export const updateSetting = async (
  category: string,
  key: string,
  value: string,
  description?: string
): Promise<Setting> => {
  const response = await client.put(`/api/v1/settings/${category}/${key}`, {
    value,
    description
  })
  return response.data
}

// Delete (clear) a setting
export const clearSetting = async (category: string, key: string): Promise<void> => {
  await client.delete(`/api/v1/settings/${category}/${key}`)
}

// Test a setting (e.g., API key validation)
export const testSetting = async (category: string, key: string): Promise<SettingTestResult> => {
  const response = await client.post(`/api/v1/settings/test/${category}/${key}`)
  return response.data
}

// Test all settings in a category
export const testCategorySettings = async (category: string): Promise<{ results: Record<string, { valid: boolean; message: string }> }> => {
  const response = await client.post(`/api/v1/settings/test/${category}`)
  return response.data
}

// Seed settings from environment variables
export const seedSettingsFromEnv = async (overwrite: boolean = false): Promise<{ seeded: string[]; skipped: string[]; seeded_count: number; skipped_count: number }> => {
  const response = await client.post(`/api/v1/settings/seed-from-env?overwrite=${overwrite}`)
  return response.data
}

// ========================================
// Ontology API
// ========================================

export const createOntology = async (
  orgId: string,
  name: string,
  description?: string,
  actor: string = 'user'
) => {
  const response = await client.post('/api/v1/ontology/', {
    org_id: orgId,
    name,
    description,
    actor
  })
  return response.data
}

export const listOntologies = async (orgId: string = 'demo') => {
  try {
    const response = await client.get('/api/v1/ontology/', {
      params: { org_id: orgId }
    })
    return response.data
  } catch {
    return []
  }
}

export const getOntology = async (ontologyId: string) => {
  const response = await client.get(`/api/v1/ontology/${ontologyId}`)
  return response.data
}

export const addOntologyTerms = async (
  ontologyId: string,
  terms: Array<{term: string, definition?: string, metadata?: any}>,
  actor: string = 'user'
) => {
  const response = await client.post(`/api/v1/ontology/${ontologyId}/terms`, {
    items: terms,
    actor
  })
  return response.data
}

export const addOntologyRelations = async (
  ontologyId: string,
  relations: Array<{src_term: string, rel_type: string, dst_term: string, metadata?: any}>,
  actor: string = 'user'
) => {
  const response = await client.post(`/api/v1/ontology/${ontologyId}/relations`, {
    items: relations,
    actor
  })
  return response.data
}

export const publishOntologyVersion = async (
  ontologyId: string,
  changeSummary?: string,
  actor: string = 'user'
) => {
  const response = await client.post(`/api/v1/ontology/${ontologyId}/publish`, {
    change_summary: changeSummary,
    actor
  })
  return response.data
}

export const getOntologyDiff = async (ontologyId: string) => {
  const response = await client.get(`/api/v1/ontology/${ontologyId}/diff`)
  return response.data
}

// AI-assisted ontology helpers (future integration with MCP tools)
export const proposeOntologyTerms = async (prompt: string, count: number = 20) => {
  // This will call the AI MCP tool when we integrate it
  // For now, return mock data or call backend endpoint if available
  return {
    items: []
  }
}

// ========================================
// Query Workbench API
// ========================================

export interface QueryParameter {
  name: string
  type: string
  default?: string
  description?: string
}

export interface SavedQuery {
  id: string
  name: string
  description?: string
  sql: string
  db_id: string
  folder?: string
  tags?: string[]
  parameters?: QueryParameter[]
  is_public: boolean
  created_by?: string
  schedule_cron?: string
  schedule_enabled: boolean
  cache_ttl_seconds?: number
  run_count: number
  last_run_at?: string
  avg_execution_time_ms?: number
  created_at: string
  updated_at: string
}

export interface SavedQueryListItem {
  id: string
  name: string
  description?: string
  db_id: string
  folder?: string
  tags?: string[]
  is_public: boolean
  created_by?: string
  run_count: number
  last_run_at?: string
  avg_execution_time_ms?: number
  created_at: string
}

export interface QueryExecution {
  id: string
  saved_query_id?: string
  sql_snapshot: string
  db_id: string
  parameters_used?: Record<string, any>
  status: string
  started_at: string
  finished_at?: string
  execution_time_ms?: number
  row_count?: number
  column_count?: number
  result_preview?: { columns: string[]; rows: any[][] }
  error_message?: string
  error_code?: string
  executed_by?: string
  source: string
}

export interface QueryResult {
  execution_id: string
  columns: string[]
  rows: any[][]
  total_rows: number
  execution_time_ms: number
  page: number
  page_size: number
}

export interface FolderInfo {
  name: string
  query_count: number
}

// List saved queries
export const listSavedQueries = async (params?: {
  db_id?: string
  folder?: string
  tags?: string
  search?: string
  is_public?: boolean
  page?: number
  page_size?: number
}): Promise<{ queries: SavedQueryListItem[]; total: number; page: number; page_size: number }> => {
  const response = await client.get('/api/v1/data-explorer/workbench/queries', { params })
  return response.data
}

// Get a saved query
export const getSavedQuery = async (queryId: string): Promise<SavedQuery> => {
  const response = await client.get(`/api/v1/data-explorer/workbench/queries/${queryId}`)
  return response.data
}

// Create a saved query
export const createSavedQuery = async (data: {
  name: string
  sql: string
  db_id?: string
  description?: string
  folder?: string
  tags?: string[]
  parameters?: QueryParameter[]
  is_public?: boolean
}): Promise<SavedQuery> => {
  const response = await client.post('/api/v1/data-explorer/workbench/queries', data)
  return response.data
}

// Update a saved query
export const updateSavedQuery = async (
  queryId: string,
  data: {
    name?: string
    sql?: string
    description?: string
    folder?: string
    tags?: string[]
    parameters?: QueryParameter[]
    is_public?: boolean
    schedule_cron?: string
    schedule_enabled?: boolean
    cache_ttl_seconds?: number
  }
): Promise<SavedQuery> => {
  const response = await client.put(`/api/v1/data-explorer/workbench/queries/${queryId}`, data)
  return response.data
}

// Delete a saved query
export const deleteSavedQuery = async (queryId: string): Promise<void> => {
  await client.delete(`/api/v1/data-explorer/workbench/queries/${queryId}`)
}

// Clone a saved query
export const cloneSavedQuery = async (queryId: string, newName: string): Promise<SavedQuery> => {
  const response = await client.post(
    `/api/v1/data-explorer/workbench/queries/${queryId}/clone?new_name=${encodeURIComponent(newName)}`
  )
  return response.data
}

// Execute a saved query
export const executeSavedQuery = async (
  queryId: string,
  data?: {
    parameters?: Record<string, any>
    page?: number
    page_size?: number
  }
): Promise<QueryResult> => {
  const response = await client.post(`/api/v1/data-explorer/workbench/queries/${queryId}/execute`, data || {})
  return response.data
}

// Execute an ad-hoc query
export const executeWorkbenchQuery = async (data: {
  sql: string
  db_id?: string
  parameters?: Record<string, any>
  page?: number
  page_size?: number
}): Promise<QueryResult> => {
  const response = await client.post('/api/v1/data-explorer/workbench/execute', data)
  return response.data
}

// Get query executions for a saved query
export const getQueryExecutions = async (
  queryId: string,
  limit: number = 50
): Promise<{ executions: QueryExecution[]; total: number }> => {
  const response = await client.get(`/api/v1/data-explorer/workbench/queries/${queryId}/executions`, {
    params: { limit }
  })
  return response.data
}

// Get recent executions
export const getRecentExecutions = async (params?: {
  db_id?: string
  status?: string
  limit?: number
}): Promise<{ executions: QueryExecution[]; total: number }> => {
  const response = await client.get('/api/v1/data-explorer/workbench/executions', { params })
  return response.data
}

// Get execution detail
export const getQueryExecution = async (executionId: string): Promise<QueryExecution> => {
  const response = await client.get(`/api/v1/data-explorer/workbench/executions/${executionId}`)
  return response.data
}

// Get folders
export const getQueryFolders = async (dbId?: string): Promise<FolderInfo[]> => {
  const params = dbId ? { db_id: dbId } : {}
  const response = await client.get('/api/v1/data-explorer/workbench/folders', { params })
  return response.data
}
