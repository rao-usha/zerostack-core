/**
 * Custom hook for Distillation Workbench state and data management.
 * Extracted from DistillationWorkbench.tsx for modularity.
 */
import { useState, useEffect, useCallback } from 'react'
import { useToast } from '../contexts/ToastContext'
import {
  Domain, Topic, TagItem, Task, Response, BankedItem, Comparison,
  ComparisonDetail, Statistics, ModelPreferences, SchemaDefinition,
  StructuredItem, Dataset, DatasetStats, ReviewQueue, ReviewItem,
  AvailableModel, NewTask, NewDataset, NewQueue, ViewMode
} from '../types/distillation'

export interface DistillationState {
  // Core data
  domains: Domain[]
  topics: Topic[]
  tags: TagItem[]
  tasks: Task[]
  responses: Response[]
  comparisons: Comparison[]
  statistics: Statistics | null
  modelPreferences: ModelPreferences | null

  // View state
  viewMode: ViewMode
  loading: boolean
  error: string | null

  // Chat state
  chatMessage: string
  selectedModels: string[]
  chatResponses: Response[]
  chatLoading: boolean
  streamingStatus: string
  streamingContent: Record<string, string>
  activeModel: string | null

  // Search/Filter state
  searchQuery: string
  filterProvider: string

  // Tagging state
  tagModalOpen: boolean
  tagResponseId: string | null
  newTagName: string

  // Comparison state
  selectedComparison: ComparisonDetail | null
  comparisonLoading: boolean
  blindMode: boolean
  selectedWinner: string | null

  // Structuring state
  schemas: SchemaDefinition[]
  bankedItems: BankedItem[]
  structuredItems: StructuredItem[]
  selectedBanked: BankedItem | null
  selectedSchema: string
  structureModalOpen: boolean
  structuredData: Record<string, any>
  extracting: boolean

  // Dataset state
  datasets: Dataset[]
  selectedDataset: Dataset | null
  datasetStats: DatasetStats | null
  datasetItems: any[]
  createDatasetOpen: boolean
  newDataset: NewDataset

  // Review state
  reviewQueues: ReviewQueue[]
  selectedQueue: ReviewQueue | null
  reviewItems: ReviewItem[]
  currentReviewItem: { item: ReviewItem; response: Response } | null
  reviewNotes: string
  reviewScore: string
  createQueueOpen: boolean
  newQueue: NewQueue
  reviewLoading: boolean

  // Model selection state
  availableModels: AvailableModel[]
  apiKeys: Record<string, boolean>
  loadingModels: boolean

  // Task creation state
  createTaskOpen: boolean
  newTask: NewTask
  taskLoading: boolean
}

export interface DistillationActions {
  setViewMode: (mode: ViewMode) => void
  setChatMessage: (message: string) => void
  setSelectedModels: (models: string[]) => void
  setSearchQuery: (query: string) => void
  setFilterProvider: (provider: string) => void
  setTagModalOpen: (open: boolean) => void
  setTagResponseId: (id: string | null) => void
  setNewTagName: (name: string) => void
  setBlindMode: (blind: boolean) => void
  setSelectedWinner: (winner: string | null) => void
  setSelectedBanked: (banked: BankedItem | null) => void
  setSelectedSchema: (schema: string) => void
  setStructureModalOpen: (open: boolean) => void
  setStructuredData: (data: Record<string, any>) => void
  setSelectedDataset: (dataset: Dataset | null) => void
  setCreateDatasetOpen: (open: boolean) => void
  setNewDataset: (dataset: NewDataset) => void
  setSelectedQueue: (queue: ReviewQueue | null) => void
  setReviewNotes: (notes: string) => void
  setReviewScore: (score: string) => void
  setCreateQueueOpen: (open: boolean) => void
  setNewQueue: (queue: NewQueue) => void
  setCreateTaskOpen: (open: boolean) => void
  setNewTask: (task: NewTask) => void
  setError: (error: string | null) => void
  setDatasetStats: (stats: DatasetStats | null) => void
  setDatasetItems: (items: any[]) => void
  setReviewItems: (items: ReviewItem[]) => void
  setCurrentReviewItem: (item: { item: ReviewItem; response: Response } | null) => void
  setSelectedComparison: (comp: ComparisonDetail | null) => void

