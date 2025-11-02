import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

