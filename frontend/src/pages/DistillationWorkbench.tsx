import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  FlaskConical,
  MessageSquare,
  List,
  Database,
  GitCompare,
  FolderOpen,
  Plus,
  RefreshCw,
  Play,
  Send,
  ThumbsUp,
  ChevronRight,
  Loader2,
  Tag,
  Search,
  Filter,
  X,
  Check,
  Award,
  BarChart3,
  Eye,
  EyeOff,
  FileJson,
  FileText,
  Download,
  Trash2,
  Edit3,
  Wand2,
  ClipboardCheck,
  ThumbsDown,
  AlertCircle,
  Users,
  ChevronDown
} from 'lucide-react'

// Types
interface Domain {
  id: string
  name: string
  description?: string
  icon?: string
  color?: string
  topic_count: number
}

interface Topic {
  id: string
  domain_id: string
  name: string
  description?: string
}

interface TagItem {
  id: string
  name: string
  color?: string
}

interface Task {
  id: string
  name: string
  description?: string
  task_type: string
  target_models: string[]
  domain_id?: string
  topic_id?: string
  is_active: boolean
}

interface Response {
  id: string
  run_id: string
  provider: string
  model: string
  prompt_sent: string
  response_text: string
  latency_ms?: number
  created_at: string
  domain_id?: string
  topic_id?: string
  quality_rating?: number
  tags?: TagItem[]
}

interface BankedItem {
  id: string
  response_id: string
  quality_score?: number
  status: string
  notes?: string
  banked_at: string
}

interface Comparison {
  id: string
  comparison_type: string
  prompt_used: string
  status: string
  created_at: string
}

interface ComparisonDetail {
  comparison: Comparison
  responses: Array<{
    response: Response
    display_order: number
    display_label?: string
  }>
  votes: Vote[]
  vote_count: number
}

interface Vote {
  id: string
  comparison_id: string
  winner_response_id?: string
  vote_type: string
  voter?: string
  notes?: string
  created_at: string
}

interface Statistics {
  total_responses: number
  total_banked: number
  by_provider: Record<string, number>
  by_model: Record<string, number>
}

interface ModelPreferences {
  model_wins: Record<string, number>
  model_appearances: Record<string, number>
  win_rates: Record<string, number>
  total_votes: number
}

interface SchemaDefinition {
  key: string
  name: string
  description: string
  fields: Record<string, { type: string; required: boolean; description?: string }>
}

interface StructuredItem {
  id: string
  banked_id: string
  schema_name: string
  structured_data: Record<string, any>
  extraction_method?: string
  extracted_at: string
}

interface Dataset {
  id: string
  name: string
  version: string
  description?: string
  dataset_type: string
  item_count: number
  status: string
  created_at: string
}

interface DatasetStats {
  total_items: number
  by_split: Record<string, number>
  by_schema: Record<string, number>
  has_structured: number
  has_banked_only: number
}

// Phase 6: Expert Review types
interface ReviewQueue {
  id: string
  name: string
  description?: string
  domain_id?: string
  topic_id?: string
  min_quality_score?: number
  assigned_experts: string[]
  is_active: boolean
  created_at: string
  pending_count?: number
  completed_count?: number
}

interface ReviewItem {
  id: string
  queue_id: string
  banked_id: string
  status: string
  assigned_to?: string
  review_notes?: string
  review_score?: number
  reviewed_by?: string
  reviewed_at?: string
  priority: number
  created_at: string
  banked?: BankedItem
}

type ViewMode = 'chat' | 'tasks' | 'bank' | 'compare' | 'structure' | 'datasets' | 'review' | 'stats'

