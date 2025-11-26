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

// Ontology API
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

