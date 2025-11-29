import { useState, useEffect, useRef } from 'react'
import { Send, Plus, Database, MessageSquare, Settings, Loader2, AlertCircle } from 'lucide-react'
import {
  createConversation,
  listConversations,
  getConversation,
  updateConversation,
  sendMessage,
  deleteConversation
} from '../api/client'

interface Conversation {
  id: string
  title: string | null
  created_at: string
  updated_at: string
  provider: string
  model: string
  connection_id: string | null
  message_count: number
}

interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string | null
  created_at: string
  tool_name?: string | null
  tool_input?: any
  tool_output?: any
}

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', models: ['gpt-4-turbo-preview', 'gpt-4', 'gpt-3.5-turbo'] },
  { id: 'anthropic', name: 'Anthropic', models: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'] },
  { id: 'google', name: 'Google', models: ['gemini-pro', 'gemini-ultra'] },
  { id: 'xai', name: 'xAI', models: ['grok-beta'] }
]

export default function Chat() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  
  // Settings
  const [selectedProvider, setSelectedProvider] = useState('openai')
  const [selectedModel, setSelectedModel] = useState('gpt-4-turbo-preview')
  const [connectionId, setConnectionId] = useState('default')
  const [availableDatabases, setAvailableDatabases] = useState<any[]>([])
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    loadConversations()
    loadDatabases()
  }, [])

  const loadDatabases = async () => {
    try {
      // Call the Data Explorer API to get available databases
      const response = await fetch('http://localhost:8000/api/v1/data-explorer/databases')
      const data = await response.json()
      setAvailableDatabases(data)
      if (data.length > 0 && !connectionId) {
        setConnectionId(data[0].id)
      }
    } catch (error) {
      console.error('Failed to load databases:', error)
      // Fallback to default if API fails
      setAvailableDatabases([{ id: 'default', name: 'Default Database', description: 'localhost:5433' }])
    }
  }

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation)
    }
  }, [selectedConversation])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])
  

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadConversations = async () => {
    try {
      const data = await listConversations()
      setConversations(data)
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const loadMessages = async (conversationId: string) => {
    try {
      const data = await getConversation(conversationId)
      const messages = data.messages || []
      setMessages(messages)
      setSelectedProvider(data.provider)
      setSelectedModel(data.model)
      setConnectionId(data.connection_id || 'default')
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  const createNewConversation = async () => {
    try {
      const data = await createConversation({
        provider: selectedProvider,
        model: selectedModel,
        connection_id: connectionId
      })
      setConversations([data, ...conversations])
      setSelectedConversation(data.id)
      setMessages([])
      setShowSettings(false)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !selectedConversation || isStreaming) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setIsStreaming(true)
    setStreamingContent('')

    // Optimistically add user message
    const tempUserMessage: Message = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      // Use EventSource for SSE streaming
      const url = `http://localhost:8000/api/v1/chat/conversations/${selectedConversation}/messages`
      
      // First, send the POST request with fetch to initiate streaming
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: userMessage,
          stream: true
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Read the SSE stream
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('No response body')
      }

      let buffer = ''
      let currentContent = ''
      let currentEventType = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })
        
        // Process complete SSE messages
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEventType = line.substring(6).trim()
            continue
          }
          
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.substring(5).trim())
              
              if (currentEventType === 'delta' && data.content) {
                // Delta event - streaming text
                currentContent += data.content
                setStreamingContent(currentContent)
              } 
              else if (currentEventType === 'tool_call') {
                // Tool call event - show in UI as a step
                const toolMessage: Message = {
                  id: 'tool-' + Date.now() + '-' + Math.random(),
                  role: 'tool',
                  content: null,
                  created_at: new Date().toISOString(),
                  tool_name: data.tool_name,
                  tool_input: data.tool_input,
                  tool_output: { status: 'executing' } // Mark as executing
                }
                setMessages(prev => [...prev, toolMessage])
              }
              else if (currentEventType === 'tool_result') {
                // Tool result event - update the matching tool message
                setMessages(prev => {
                  const updated = [...prev]
                  // Find the most recent tool message with matching name and executing status
                  for (let i = updated.length - 1; i >= 0; i--) {
                    if (updated[i].role === 'tool' && 
                        updated[i].tool_name === data.tool_name &&
                        updated[i].tool_output?.status === 'executing') {
                      updated[i] = {
                        ...updated[i],
                        tool_output: data.result
                      }
                      break
                    }
                  }
                  return updated
                })
              }
              else if (currentEventType === 'done') {
                // Done event
                if (currentContent) {
                  const assistantMessage: Message = {
                    id: data.message_id,
                    role: 'assistant',
                    content: currentContent,
                    created_at: new Date().toISOString()
                  }
                  setMessages(prev => [...prev, assistantMessage])
                }
                setStreamingContent('')
                setIsStreaming(false)
                
                // Don't reload - we already have all messages from streaming
                // Just update the conversation list to show latest timestamp
                loadConversations()
              }
              else if (currentEventType === 'error') {
                // Error event
                console.error('Stream error:', data.error)
                setIsStreaming(false)
                setStreamingContent('')
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', line, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  const handleRename = async (conversationId: string, newTitle: string) => {
    try {
      await updateConversation(conversationId, { title: newTitle })
      loadConversations()
    } catch (error) {
      console.error('Failed to rename conversation:', error)
    }
  }

  const handleDelete = async (conversationId: string) => {
    if (!confirm('Are you sure you want to delete this conversation?')) return
    
    try {
      await deleteConversation(conversationId)
      setConversations(conversations.filter(c => c.id !== conversationId))
      if (selectedConversation === conversationId) {
        setSelectedConversation(null)
        setMessages([])
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'Just now'
  }

  return (
    <div className="flex h-screen" style={{ backgroundColor: '#0a0e1a' }}>
      {/* Sidebar */}
      <div className="w-80 flex flex-col" style={{ 
        backgroundColor: '#0f1419',
        borderRight: '1px solid rgba(168, 216, 255, 0.2)'
      }}>
        <div className="p-4" style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)' }}>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all duration-200"
            style={{
              background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
              color: '#a8d8ff',
              border: '1px solid rgba(168, 216, 255, 0.4)'
            }}
          >
            <Plus size={20} />
            New Chat
          </button>
        </div>

        {showSettings && (
          <div className="p-4" style={{ 
            borderBottom: '1px solid rgba(168, 216, 255, 0.2)',
            backgroundColor: 'rgba(168, 216, 255, 0.05)'
          }}>
            <h3 className="text-sm font-semibold mb-3" style={{ color: '#a8d8ff' }}>New Chat Settings</h3>
            
            <div className="mb-3">
              <label className="block text-sm font-medium mb-1" style={{ color: '#b3d9ff' }}>
                Provider
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => {
                  setSelectedProvider(e.target.value)
                  const provider = PROVIDERS.find(p => p.id === e.target.value)
                  if (provider) setSelectedModel(provider.models[0])
                }}
                className="w-full px-3 py-2 rounded-md text-sm"
                style={{
                  backgroundColor: '#0f1419',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
              >
                {PROVIDERS.map(provider => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))}
              </select>
      </div>

            <div className="mb-3">
              <label className="block text-sm font-medium mb-1" style={{ color: '#b3d9ff' }}>
                Model
        </label>
        <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3 py-2 rounded-md text-sm"
                style={{
                  backgroundColor: '#0f1419',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
              >
                {PROVIDERS.find(p => p.id === selectedProvider)?.models.map(model => (
                  <option key={model} value={model}>
                    {model}
            </option>
          ))}
        </select>
      </div>

            <div className="mb-3">
              <label className="block text-sm font-medium mb-1" style={{ color: '#b3d9ff' }}>
                Database Connection
              </label>
              <select
                value={connectionId}
                onChange={(e) => setConnectionId(e.target.value)}
                className="w-full px-3 py-2 rounded-md text-sm"
                style={{
                  backgroundColor: '#0f1419',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#f0f0f5'
                }}
              >
                {availableDatabases.map(db => (
                  <option key={db.id} value={db.id}>
                    {db.name} - {db.description}
                  </option>
                ))}
              </select>
              {availableDatabases.length === 0 && (
                <p className="text-xs mt-1" style={{ color: '#8ab3cc' }}>
                  Loading databases...
                </p>
              )}
            </div>

            <button
              onClick={createNewConversation}
              className="w-full px-4 py-2 rounded-md text-sm transition-all duration-200"
              style={{
                background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.2), rgba(196, 181, 253, 0.2))',
                color: '#a8d8ff',
                border: '1px solid rgba(168, 216, 255, 0.4)'
              }}
            >
              Create Conversation
            </button>
          </div>
        )}

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto">
          {conversations.map(conversation => (
            <div
              key={conversation.id}
              onClick={() => setSelectedConversation(conversation.id)}
              className="p-4 cursor-pointer transition-all duration-200"
              style={selectedConversation === conversation.id ? {
                background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                borderBottom: '1px solid rgba(168, 216, 255, 0.2)',
                borderLeft: '3px solid #a8d8ff'
              } : {
                borderBottom: '1px solid rgba(168, 216, 255, 0.1)',
                backgroundColor: 'transparent'
              }}
              onMouseEnter={(e) => {
                if (selectedConversation !== conversation.id) {
                  e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.05)'
                }
              }}
              onMouseLeave={(e) => {
                if (selectedConversation !== conversation.id) {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium truncate" style={{ color: '#f0f0f5' }}>
                    {conversation.title || 'New Conversation'}
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs" style={{ color: '#8ab3cc' }}>
                      {conversation.provider} • {conversation.message_count} msgs
                    </span>
                  </div>
                  <p className="text-xs mt-1" style={{ color: '#6a8399' }}>
                    {formatTimestamp(conversation.updated_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(conversation.id)
                  }}
                  className="ml-2 text-2xl leading-none transition-colors"
                  style={{ color: '#6a8399' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#ff6b6b'}
                  onMouseLeave={(e) => e.currentTarget.style.color = '#6a8399'}
                >
                  ×
                </button>
              </div>
            </div>
          ))}

          {conversations.length === 0 && (
            <div className="p-8 text-center" style={{ color: '#8ab3cc' }}>
              <MessageSquare size={48} className="mx-auto mb-3 opacity-50" style={{ color: '#a8d8ff' }} />
              <p className="text-sm" style={{ color: '#b3d9ff' }}>No conversations yet</p>
              <p className="text-xs mt-1" style={{ color: '#8ab3cc' }}>Create a new chat to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            {/* Header */}
            <div className="p-4" style={{ 
              backgroundColor: '#0f1419',
              borderBottom: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold" style={{ color: '#f0f0f5' }}>
                    {conversations.find(c => c.id === selectedConversation)?.title || 'New Conversation'}
                  </h2>
                  <div className="flex items-center gap-2 mt-1 text-sm" style={{ color: '#8ab3cc' }}>
                    <Database size={14} />
                    <span>
                      {selectedProvider} • {selectedModel}
                    </span>
                    {connectionId && (
                      <>
                        <span>•</span>
                        <span className="font-medium" style={{ color: '#a8d8ff' }}>
                          DB: {availableDatabases.find(db => db.id === connectionId)?.name || connectionId}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ backgroundColor: '#0a0e1a' }}>
              {messages.map((message, index) => {
                const prevMessage = index > 0 ? messages[index - 1] : null
                const showConnector = message.role === 'tool' && prevMessage?.role === 'tool'
                const uniqueKey = message.id ? `${message.id}-${message.role}` : `msg-${index}-${message.role}-${message.tool_name || 'none'}`
                
                return (
                  <div key={uniqueKey}>
                    {/* Connector line for consecutive tool steps */}
                    {showConnector && (
                      <div className="flex justify-start mb-2">
                        <div className="ml-8 w-0.5 h-4" style={{ 
                          backgroundColor: 'rgba(196, 181, 253, 0.3)'
                        }} />
                      </div>
                    )}
                    
                    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                  {message.role === 'tool' ? (
                    <div 
                      className="max-w-2xl w-full px-3 py-2 rounded-lg"
                      style={{
                        backgroundColor: 'rgba(196, 181, 253, 0.1)',
                        border: '1px solid rgba(196, 181, 253, 0.4)'
                      }}
                    >
                      {/* Tool header with status */}
                      <div className="flex items-center gap-2 mb-1">
                        {message.tool_output?.status === 'executing' ? (
                          <>
                            <Loader2 size={14} className="animate-spin" style={{ color: '#c4b5fd' }} />
                            <span className="font-medium text-xs" style={{ color: '#c4b5fd' }}>
                              Executing: {message.tool_name}
                            </span>
                          </>
                        ) : message.tool_output?.success !== false ? (
                          <>
                            <div className="flex-shrink-0 w-3 h-3 rounded-full flex items-center justify-center" style={{ 
                              backgroundColor: '#10b981',
                              color: 'white'
                            }}>
                              <span style={{ fontSize: '8px' }}>✓</span>
                            </div>
                            <span className="font-medium text-xs" style={{ color: '#10b981' }}>
                              {message.tool_name}
                            </span>
                          </>
                        ) : (
                          <>
                            <div className="flex-shrink-0 w-3 h-3 rounded-full flex items-center justify-center" style={{ 
                              backgroundColor: '#ef4444',
                              color: 'white'
                            }}>
                              <span style={{ fontSize: '8px' }}>✗</span>
                            </div>
                            <span className="font-medium text-xs" style={{ color: '#ef4444' }}>
                              Failed: {message.tool_name}
                            </span>
                          </>
                        )}
                      </div>
                      
                      {/* Tool input - collapsed by default */}
                      {message.tool_input && Object.keys(message.tool_input).length > 0 && (
                        <details className="mb-1" style={{ fontSize: '11px', color: '#b3d9ff' }}>
                          <summary className="cursor-pointer font-medium hover:opacity-80" style={{ color: '#c4b5fd' }}>
                            Input
                          </summary>
                          <div className="mt-1 pl-2" style={{ color: '#8ab3cc', fontSize: '10px' }}>
                            {Object.entries(message.tool_input).map(([key, value]) => (
                              <div key={key}>
                                <span className="font-medium" style={{ color: '#b3d9ff' }}>{key}:</span>{' '}
                                <span className="font-mono">{JSON.stringify(value)}</span>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      
                      {/* Tool output - show summary or status */}
                      {message.tool_output && message.tool_output.status !== 'executing' && (
                        <>
                          {/* Quick summary */}
                          {message.tool_output.success && message.tool_output.data && (
                            <div className="mb-1 py-1 px-2 rounded" style={{ 
                              backgroundColor: 'rgba(16, 185, 129, 0.1)',
                              color: '#6ee7b7',
                              fontSize: '11px'
                            }}>
                              {Array.isArray(message.tool_output.data) && (
                                <div>
                                  Found {message.tool_output.data.length} result(s)
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Expandable full results */}
                          <details style={{ fontSize: '11px', color: '#8ab3cc' }}>
                            <summary className="cursor-pointer font-medium hover:opacity-80" style={{ color: '#b3d9ff' }}>
                              Details
                            </summary>
                            <div className="mt-1 p-2 rounded overflow-auto max-h-40" style={{ 
                              backgroundColor: 'rgba(10, 14, 26, 0.5)',
                              border: '1px solid rgba(168, 216, 255, 0.1)',
                              fontSize: '10px'
                            }}>
                              <pre style={{ color: '#a8d8ff' }}>
                                {JSON.stringify(message.tool_output, null, 2)}
                              </pre>
                            </div>
                          </details>
                        </>
                      )}
                    </div>
                  ) : (
                    <div
                      className="max-w-2xl px-4 py-3 rounded-2xl"
                      style={message.role === 'user' ? {
                        background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.3), rgba(196, 181, 253, 0.3))',
                        border: '1px solid rgba(168, 216, 255, 0.4)',
                        color: '#f0f0f5'
                      } : {
                        backgroundColor: '#0f1419',
                        border: '1px solid rgba(168, 216, 255, 0.2)',
                        color: '#f0f0f5'
                      }}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    </div>
                  )}
                    </div>
                  </div>
                )
              })}

              {/* Streaming message */}
              {isStreaming && (
                <div className="flex justify-start">
                  {streamingContent ? (
                    <div className="max-w-2xl px-4 py-3 rounded-2xl" style={{
                      backgroundColor: '#0f1419',
                      border: '1px solid rgba(168, 216, 255, 0.2)',
                      color: '#f0f0f5'
                    }}>
                      <p className="text-sm whitespace-pre-wrap">{streamingContent}</p>
                      <div className="flex items-center gap-1 mt-2" style={{ color: '#a8d8ff' }}>
                        <Loader2 size={14} className="animate-spin" />
                        <span className="text-xs">Generating...</span>
                      </div>
                    </div>
                  ) : (
                    <div className="px-4 py-3 rounded-2xl flex items-center gap-2" style={{
                      backgroundColor: 'rgba(196, 181, 253, 0.1)',
                      border: '1px solid rgba(196, 181, 253, 0.3)',
                      color: '#c4b5fd'
                    }}>
                      <Loader2 size={16} className="animate-spin" />
                      <span className="text-sm">Analyzing your data...</span>
              </div>
                  )}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

            {/* Input */}
            <div className="p-4" style={{ 
              backgroundColor: '#0f1419',
              borderTop: '1px solid rgba(168, 216, 255, 0.2)'
            }}>
              <div className="flex gap-3">
            <input
              type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                  disabled={isStreaming}
                  placeholder="Ask about your data..."
                  className="flex-1 px-4 py-3 rounded-xl focus:outline-none transition-all"
                  style={{
                    backgroundColor: '#0a0e1a',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  }}
                  onFocus={(e) => e.target.style.border = '1px solid rgba(168, 216, 255, 0.6)'}
                  onBlur={(e) => e.target.style.border = '1px solid rgba(168, 216, 255, 0.3)'}
            />
            <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isStreaming}
                  className="px-6 py-3 rounded-xl transition-all duration-200"
                  style={!inputValue.trim() || isStreaming ? {
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    border: '1px solid rgba(168, 216, 255, 0.2)',
                    color: '#6a8399',
                    cursor: 'not-allowed'
                  } : {
                    background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.2), rgba(196, 181, 253, 0.2))',
                    border: '1px solid rgba(168, 216, 255, 0.4)',
                    color: '#a8d8ff'
                  }}
                >
                  {isStreaming ? (
                    <Loader2 size={20} className="animate-spin" />
                  ) : (
                    <Send size={20} />
                  )}
            </button>
          </div>
              <p className="text-xs mt-2" style={{ color: '#8ab3cc' }}>
                The AI can explore your database using tools like list_tables, profile_table, and run_query
          </p>
        </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center" style={{ color: '#8ab3cc' }}>
            <div className="text-center">
              <MessageSquare size={64} className="mx-auto mb-4 opacity-50" style={{ color: '#a8d8ff' }} />
              <h3 className="text-xl font-semibold mb-2" style={{ 
                background: 'linear-gradient(90deg, #a8d8ff 0%, #c4b5fd 50%, #ffc4e5 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>Chat with Your Data</h3>
              <p className="text-sm mb-4" style={{ color: '#b3d9ff' }}>Select a conversation or create a new one to start chatting</p>
              <button
                onClick={() => setShowSettings(true)}
                className="px-6 py-3 rounded-lg inline-flex items-center gap-2 transition-all duration-200"
                style={{
                  background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                  color: '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.4)'
                }}
              >
                <Plus size={20} />
                New Chat
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
