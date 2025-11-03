import { useState, useEffect } from 'react'
import {
  Layers,
  Plus,
  BookOpen,
  GitBranch,
  Download,
  Edit,
  Trash2,
  Filter,
  Sparkles,
  Settings,
  X,
  FileText,
  Upload,
  File,
  Sparkles as SparklesIcon,
} from 'lucide-react'
import {
  listContexts,
  createContext,
  getContext,
  getContextLayers,
  addContextLayer,
  updateContextLayer,
  deleteContextLayer,
  createContextVersion,
  getContextVersions,
  upsertContextDictionary,
  getContextDictionaries,
  exportContextPack,
  uploadContextDocument,
  getContextDocuments,
  summarizeDocument,
  deleteContextDocument,
} from '../api/client'

interface Context {
  id: string
  name: string
  description?: string
  metadata?: any
  created_at?: string
}

interface Layer {
  id: string
  kind: string
  name: string
  spec: any
  enabled: boolean
  order: number
}

interface Dictionary {
  id: string
  name: string
  entries: Record<string, string>
}

interface Document {
  id: string
  name: string
  filename: string
  file_size: number
  content_type?: string
  summary?: string
  sha256?: string
  created_at?: string
}

interface Version {
  id: string
  version: string
  digest: string
  diff_summary?: string
  created_at?: string
}