  // Data loading
  refreshAll: () => void
  loadResponses: () => Promise<void>
  loadComparisons: () => Promise<void>
  loadStatistics: () => Promise<void>
  loadBanked: () => Promise<void>
  loadStructured: () => Promise<void>
  loadDatasets: () => Promise<void>
  loadReviewQueues: () => Promise<void>
  loadReviewItems: (queueId: string) => Promise<void>
  loadComparisonDetails: (comparisonId: string) => Promise<void>
  loadDatasetDetails: (datasetId: string) => Promise<void>
  searchResponses: () => Promise<void>

  // Actions
  handleChat: () => Promise<void>
  handleBankResponse: (responseId: string) => Promise<void>
  handleDeleteResponse: (responseId: string) => Promise<void>
  handleUpdateResponse: (responseId: string, updates: { domain_id?: string | null; topic_id?: string | null; quality_rating?: number | null }) => Promise<void>
  handleAddTags: () => Promise<void>
  handleSubmitVote: () => Promise<void>
  handleLLMExtract: (bankedId: string, schemaName: string) => Promise<void>
  handleSaveStructured: () => Promise<void>
  handleCreateDataset: () => Promise<void>
  handleAddToDataset: (datasetId: string, bankedId?: string, structuredId?: string) => Promise<void>
  handleExportDataset: (datasetId: string, format: 'jsonl' | 'csv' | 'alpaca') => Promise<void>
  handleCreateQueue: () => Promise<void>
  handleAutoPopulateQueue: (queueId: string) => Promise<void>
  handleSubmitReview: (action: string) => Promise<void>
  handleExportQueue: (queueId: string, format: string) => Promise<void>
  getNextReviewItem: (queueId: string) => Promise<void>
  handleCreateTask: () => Promise<void>
}