export default function DistillationWorkbench() {
  const [viewMode, setViewMode] = useState<ViewMode>('chat')
  const [domains, setDomains] = useState<Domain[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [tags, setTags] = useState<TagItem[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [responses, setResponses] = useState<Response[]>([])
  const [comparisons, setComparisons] = useState<Comparison[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [modelPreferences, setModelPreferences] = useState<ModelPreferences | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Chat state
  const [chatMessage, setChatMessage] = useState('')
  const [selectedModels, setSelectedModels] = useState<string[]>(['gpt-4o'])
  const [chatResponses, setChatResponses] = useState<Response[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  
  // Streaming state
  const [streamingStatus, setStreamingStatus] = useState<string>('')
  const [streamingContent, setStreamingContent] = useState<Record<string, string>>({}) // model -> content
  const [activeModel, setActiveModel] = useState<string | null>(null)

  // Search/Filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [filterProvider, setFilterProvider] = useState('')
  const [filterBanked, setFilterBanked] = useState<boolean | null>(null)
  const [selectedTagFilter, setSelectedTagFilter] = useState<string[]>([])

  // Tagging state
  const [tagModalOpen, setTagModalOpen] = useState(false)
  const [tagResponseId, setTagResponseId] = useState<string | null>(null)
  const [newTagName, setNewTagName] = useState('')

  // Comparison state
  const [selectedComparison, setSelectedComparison] = useState<ComparisonDetail | null>(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  const [blindMode, setBlindMode] = useState(false)
  const [selectedWinner, setSelectedWinner] = useState<string | null>(null)

  // Structuring state (Phase 5)
  const [schemas, setSchemas] = useState<SchemaDefinition[]>([])
  const [bankedItems, setBankedItems] = useState<BankedItem[]>([])
  const [structuredItems, setStructuredItems] = useState<StructuredItem[]>([])
  const [selectedBanked, setSelectedBanked] = useState<BankedItem | null>(null)
  const [selectedSchema, setSelectedSchema] = useState<string>('')
  const [structureModalOpen, setStructureModalOpen] = useState(false)
  const [structuredData, setStructuredData] = useState<Record<string, any>>({})
  const [extracting, setExtracting] = useState(false)

  // Dataset state (Phase 7)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [datasetStats, setDatasetStats] = useState<DatasetStats | null>(null)
  const [datasetItems, setDatasetItems] = useState<any[]>([])
  const [createDatasetOpen, setCreateDatasetOpen] = useState(false)
  const [newDataset, setNewDataset] = useState({ name: '', version: '1.0', description: '', dataset_type: 'training' })

  // Review state (Phase 6)
  const [reviewQueues, setReviewQueues] = useState<ReviewQueue[]>([])
  const [selectedQueue, setSelectedQueue] = useState<ReviewQueue | null>(null)
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([])
  const [currentReviewItem, setCurrentReviewItem] = useState<{ item: ReviewItem; response: Response } | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewScore, setReviewScore] = useState<string>('')
  const [createQueueOpen, setCreateQueueOpen] = useState(false)
  const [newQueue, setNewQueue] = useState({ name: '', description: '' })
  const [reviewLoading, setReviewLoading] = useState(false)

  // Model selection state (dynamic)
  const [availableModels, setAvailableModels] = useState<Array<{ id: string; name: string; provider: string }>>([])
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({})
  const [loadingModels, setLoadingModels] = useState(true)

  // Task creation state
  const [createTaskOpen, setCreateTaskOpen] = useState(false)
  const [newTask, setNewTask] = useState({
    name: '',
    description: '',
    task_type: 'freeform',
    prompt_template: '',
    system_prompt: '',
    target_models: ['gpt-4o'],
    domain_id: '',
    topic_id: ''
  })
  const [taskLoading, setTaskLoading] = useState(false)

  useEffect(() => {
    loadDomains()
    loadTopics()
    loadTags()
    loadAvailableModels()
    loadTasks()
    loadResponses()
    loadComparisons()
    loadStatistics()
    loadModelPreferences()
    loadSchemas()
    loadBanked()
    loadStructured()
    loadDatasets()
    loadReviewQueues()
  }, [])

  const loadAvailableModels = async () => {
    setLoadingModels(true)
    try {
      const [modelsRes, keysRes] = await Promise.all([
        fetch('/api/v1/ai-models/available'),
        fetch('/api/v1/ai-models/check-keys')
      ])
      
      if (modelsRes.ok && keysRes.ok) {
        const modelsData = await modelsRes.json()
        const keysData = await keysRes.json()
        
        // Build flat model list with provider info
        const models: Array<{ id: string; name: string; provider: string }> = []
        for (const providerData of modelsData.providers) {
          for (const modelId of providerData.models) {
            models.push({
              id: modelId,
              name: modelId,
              provider: providerData.provider
            })
          }
        }
        
        setAvailableModels(models)
        setApiKeys(keysData)
        
        // Set default selection to first model with API key
        const firstWithKey = models.find(m => keysData[m.provider])
        if (firstWithKey && selectedModels.length === 0) {
          setSelectedModels([firstWithKey.id])
        }
      }
    } catch (err) {
      console.error('Failed to load models:', err)
      // Fallback to defaults
      setAvailableModels([
        { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
        { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', provider: 'openai' },
        { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', provider: 'anthropic' },
        { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', provider: 'anthropic' },
        { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash', provider: 'google' },
        { id: 'grok-beta', name: 'Grok Beta', provider: 'xai' },
      ])
    } finally {
      setLoadingModels(false)
    }
  }

  const loadDomains = async () => {
    try {
      const res = await fetch('/api/v1/distillation/domains')
      if (res.ok) {
        const data = await res.json()
        setDomains(data.domains || [])
      }
    } catch (err) {
      console.error('Failed to load domains:', err)
    }
  }

  const loadTopics = async () => {
    try {
      const res = await fetch('/api/v1/distillation/topics')
      if (res.ok) {
        const data = await res.json()
        setTopics(data.topics || [])
      }
    } catch (err) {
      console.error('Failed to load topics:', err)
    }
  }

  const loadTags = async () => {
    try {
      const res = await fetch('/api/v1/distillation/tags')
      if (res.ok) {
        const data = await res.json()
        setTags(data || [])
      }
    } catch (err) {
      console.error('Failed to load tags:', err)
    }
  }

  const loadTasks = async () => {
    try {
      const res = await fetch('/api/v1/distillation/tasks')
      if (res.ok) {
        const data = await res.json()
        setTasks(data.tasks || [])
      }
    } catch (err) {
      console.error('Failed to load tasks:', err)
    }
  }

  const handleCreateTask = async () => {
    if (!newTask.name.trim() || !newTask.prompt_template.trim()) {
      alert('Task name and prompt template are required')
      return
    }
    
    setTaskLoading(true)
    try {
      const payload = {
        name: newTask.name,
        description: newTask.description || null,
        task_type: newTask.task_type,
        prompt_template: newTask.prompt_template,
        system_prompt: newTask.system_prompt || null,
        target_models: newTask.target_models,
        domain_id: newTask.domain_id || null,
        topic_id: newTask.topic_id || null
      }
      
      const res = await fetch('/api/v1/distillation/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      if (res.ok) {
        setCreateTaskOpen(false)
        setNewTask({
          name: '',
          description: '',
          task_type: 'freeform',
          prompt_template: '',
          system_prompt: '',
          target_models: ['gpt-4o'],
          domain_id: '',
          topic_id: ''
        })
        loadTasks()
      } else {
        const err = await res.json()
        alert(`Failed to create task: ${err.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Failed to create task:', err)
      alert('Failed to create task')
    } finally {
      setTaskLoading(false)
    }
  }

  const loadResponses = async () => {
    try {
      const res = await fetch('/api/v1/distillation/responses?limit=50')
      if (res.ok) {
        const data = await res.json()
        setResponses(data.responses || [])
      }
    } catch (err) {
      console.error('Failed to load responses:', err)
    }
  }

  const searchResponses = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append('query', searchQuery)
      if (filterProvider) params.append('provider', filterProvider)
      if (filterBanked !== null) params.append('is_banked', filterBanked.toString())
      if (selectedTagFilter.length > 0) params.append('tag_ids', selectedTagFilter.join(','))
      params.append('limit', '50')

      const res = await fetch(`/api/v1/distillation/responses/search?${params}`)
      if (res.ok) {
        const data = await res.json()
        setResponses(data.responses || [])
      }
    } catch (err) {
      console.error('Failed to search responses:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadComparisons = async () => {
    try {
      const res = await fetch('/api/v1/distillation/comparisons?limit=20')
      if (res.ok) {
        const data = await res.json()
        setComparisons(data.comparisons || [])
      }
    } catch (err) {
      console.error('Failed to load comparisons:', err)
    }
  }

  const loadStatistics = async () => {
    try {
      const res = await fetch('/api/v1/distillation/statistics')
      if (res.ok) {
        const data = await res.json()
        setStatistics(data)
      }
    } catch (err) {
      console.error('Failed to load statistics:', err)
    }
  }

  const loadModelPreferences = async () => {
    try {
      const res = await fetch('/api/v1/distillation/model-preferences')
      if (res.ok) {
        const data = await res.json()
        setModelPreferences(data)
      }
    } catch (err) {
      console.error('Failed to load model preferences:', err)
    }
  }

  const loadSchemas = async () => {
    try {
      const res = await fetch('/api/v1/distillation/schemas')
      if (res.ok) {
        const data = await res.json()
        setSchemas(data.schemas || [])
      }
    } catch (err) {
      console.error('Failed to load schemas:', err)
    }
  }

  const loadBanked = async () => {
    try {
      const res = await fetch('/api/v1/distillation/banked?limit=100')
      if (res.ok) {
        const data = await res.json()
        setBankedItems(data.banked || [])
      }
    } catch (err) {
      console.error('Failed to load banked:', err)
    }
  }

  const loadStructured = async () => {
    try {
      const res = await fetch('/api/v1/distillation/structured?limit=100')
      if (res.ok) {
        const data = await res.json()
        setStructuredItems(data.structured || [])
      }
    } catch (err) {
      console.error('Failed to load structured:', err)
    }
  }

  const loadDatasets = async () => {
    try {
      const res = await fetch('/api/v1/distillation/datasets')
      if (res.ok) {
        const data = await res.json()
        setDatasets(data.datasets || [])
      }
    } catch (err) {
      console.error('Failed to load datasets:', err)
    }
  }

  // Phase 6: Review functions
  const loadReviewQueues = async () => {
    try {
      const res = await fetch('/api/v1/distillation/review-queues')
      if (res.ok) {
        const data = await res.json()
        setReviewQueues(data.queues || [])
      }
    } catch (err) {
      console.error('Failed to load review queues:', err)
    }
  }

  const loadReviewItems = async (queueId: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/items`)
      if (res.ok) {
        const data = await res.json()
        setReviewItems(data.items || [])
      }
    } catch (err) {
      console.error('Failed to load review items:', err)
    }
  }

  const getNextReviewItem = async (queueId: string) => {
    setReviewLoading(true)
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/next`)
      if (res.ok) {
        const data = await res.json()
        if (data.item) {
          setCurrentReviewItem({ item: data.item, response: data.response })
          setReviewNotes('')
          setReviewScore('')
        } else {
          setCurrentReviewItem(null)
          alert('No more items to review!')
        }
      }
    } catch (err) {
      console.error('Failed to get next review item:', err)
    } finally {
      setReviewLoading(false)
    }
  }

  const handleCreateQueue = async () => {
    try {
      const res = await fetch('/api/v1/distillation/review-queues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newQueue)
      })
      if (res.ok) {
        loadReviewQueues()
        setCreateQueueOpen(false)
        setNewQueue({ name: '', description: '' })
        alert('Queue created!')
      }
    } catch (err) {
      console.error('Failed to create queue:', err)
    }
  }

  const handleAutoPopulateQueue = async (queueId: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/auto-populate`, {
        method: 'POST'
      })
      if (res.ok) {
        const data = await res.json()
        loadReviewItems(queueId)
        alert(`Added ${data.items_added} items to queue!`)
      }
    } catch (err) {
      console.error('Failed to auto-populate:', err)
    }
  }

  const handleAddBankedToQueue = async (queueId: string, bankedIds: string[]) => {
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ banked_ids: bankedIds })
      })
      if (res.ok) {
        loadReviewItems(queueId)
        alert('Added to review queue!')
      }
    } catch (err) {
      console.error('Failed to add to queue:', err)
    }
  }

  const handleSubmitReview = async (action: string) => {
    if (!currentReviewItem) return

    try {
      const res = await fetch(`/api/v1/distillation/review-items/${currentReviewItem.item.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          review_notes: reviewNotes || null,
          review_score: reviewScore ? parseFloat(reviewScore) : null
        })
      })
      if (res.ok) {
        if (selectedQueue) {
          loadReviewItems(selectedQueue.id)
          loadReviewQueues()
          // Get next item
          getNextReviewItem(selectedQueue.id)
        }
      }
    } catch (err) {
      console.error('Failed to submit review:', err)
    }
  }

  const handleExportQueue = async (queueId: string, format: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/review-queues/${queueId}/export?export_format=${format}`, {
        method: 'POST'
      })
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `review_queue.${format}`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('Failed to export queue:', err)
    }
  }

  const loadComparisonDetails = async (comparisonId: string) => {
    setComparisonLoading(true)
    try {
      const res = await fetch(`/api/v1/distillation/comparisons/${comparisonId}/details`)
      if (res.ok) {
        const data = await res.json()
        setSelectedComparison(data)
        setSelectedWinner(null)
      }
    } catch (err) {
      console.error('Failed to load comparison details:', err)
    } finally {
      setComparisonLoading(false)
    }
  }

  const loadDatasetDetails = async (datasetId: string) => {
    try {
      const [statsRes, itemsRes] = await Promise.all([
        fetch(`/api/v1/distillation/datasets/${datasetId}/statistics`),
        fetch(`/api/v1/distillation/datasets/${datasetId}/items`)
      ])
      if (statsRes.ok) {
        const stats = await statsRes.json()
        setDatasetStats(stats)
      }
      if (itemsRes.ok) {
        const items = await itemsRes.json()
        setDatasetItems(items.items || [])
      }
    } catch (err) {
      console.error('Failed to load dataset details:', err)
    }
  }

  const handleChat = async () => {
    if (!chatMessage.trim() || selectedModels.length === 0) return

    // Validate all selected models have API keys
    const invalidModels = selectedModels.filter(modelId => {
      const model = availableModels.find(m => m.id === modelId)
      return model && !apiKeys[model.provider]
    })
    
    if (invalidModels.length > 0) {
      setError('Some selected models do not have API keys configured. Please deselect them or add the required API keys.')
      return
    }

    setChatLoading(true)
    setError(null)
    setChatResponses([])
    setStreamingContent({})
    setStreamingStatus('Starting...')
    setActiveModel(null)

    try {
      console.log('Starting streaming chat with models:', selectedModels)
      
      const response = await fetch('/api/v1/distillation/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: chatMessage,
          models: selectedModels,
          create_comparison: selectedModels.length > 1
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('No response body')
      }

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
                if (data.stage === 'model_start') {
                  setActiveModel(data.model)
                }
              }
              else if (currentEventType === 'delta') {
                // Streaming text from a model
                const modelKey = data.model
                contentByModel[modelKey] = (contentByModel[modelKey] || '') + data.content
                setStreamingContent({ ...contentByModel })
              }
              else if (currentEventType === 'complete') {
                // Final response with all data
                setChatResponses(data.responses || [])
                if (data.error) {
                  setError(data.error)
                }
                setStreamingStatus('')
                setStreamingContent({})
                setActiveModel(null)
                setChatMessage('')
                
                loadResponses()
                loadComparisons()
                loadStatistics()
              }
              else if (currentEventType === 'error') {
                console.error('Stream error:', data.error)
                setError(data.error || 'An error occurred')
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', line, e)
            }
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
  }

  const handleBankResponse = async (responseId: string) => {
    try {
      const res = await fetch(`/api/v1/distillation/responses/${responseId}/bank`, {
        method: 'POST'
      })
      if (res.ok) {
        loadStatistics()
        loadBanked()
        alert('Response banked successfully!')
      }
    } catch (err) {
      console.error('Failed to bank response:', err)
    }
  }

  const handleDeleteResponse = async (responseId: string) => {
    if (!confirm('Are you sure you want to delete this response?')) return
    
    try {
      const res = await fetch(`/api/v1/distillation/responses/${responseId}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        loadResponses()
        loadStatistics()
      } else {
        alert('Failed to delete response')
      }
    } catch (err) {
      console.error('Failed to delete response:', err)
    }
  }

  const handleUpdateResponse = async (responseId: string, updates: { domain_id?: string | null; topic_id?: string | null; quality_rating?: number | null }) => {
    try {
      const res = await fetch(`/api/v1/distillation/responses/${responseId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      if (res.ok) {
        loadResponses()
      }
    } catch (err) {
      console.error('Failed to update response:', err)
    }
  }

  const handleAddTags = async () => {
    if (!tagResponseId || !newTagName.trim()) return

    try {
      const res = await fetch(`/api/v1/distillation/responses/${tagResponseId}/tags`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([newTagName.trim()])
      })
      if (res.ok) {
        setNewTagName('')
        setTagModalOpen(false)
        loadTags()
        loadResponses()
      }
    } catch (err) {
      console.error('Failed to add tags:', err)
    }
  }

  const handleSubmitVote = async () => {
    if (!selectedComparison || !selectedWinner) return

    try {
      const res = await fetch(`/api/v1/distillation/comparisons/${selectedComparison.comparison.id}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          comparison_id: selectedComparison.comparison.id,
          vote_type: 'winner',
          winner_response_id: selectedWinner
        })
      })
      if (res.ok) {
        loadComparisonDetails(selectedComparison.comparison.id)
        loadModelPreferences()
        alert('Vote submitted!')
      }
    } catch (err) {
      console.error('Failed to submit vote:', err)
    }
  }

  // Phase 5: Structuring handlers
  const handleLLMExtract = async (bankedId: string, schemaName: string) => {
    setExtracting(true)
    try {
      const res = await fetch(`/api/v1/distillation/banked/${bankedId}/extract?schema_name=${schemaName}`, {
        method: 'POST'
      })
      if (res.ok) {
        loadStructured()
        alert('Extraction complete!')
      } else {
        alert('Extraction failed')
      }
    } catch (err) {
      console.error('Failed to extract:', err)
    } finally {
      setExtracting(false)
    }
  }

  const handleSaveStructured = async () => {
    if (!selectedBanked || !selectedSchema) return

    try {
      const res = await fetch('/api/v1/distillation/structured', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          banked_id: selectedBanked.id,
          schema_name: selectedSchema,
          structured_data: structuredData,
          extraction_method: 'manual'
        })
      })
      if (res.ok) {
        loadStructured()
        setStructureModalOpen(false)
        setStructuredData({})
        alert('Structured data saved!')
      }
    } catch (err) {
      console.error('Failed to save structured:', err)
    }
  }

  // Phase 7: Dataset handlers
  const handleCreateDataset = async () => {
    try {
      const res = await fetch('/api/v1/distillation/datasets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newDataset)
      })
      if (res.ok) {
        loadDatasets()
        setCreateDatasetOpen(false)
        setNewDataset({ name: '', version: '1.0', description: '', dataset_type: 'training' })
        alert('Dataset created!')
      }
    } catch (err) {
      console.error('Failed to create dataset:', err)
    }
  }

  const handleAddToDataset = async (datasetId: string, bankedId?: string, structuredId?: string) => {
    try {
      const body: any = { split: 'train' }
      if (bankedId) body.banked_ids = [bankedId]
      if (structuredId) body.structured_ids = [structuredId]

      const res = await fetch(`/api/v1/distillation/datasets/${datasetId}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (res.ok) {
        loadDatasets()
        if (selectedDataset?.id === datasetId) {
          loadDatasetDetails(datasetId)
        }
        alert('Added to dataset!')
      }
    } catch (err) {
      console.error('Failed to add to dataset:', err)
    }
  }

  const handleExportDataset = async (datasetId: string, format: 'jsonl' | 'csv' | 'alpaca') => {
    try {
      const res = await fetch(`/api/v1/distillation/datasets/${datasetId}/export/${format}`, {
        method: 'POST'
      })
      if (res.ok) {
        const blob = await res.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `dataset.${format === 'alpaca' ? 'json' : format}`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('Failed to export:', err)
    }
  }

  const toggleModel = (modelId: string) => {
    setSelectedModels(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(m => m !== modelId)
      }
      // Limit to 3 models max
      if (prev.length >= 3) {
        return prev
      }
      return [...prev, modelId]
    })
  }

  const navItems = [
    { mode: 'chat' as ViewMode, label: 'Interactive Chat', icon: MessageSquare },
    { mode: 'tasks' as ViewMode, label: 'Task Library', icon: List },
    { mode: 'bank' as ViewMode, label: 'Response Bank', icon: Database },
    { mode: 'compare' as ViewMode, label: 'Compare', icon: GitCompare },
    { mode: 'structure' as ViewMode, label: 'Structure', icon: FileJson },
    { mode: 'review' as ViewMode, label: 'Expert Review', icon: ClipboardCheck },
    { mode: 'datasets' as ViewMode, label: 'Datasets', icon: FolderOpen },
    { mode: 'stats' as ViewMode, label: 'Statistics', icon: BarChart3 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-3" style={{ color: '#a8d8ff' }}>
            <FlaskConical className="h-8 w-8" />
            <span>Distillation Workbench</span>
          </h1>
          <p className="mt-2" style={{ color: '#b3d9ff' }}>
            Capture domain knowledge from SOTA models and build training datasets
          </p>
        </div>
        <button
          onClick={() => {
            loadDomains(); loadTopics(); loadTags(); loadTasks(); loadResponses(); loadComparisons()
            loadStatistics(); loadModelPreferences(); loadSchemas(); loadBanked()
            loadStructured(); loadDatasets(); loadReviewQueues()
          }}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg transition-all"
          style={{
            backgroundColor: 'rgba(168, 216, 255, 0.15)',
            border: '1px solid rgba(168, 216, 255, 0.4)',
            color: '#a8d8ff'
          }}
        >
          <RefreshCw className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg" style={{
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#fca5a5'
        }}>
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1 rounded-lg p-4" style={{
          backgroundColor: 'rgba(30, 30, 40, 0.8)',
          border: '1px solid rgba(168, 216, 255, 0.2)'
        }}>
          <h2 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>Workbench</h2>
          <div className="space-y-2">
            {navItems.map(({ mode, label, icon: Icon }) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all"
                style={viewMode === mode ? {
                  background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                  color: '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.4)'
                } : { color: '#f0f0f5' }}
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium">{label}</span>
              </button>
            ))}
          </div>

          {/* Quick Stats */}
          {statistics && (
            <div className="mt-6 space-y-2">
              <h3 className="text-sm font-semibold" style={{ color: '#a8d8ff' }}>Quick Stats</h3>
              <div className="text-sm" style={{ color: '#b3d9ff' }}>
                <div className="flex justify-between"><span>Responses:</span><span>{statistics.total_responses}</span></div>
                <div className="flex justify-between"><span>Banked:</span><span>{statistics.total_banked}</span></div>
                <div className="flex justify-between"><span>Structured:</span><span>{structuredItems.length}</span></div>
                <div className="flex justify-between"><span>Datasets:</span><span>{datasets.length}</span></div>
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="lg:col-span-4 space-y-4">
          {/* Interactive Chat View */}
          {viewMode === 'chat' && (
            <div className="rounded-lg p-6" style={{
              backgroundColor: 'rgba(30, 30, 40, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Interactive Chat</h2>
              <p className="text-sm mb-4" style={{ color: '#b3d9ff' }}>Query SOTA models and bank great responses for training data</p>

              {/* Compact Model Selection */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm" style={{ color: '#b3d9ff' }}>
                    Models ({selectedModels.length}/3)
                  </label>
                  {selectedModels.length > 1 && (
                    <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
                      Compare mode
                    </span>
                  )}
                </div>
                
                {/* Selected Models Tags */}
                <div className="flex flex-wrap gap-2 mb-2">
                  {selectedModels.filter(id => id).map(modelId => {
                    const model = availableModels.find(m => m.id === modelId)
                    // Try to extract provider from modelId if not found in availableModels
                    let provider = model?.provider
                    if (!provider) {
                      if (modelId.startsWith('gpt') || modelId.startsWith('o1')) provider = 'openai'
                      else if (modelId.startsWith('claude')) provider = 'anthropic'
                      else if (modelId.startsWith('gemini')) provider = 'google'
                      else if (modelId.startsWith('grok')) provider = 'xai'
                    }
                    return (
                      <span
                        key={modelId}
                        className="inline-flex items-center px-2 py-1 rounded text-xs"
                        style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.2)',
                          border: '1px solid rgba(168, 216, 255, 0.4)',
                          color: '#a8d8ff'
                        }}
                      >
                        <span className="opacity-60 mr-1">{provider || 'unknown'}:</span>
                        {modelId}
                        <button
                          onClick={() => setSelectedModels(prev => prev.filter(id => id !== modelId))}
                          className="ml-1.5 hover:text-red-400"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    )
                  })}
                  
                  {/* Add Model Dropdown */}
                  {selectedModels.filter(id => id).length < 3 && !loadingModels && (
                    <div className="relative">
                      <select
                        onChange={e => {
                          const selectedOption = e.target.options[e.target.selectedIndex]
                          const value = selectedOption?.value
                          console.log('Model select onChange:', { value, selectedIndex: e.target.selectedIndex })
                          if (value && value.trim() && !selectedModels.includes(value)) {
                            console.log('Adding model:', value)
                            setSelectedModels(prev => [...prev.filter(id => id), value])
                          }
                          // Reset to placeholder after a tick
                          setTimeout(() => { e.target.selectedIndex = 0 }, 0)
                        }}
                        className="appearance-none px-2 py-1 pr-6 rounded text-xs cursor-pointer"
                        style={{
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          color: '#f0f0f5'
                        }}
                        value=""
                      >
                        <option value="" disabled>+ Add model</option>
                        {availableModels
                          .filter(m => !selectedModels.includes(m.id) && apiKeys[m.provider])
                          .map(m => (
                            <option key={m.id} value={m.id}>
                              {m.provider}: {m.id}
                            </option>
                          ))
                        }
                      </select>
                      <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 h-3 w-3 pointer-events-none" style={{ color: '#b3d9ff' }} />
                    </div>
                  )}
                </div>
                
                {/* Warnings */}
                {loadingModels && (
                  <div className="flex items-center space-x-2 text-xs" style={{ color: '#b3d9ff' }}>
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span>Loading models...</span>
                  </div>
                )}
                {!loadingModels && availableModels.filter(m => apiKeys[m.provider]).length === 0 && (
                  <p className="text-xs" style={{ color: '#fbbf24' }}>
                    No API keys configured. Add OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
                  </p>
                )}
              </div>

              {/* Chat Input */}
              <div className="flex space-x-2 mb-4">
                <textarea
                  value={chatMessage}
                  onChange={e => setChatMessage(e.target.value)}
                  placeholder="Ask a question to capture domain knowledge..."
                  className="flex-1 px-4 py-3 rounded-lg resize-none"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                  rows={3}
                />
                <button
                  onClick={handleChat}
                  disabled={chatLoading || !chatMessage.trim() || selectedModels.length === 0}
                  className="px-4 py-2 rounded-lg flex items-center space-x-2 transition-all disabled:opacity-50"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.2)',
                    border: '1px solid rgba(168, 216, 255, 0.4)',
                    color: '#a8d8ff'
                  }}
                >
                  {chatLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                </button>
              </div>

              {/* Streaming Status & Content */}
              {chatLoading && (
                <div className="space-y-4">
                  {/* Status Bar */}
                  <div className="flex items-center space-x-3 px-3 py-2 rounded-lg" style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    border: '1px solid rgba(168, 216, 255, 0.2)'
                  }}>
                    <Loader2 className="h-4 w-4 animate-spin" style={{ color: '#a8d8ff' }} />
                    <span className="text-sm" style={{ color: '#a8d8ff' }}>{streamingStatus || 'Processing...'}</span>
                  </div>
                  
                  {/* Streaming Content per Model */}
                  {Object.keys(streamingContent).length > 0 && (
                    <div className="space-y-4">
                      {Object.entries(streamingContent).map(([modelId, content]) => {
                        const model = availableModels.find(m => m.id === modelId)
                        const isActive = activeModel === modelId
                        return (
                          <div key={modelId} className="p-4 rounded-lg" style={{
                            backgroundColor: 'rgba(20, 20, 30, 0.6)',
                            border: isActive ? '1px solid rgba(168, 216, 255, 0.4)' : '1px solid rgba(168, 216, 255, 0.1)'
                          }}>
                            <div className="flex items-center justify-between mb-2">
                              <span className="px-2 py-1 rounded text-xs" style={{
                                backgroundColor: 'rgba(168, 216, 255, 0.2)',
                                color: '#a8d8ff'
                              }}>
                                {model?.provider || 'unknown'} / {modelId}
                              </span>
                              {isActive && (
                                <span className="flex items-center space-x-1 text-xs" style={{ color: '#10b981' }}>
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                  <span>Streaming...</span>
                                </span>
                              )}
                            </div>
                            <div className="prose prose-sm prose-invert max-w-none" style={{ color: '#f0f0f5' }}>
                              <ReactMarkdown
                                components={{
                                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                  code: ({ children, className }) => {
                                    const isInline = !className
                                    return isInline ? (
                                      <code className="px-1 py-0.5 rounded text-xs" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)', color: '#a8d8ff' }}>{children}</code>
                                    ) : (
                                      <code className="block p-2 rounded text-xs overflow-x-auto" style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}>{children}</code>
                                    )
                                  },
                                }}
                              >
                                {content}
                              </ReactMarkdown>
                              {isActive && <span className="inline-block w-2 h-4 ml-1 animate-pulse" style={{ backgroundColor: '#a8d8ff' }} />}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Chat Responses */}
              {chatResponses.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium" style={{ color: '#a8d8ff' }}>
                    Responses {chatResponses.length > 1 && '(Comparison Created)'}
                  </h3>
                  {chatResponses.map(response => (
                    <div key={response.id} className="p-4 rounded-lg" style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.6)',
                      border: '1px solid rgba(168, 216, 255, 0.1)'
                    }}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="px-2 py-1 rounded text-xs" style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.2)',
                          color: '#a8d8ff'
                        }}>
                          {response.provider} / {response.model}
                        </span>
                        <div className="flex items-center space-x-2">
                          {response.latency_ms && (
                            <span className="text-xs" style={{ color: '#b3d9ff' }}>{response.latency_ms}ms</span>
                          )}
                          <button
                            onClick={() => { setTagResponseId(response.id); setTagModalOpen(true) }}
                            className="px-2 py-1 rounded text-xs flex items-center space-x-1 hover:bg-white/10"
                            style={{ color: '#a8d8ff' }}
                          >
                            <Tag className="h-3 w-3" /><span>Tag</span>
                          </button>
                          <button
                            onClick={() => handleBankResponse(response.id)}
                            className="px-2 py-1 rounded text-xs flex items-center space-x-1 hover:bg-white/10"
                            style={{ color: '#10b981' }}
                          >
                            <ThumbsUp className="h-3 w-3" /><span>Bank This</span>
                          </button>
                        </div>
                      </div>
                      <div className="prose prose-sm prose-invert max-w-none" style={{ color: '#f0f0f5' }}>
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                            li: ({ children }) => <li className="mb-1">{children}</li>,
                            code: ({ children, className }) => {
                              const isInline = !className
                              return isInline ? (
                                <code className="px-1 py-0.5 rounded text-xs" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)', color: '#a8d8ff' }}>{children}</code>
                              ) : (
                                <code className="block p-2 rounded text-xs overflow-x-auto" style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}>{children}</code>
                              )
                            },
                            pre: ({ children }) => <pre className="p-2 rounded overflow-x-auto mb-2" style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}>{children}</pre>,
                            h1: ({ children }) => <h1 className="text-lg font-bold mb-2" style={{ color: '#a8d8ff' }}>{children}</h1>,
                            h2: ({ children }) => <h2 className="text-base font-bold mb-2" style={{ color: '#a8d8ff' }}>{children}</h2>,
                            h3: ({ children }) => <h3 className="text-sm font-bold mb-1" style={{ color: '#a8d8ff' }}>{children}</h3>,
                            strong: ({ children }) => <strong className="font-semibold" style={{ color: '#a8d8ff' }}>{children}</strong>,
                            a: ({ children, href }) => <a href={href} className="underline" style={{ color: '#a8d8ff' }} target="_blank" rel="noopener noreferrer">{children}</a>,
                          }}
                        >
                          {response.response_text}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Task Library View */}
          {viewMode === 'tasks' && (
            <div className="rounded-lg p-6" style={{
              backgroundColor: 'rgba(30, 30, 40, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>Task Library</h2>
                <button 
                  onClick={() => setCreateTaskOpen(true)}
                  className="px-3 py-2 rounded-lg flex items-center space-x-2 hover:bg-opacity-25 transition-all" 
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.15)',
                    border: '1px solid rgba(168, 216, 255, 0.4)',
                    color: '#a8d8ff'
                  }}
                >
                  <Plus className="h-4 w-4" /><span>New Task</span>
                </button>
              </div>

              {tasks.length === 0 ? (
                <p style={{ color: '#b3d9ff' }}>No tasks created yet. Create a task to automate knowledge extraction.</p>
              ) : (
                <div className="space-y-3">
                  {tasks.map(task => (
                    <div key={task.id} className="p-4 rounded-lg flex items-center justify-between" style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.6)',
                      border: '1px solid rgba(168, 216, 255, 0.1)'
                    }}>
                      <div>
                        <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{task.name}</h3>
                        <p className="text-sm mt-1" style={{ color: '#b3d9ff' }}>{task.description || `Type: ${task.task_type}`}</p>
                        <div className="flex items-center space-x-2 mt-2">
                          {task.target_models.map(model => (
                            <span key={model} className="px-2 py-0.5 rounded text-xs" style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.1)',
                              color: '#a8d8ff'
                            }}>{model}</span>
                          ))}
                        </div>
                      </div>
                      <button className="p-2 rounded hover:bg-white/10" style={{ color: '#10b981' }}>
                        <Play className="h-5 w-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Response Bank View */}
          {viewMode === 'bank' && (
            <div className="rounded-lg p-6" style={{
              backgroundColor: 'rgba(30, 30, 40, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Response Bank</h2>

              {/* Search and Filters */}
              <div className="space-y-3 mb-4">
                <div className="flex flex-wrap gap-2">
                  <div className="flex-1 min-w-[200px] relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: '#b3d9ff' }} />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      placeholder="Search responses..."
                      className="w-full pl-10 pr-4 py-2 rounded-lg text-sm"
                      style={{
                        backgroundColor: 'rgba(20, 20, 30, 0.8)',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                        color: '#f0f0f5'
                      }}
                    />
                  </div>
                  <select
                    value={filterProvider}
                    onChange={e => setFilterProvider(e.target.value)}
                    className="px-3 py-2 rounded-lg text-sm"
                    style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.8)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                  >
                    <option value="">All Providers</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="google">Google</option>
                    <option value="xai">xAI</option>
                  </select>
                  <button
                    onClick={searchResponses}
                    className="px-4 py-2 rounded-lg flex items-center space-x-2"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.2)',
                      border: '1px solid rgba(168, 216, 255, 0.4)',
                      color: '#a8d8ff'
                    }}
                  >
                    <Filter className="h-4 w-4" /><span>Search</span>
                  </button>
                </div>
              </div>

              {/* Response List */}
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" style={{ color: '#a8d8ff' }} />
                </div>
              ) : responses.length === 0 ? (
                <p style={{ color: '#b3d9ff' }}>No responses found. Use Interactive Chat to capture knowledge.</p>
              ) : (
                <div className="space-y-3">
                  {responses.map(response => (
                    <div key={response.id} className="p-4 rounded-lg" style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.6)',
                      border: '1px solid rgba(168, 216, 255, 0.1)'
                    }}>
                      {/* Header */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="px-2 py-1 rounded text-xs" style={{
                            backgroundColor: 'rgba(168, 216, 255, 0.2)',
                            color: '#a8d8ff'
                          }}>
                            {response.provider} / {response.model}
                          </span>
                          {response.quality_rating && (
                            <span className="flex items-center text-xs" style={{ color: '#fbbf24' }}>
                              {'★'.repeat(response.quality_rating)}{'☆'.repeat(5 - response.quality_rating)}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs" style={{ color: '#b3d9ff' }}>
                            {new Date(response.created_at).toLocaleString()}
                          </span>
                          <button
                            onClick={() => handleDeleteResponse(response.id)}
                            className="p-1 rounded hover:bg-red-500/20 text-red-400"
                            title="Delete response"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>

                      {/* Content */}
                      <p className="text-sm text-gray-400 mb-2 line-clamp-1">
                        <strong>Prompt:</strong> {response.prompt_sent}
                      </p>
                      <p className="text-sm line-clamp-3 mb-3" style={{ color: '#f0f0f5' }}>
                        {response.response_text}
                      </p>

                      {/* Organization Row */}
                      <div className="flex flex-wrap items-center gap-2 mb-2 pb-2" style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.1)' }}>
                        <select
                          value={response.domain_id || ''}
                          onChange={e => handleUpdateResponse(response.id, { domain_id: e.target.value || null })}
                          className="px-2 py-1 rounded text-xs"
                          style={{
                            backgroundColor: 'rgba(20, 20, 30, 0.8)',
                            border: '1px solid rgba(168, 216, 255, 0.2)',
                            color: '#b3d9ff'
                          }}
                        >
                          <option value="">No Domain</option>
                          {domains.map(d => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                          ))}
                        </select>

                        <select
                          value={response.topic_id || ''}
                          onChange={e => handleUpdateResponse(response.id, { topic_id: e.target.value || null })}
                          className="px-2 py-1 rounded text-xs"
                          style={{
                            backgroundColor: 'rgba(20, 20, 30, 0.8)',
                            border: '1px solid rgba(168, 216, 255, 0.2)',
                            color: '#b3d9ff'
                          }}
                        >
                          <option value="">No Topic</option>
                          {topics.filter(t => !response.domain_id || t.domain_id === response.domain_id).map(t => (
                            <option key={t.id} value={t.id}>{t.name}</option>
                          ))}
                        </select>

                        {/* Rating */}
                        <div className="flex items-center space-x-1">
                          {[1, 2, 3, 4, 5].map(rating => (
                            <button
                              key={rating}
                              onClick={() => handleUpdateResponse(response.id, { quality_rating: rating })}
                              className="text-sm hover:scale-110 transition-transform"
                              style={{ color: (response.quality_rating || 0) >= rating ? '#fbbf24' : '#4b5563' }}
                            >
                              ★
                            </button>
                          ))}
                        </div>

                        {/* Tags display */}
                        {response.tags && response.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {response.tags.map(tag => (
                              <span key={tag.id} className="px-1.5 py-0.5 rounded text-xs" style={{
                                backgroundColor: tag.color ? `${tag.color}30` : 'rgba(168, 216, 255, 0.1)',
                                color: tag.color || '#a8d8ff'
                              }}>
                                {tag.name}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => { setTagResponseId(response.id); setTagModalOpen(true) }}
                          className="px-2 py-1 rounded text-xs flex items-center space-x-1 hover:bg-white/10"
                          style={{ color: '#a8d8ff' }}
                        >
                          <Tag className="h-3 w-3" /><span>Tag</span>
                        </button>
                        <button
                          onClick={() => handleBankResponse(response.id)}
                          className="px-2 py-1 rounded text-xs flex items-center space-x-1 hover:bg-white/10"
                          style={{ color: '#10b981' }}
                        >
                          <ThumbsUp className="h-3 w-3" /><span>Bank</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Compare View */}
          {viewMode === 'compare' && (
            <div className="rounded-lg p-6" style={{
              backgroundColor: 'rgba(30, 30, 40, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>Model Comparison</h2>
                <button
                  onClick={() => setBlindMode(!blindMode)}
                  className="px-3 py-2 rounded-lg flex items-center space-x-2"
                  style={{
                    backgroundColor: blindMode ? 'rgba(168, 216, 255, 0.3)' : 'rgba(168, 216, 255, 0.15)',
                    border: '1px solid rgba(168, 216, 255, 0.4)',
                    color: '#a8d8ff'
                  }}
                >
                  {blindMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  <span>{blindMode ? 'Blind Mode On' : 'Blind Mode Off'}</span>
                </button>
              </div>

              {!selectedComparison ? (
                <div className="space-y-3">
                  {comparisons.length === 0 ? (
                    <p style={{ color: '#b3d9ff' }}>No comparisons yet. Use Interactive Chat with multiple models.</p>
                  ) : (
                    comparisons.map(comp => (
                      <button
                        key={comp.id}
                        onClick={() => loadComparisonDetails(comp.id)}
                        className="w-full p-4 rounded-lg text-left hover:bg-white/5 transition-all"
                        style={{
                          backgroundColor: 'rgba(20, 20, 30, 0.6)',
                          border: '1px solid rgba(168, 216, 255, 0.1)'
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`px-2 py-1 rounded text-xs ${
                            comp.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                          }`}>{comp.status}</span>
                          <span className="text-xs" style={{ color: '#b3d9ff' }}>
                            {new Date(comp.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm mt-2 line-clamp-2" style={{ color: '#f0f0f5' }}>{comp.prompt_used}</p>
                      </button>
                    ))
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <button
                    onClick={() => setSelectedComparison(null)}
                    className="text-sm flex items-center space-x-1"
                    style={{ color: '#a8d8ff' }}
                  >
                    <ChevronRight className="h-4 w-4 rotate-180" /><span>Back to list</span>
                  </button>

                  <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                    <p className="text-sm font-medium" style={{ color: '#a8d8ff' }}>Prompt:</p>
                    <p className="text-sm" style={{ color: '#f0f0f5' }}>{selectedComparison.comparison.prompt_used}</p>
                  </div>

                  {comparisonLoading ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin" style={{ color: '#a8d8ff' }} />
                    </div>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedComparison.responses.map(item => (
                          <div
                            key={item.response.id}
                            onClick={() => setSelectedWinner(item.response.id)}
                            className={`p-4 rounded-lg cursor-pointer transition-all ${
                              selectedWinner === item.response.id ? 'ring-2 ring-green-500' : ''
                            }`}
                            style={{
                              backgroundColor: 'rgba(20, 20, 30, 0.6)',
                              border: selectedWinner === item.response.id
                                ? '2px solid #10b981'
                                : '1px solid rgba(168, 216, 255, 0.1)'
                            }}
                          >
                            <div className="flex items-center justify-between mb-2">
                              {blindMode ? (
                                <span className="px-3 py-1 rounded text-lg font-bold" style={{
                                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                                  color: '#a8d8ff'
                                }}>
                                  {item.display_label || String.fromCharCode(65 + item.display_order)}
                                </span>
                              ) : (
                                <span className="px-2 py-1 rounded text-xs" style={{
                                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                                  color: '#a8d8ff'
                                }}>
                                  {item.response.provider} / {item.response.model}
                                </span>
                              )}
                              {selectedWinner === item.response.id && <Check className="h-5 w-5 text-green-500" />}
                            </div>
                            <div className="prose prose-sm prose-invert max-w-none text-sm" style={{ color: '#f0f0f5' }}>
                              <ReactMarkdown
                                components={{
                                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                  code: ({ children, className }) => {
                                    const isInline = !className
                                    return isInline ? (
                                      <code className="px-1 py-0.5 rounded text-xs" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)', color: '#a8d8ff' }}>{children}</code>
                                    ) : (
                                      <code className="block p-2 rounded text-xs overflow-x-auto" style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}>{children}</code>
                                    )
                                  },
                                }}
                              >
                                {item.response.response_text}
                              </ReactMarkdown>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="flex justify-center">
                        <button
                          onClick={handleSubmitVote}
                          disabled={!selectedWinner}
                          className="px-6 py-3 rounded-lg flex items-center space-x-2 disabled:opacity-50"
                          style={{
                            backgroundColor: selectedWinner ? 'rgba(16, 185, 129, 0.2)' : 'rgba(168, 216, 255, 0.15)',
                            border: `1px solid ${selectedWinner ? 'rgba(16, 185, 129, 0.6)' : 'rgba(168, 216, 255, 0.4)'}`,
                            color: selectedWinner ? '#10b981' : '#a8d8ff'
                          }}
                        >
                          <Award className="h-5 w-5" /><span>Submit Vote</span>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Structure View (Phase 5) */}
          {viewMode === 'structure' && (
            <div className="rounded-lg p-6" style={{
              backgroundColor: 'rgba(30, 30, 40, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Structuring</h2>
              <p className="text-sm mb-4" style={{ color: '#b3d9ff' }}>
                Extract structured data from banked responses using schemas
              </p>

              {/* Schema Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {schemas.map(schema => (
                  <div key={schema.key} className="p-4 rounded-lg" style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.6)',
                    border: '1px solid rgba(168, 216, 255, 0.1)'
                  }}>
                    <h3 className="font-medium" style={{ color: '#a8d8ff' }}>{schema.name}</h3>
                    <p className="text-xs mt-1" style={{ color: '#b3d9ff' }}>{schema.description}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {Object.keys(schema.fields).map(field => (
                        <span key={field} className="px-1 py-0.5 rounded text-xs" style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.1)',
                          color: '#a8d8ff'
                        }}>{field}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Banked Items for Structuring */}
              <h3 className="text-lg font-medium mb-3" style={{ color: '#a8d8ff' }}>Banked Responses</h3>
              {bankedItems.length === 0 ? (
                <p style={{ color: '#b3d9ff' }}>No banked responses. Bank some responses first.</p>
              ) : (
                <div className="space-y-3">
                  {bankedItems.map(banked => (
                    <div key={banked.id} className="p-4 rounded-lg" style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.6)',
                      border: '1px solid rgba(168, 216, 255, 0.1)'
                    }}>
                      <div className="flex items-center justify-between">
                        <div>
                          <span className={`px-2 py-1 rounded text-xs ${
                            banked.status === 'approved' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                          }`}>{banked.status}</span>
                          <span className="ml-2 text-xs" style={{ color: '#b3d9ff' }}>
                            {new Date(banked.banked_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <select
                            value={selectedSchema}
                            onChange={e => setSelectedSchema(e.target.value)}
                            className="px-2 py-1 rounded text-xs"
                            style={{
                              backgroundColor: 'rgba(20, 20, 30, 0.8)',
                              border: '1px solid rgba(168, 216, 255, 0.3)',
                              color: '#f0f0f5'
                            }}
                          >
                            <option value="">Select schema</option>
                            {schemas.map(s => (
                              <option key={s.key} value={s.key}>{s.name}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => selectedSchema && handleLLMExtract(banked.id, selectedSchema)}
                            disabled={!selectedSchema || extracting}
                            className="px-2 py-1 rounded text-xs flex items-center space-x-1 disabled:opacity-50"
                            style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.2)',
                              border: '1px solid rgba(168, 216, 255, 0.4)',
                              color: '#a8d8ff'
                            }}
                          >
                            {extracting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wand2 className="h-3 w-3" />}
                            <span>Auto Extract</span>
                          </button>
                          <button
                            onClick={() => {
                              setSelectedBanked(banked)
                              setStructureModalOpen(true)
                            }}
                            className="px-2 py-1 rounded text-xs flex items-center space-x-1"
                            style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.2)',
                              border: '1px solid rgba(168, 216, 255, 0.4)',
                              color: '#a8d8ff'
                            }}
                          >
                            <Edit3 className="h-3 w-3" /><span>Manual</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Structured Items */}
              <h3 className="text-lg font-medium mt-6 mb-3" style={{ color: '#a8d8ff' }}>
                Structured Extractions ({structuredItems.length})
              </h3>
              {structuredItems.length === 0 ? (
                <p style={{ color: '#b3d9ff' }}>No structured extractions yet.</p>
              ) : (
                <div className="space-y-3">
                  {structuredItems.map(item => (
                    <div key={item.id} className="p-4 rounded-lg" style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.6)',
                      border: '1px solid rgba(168, 216, 255, 0.1)'
                    }}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="px-2 py-1 rounded text-xs" style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.2)',
                          color: '#a8d8ff'
                        }}>{item.schema_name}</span>
                        <span className="text-xs" style={{ color: '#b3d9ff' }}>{item.extraction_method}</span>
                      </div>
                      <pre className="text-xs overflow-auto max-h-32 p-2 rounded" style={{
                        backgroundColor: 'rgba(0, 0, 0, 0.3)',
                        color: '#f0f0f5'
                      }}>
                        {JSON.stringify(item.structured_data, null, 2)}
                      </pre>
                      <div className="flex justify-end mt-2">
                        {datasets.length > 0 && (
                          <select
                            onChange={e => e.target.value && handleAddToDataset(e.target.value, undefined, item.id)}
                            className="px-2 py-1 rounded text-xs"
                            style={{
                              backgroundColor: 'rgba(20, 20, 30, 0.8)',
                              border: '1px solid rgba(168, 216, 255, 0.3)',
                              color: '#f0f0f5'
                            }}
                          >
                            <option value="">Add to dataset...</option>
                            {datasets.map(d => (
                              <option key={d.id} value={d.id}>{d.name}</option>
                            ))}
                          </select>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Datasets View (Phase 7) */}
          {viewMode === 'datasets' && (
            <div className="rounded-lg p-6" style={{
              backgroundColor: 'rgba(30, 30, 40, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>Datasets</h2>
                <button
                  onClick={() => setCreateDatasetOpen(true)}
                  className="px-3 py-2 rounded-lg flex items-center space-x-2"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.15)',
                    border: '1px solid rgba(168, 216, 255, 0.4)',
                    color: '#a8d8ff'
                  }}
                >
                  <Plus className="h-4 w-4" /><span>New Dataset</span>
                </button>
              </div>

              {!selectedDataset ? (
                <div className="space-y-3">
                  {datasets.length === 0 ? (
                    <p style={{ color: '#b3d9ff' }}>No datasets yet. Create one to start building training data.</p>
                  ) : (
                    datasets.map(dataset => (
                      <div
                        key={dataset.id}
                        onClick={() => {
                          setSelectedDataset(dataset)
                          loadDatasetDetails(dataset.id)
                        }}
                        className="p-4 rounded-lg cursor-pointer hover:bg-white/5 transition-all"
                        style={{
                          backgroundColor: 'rgba(20, 20, 30, 0.6)',
                          border: '1px solid rgba(168, 216, 255, 0.1)'
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{dataset.name}</h3>
                            <p className="text-xs mt-1" style={{ color: '#b3d9ff' }}>
                              v{dataset.version} • {dataset.item_count} items • {dataset.dataset_type}
                            </p>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs ${
                            dataset.status === 'exported' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
                          }`}>{dataset.status}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => { setSelectedDataset(null); setDatasetStats(null); setDatasetItems([]) }}
                      className="text-sm flex items-center space-x-1"
                      style={{ color: '#a8d8ff' }}
                    >
                      <ChevronRight className="h-4 w-4 rotate-180" /><span>Back to list</span>
                    </button>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleExportDataset(selectedDataset.id, 'jsonl')}
                        className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                        style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.2)',
                          border: '1px solid rgba(168, 216, 255, 0.4)',
                          color: '#a8d8ff'
                        }}
                      >
                        <Download className="h-3 w-3" /><span>JSONL</span>
                      </button>
                      <button
                        onClick={() => handleExportDataset(selectedDataset.id, 'csv')}
                        className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                        style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.2)',
                          border: '1px solid rgba(168, 216, 255, 0.4)',
                          color: '#a8d8ff'
                        }}
                      >
                        <FileText className="h-3 w-3" /><span>CSV</span>
                      </button>
                      <button
                        onClick={() => handleExportDataset(selectedDataset.id, 'alpaca')}
                        className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                        style={{
                          backgroundColor: 'rgba(168, 216, 255, 0.2)',
                          border: '1px solid rgba(168, 216, 255, 0.4)',
                          color: '#a8d8ff'
                        }}
                      >
                        <FileJson className="h-3 w-3" /><span>Alpaca</span>
                      </button>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                    <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{selectedDataset.name}</h3>
                    <p className="text-sm mt-1" style={{ color: '#b3d9ff' }}>{selectedDataset.description || 'No description'}</p>
                  </div>

                  {/* Stats */}
                  {datasetStats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                        <div className="text-lg font-bold" style={{ color: '#a8d8ff' }}>{datasetStats.total_items}</div>
                        <div className="text-xs" style={{ color: '#b3d9ff' }}>Total Items</div>
                      </div>
                      {Object.entries(datasetStats.by_split).map(([split, count]) => (
                        <div key={split} className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                          <div className="text-lg font-bold" style={{ color: '#c4b5fd' }}>{count}</div>
                          <div className="text-xs capitalize" style={{ color: '#b3d9ff' }}>{split}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Items */}
                  <h4 className="font-medium" style={{ color: '#a8d8ff' }}>Items ({datasetItems.length})</h4>
                  <div className="space-y-2 max-h-96 overflow-auto">
                    {datasetItems.map((item, idx) => (
                      <div key={item.id} className="p-3 rounded-lg flex items-center justify-between" style={{
                        backgroundColor: 'rgba(20, 20, 30, 0.6)',
                        border: '1px solid rgba(168, 216, 255, 0.1)'
                      }}>
                        <div className="flex items-center space-x-3">
                          <span className="text-xs" style={{ color: '#b3d9ff' }}>#{idx + 1}</span>
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            item.split === 'train' ? 'bg-blue-500/20 text-blue-400' :
                            item.split === 'validation' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-green-500/20 text-green-400'
                          }`}>{item.split}</span>
                          {item.structured && (
                            <span className="px-2 py-0.5 rounded text-xs" style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.1)',
                              color: '#a8d8ff'
                            }}>{item.structured.schema_name}</span>
                          )}
                        </div>
                        <button
                          onClick={async () => {
                            await fetch(`/api/v1/distillation/datasets/${selectedDataset.id}/items/${item.id}`, { method: 'DELETE' })
                            loadDatasetDetails(selectedDataset.id)
                            loadDatasets()
                          }}
                          className="p-1 rounded hover:bg-white/10"
                          style={{ color: '#ef4444' }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Expert Review View (Phase 6) */}
          {viewMode === 'review' && (
            <div className="rounded-lg p-6" style={{
              backgroundColor: 'rgba(30, 30, 40, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>Expert Review</h2>
                <button
                  onClick={() => setCreateQueueOpen(true)}
                  className="px-3 py-2 rounded-lg flex items-center space-x-2"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.15)',
                    border: '1px solid rgba(168, 216, 255, 0.4)',
                    color: '#a8d8ff'
                  }}
                >
                  <Plus className="h-4 w-4" /><span>New Queue</span>
                </button>
              </div>

              {!selectedQueue && !currentReviewItem ? (
                // Queue List
                <div className="space-y-3">
                  {reviewQueues.length === 0 ? (
                    <p style={{ color: '#b3d9ff' }}>No review queues yet. Create one to start expert review.</p>
                  ) : (
                    reviewQueues.map(queue => (
                      <div
                        key={queue.id}
                        className="p-4 rounded-lg"
                        style={{
                          backgroundColor: 'rgba(20, 20, 30, 0.6)',
                          border: '1px solid rgba(168, 216, 255, 0.1)'
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{queue.name}</h3>
                            <p className="text-xs mt-1" style={{ color: '#b3d9ff' }}>
                              {queue.description || 'No description'}
                            </p>
                            <div className="flex items-center space-x-4 mt-2">
                              <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">
                                {queue.pending_count || 0} pending
                              </span>
                              <span className="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400">
                                {queue.completed_count || 0} completed
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleAutoPopulateQueue(queue.id)}
                              className="px-2 py-1 rounded text-xs flex items-center space-x-1"
                              style={{
                                backgroundColor: 'rgba(168, 216, 255, 0.2)',
                                border: '1px solid rgba(168, 216, 255, 0.4)',
                                color: '#a8d8ff'
                              }}
                            >
                              <Users className="h-3 w-3" /><span>Populate</span>
                            </button>
                            <button
                              onClick={() => handleExportQueue(queue.id, 'csv')}
                              className="px-2 py-1 rounded text-xs flex items-center space-x-1"
                              style={{
                                backgroundColor: 'rgba(168, 216, 255, 0.2)',
                                border: '1px solid rgba(168, 216, 255, 0.4)',
                                color: '#a8d8ff'
                              }}
                            >
                              <Download className="h-3 w-3" /><span>Export</span>
                            </button>
                            <button
                              onClick={() => {
                                setSelectedQueue(queue)
                                loadReviewItems(queue.id)
                              }}
                              className="px-2 py-1 rounded text-xs"
                              style={{
                                backgroundColor: 'rgba(168, 216, 255, 0.2)',
                                border: '1px solid rgba(168, 216, 255, 0.4)',
                                color: '#a8d8ff'
                              }}
                            >
                              View Items
                            </button>
                            <button
                              onClick={() => getNextReviewItem(queue.id)}
                              className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                              style={{
                                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                                border: '1px solid rgba(16, 185, 129, 0.6)',
                                color: '#10b981'
                              }}
                            >
                              <Play className="h-3 w-3" /><span>Start Review</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              ) : currentReviewItem ? (
                // Active Review Interface
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => {
                        setCurrentReviewItem(null)
                        setSelectedQueue(null)
                      }}
                      className="text-sm flex items-center space-x-1"
                      style={{ color: '#a8d8ff' }}
                    >
                      <ChevronRight className="h-4 w-4 rotate-180" /><span>Back to queues</span>
                    </button>
                    <span className="text-sm" style={{ color: '#b3d9ff' }}>
                      Reviewing: {currentReviewItem.item.id.slice(0, 8)}...
                    </span>
                  </div>

                  {reviewLoading ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin" style={{ color: '#a8d8ff' }} />
                    </div>
                  ) : (
                    <>
                      {/* Response to Review */}
                      <div className="p-4 rounded-lg" style={{
                        backgroundColor: 'rgba(20, 20, 30, 0.6)',
                        border: '1px solid rgba(168, 216, 255, 0.1)'
                      }}>
                        {currentReviewItem.response && (
                          <>
                            <div className="flex items-center justify-between mb-2">
                              <span className="px-2 py-1 rounded text-xs" style={{
                                backgroundColor: 'rgba(168, 216, 255, 0.2)',
                                color: '#a8d8ff'
                              }}>
                                {currentReviewItem.response.provider} / {currentReviewItem.response.model}
                              </span>
                            </div>
                            <p className="text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>Prompt:</p>
                            <p className="text-sm mb-4 p-2 rounded" style={{
                              backgroundColor: 'rgba(0, 0, 0, 0.3)',
                              color: '#f0f0f5'
                            }}>
                              {currentReviewItem.response.prompt_sent}
                            </p>
                            <p className="text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>Response:</p>
                            <div className="prose prose-sm prose-invert max-w-none p-2 rounded" style={{
                              backgroundColor: 'rgba(0, 0, 0, 0.3)',
                              color: '#f0f0f5'
                            }}>
                              <ReactMarkdown
                                components={{
                                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                  code: ({ children, className }) => {
                                    const isInline = !className
                                    return isInline ? (
                                      <code className="px-1 py-0.5 rounded text-xs" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)', color: '#a8d8ff' }}>{children}</code>
                                    ) : (
                                      <code className="block p-2 rounded text-xs overflow-x-auto" style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}>{children}</code>
                                    )
                                  },
                                }}
                              >
                                {currentReviewItem.response.response_text}
                              </ReactMarkdown>
                            </div>
                          </>
                        )}
                      </div>

                      {/* Review Controls */}
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Quality Score (0-1)</label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={reviewScore}
                            onChange={e => setReviewScore(e.target.value)}
                            placeholder="0.8"
                            className="w-32 px-3 py-2 rounded-lg"
                            style={{
                              backgroundColor: 'rgba(20, 20, 30, 0.8)',
                              border: '1px solid rgba(168, 216, 255, 0.3)',
                              color: '#f0f0f5'
                            }}
                          />
                        </div>
                        <div>
                          <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Review Notes</label>
                          <textarea
                            value={reviewNotes}
                            onChange={e => setReviewNotes(e.target.value)}
                            placeholder="Optional notes about this response..."
                            className="w-full px-3 py-2 rounded-lg"
                            style={{
                              backgroundColor: 'rgba(20, 20, 30, 0.8)',
                              border: '1px solid rgba(168, 216, 255, 0.3)',
                              color: '#f0f0f5'
                            }}
                            rows={2}
                          />
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center justify-center space-x-4">
                        <button
                          onClick={() => handleSubmitReview('rejected')}
                          className="px-4 py-2 rounded-lg flex items-center space-x-2"
                          style={{
                            backgroundColor: 'rgba(239, 68, 68, 0.2)',
                            border: '1px solid rgba(239, 68, 68, 0.6)',
                            color: '#ef4444'
                          }}
                        >
                          <ThumbsDown className="h-4 w-4" /><span>Reject</span>
                        </button>
                        <button
                          onClick={() => handleSubmitReview('needs_revision')}
                          className="px-4 py-2 rounded-lg flex items-center space-x-2"
                          style={{
                            backgroundColor: 'rgba(251, 191, 36, 0.2)',
                            border: '1px solid rgba(251, 191, 36, 0.6)',
                            color: '#fbbf24'
                          }}
                        >
                          <AlertCircle className="h-4 w-4" /><span>Needs Revision</span>
                        </button>
                        <button
                          onClick={() => handleSubmitReview('approved')}
                          className="px-4 py-2 rounded-lg flex items-center space-x-2"
                          style={{
                            backgroundColor: 'rgba(16, 185, 129, 0.2)',
                            border: '1px solid rgba(16, 185, 129, 0.6)',
                            color: '#10b981'
                          }}
                        >
                          <ThumbsUp className="h-4 w-4" /><span>Approve</span>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : selectedQueue && (
                // Queue Items List
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => { setSelectedQueue(null); setReviewItems([]) }}
                      className="text-sm flex items-center space-x-1"
                      style={{ color: '#a8d8ff' }}
                    >
                      <ChevronRight className="h-4 w-4 rotate-180" /><span>Back to queues</span>
                    </button>
                    <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{selectedQueue.name}</h3>
                  </div>

                  <div className="space-y-2">
                    {reviewItems.length === 0 ? (
                      <p style={{ color: '#b3d9ff' }}>No items in this queue. Click "Populate" to add items.</p>
                    ) : (
                      reviewItems.map(item => (
                        <div key={item.id} className="p-3 rounded-lg flex items-center justify-between" style={{
                          backgroundColor: 'rgba(20, 20, 30, 0.6)',
                          border: '1px solid rgba(168, 216, 255, 0.1)'
                        }}>
                          <div className="flex items-center space-x-3">
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              item.status === 'approved' ? 'bg-green-500/20 text-green-400' :
                              item.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                              item.status === 'needs_revision' ? 'bg-yellow-500/20 text-yellow-400' :
                              item.status === 'in_review' ? 'bg-blue-500/20 text-blue-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>{item.status}</span>
                            {item.review_score !== null && (
                              <span className="text-xs" style={{ color: '#b3d9ff' }}>
                                Score: {item.review_score}
                              </span>
                            )}
                          </div>
                          <span className="text-xs" style={{ color: '#b3d9ff' }}>
                            Priority: {item.priority}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Statistics View */}
          {viewMode === 'stats' && (
            <div className="space-y-6">
              <div className="rounded-lg p-6" style={{
                backgroundColor: 'rgba(30, 30, 40, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.2)'
              }}>
                <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Statistics</h2>
                {statistics && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                      <div className="text-2xl font-bold" style={{ color: '#a8d8ff' }}>{statistics.total_responses}</div>
                      <div className="text-sm" style={{ color: '#b3d9ff' }}>Total Responses</div>
                    </div>
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                      <div className="text-2xl font-bold" style={{ color: '#10b981' }}>{statistics.total_banked}</div>
                      <div className="text-sm" style={{ color: '#b3d9ff' }}>Banked</div>
                    </div>
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                      <div className="text-2xl font-bold" style={{ color: '#c4b5fd' }}>{structuredItems.length}</div>
                      <div className="text-sm" style={{ color: '#b3d9ff' }}>Structured</div>
                    </div>
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                      <div className="text-2xl font-bold" style={{ color: '#fbbf24' }}>{datasets.length}</div>
                      <div className="text-sm" style={{ color: '#b3d9ff' }}>Datasets</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Model Preferences */}
              <div className="rounded-lg p-6" style={{
                backgroundColor: 'rgba(30, 30, 40, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.2)'
              }}>
                <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Model Preferences</h2>
                {modelPreferences && modelPreferences.total_votes > 0 ? (
                  <div className="space-y-3">
                    <p className="text-sm" style={{ color: '#b3d9ff' }}>Based on {modelPreferences.total_votes} votes</p>
                    {Object.entries(modelPreferences.win_rates).map(([model, rate]) => (
                      <div key={model}>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm" style={{ color: '#f0f0f5' }}>{model}</span>
                          <span className="text-sm" style={{ color: '#a8d8ff' }}>{rate}%</span>
                        </div>
                        <div className="h-2 rounded-full" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>
                          <div className="h-full rounded-full" style={{ width: `${rate}%`, backgroundColor: '#a8d8ff' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: '#b3d9ff' }}>No votes recorded yet.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tag Modal */}
      {tagModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="rounded-lg p-6 w-full max-w-md" style={{
            backgroundColor: 'rgba(30, 30, 40, 0.95)',
            border: '1px solid rgba(168, 216, 255, 0.3)'
          }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Add Tags</h3>
              <button onClick={() => { setTagModalOpen(false); setNewTagName('') }} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex space-x-2 mb-4">
              <input
                type="text"
                value={newTagName}
                onChange={e => setNewTagName(e.target.value)}
                placeholder="Enter tag name..."
                className="flex-1 px-3 py-2 rounded-lg"
                style={{
                  backgroundColor: 'rgba(20, 20, 30, 0.8)',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
                onKeyPress={e => e.key === 'Enter' && handleAddTags()}
              />
              <button
                onClick={handleAddTags}
                disabled={!newTagName.trim()}
                className="px-4 py-2 rounded-lg disabled:opacity-50"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  color: '#a8d8ff'
                }}
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {tags.map(tag => (
                <button
                  key={tag.id}
                  onClick={() => setNewTagName(tag.name)}
                  className="px-2 py-1 rounded text-xs"
                  style={{ backgroundColor: tag.color || 'rgba(168, 216, 255, 0.1)', color: '#f0f0f5' }}
                >
                  {tag.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Create Dataset Modal */}
      {createDatasetOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="rounded-lg p-6 w-full max-w-md" style={{
            backgroundColor: 'rgba(30, 30, 40, 0.95)',
            border: '1px solid rgba(168, 216, 255, 0.3)'
          }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Create Dataset</h3>
              <button onClick={() => setCreateDatasetOpen(false)} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Name</label>
                <input
                  type="text"
                  value={newDataset.name}
                  onChange={e => setNewDataset({ ...newDataset, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Version</label>
                <input
                  type="text"
                  value={newDataset.version}
                  onChange={e => setNewDataset({ ...newDataset, version: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Type</label>
                <select
                  value={newDataset.dataset_type}
                  onChange={e => setNewDataset({ ...newDataset, dataset_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                >
                  <option value="training">Training</option>
                  <option value="evaluation">Evaluation</option>
                  <option value="benchmark">Benchmark</option>
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Description</label>
                <textarea
                  value={newDataset.description}
                  onChange={e => setNewDataset({ ...newDataset, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                  rows={3}
                />
              </div>
              <button
                onClick={handleCreateDataset}
                disabled={!newDataset.name || !newDataset.version}
                className="w-full py-2 rounded-lg disabled:opacity-50"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  color: '#a8d8ff'
                }}
              >
                Create Dataset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Structure Modal */}
      {structureModalOpen && selectedBanked && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-auto" style={{
            backgroundColor: 'rgba(30, 30, 40, 0.95)',
            border: '1px solid rgba(168, 216, 255, 0.3)'
          }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Manual Structuring</h3>
              <button onClick={() => { setStructureModalOpen(false); setStructuredData({}) }} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Schema</label>
                <select
                  value={selectedSchema}
                  onChange={e => setSelectedSchema(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                >
                  <option value="">Select schema</option>
                  {schemas.map(s => (
                    <option key={s.key} value={s.key}>{s.name}</option>
                  ))}
                </select>
              </div>
              {selectedSchema && schemas.find(s => s.key === selectedSchema) && (
                <div className="space-y-3">
                  {Object.entries(schemas.find(s => s.key === selectedSchema)!.fields).map(([field, info]) => (
                    <div key={field}>
                      <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>
                        {field} {info.required && <span className="text-red-400">*</span>}
                      </label>
                      <textarea
                        value={structuredData[field] || ''}
                        onChange={e => setStructuredData({ ...structuredData, [field]: e.target.value })}
                        placeholder={info.description}
                        className="w-full px-3 py-2 rounded-lg"
                        style={{
                          backgroundColor: 'rgba(20, 20, 30, 0.8)',
                          border: '1px solid rgba(168, 216, 255, 0.3)',
                          color: '#f0f0f5'
                        }}
                        rows={2}
                      />
                    </div>
                  ))}
                </div>
              )}
              <button
                onClick={handleSaveStructured}
                disabled={!selectedSchema}
                className="w-full py-2 rounded-lg disabled:opacity-50"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  color: '#a8d8ff'
                }}
              >
                Save Structured Data
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Task Modal */}
      {createTaskOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto" style={{
            backgroundColor: 'rgba(30, 30, 40, 0.95)',
            border: '1px solid rgba(168, 216, 255, 0.3)'
          }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Create New Task</h3>
              <button onClick={() => setCreateTaskOpen(false)} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Task Name *</label>
                <input
                  type="text"
                  value={newTask.name}
                  onChange={e => setNewTask({ ...newTask, name: e.target.value })}
                  placeholder="e.g., Insurance FAQ Generator"
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Description</label>
                <input
                  type="text"
                  value={newTask.description}
                  onChange={e => setNewTask({ ...newTask, description: e.target.value })}
                  placeholder="Optional description..."
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Task Type</label>
                <select
                  value={newTask.task_type}
                  onChange={e => setNewTask({ ...newTask, task_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                >
                  <option value="freeform">Freeform</option>
                  <option value="qa">Q&A</option>
                  <option value="summary">Summary</option>
                  <option value="instruction">Instruction</option>
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Prompt Template *</label>
                <textarea
                  value={newTask.prompt_template}
                  onChange={e => setNewTask({ ...newTask, prompt_template: e.target.value })}
                  placeholder="Enter the prompt template. Use {{variable}} for dynamic values..."
                  className="w-full px-3 py-2 rounded-lg font-mono text-sm"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                  rows={4}
                />
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>System Prompt</label>
                <textarea
                  value={newTask.system_prompt}
                  onChange={e => setNewTask({ ...newTask, system_prompt: e.target.value })}
                  placeholder="Optional system prompt for the model..."
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                  rows={2}
                />
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Target Models</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {newTask.target_models.map((model, idx) => (
                    <span key={idx} className="px-2 py-1 rounded text-xs flex items-center space-x-1" style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.2)',
                      color: '#a8d8ff'
                    }}>
                      <span>{model}</span>
                      <button 
                        onClick={() => setNewTask({
                          ...newTask,
                          target_models: newTask.target_models.filter((_, i) => i !== idx)
                        })}
                        className="hover:text-red-400"
                      >×</button>
                    </span>
                  ))}
                </div>
                <select
                  value=""
                  onChange={e => {
                    if (e.target.value && !newTask.target_models.includes(e.target.value)) {
                      setNewTask({
                        ...newTask,
                        target_models: [...newTask.target_models, e.target.value]
                      })
                    }
                  }}
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                >
                  <option value="">+ Add model</option>
                  {availableModels
                    .filter(m => !newTask.target_models.includes(m.id) && apiKeys[m.provider])
                    .map(m => (
                      <option key={m.id} value={m.id}>{m.provider}: {m.name}</option>
                    ))
                  }
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Domain</label>
                  <select
                    value={newTask.domain_id}
                    onChange={e => setNewTask({ ...newTask, domain_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg"
                    style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.8)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                  >
                    <option value="">No domain</option>
                    {domains.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Topic</label>
                  <select
                    value={newTask.topic_id}
                    onChange={e => setNewTask({ ...newTask, topic_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg"
                    style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.8)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                  >
                    <option value="">No topic</option>
                    {topics.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex space-x-3 pt-2">
                <button
                  onClick={() => setCreateTaskOpen(false)}
                  className="flex-1 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(100, 100, 100, 0.2)',
                    border: '1px solid rgba(100, 100, 100, 0.4)',
                    color: '#999'
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTask}
                  disabled={!newTask.name.trim() || !newTask.prompt_template.trim() || taskLoading}
                  className="flex-1 py-2 rounded-lg disabled:opacity-50 flex items-center justify-center space-x-2"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.2)',
                    border: '1px solid rgba(168, 216, 255, 0.4)',
                    color: '#a8d8ff'
                  }}
                >
                  {taskLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    <span>Create Task</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Queue Modal */}
      {createQueueOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="rounded-lg p-6 w-full max-w-md" style={{
            backgroundColor: 'rgba(30, 30, 40, 0.95)',
            border: '1px solid rgba(168, 216, 255, 0.3)'
          }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Create Review Queue</h3>
              <button onClick={() => setCreateQueueOpen(false)} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Name</label>
                <input
                  type="text"
                  value={newQueue.name}
                  onChange={e => setNewQueue({ ...newQueue, name: e.target.value })}
                  placeholder="e.g., Insurance Q&A Review"
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                />
              </div>
              <div>
                <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Description</label>
                <textarea
                  value={newQueue.description}
                  onChange={e => setNewQueue({ ...newQueue, description: e.target.value })}
                  placeholder="Optional description..."
                  className="w-full px-3 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                  rows={3}
                />
              </div>
              <button
                onClick={handleCreateQueue}
                disabled={!newQueue.name}
                className="w-full py-2 rounded-lg disabled:opacity-50"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  color: '#a8d8ff'
                }}
              >
                Create Queue
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
