import axios from 'axios'

// In development, use relative URLs so Vite proxy handles routing to backend:8000
// In production, VITE_API_URL can be set to the actual backend URL
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || ''

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