export function useDistillation(): [DistillationState, DistillationActions] {
  const toast = useToast()

  // Core data state
  const [domains, setDomains] = useState<Domain[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [tags, setTags] = useState<TagItem[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [responses, setResponses] = useState<Response[]>([])
  const [comparisons, setComparisons] = useState<Comparison[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [modelPreferences, setModelPreferences] = useState<ModelPreferences | null>(null)

  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('chat')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Chat state
  const [chatMessage, setChatMessage] = useState('')
  const [selectedModels, setSelectedModels] = useState<string[]>(['gpt-4o'])
  const [chatResponses, setChatResponses] = useState<Response[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  const [streamingStatus, setStreamingStatus] = useState('')
  const [streamingContent, setStreamingContent] = useState<Record<string, string>>({})
  const [activeModel, setActiveModel] = useState<string | null>(null)

  // Search/Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [filterProvider, setFilterProvider] = useState('')
  const [filterBanked] = useState<boolean | null>(null)
  const [selectedTagFilter] = useState<string[]>([])

  // Tagging state
  const [tagModalOpen, setTagModalOpen] = useState(false)
  const [tagResponseId, setTagResponseId] = useState<string | null>(null)
  const [newTagName, setNewTagName] = useState('')

  // Comparison state
  const [selectedComparison, setSelectedComparison] = useState<ComparisonDetail | null>(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  const [blindMode, setBlindMode] = useState(false)
  const [selectedWinner, setSelectedWinner] = useState<string | null>(null)

  // Structuring state
  const [schemas, setSchemas] = useState<SchemaDefinition[]>([])
  const [bankedItems, setBankedItems] = useState<BankedItem[]>([])
  const [structuredItems, setStructuredItems] = useState<StructuredItem[]>([])
  const [selectedBanked, setSelectedBanked] = useState<BankedItem | null>(null)
  const [selectedSchema, setSelectedSchema] = useState('')
  const [structureModalOpen, setStructureModalOpen] = useState(false)
  const [structuredData, setStructuredData] = useState<Record<string, any>>({})
  const [extracting, setExtracting] = useState(false)

  // Dataset state
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [datasetStats, setDatasetStats] = useState<DatasetStats | null>(null)
  const [datasetItems, setDatasetItems] = useState<any[]>([])
  const [createDatasetOpen, setCreateDatasetOpen] = useState(false)
  const [newDataset, setNewDataset] = useState<NewDataset>({ name: '', version: '1.0', description: '', dataset_type: 'training' })

  // Review state
  const [reviewQueues, setReviewQueues] = useState<ReviewQueue[]>([])
  const [selectedQueue, setSelectedQueue] = useState<ReviewQueue | null>(null)
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([])
  const [currentReviewItem, setCurrentReviewItem] = useState<{ item: ReviewItem; response: Response } | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewScore, setReviewScore] = useState('')
  const [createQueueOpen, setCreateQueueOpen] = useState(false)
  const [newQueue, setNewQueue] = useState<NewQueue>({ name: '', description: '' })
  const [reviewLoading, setReviewLoading] = useState(false)

  // Model selection state
  const [availableModels, setAvailableModels] = useState<AvailableModel[]>([])
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({})
  const [loadingModels, setLoadingModels] = useState(true)

  // Task creation state
  const [createTaskOpen, setCreateTaskOpen] = useState(false)
  const [newTask, setNewTask] = useState<NewTask>({
    name: '', description: '', task_type: 'freeform', prompt_template: '',
    system_prompt: '', target_models: ['gpt-4o'], domain_id: '', topic_id: ''
  })
  const [taskLoading, setTaskLoading] = useState(false)

  // ============================================================================
  // Data Loading Functions
  // ============================================================================

  const loadAvailableModels = useCallback(async () => {
    setLoadingModels(true)
    try {
      const [modelsRes, keysRes] = await Promise.all([
        fetch('/api/v1/ai-models/available'),
        fetch('/api/v1/ai-models/check-keys')
      ])

      if (modelsRes.ok && keysRes.ok) {
        const modelsData = await modelsRes.json()
        const keysData = await keysRes.json()

        const models: AvailableModel[] = []
        for (const providerData of modelsData.providers) {
          for (const modelId of providerData.models) {
            models.push({ id: modelId, name: modelId, provider: providerData.provider })
          }
        }

        setAvailableModels(models)
        setApiKeys(keysData)

        const firstWithKey = models.find(m => keysData[m.provider])
        if (firstWithKey && selectedModels.length === 0) {
          setSelectedModels([firstWithKey.id])
        }
      }
    } catch (err) {
      console.error('Failed to load models:', err)
      setAvailableModels([
        { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
        { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', provider: 'anthropic' },
      ])
    } finally {
      setLoadingModels(false)
    }
  }, [selectedModels.length])

  const loadDomains = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/domains')
      if (res.ok) { const data = await res.json(); setDomains(data.domains || []) }
    } catch (err) { console.error('Failed to load domains:', err) }
  }, [])

  const loadTopics = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/topics')
      if (res.ok) { const data = await res.json(); setTopics(data.topics || []) }
    } catch (err) { console.error('Failed to load topics:', err) }
  }, [])

  const loadTags = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/tags')
      if (res.ok) { const data = await res.json(); setTags(data || []) }
    } catch (err) { console.error('Failed to load tags:', err) }
  }, [])

  const loadTasks = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/tasks')
      if (res.ok) { const data = await res.json(); setTasks(data.tasks || []) }
    } catch (err) { console.error('Failed to load tasks:', err) }
  }, [])

  const loadResponses = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/responses?limit=50')
      if (res.ok) { const data = await res.json(); setResponses(data.responses || []) }
    } catch (err) { console.error('Failed to load responses:', err) }
  }, [])

  const loadComparisons = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/comparisons?limit=20')
      if (res.ok) { const data = await res.json(); setComparisons(data.comparisons || []) }
    } catch (err) { console.error('Failed to load comparisons:', err) }
  }, [])

  const loadStatistics = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/statistics')
      if (res.ok) { const data = await res.json(); setStatistics(data) }
    } catch (err) { console.error('Failed to load statistics:', err) }
  }, [])

  const loadModelPreferences = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/model-preferences')
      if (res.ok) { const data = await res.json(); setModelPreferences(data) }
    } catch (err) { console.error('Failed to load model preferences:', err) }
  }, [])

  const loadSchemas = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/schemas')
      if (res.ok) { const data = await res.json(); setSchemas(data.schemas || []) }
    } catch (err) { console.error('Failed to load schemas:', err) }
  }, [])

  const loadBanked = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/banked?limit=100')
      if (res.ok) { const data = await res.json(); setBankedItems(data.banked || []) }
    } catch (err) { console.error('Failed to load banked:', err) }
  }, [])

  const loadStructured = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/structured?limit=100')
      if (res.ok) { const data = await res.json(); setStructuredItems(data.structured || []) }
    } catch (err) { console.error('Failed to load structured:', err) }
  }, [])

  const loadDatasets = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/datasets')
      if (res.ok) { const data = await res.json(); setDatasets(data.datasets || []) }
    } catch (err) { console.error('Failed to load datasets:', err) }
  }, [])

  const loadReviewQueues = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/review-queues')
      if (res.ok) { const data = await res.json(); setReviewQueues(data.queues || []) }
    } catch (err) { console.error('Failed to load review queues:', err) }
  }, [])

  const loadReviewItems = useCallback(async (queueId: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/items`)
      if (res.ok) { const data = await res.json(); setReviewItems(data.items || []) }
    } catch (err) { console.error('Failed to load review items:', err) }
  }, [])

  const loadComparisonDetails = useCallback(async (comparisonId: string) => {
    setComparisonLoading(true)
    try {
      const res = await fetch(`/api/v1/distillation/comparisons/${comparisonId}/details`)
      if (res.ok) { const data = await res.json(); setSelectedComparison(data); setSelectedWinner(null) }
    } catch (err) { console.error('Failed to load comparison details:', err) }
    finally { setComparisonLoading(false) }
  }, [])

  const loadDatasetDetails = useCallback(async (datasetId: string) => {
    try {
      const [statsRes, itemsRes] = await Promise.all([
        fetch(`/api/v1/distillation/datasets/${datasetId}/statistics`),
        fetch(`/api/v1/distillation/datasets/${datasetId}/items`)
      ])
      if (statsRes.ok) { const stats = await statsRes.json(); setDatasetStats(stats) }
      if (itemsRes.ok) { const items = await itemsRes.json(); setDatasetItems(items.items || []) }
    } catch (err) { console.error('Failed to load dataset details:', err) }
  }, [])

  const searchResponses = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append('query', searchQuery)
      if (filterProvider) params.append('provider', filterProvider)
      if (filterBanked !== null) params.append('is_banked', filterBanked.toString())
      if (selectedTagFilter.length > 0) params.append('tag_ids', selectedTagFilter.join(','))
      params.append('limit', '50')
      const res = await fetch(`/api/v1/distillation/responses/search?${params}`)
      if (res.ok) { const data = await res.json(); setResponses(data.responses || []) }
    } catch (err) { console.error('Failed to search responses:', err) }
    finally { setLoading(false) }
  }, [searchQuery, filterProvider, filterBanked, selectedTagFilter])

  const refreshAll = useCallback(() => {
    loadDomains(); loadTopics(); loadTags(); loadTasks(); loadResponses()
    loadComparisons(); loadStatistics(); loadModelPreferences(); loadSchemas()
    loadBanked(); loadStructured(); loadDatasets(); loadReviewQueues()
  }, [loadDomains, loadTopics, loadTags, loadTasks, loadResponses, loadComparisons,
      loadStatistics, loadModelPreferences, loadSchemas, loadBanked, loadStructured,
      loadDatasets, loadReviewQueues])

  // ============================================================================
  // Action Handlers
  // ============================================================================

  const handleChat = useCallback(async () => {
    if (!chatMessage.trim() || selectedModels.length === 0) return

    const invalidModels = selectedModels.filter(modelId => {
      const model = availableModels.find(m => m.id === modelId)
      return model && !apiKeys[model.provider]
    })

    if (invalidModels.length > 0) {
      setError('Some selected models do not have API keys configured.')
      return
    }

    setChatLoading(true)
    setError(null)
    setChatResponses([])
    setStreamingContent({})
    setStreamingStatus('Starting...')
    setActiveModel(null)

    try {
      const response = await fetch('/api/v1/distillation/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: chatMessage,
          models: selectedModels,
          create_comparison: selectedModels.length > 1
        })
      })

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) throw new Error('No response body')

      let buffer = ''
      let currentEventType = ''
      const contentByModel: Record<string, string> = {}

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEventType = line.substring(6).trim()
            continue
          }

          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.substring(5).trim())

              if (currentEventType === 'status') {
                const messages: Record<string, string> = {
                  'starting': 'Initializing...',
                  'run_created': 'Run created, querying models...',
                  'model_start': `Querying ${data.provider}/${data.model}...`,
                  'model_complete': `✓ ${data.model} completed (${data.latency_ms}ms)`
                }
                setStreamingStatus(messages[data.stage] || data.stage)
                if (data.stage === 'model_start') setActiveModel(data.model)
              }
              else if (currentEventType === 'delta') {
                contentByModel[data.model] = (contentByModel[data.model] || '') + data.content
                setStreamingContent({ ...contentByModel })
              }
              else if (currentEventType === 'complete') {
                setChatResponses(data.responses || [])
                if (data.error) setError(data.error)
                setStreamingStatus('')
                setStreamingContent({})
                setActiveModel(null)
                setChatMessage('')
                loadResponses()
                loadComparisons()
                loadStatistics()
              }
              else if (currentEventType === 'error') {
                setError(data.error || 'An error occurred')
              }
            } catch (e) { console.error('Failed to parse SSE data:', line, e) }
          }
        }
      }
    } catch (err: any) {
      console.error('Chat error:', err)
      setError(err.message || 'Failed to send message')
    } finally {
      setChatLoading(false)
      setStreamingStatus('')
      setActiveModel(null)
    }
  }, [chatMessage, selectedModels, availableModels, apiKeys, loadResponses, loadComparisons, loadStatistics])

  const handleBankResponse = useCallback(async (responseId: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/responses/${responseId}/bank`, { method: 'POST' })
      if (res.ok) { loadStatistics(); loadBanked(); toast.success('Response banked successfully!') }
    } catch (err) { console.error('Failed to bank response:', err) }
  }, [loadStatistics, loadBanked, toast])

  const handleDeleteResponse = useCallback(async (responseId: string) => {
    if (!confirm('Are you sure you want to delete this response?')) return
    try {
      const res = await fetch(`/api/v1/distillation/responses/${responseId}`, { method: 'DELETE' })
      if (res.ok) { loadResponses(); loadStatistics() }
      else { toast.error('Failed to delete response') }
    } catch (err) { console.error('Failed to delete response:', err) }
  }, [loadResponses, loadStatistics, toast])

  const handleUpdateResponse = useCallback(async (responseId: string, updates: any) => {
    try {
      const res = await fetch(`/api/v1/distillation/responses/${responseId}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(updates)
      })
      if (res.ok) loadResponses()
    } catch (err) { console.error('Failed to update response:', err) }
  }, [loadResponses])

  const handleAddTags = useCallback(async () => {
    if (!tagResponseId || !newTagName.trim()) return
    try {
      const res = await fetch(`/api/v1/distillation/responses/${tagResponseId}/tags`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify([newTagName.trim()])
      })
      if (res.ok) { setNewTagName(''); setTagModalOpen(false); loadTags(); loadResponses() }
    } catch (err) { console.error('Failed to add tags:', err) }
  }, [tagResponseId, newTagName, loadTags, loadResponses])

  const handleSubmitVote = useCallback(async () => {
    if (!selectedComparison || !selectedWinner) return
    try {
      const res = await fetch(`/api/v1/distillation/comparisons/${selectedComparison.comparison.id}/vote`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comparison_id: selectedComparison.comparison.id, vote_type: 'winner', winner_response_id: selectedWinner })
      })
      if (res.ok) { loadComparisonDetails(selectedComparison.comparison.id); loadModelPreferences(); toast.success('Vote submitted!') }
    } catch (err) { console.error('Failed to submit vote:', err) }
  }, [selectedComparison, selectedWinner, loadComparisonDetails, loadModelPreferences, toast])

  const handleLLMExtract = useCallback(async (bankedId: string, schemaName: string) => {
    setExtracting(true)
    try {
      const res = await fetch(`/api/v1/distillation/banked/${bankedId}/extract?schema_name=${schemaName}`, { method: 'POST' })
      if (res.ok) { loadStructured(); toast.success('Extraction complete!') }
      else { toast.error('Extraction failed') }
    } catch (err) { console.error('Failed to extract:', err) }
    finally { setExtracting(false) }
  }, [loadStructured, toast])

  const handleSaveStructured = useCallback(async () => {
    if (!selectedBanked || !selectedSchema) return
    try {
      const res = await fetch('/api/v1/distillation/structured', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ banked_id: selectedBanked.id, schema_name: selectedSchema, structured_data: structuredData, extraction_method: 'manual' })
      })
      if (res.ok) { loadStructured(); setStructureModalOpen(false); setStructuredData({}); toast.success('Structured data saved!') }
    } catch (err) { console.error('Failed to save structured:', err) }
  }, [selectedBanked, selectedSchema, structuredData, loadStructured, toast])

  const handleCreateDataset = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/datasets', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newDataset)
      })
      if (res.ok) { loadDatasets(); setCreateDatasetOpen(false); setNewDataset({ name: '', version: '1.0', description: '', dataset_type: 'training' }); toast.success('Dataset created!') }
    } catch (err) { console.error('Failed to create dataset:', err) }
  }, [newDataset, loadDatasets, toast])

  const handleAddToDataset = useCallback(async (datasetId: string, bankedId?: string, structuredId?: string) => {
    try {
      const body: any = { split: 'train' }
      if (bankedId) body.banked_ids = [bankedId]
      if (structuredId) body.structured_ids = [structuredId]
      const res = await fetch(`/api/v1/distillation/datasets/${datasetId}/items`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
      })
      if (res.ok) { loadDatasets(); if (selectedDataset?.id === datasetId) loadDatasetDetails(datasetId); toast.success('Added to dataset!') }
    } catch (err) { console.error('Failed to add to dataset:', err) }
  }, [loadDatasets, selectedDataset, loadDatasetDetails, toast])

  const handleExportDataset = useCallback(async (datasetId: string, format: 'jsonl' | 'csv' | 'alpaca') => {
    try {
      const res = await fetch(`/api/v1/distillation/datasets/${datasetId}/export/${format}`, { method: 'POST' })
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a'); a.href = url; a.download = `dataset.${format === 'alpaca' ? 'json' : format}`; a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) { console.error('Failed to export:', err) }
  }, [])

  const handleCreateQueue = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/distillation/review-queues', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newQueue)
      })
      if (res.ok) { loadReviewQueues(); setCreateQueueOpen(false); setNewQueue({ name: '', description: '' }); toast.success('Queue created!') }
    } catch (err) { console.error('Failed to create queue:', err) }
  }, [newQueue, loadReviewQueues, toast])

  const handleAutoPopulateQueue = useCallback(async (queueId: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/auto-populate`, { method: 'POST' })
      if (res.ok) { const data = await res.json(); loadReviewItems(queueId); toast.success(`Added ${data.items_added} items to queue!`) }
    } catch (err) { console.error('Failed to auto-populate:', err) }
  }, [loadReviewItems, toast])

  const getNextReviewItem = useCallback(async (queueId: string) => {
    setReviewLoading(true)
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/next`)
      if (res.ok) {
        const data = await res.json()
        if (data.item) { setCurrentReviewItem({ item: data.item, response: data.response }); setReviewNotes(''); setReviewScore('') }
        else { setCurrentReviewItem(null); toast.info('No more items to review!') }
      }
    } catch (err) { console.error('Failed to get next review item:', err) }
    finally { setReviewLoading(false) }
  }, [toast])

  const handleSubmitReview = useCallback(async (action: string) => {
    if (!currentReviewItem) return
    try {
      const res = await fetch(`/api/v1/distillation/review-items/${currentReviewItem.item.id}/review`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, review_notes: reviewNotes || null, review_score: reviewScore ? parseFloat(reviewScore) : null })
      })
      if (res.ok && selectedQueue) { loadReviewItems(selectedQueue.id); loadReviewQueues(); getNextReviewItem(selectedQueue.id) }
    } catch (err) { console.error('Failed to submit review:', err) }
  }, [currentReviewItem, reviewNotes, reviewScore, selectedQueue, loadReviewItems, loadReviewQueues, getNextReviewItem])

  const handleExportQueue = useCallback(async (queueId: string, format: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/export?export_format=${format}`, { method: 'POST' })
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a'); a.href = url; a.download = `review_queue.${format}`; a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) { console.error('Failed to export queue:', err) }
  }, [])

  const handleCreateTask = useCallback(async () => {
    if (!newTask.name.trim() || !newTask.prompt_template.trim()) {
      toast.warning('Task name and prompt template are required')
      return
    }
    setTaskLoading(true)
    try {
      const payload = {
        name: newTask.name, description: newTask.description || null, task_type: newTask.task_type,
        prompt_template: newTask.prompt_template, system_prompt: newTask.system_prompt || null,
        target_models: newTask.target_models, domain_id: newTask.domain_id || null, topic_id: newTask.topic_id || null
      }
      const res = await fetch('/api/v1/distillation/tasks', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      })
      if (res.ok) {
        setCreateTaskOpen(false)
        setNewTask({ name: '', description: '', task_type: 'freeform', prompt_template: '', system_prompt: '', target_models: ['gpt-4o'], domain_id: '', topic_id: '' })
        loadTasks()
      } else { const err = await res.json(); toast.error(`Failed to create task: ${err.detail || 'Unknown error'}`) }
    } catch (err) { console.error('Failed to create task:', err); toast.error('Failed to create task') }
    finally { setTaskLoading(false) }
  }, [newTask, loadTasks, toast])

  // ============================================================================
  // Initial Load
  // ============================================================================

  useEffect(() => {
    loadAvailableModels()
    refreshAll()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ============================================================================
  // Return State and Actions
  // ============================================================================

  const state: DistillationState = {
    domains, topics, tags, tasks, responses, comparisons, statistics, modelPreferences,
    viewMode, loading, error,
    chatMessage, selectedModels, chatResponses, chatLoading, streamingStatus, streamingContent, activeModel,
    searchQuery, filterProvider,
    tagModalOpen, tagResponseId, newTagName,
    selectedComparison, comparisonLoading, blindMode, selectedWinner,
    schemas, bankedItems, structuredItems, selectedBanked, selectedSchema, structureModalOpen, structuredData, extracting,
    datasets, selectedDataset, datasetStats, datasetItems, createDatasetOpen, newDataset,
    reviewQueues, selectedQueue, reviewItems, currentReviewItem, reviewNotes, reviewScore, createQueueOpen, newQueue, reviewLoading,
    availableModels, apiKeys, loadingModels,
    createTaskOpen, newTask, taskLoading
  }

  const actions: DistillationActions = {
    setViewMode, setChatMessage, setSelectedModels, setSearchQuery, setFilterProvider,
    setTagModalOpen, setTagResponseId, setNewTagName, setBlindMode, setSelectedWinner,
    setSelectedBanked, setSelectedSchema, setStructureModalOpen, setStructuredData,
    setSelectedDataset, setCreateDatasetOpen, setNewDataset, setSelectedQueue,
    setReviewNotes, setReviewScore, setCreateQueueOpen, setNewQueue,
    setCreateTaskOpen, setNewTask, setError,
    setDatasetStats, setDatasetItems, setReviewItems, setCurrentReviewItem, setSelectedComparison,
    refreshAll, loadResponses, loadComparisons, loadStatistics, loadBanked, loadStructured,
    loadDatasets, loadReviewQueues, loadReviewItems, loadComparisonDetails, loadDatasetDetails, searchResponses,
    handleChat, handleBankResponse, handleDeleteResponse, handleUpdateResponse, handleAddTags,
    handleSubmitVote, handleLLMExtract, handleSaveStructured, handleCreateDataset, handleAddToDataset,
    handleExportDataset, handleCreateQueue, handleAutoPopulateQueue, handleSubmitReview,
    handleExportQueue, getNextReviewItem, handleCreateTask
  }

  return [state, actions]
}
