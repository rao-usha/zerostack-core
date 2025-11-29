import { useEffect, useState } from 'react'
import { FlaskConical, RefreshCw, AlertCircle, ChevronRight, Package, Layers, Database, FileText, Users, Target } from 'lucide-react'
import {
  listCollectorContexts,
  listCollectorDatasets,
  getCollectorVariant,
  getCollectorDataset,
  getCollectorContext,
  checkCollectorHealth,
  queryTable
} from '../api/client'

interface Variant {
  id: string
  context_id: string
  domain?: string
  persona?: string
  task?: string
  style?: string
  body_text?: string
  created_at: string
}

interface Dataset {
  id: string
  name: string
  version: string
  kind: string
  variant_ids: string[]
  file_uris: string[]
  created_at: string
}

type ViewMode = 'variants' | 'datasets' | 'examples' | 'teacher_runs' | 'targets' | 'contexts'

export default function Distillation() {
  const [variants, setVariants] = useState<Variant[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [examples, setExamples] = useState<any[]>([])
  const [teacherRuns, setTeacherRuns] = useState<any[]>([])
  const [targets, setTargets] = useState<any[]>([])
  const [contexts, setContexts] = useState<any[]>([])
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [healthStatus, setHealthStatus] = useState<{ ok: boolean } | null>(null)
  
  const [viewMode, setViewMode] = useState<ViewMode>('variants')
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    checkHealth()
    loadData()
  }, [])

  useEffect(() => {
    if (viewMode !== 'variants' && viewMode !== 'datasets') {
      loadTableData(viewMode)
    }
  }, [viewMode])

  const checkHealth = async () => {
    try {
      const status = await checkCollectorHealth()
      setHealthStatus(status)
    } catch (err: any) {
      setError(`Cannot connect to nex-collector: ${err.message}`)
      setHealthStatus({ ok: false })
    }
  }

  const loadData = async () => {
    await Promise.all([
      loadVariants(),
      loadDatasets()
    ])
  }

  const loadVariants = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listCollectorContexts()
      setVariants(data)
    } catch (err: any) {
      setError(`Failed to load variants: ${err.message}`)
      console.error('Failed to load variants:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadDatasets = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listCollectorDatasets()
      setDatasets(data)
    } catch (err: any) {
      setError(`Failed to load datasets: ${err.message}`)
      console.error('Failed to load datasets:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadTableData = async (tableName: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await queryTable(tableName, 100, 0)
      
      if (tableName === 'synthetic_examples') {
        setExamples(data.data || [])
      } else if (tableName === 'teacher_runs') {
        setTeacherRuns(data.data || [])
      } else if (tableName === 'targets') {
        setTargets(data.data || [])
      } else if (tableName === 'context_docs') {
        setContexts(data.data || [])
      }
    } catch (err: any) {
      setError(`Failed to load ${tableName}: ${err.message}`)
      console.error(`Failed to load ${tableName}:`, err)
    } finally {
      setLoading(false)
    }
  }

  const handleItemClick = async (item: any, type: ViewMode) => {
    try {
      setLoading(true)
      setError(null)
      
      if (type === 'variants') {
        const detail = await getCollectorVariant(item.id)
        setSelectedItem(detail)
      } else if (type === 'datasets') {
        const detail = await getCollectorDataset(item.id)
        setSelectedItem(detail)
      } else if (type === 'contexts') {
        const detail = await getCollectorContext(item.id)
        setSelectedItem(detail)
      } else {
        setSelectedItem(item)
      }
    } catch (err: any) {
      setError(`Failed to load details: ${err.message}`)
      console.error('Failed to load details:', err)
    } finally {
      setLoading(false)
    }
  }

  const getCurrentItems = () => {
    const items = {
      variants,
      datasets,
      examples,
      teacher_runs: teacherRuns,
      targets,
      contexts
    }[viewMode] || []
    
    if (!searchTerm) return items
    
    const searchLower = searchTerm.toLowerCase()
    return items.filter((item: any) => 
      JSON.stringify(item).toLowerCase().includes(searchLower)
    )
  }

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'null'
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2)
    }
    return String(value)
  }

  const currentItems = getCurrentItems()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-3" style={{ color: '#a8d8ff' }}>
            <FlaskConical className="h-8 w-8" />
            <span>Distillation Explorer</span>
          </h1>
          <p className="mt-2" style={{ color: '#b3d9ff' }}>
            Explore distillation data from nex-collector (localhost:8080)
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {healthStatus && (
            <div className="flex items-center space-x-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  healthStatus.ok ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span style={{ color: '#b3d9ff' }}>
                {healthStatus.ok ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          )}
          <button
            onClick={() => {
              loadData()
              if (viewMode !== 'variants' && viewMode !== 'datasets') {
                loadTableData(viewMode)
              }
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
      </div>

      {error && (
        <div
          className="p-4 rounded-lg flex items-center space-x-2"
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#fca5a5'
          }}
        >
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar - View Selector */}
        <div
          className="lg:col-span-1 rounded-lg p-4"
          style={{
            backgroundColor: 'rgba(30, 30, 40, 0.8)',
            border: '1px solid rgba(168, 216, 255, 0.2)'
          }}
        >
          <h2 className="text-lg font-semibold mb-4" style={{ color: '#a8d8ff' }}>
            Data Views
          </h2>
          <div className="space-y-2">
            {[
              { mode: 'variants' as ViewMode, label: 'Variants', icon: Layers },
              { mode: 'contexts' as ViewMode, label: 'Contexts', icon: FileText },
              { mode: 'datasets' as ViewMode, label: 'Datasets', icon: Package },
              { mode: 'examples' as ViewMode, label: 'Examples', icon: Database },
              { mode: 'teacher_runs' as ViewMode, label: 'Teacher Runs', icon: Users },
              { mode: 'targets' as ViewMode, label: 'Targets', icon: Target },
            ].map(({ mode, label, icon: Icon }) => (
              <button
                key={mode}
                onClick={() => {
                  setViewMode(mode)
                  setSelectedItem(null)
                  setSearchTerm('')
                }}
                className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all"
                style={
                  viewMode === mode
                    ? {
                        background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                        color: '#a8d8ff',
                        border: '1px solid rgba(168, 216, 255, 0.4)'
                      }
                    : {
                        color: '#f0f0f5'
                      }
                }
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="lg:col-span-3">
          <div className="space-y-4">
            {/* Search */}
            <div
              className="rounded-lg p-4"
              style={{
                backgroundColor: 'rgba(30, 30, 40, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.2)'
              }}
            >
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 rounded-lg"
                style={{
                  backgroundColor: 'rgba(20, 20, 30, 0.8)',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
              />
            </div>

            {/* Items List */}
            {loading && currentItems.length === 0 ? (
              <div className="text-center py-8" style={{ color: '#b3d9ff' }}>
                Loading...
              </div>
            ) : currentItems.length === 0 ? (
              <div className="text-center py-8" style={{ color: '#b3d9ff' }}>
                No items found
              </div>
            ) : (
              <div
                className="rounded-lg overflow-hidden"
                style={{
                  backgroundColor: 'rgba(30, 30, 40, 0.8)',
                  border: '1px solid rgba(168, 216, 255, 0.2)'
                }}
              >
                <div className="divide-y" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
                  {currentItems.map((item: any, idx: number) => (
                    <button
                      key={idx}
                      onClick={() => handleItemClick(item, viewMode)}
                      className="w-full text-left p-4 hover:bg-opacity-50 transition-all"
                      style={{
                        backgroundColor: selectedItem?.id === item.id
                          ? 'rgba(168, 216, 255, 0.15)'
                          : 'transparent'
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium mb-1" style={{ color: '#f0f0f5' }}>
                            {item.id || item.name || `Item ${idx + 1}`}
                          </div>
                          <div className="text-sm space-y-1" style={{ color: '#b3d9ff' }}>
                            {viewMode === 'variants' && (
                              <>
                                <div>Domain: {item.domain || 'N/A'} | Persona: {item.persona || 'N/A'} | Task: {item.task || 'N/A'}</div>
                                <div>Context: {item.context_id}</div>
                              </>
                            )}
                            {viewMode === 'datasets' && (
                              <>
                                <div>{item.name}@{item.version} ({item.kind})</div>
                                <div>Variants: {item.variant_ids?.length || 0} | Files: {item.file_uris?.length || 0}</div>
                              </>
                            )}
                            {viewMode === 'examples' && (
                              <>
                                <div>Type: {item.example_type} | Variant: {item.variant_id}</div>
                                <div className="truncate max-w-md">
                                  {formatValue(item.input_json).substring(0, 100)}...
                                </div>
                              </>
                            )}
                            {viewMode === 'teacher_runs' && (
                              <>
                                <div>Provider: {item.provider} | Model: {item.model}</div>
                                <div>Example: {item.example_id}</div>
                              </>
                            )}
                            {viewMode === 'targets' && (
                              <>
                                <div>Example: {item.example_id}</div>
                                <div className="truncate max-w-md">
                                  {item.y_text?.substring(0, 100)}...
                                </div>
                              </>
                            )}
                            {viewMode === 'contexts' && (
                              <>
                                <div>{item.title} (v{item.version})</div>
                                <div className="truncate max-w-md">
                                  {item.body_text?.substring(0, 100)}...
                                </div>
                              </>
                            )}
                            {item.created_at && (
                              <div className="text-xs opacity-75">
                                {new Date(item.created_at).toLocaleString()}
                              </div>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="h-5 w-5 ml-4" style={{ color: '#a8d8ff' }} />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Detail Panel */}
      {selectedItem && (
        <div
          className="rounded-lg p-6 mt-6"
          style={{
            backgroundColor: 'rgba(30, 30, 40, 0.8)',
            border: '1px solid rgba(168, 216, 255, 0.2)'
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>
              Details
            </h2>
            <button
              onClick={() => setSelectedItem(null)}
              className="px-3 py-1 rounded-lg text-sm"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                border: '1px solid rgba(168, 216, 255, 0.4)',
                color: '#a8d8ff'
              }}
            >
              Close
            </button>
          </div>
          <div className="space-y-2">
            {Object.entries(selectedItem).map(([key, value]) => (
              <div key={key} className="border-b pb-2" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
                <div className="font-medium mb-1" style={{ color: '#a8d8ff' }}>{key}</div>
                <div className="text-sm whitespace-pre-wrap break-words" style={{ color: '#f0f0f5' }}>
                  {formatValue(value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