export default function Contexts() {
  const [contexts, setContexts] = useState<Context[]>([])
  const [selectedContext, setSelectedContext] = useState<Context | null>(null)
  const [layers, setLayers] = useState<Layer[]>([])
  const [dictionaries, setDictionaries] = useState<Dictionary[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [versions, setVersions] = useState<Version[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showLayerModal, setShowLayerModal] = useState(false)
  const [showDictionaryModal, setShowDictionaryModal] = useState(false)
  const [showDocumentModal, setShowDocumentModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'layers' | 'dictionaries' | 'versions'>('overview')
  const [newContextName, setNewContextName] = useState('')
  const [newContextDesc, setNewContextDesc] = useState('')
  const [newLayerKind, setNewLayerKind] = useState('select')
  const [newLayerName, setNewLayerName] = useState('')
  const [newLayerSpec, setNewLayerSpec] = useState('{}')
  const [newDictName, setNewDictName] = useState('')
  const [newDictEntries, setNewDictEntries] = useState('')

  useEffect(() => {
    loadContexts()
  }, [])

  useEffect(() => {
    if (selectedContext) {
      setActiveTab('overview')
      loadContextData()
    }
  }, [selectedContext])

  const loadContexts = async () => {
    try {
      const data = await listContexts()
      setContexts(data)
    } catch (error) {
      console.error('Failed to load contexts:', error)
      alert('Failed to load contexts')
    }
  }

  const loadContextData = async () => {
    if (!selectedContext) return
    try {
      const [layersData, dictsData, docsData, versionsData] = await Promise.all([
        getContextLayers(selectedContext.id),
        getContextDictionaries(selectedContext.id),
        getContextDocuments(selectedContext.id),
        getContextVersions(selectedContext.id),
      ])
      setLayers(layersData)
      setDictionaries(dictsData)
      setDocuments(docsData)
      setVersions(versionsData)
    } catch (error) {
      console.error('Failed to load context data:', error)
    }
  }

  const handleCreateContext = async () => {
    if (!newContextName.trim()) {
      alert('Context name is required')
      return
    }
    setLoading(true)
    try {
      await createContext(newContextName, newContextDesc)
      setNewContextName('')
      setNewContextDesc('')
      setShowCreateModal(false)
      loadContexts()
    } catch (error: any) {
      console.error('Failed to create context:', error)
      alert(error.response?.data?.detail || 'Failed to create context')
    } finally {
      setLoading(false)
    }
  }

  const handleAddLayer = async () => {
    if (!selectedContext || !newLayerName.trim()) {
      alert('Context must be selected and layer name is required')
      return
    }
    setLoading(true)
    try {
      let spec = {}
      try {
        spec = JSON.parse(newLayerSpec)
      } catch (e) {
        alert('Invalid JSON in layer spec')
        return
      }
      await addContextLayer(selectedContext.id, newLayerKind, newLayerName, spec)
      setNewLayerKind('select')
      setNewLayerName('')
      setNewLayerSpec('{}')
      setShowLayerModal(false)
      loadContextData()
    } catch (error: any) {
      console.error('Failed to add layer:', error)
      alert(error.response?.data?.detail || 'Failed to add layer')
    } finally {
      setLoading(false)
    }
  }

  const handleAddDictionary = async () => {
    if (!selectedContext || !newDictName.trim()) {
      alert('Context must be selected and dictionary name is required')
      return
    }
    setLoading(true)
    try {
      const entries: Record<string, string> = {}
      newDictEntries.split('\n').forEach((line) => {
        const [key, ...valueParts] = line.split(':')
        if (key && valueParts.length > 0) {
          entries[key.trim()] = valueParts.join(':').trim()
        }
      })
      await upsertContextDictionary(selectedContext.id, newDictName, entries)
      setNewDictName('')
      setNewDictEntries('')
      setShowDictionaryModal(false)
      loadContextData()
    } catch (error: any) {
      console.error('Failed to add dictionary:', error)
      alert(error.response?.data?.detail || 'Failed to add dictionary')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateVersion = async () => {
    if (!selectedContext) return
    setLoading(true)
    try {
      await createContextVersion(selectedContext.id)
      loadContextData()
      alert('Context versioned successfully!')
    } catch (error: any) {
      console.error('Failed to create version:', error)
      alert(error.response?.data?.detail || 'Failed to create version')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (versionId?: string) => {
    if (!selectedContext) return
    try {
      const pack = await exportContextPack(selectedContext.id, versionId)
      const blob = new Blob([JSON.stringify(pack, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `context_${selectedContext.id}${versionId ? `_v${versionId}` : ''}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error: any) {
      console.error('Failed to export:', error)
      alert(error.response?.data?.detail || 'Failed to export context')
    }
  }

  const handleToggleLayer = async (layerId: string, currentEnabled: boolean) => {
    try {
      await updateContextLayer(layerId, !currentEnabled)
      loadContextData()
    } catch (error: any) {
      console.error('Failed to update layer:', error)
      alert(error.response?.data?.detail || 'Failed to update layer')
    }
  }

  const handleDeleteLayer = async (layerId: string) => {
    if (!confirm('Delete this layer?')) return
    try {
      await deleteContextLayer(layerId)
      loadContextData()
    } catch (error: any) {
      console.error('Failed to delete layer:', error)
      alert(error.response?.data?.detail || 'Failed to delete layer')
    }
  }

  const handleUploadDocument = async () => {
    if (!selectedContext || !selectedFile) {
      alert('Please select a file')
      return
    }
    setLoading(true)
    try {
      await uploadContextDocument(selectedContext.id, selectedFile, undefined, true)
      setSelectedFile(null)
      setShowDocumentModal(false)
      loadContextData()
      alert('Document uploaded and summarized successfully!')
    } catch (error: any) {
      console.error('Failed to upload document:', error)
      alert(error.response?.data?.detail || 'Failed to upload document')
    } finally {
      setLoading(false)
    }
  }

  const handleSummarizeDocument = async (documentId: string) => {
    setLoading(true)
    try {
      const result = await summarizeDocument(documentId)
      loadContextData()
      alert('Document summarized successfully!')
    } catch (error: any) {
      console.error('Failed to summarize document:', error)
      alert(error.response?.data?.detail || 'Failed to summarize document')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm('Delete this document?')) return
    try {
      await deleteContextDocument(documentId)
      loadContextData()
    } catch (error: any) {
      console.error('Failed to delete document:', error)
      alert(error.response?.data?.detail || 'Failed to delete document')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: '#a8d8ff' }}>
            Context Engineering
          </h1>
          <p className="mt-2" style={{ color: '#9ca3af' }}>
            Create, version, and export context workspaces
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 rounded-lg font-medium flex items-center gap-2"
          style={{
            backgroundColor: 'rgba(168, 216, 255, 0.1)',
            color: '#a8d8ff',
            border: '1px solid rgba(168, 216, 255, 0.3)',
          }}
        >
          <Plus className="w-4 h-4" />
          New Context
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Contexts List */}
        <div
          className="lg:col-span-1 rounded-lg p-6"
          style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}
        >
          <h2 className="text-xl font-semibold mb-4" style={{ color: '#f0f0f5' }}>
            Contexts
          </h2>
          <div className="space-y-2">
            {contexts.length === 0 ? (
              <p className="text-sm" style={{ color: '#9ca3af' }}>
                No contexts yet. Create one to get started.
              </p>
            ) : (
              contexts.map((ctx) => (
                <button
                  key={ctx.id}
                  onClick={() => setSelectedContext(ctx)}
                  className={`w-full text-left p-3 rounded-lg transition-all ${
                    selectedContext?.id === ctx.id
                      ? 'ring-2'
                      : 'hover:bg-opacity-50'
                  }`}
                  style={{
                    backgroundColor:
                      selectedContext?.id === ctx.id
                        ? 'rgba(168, 216, 255, 0.2)'
                        : 'rgba(168, 216, 255, 0.05)',
                    border:
                      selectedContext?.id === ctx.id
                        ? '1px solid rgba(168, 216, 255, 0.5)'
                        : '1px solid rgba(168, 216, 255, 0.1)',
                    color: selectedContext?.id === ctx.id ? '#a8d8ff' : '#f0f0f5',
                  }}
                >
                  <div className="font-medium">{ctx.name}</div>
                  {ctx.description && (
                    <div className="text-sm mt-1 opacity-75">{ctx.description}</div>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Context Details */}
        <div
          className="lg:col-span-2 rounded-lg p-6 space-y-6"
          style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.15)' }}
        >
          {selectedContext ? (
            <>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>
                    {selectedContext.name}
                  </h2>
                  {selectedContext.description && (
                    <p className="mt-1" style={{ color: '#9ca3af' }}>
                      {selectedContext.description}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleCreateVersion}
                    disabled={loading}
                    className="px-4 py-2 rounded-lg font-medium flex items-center gap-2"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.1)',
                      color: '#a8d8ff',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                    }}
                  >
                    <GitBranch className="w-4 h-4" />
                    Version
                  </button>
                  <button
                    onClick={() => handleExport()}
                    className="px-4 py-2 rounded-lg font-medium flex items-center gap-2"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.1)',
                      color: '#a8d8ff',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                    }}
                  >
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-2 border-b" style={{ borderColor: 'rgba(168, 216, 255, 0.15)' }}>
                {(['overview', 'documents', 'layers', 'dictionaries', 'versions'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className="px-4 py-2 font-medium capitalize transition-all"
                    style={{
                      color: activeTab === tab ? '#a8d8ff' : '#9ca3af',
                      borderBottom: activeTab === tab ? '2px solid #a8d8ff' : '2px solid transparent',
                    }}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6 mt-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                        <span className="text-sm font-medium" style={{ color: '#9ca3af' }}>Documents</span>
                      </div>
                      <div className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>{documents.length}</div>
                    </div>
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                      <div className="flex items-center gap-2 mb-2">
                        <Layers className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                        <span className="text-sm font-medium" style={{ color: '#9ca3af' }}>Layers</span>
                      </div>
                      <div className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>{layers.length}</div>
                    </div>
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                      <div className="flex items-center gap-2 mb-2">
                        <BookOpen className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                        <span className="text-sm font-medium" style={{ color: '#9ca3af' }}>Dictionaries</span>
                      </div>
                      <div className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>{dictionaries.length}</div>
                    </div>
                    <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                      <div className="flex items-center gap-2 mb-2">
                        <GitBranch className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                        <span className="text-sm font-medium" style={{ color: '#9ca3af' }}>Versions</span>
                      </div>
                      <div className="text-2xl font-bold" style={{ color: '#f0f0f5' }}>{versions.length}</div>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3" style={{ color: '#f0f0f5' }}>Quick Actions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <button
                        onClick={() => setActiveTab('documents')}
                        className="p-4 rounded-lg text-left flex items-center justify-between hover:scale-[1.02] transition-transform"
                        style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                      >
                        <div className="flex items-center gap-3">
                          <Upload className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                          <span style={{ color: '#f0f0f5' }}>Upload Document</span>
                        </div>
                        <Plus className="w-4 h-4" style={{ color: '#a8d8ff' }} />
                      </button>
                      <button
                        onClick={() => setActiveTab('layers')}
                        className="p-4 rounded-lg text-left flex items-center justify-between hover:scale-[1.02] transition-transform"
                        style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                      >
                        <div className="flex items-center gap-3">
                          <Layers className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                          <span style={{ color: '#f0f0f5' }}>Add Layer</span>
                        </div>
                        <Plus className="w-4 h-4" style={{ color: '#a8d8ff' }} />
                      </button>
                      <button
                        onClick={() => setActiveTab('dictionaries')}
                        className="p-4 rounded-lg text-left flex items-center justify-between hover:scale-[1.02] transition-transform"
                        style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                      >
                        <div className="flex items-center gap-3">
                          <BookOpen className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                          <span style={{ color: '#f0f0f5' }}>Add Dictionary</span>
                        </div>
                        <Plus className="w-4 h-4" style={{ color: '#a8d8ff' }} />
                      </button>
                      <button
                        onClick={handleCreateVersion}
                        disabled={loading}
                        className="p-4 rounded-lg text-left flex items-center justify-between hover:scale-[1.02] transition-transform"
                        style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                      >
                        <div className="flex items-center gap-3">
                          <GitBranch className="w-5 h-5" style={{ color: '#a8d8ff' }} />
                          <span style={{ color: '#f0f0f5' }}>Create Version</span>
                        </div>
                        <GitBranch className="w-4 h-4" style={{ color: '#a8d8ff' }} />
                      </button>
                    </div>
                  </div>

                  {/* Recent Activity */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3" style={{ color: '#f0f0f5' }}>Recent Activity</h3>
                    <div className="space-y-2">
                      {documents.slice(0, 3).map((doc) => (
                        <div key={doc.id} className="p-3 rounded-lg flex items-center gap-3" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                          <FileText className="w-4 h-4" style={{ color: '#a8d8ff' }} />
                          <span className="text-sm flex-1" style={{ color: '#f0f0f5' }}>{doc.name}</span>
                          <span className="text-xs" style={{ color: '#9ca3af' }}>{doc.summary ? '✓ Summarized' : 'Pending'}</span>
                        </div>
                      ))}
                      {documents.length === 0 && layers.length === 0 && dictionaries.length === 0 && (
                        <p className="text-sm p-4 rounded-lg text-center" style={{ color: '#9ca3af', backgroundColor: 'rgba(168, 216, 255, 0.05)' }}>
                          No activity yet. Start by uploading a document or adding layers!
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Documents Tab */}
              {activeTab === 'documents' && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2" style={{ color: '#f0f0f5' }}>
                      <FileText className="w-5 h-5" />
                      Documents ({documents.length})
                    </h3>
                    <button
                      onClick={() => setShowDocumentModal(true)}
                      className="px-3 py-1.5 text-sm rounded-lg flex items-center gap-2"
                      style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.1)',
                        color: '#a8d8ff',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                      }}
                    >
                      <Upload className="w-4 h-4" />
                      Upload Document
                    </button>
                  </div>
                  <div className="space-y-2">
                    {documents.length === 0 ? (
                      <p className="text-sm p-4 rounded-lg" style={{ color: '#9ca3af', backgroundColor: 'rgba(168, 216, 255, 0.05)' }}>
                        No documents yet. Upload documents to enrich your context.
                      </p>
                    ) : (
                      documents.map((doc) => (
                        <div
                          key={doc.id}
                          className="p-4 rounded-lg"
                          style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <File className="w-4 h-4" style={{ color: '#a8d8ff' }} />
                                <span className="font-medium" style={{ color: '#f0f0f5' }}>
                                  {doc.name}
                                </span>
                                <span className="text-xs opacity-50" style={{ color: '#9ca3af' }}>
                                  {formatFileSize(doc.file_size)}
                                </span>
                              </div>
                              {doc.summary ? (
                                <div className="mt-2 p-3 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}>
                                  <div className="flex items-center gap-2 mb-1">
                                    <SparklesIcon className="w-4 h-4" style={{ color: '#c4b5fd' }} />
                                    <span className="text-xs font-medium" style={{ color: '#c4b5fd' }}>AI Summary</span>
                                  </div>
                                  <p className="text-sm" style={{ color: '#9ca3af' }}>
                                    {doc.summary}
                                  </p>
                                </div>
                              ) : (
                                <p className="text-xs mt-1 opacity-50" style={{ color: '#9ca3af' }}>
                                  No summary available
                                </p>
                              )}
                            </div>
                            <div className="flex items-center gap-2 ml-4">
                              {!doc.summary && (
                                <button
                                  onClick={() => handleSummarizeDocument(doc.id)}
                                  disabled={loading}
                                  className="p-1.5 rounded"
                                  style={{
                                    backgroundColor: 'rgba(196, 181, 253, 0.1)',
                                    color: '#c4b5fd',
                                  }}
                                  title="Generate AI Summary"
                                >
                                  <SparklesIcon className="w-4 h-4" />
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteDocument(doc.id)}
                                className="p-1.5 rounded"
                                style={{
                                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                  color: '#ef4444',
                                }}
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Layers Tab */}
              {activeTab === 'layers' && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2" style={{ color: '#f0f0f5' }}>
                      <Layers className="w-5 h-5" />
                      Layers ({layers.length})
                    </h3>
                    <button
                      onClick={() => setShowLayerModal(true)}
                      className="px-3 py-1.5 text-sm rounded-lg flex items-center gap-2"
                      style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.1)',
                        color: '#a8d8ff',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                      }}
                    >
                      <Plus className="w-4 h-4" />
                      Add Layer
                    </button>
                  </div>
                  <div className="space-y-2">
                    {layers.length === 0 ? (
                      <p className="text-sm p-4 rounded-lg" style={{ color: '#9ca3af', backgroundColor: 'rgba(168, 216, 255, 0.05)' }}>
                        No layers yet. Add layers to enrich your context.
                      </p>
                    ) : (
                      layers.map((layer) => (
                        <div
                          key={layer.id}
                          className="p-4 rounded-lg flex items-center justify-between"
                          style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium" style={{ color: '#f0f0f5' }}>
                                {layer.name}
                              </span>
                              <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: 'rgba(168, 216, 255, 0.2)', color: '#a8d8ff' }}>
                                {layer.kind}
                              </span>
                              {!layer.enabled && (
                                <span className="text-xs opacity-50">(disabled)</span>
                              )}
                            </div>
                            {layer.spec && Object.keys(layer.spec).length > 0 && (
                              <div className="text-xs mt-1 font-mono opacity-75" style={{ color: '#9ca3af' }}>
                                {JSON.stringify(layer.spec).substring(0, 60)}...
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleToggleLayer(layer.id, layer.enabled)}
                              className="p-1.5 rounded"
                              style={{
                                backgroundColor: layer.enabled ? 'rgba(168, 216, 255, 0.2)' : 'rgba(168, 216, 255, 0.1)',
                                color: '#a8d8ff',
                              }}
                              title={layer.enabled ? 'Disable' : 'Enable'}
                            >
                              <Settings className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteLayer(layer.id)}
                              className="p-1.5 rounded"
                              style={{
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                color: '#ef4444',
                              }}
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Dictionaries Tab */}
              {activeTab === 'dictionaries' && (
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2" style={{ color: '#f0f0f5' }}>
                      <BookOpen className="w-5 h-5" />
                      Dictionaries ({dictionaries.length})
                    </h3>
                    <button
                      onClick={() => setShowDictionaryModal(true)}
                      className="px-3 py-1.5 text-sm rounded-lg flex items-center gap-2"
                      style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.1)',
                        color: '#a8d8ff',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                      }}
                    >
                      <Plus className="w-4 h-4" />
                      Add Dictionary
                    </button>
                  </div>
                  <div className="space-y-2">
                    {dictionaries.length === 0 ? (
                      <p className="text-sm p-4 rounded-lg" style={{ color: '#9ca3af', backgroundColor: 'rgba(168, 216, 255, 0.05)' }}>
                        No dictionaries yet. Add a dictionary to define terms and mappings.
                      </p>
                    ) : (
                      dictionaries.map((dict) => (
                        <div
                          key={dict.id}
                          className="p-4 rounded-lg"
                          style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                        >
                          <div className="font-medium mb-2" style={{ color: '#f0f0f5' }}>
                            {dict.name}
                          </div>
                          <div className="space-y-1">
                            {Object.entries(dict.entries).slice(0, 3).map(([key, value]) => (
                              <div key={key} className="text-sm flex gap-2">
                                <span className="font-medium" style={{ color: '#a8d8ff' }}>{key}:</span>
                                <span style={{ color: '#9ca3af' }}>{value}</span>
                              </div>
                            ))}
                            {Object.keys(dict.entries).length > 3 && (
                              <div className="text-xs opacity-50" style={{ color: '#9ca3af' }}>
                                +{Object.keys(dict.entries).length - 3} more entries
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Versions Tab */}
              {activeTab === 'versions' && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold flex items-center gap-2 mb-4" style={{ color: '#f0f0f5' }}>
                    <GitBranch className="w-5 h-5" />
                    Versions ({versions.length})
                  </h3>
                  <div className="space-y-2">
                    {versions.length === 0 ? (
                      <p className="text-sm p-4 rounded-lg" style={{ color: '#9ca3af', backgroundColor: 'rgba(168, 216, 255, 0.05)' }}>
                        No versions yet. Create a version to snapshot this context.
                      </p>
                    ) : (
                      versions.map((version) => (
                        <div
                          key={version.id}
                          className="p-4 rounded-lg flex items-center justify-between"
                          style={{ backgroundColor: 'rgba(168, 216, 255, 0.05)', border: '1px solid rgba(168, 216, 255, 0.1)' }}
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium" style={{ color: '#f0f0f5' }}>
                                Version {version.version}
                              </span>
                              <span className="text-xs font-mono opacity-50" style={{ color: '#9ca3af' }}>
                                {version.digest.substring(0, 12)}...
                              </span>
                            </div>
                            {version.diff_summary && (
                              <div className="text-sm mt-1 opacity-75" style={{ color: '#9ca3af' }}>
                                {version.diff_summary}
                              </div>
                            )}
                          </div>
                          <button
                            onClick={() => handleExport(version.id)}
                            className="p-2 rounded"
                            style={{
                              backgroundColor: 'rgba(168, 216, 255, 0.1)',
                              color: '#a8d8ff',
                            }}
                            title="Export this version"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12" style={{ color: '#9ca3af' }}>
              <Layers className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>Select a context to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Context Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div
            className="rounded-lg p-6 w-full max-w-md"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.3)' }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold" style={{ color: '#f0f0f5' }}>
                Create Context
              </h3>
              <button onClick={() => setShowCreateModal(false)} style={{ color: '#9ca3af' }}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Name *
                </label>
                <input
                  type="text"
                  value={newContextName}
                  onChange={(e) => setNewContextName(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                  placeholder="e.g., SupportTickets_Context"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Description
                </label>
                <textarea
                  value={newContextDesc}
                  onChange={(e) => setNewContextDesc(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                  rows={3}
                  placeholder="Describe this context..."
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    color: '#a8d8ff',
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateContext}
                  disabled={loading}
                  className="px-4 py-2 rounded-lg font-medium"
                  style={{
                    backgroundColor: '#a8d8ff',
                    color: '#0a0a0f',
                  }}
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Layer Modal */}
      {showLayerModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div
            className="rounded-lg p-6 w-full max-w-md"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.3)' }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold" style={{ color: '#f0f0f5' }}>
                Add Layer
              </h3>
              <button onClick={() => setShowLayerModal(false)} style={{ color: '#9ca3af' }}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Kind
                </label>
                <select
                  value={newLayerKind}
                  onChange={(e) => setNewLayerKind(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                >
                  <option value="select">Select (Filter)</option>
                  <option value="transform">Transform</option>
                  <option value="dictionary">Dictionary</option>
                  <option value="persona">Persona</option>
                  <option value="mcp">MCP Tool</option>
                  <option value="rule">Rule</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Name *
                </label>
                <input
                  type="text"
                  value={newLayerName}
                  onChange={(e) => setNewLayerName(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                  placeholder="e.g., Only_Open"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Spec (JSON)
                </label>
                <textarea
                  value={newLayerSpec}
                  onChange={(e) => setNewLayerSpec(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg font-mono text-sm"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                  rows={4}
                  placeholder={`{"where": "status = 'open'"}`}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowLayerModal(false)}
                  className="px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    color: '#a8d8ff',
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddLayer}
                  disabled={loading}
                  className="px-4 py-2 rounded-lg font-medium"
                  style={{
                    backgroundColor: '#a8d8ff',
                    color: '#0a0a0f',
                  }}
                >
                  Add
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Dictionary Modal */}
      {showDictionaryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div
            className="rounded-lg p-6 w-full max-w-md"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.3)' }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold" style={{ color: '#f0f0f5' }}>
                Add Dictionary
              </h3>
              <button onClick={() => setShowDictionaryModal(false)} style={{ color: '#9ca3af' }}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Name *
                </label>
                <input
                  type="text"
                  value={newDictName}
                  onChange={(e) => setNewDictName(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                  placeholder="e.g., SupportTerms"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Entries (one per line, format: key: value)
                </label>
                <textarea
                  value={newDictEntries}
                  onChange={(e) => setNewDictEntries(e.target.value)}
                  className="w-full px-4 py-2 rounded-lg font-mono text-sm"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                  rows={6}
                  placeholder={`RMA: Return Merchandise Authorization\nSLA: Service Level Agreement`}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowDictionaryModal(false)}
                  className="px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    color: '#a8d8ff',
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddDictionary}
                  disabled={loading}
                  className="px-4 py-2 rounded-lg font-medium"
                  style={{
                    backgroundColor: '#a8d8ff',
                    color: '#0a0a0f',
                  }}
                >
                  Add
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {showDocumentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div
            className="rounded-lg p-6 w-full max-w-md"
            style={{ backgroundColor: '#1a1a24', border: '1px solid rgba(168, 216, 255, 0.3)' }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold" style={{ color: '#f0f0f5' }}>
                Upload Document
              </h3>
              <button onClick={() => setShowDocumentModal(false)} style={{ color: '#9ca3af' }}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
                  Select File
                </label>
                <input
                  type="file"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: '#0f0f14',
                    color: '#f0f0f5',
                    border: '1px solid rgba(168, 216, 255, 0.15)',
                  }}
                  accept=".txt,.md,.csv,.json,.pdf,.docx,.yaml,.yml"
                />
                {selectedFile && (
                  <p className="text-sm mt-2" style={{ color: '#9ca3af' }}>
                    Selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
                  </p>
                )}
              </div>
              <div className="text-xs" style={{ color: '#9ca3af' }}>
                📝 Supported: TXT, MD, CSV, JSON, PDF, DOCX, YAML
                <br />
                ✨ Documents will be automatically summarized using AI
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setShowDocumentModal(false)
                    setSelectedFile(null)
                  }}
                  className="px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    color: '#a8d8ff',
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleUploadDocument}
                  disabled={loading || !selectedFile}
                  className="px-4 py-2 rounded-lg font-medium flex items-center gap-2"
                  style={{
                    backgroundColor: '#a8d8ff',
                    color: '#0a0a0f',
                    opacity: loading || !selectedFile ? 0.5 : 1,
                  }}
                >
                  {loading ? 'Uploading...' : (
                    <>
                      <Upload className="w-4 h-4" />
                      Upload & Summarize
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

