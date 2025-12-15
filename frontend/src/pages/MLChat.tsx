import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageCircle, ArrowLeft, Send, Sparkles, Settings, AlertCircle } from 'lucide-react'
import { getAvailableModels, checkApiKeys } from '../api/client'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

export default function MLChat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your ML recipe assistant. I can help you create and refine ML recipes for pricing, forecasting, next best action, and location scoring models. What would you like to build?',
      timestamp: new Date().toISOString()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // LLM Settings
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('gpt-4o')
  const [availableModels, setAvailableModels] = useState<Record<string, string[]>>({})
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({})
  const [loadingModels, setLoadingModels] = useState(false)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadModels()
  }, [])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadModels = async () => {
    setLoadingModels(true)
    try {
      const [modelsData, keysData] = await Promise.all([
        getAvailableModels(),
        checkApiKeys()
      ])
      
      // Build models map from providers array (same as Data Analysis page)
      const modelsMap: Record<string, string[]> = {}
      for (const providerData of modelsData.providers) {
        modelsMap[providerData.provider] = providerData.models
      }
      
      setAvailableModels(modelsMap)
      setApiKeys(keysData)
      
      // Set default provider/model to first available with API key
      const firstProvider = modelsData.providers.find(p => p.has_api_key && p.models.length > 0)
      if (firstProvider && firstProvider.models.length > 0) {
        setProvider(firstProvider.provider)
        setModel(firstProvider.models[0])
      }
    } catch (error) {
      console.error('Error loading models:', error)
    } finally {
      setLoadingModels(false)
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    try {
      const response = await fetch('/api/v1/ml-development/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputMessage,
          provider: provider,
          model: model,
          context: {}
        })
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.message,
          timestamp: data.timestamp
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || 'Failed to get response')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your API configuration.`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const quickPrompts = [
    'Create a pricing model recipe',
    'Build a forecasting model',
    'Set up next best action model',
    'Create location scoring recipe'
  ]

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.2)', padding: '1.5rem 2rem' }}>
        <button
          onClick={() => navigate('/model-development')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'none',
            border: 'none',
            color: '#a8d8ff',
            cursor: 'pointer',
            marginBottom: '1rem',
            fontSize: '0.95rem'
          }}
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Model Library
        </button>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <MessageCircle className="h-8 w-8" style={{ color: '#a8d8ff' }} />
            <div>
              <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#f0f0f5' }}>
                ML Recipe Chat Assistant
              </h1>
              <p style={{ color: '#b3b3c4', fontSize: '0.95rem' }}>
                Chat-driven recipe creation and editing
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            style={{
              padding: '0.75rem',
              backgroundColor: showSettings ? 'rgba(168, 216, 255, 0.15)' : 'rgba(168, 216, 255, 0.05)',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              borderRadius: '0.5rem',
              color: '#a8d8ff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Settings className="h-5 w-5" />
            Settings
          </button>
        </div>
      </div>

      {/* Chat Container */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', maxWidth: '900px', width: '100%', margin: '0 auto', padding: '2rem' }}>
        
        {/* Settings Panel */}
        {showSettings && (
          <div style={{
            padding: '1.5rem',
            backgroundColor: '#1a1a24',
            border: '1px solid rgba(168, 216, 255, 0.2)',
            borderRadius: '0.75rem',
            marginBottom: '1.5rem'
          }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#a8d8ff', marginBottom: '1rem' }}>
              LLM Settings
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Provider {loadingModels && '(Loading...)'}
                </label>
                <select
                  value={provider}
                  onChange={(e) => {
                    const newProvider = e.target.value
                    setProvider(newProvider)
                    const models = availableModels[newProvider] || []
                    if (models.length > 0) {
                      setModel(models[0])
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    borderRadius: '0.5rem',
                    color: '#f0f0f5'
                  }}
                  disabled={loadingModels}
                >
                  {Object.keys(availableModels).map(p => (
                    <option key={p} value={p}>
                      {p.charAt(0).toUpperCase() + p.slice(1)}
                      {!apiKeys[p] && ' (No API Key)'}
                      {apiKeys[p] && availableModels[p].length === 0 && ' (No Models)'}
                    </option>
                  ))}
                </select>
                
                {!apiKeys[provider] && (
                  <p className="text-xs mt-1 flex items-center gap-1" style={{ color: '#fbbf24' }}>
                    <AlertCircle className="h-3 w-3" />
                    No API key configured for {provider}
                  </p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>
                  Model
                </label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    borderRadius: '0.5rem',
                    color: '#f0f0f5'
                  }}
                  disabled={loadingModels || !apiKeys[provider]}
                >
                  {(availableModels[provider] || []).map(m => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
        
        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {messages.map((message, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
                gap: '1rem'
              }}
            >
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: message.role === 'user' ? 'rgba(196, 181, 253, 0.2)' : 'rgba(168, 216, 255, 0.2)',
                  border: `1px solid ${message.role === 'user' ? 'rgba(196, 181, 253, 0.4)' : 'rgba(168, 216, 255, 0.4)'}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}
              >
                {message.role === 'user' ? (
                  <span style={{ fontSize: '1.25rem' }}>👤</span>
                ) : (
                  <Sparkles className="h-5 w-5" style={{ color: '#a8d8ff' }} />
                )}
              </div>

              <div
                style={{
                  maxWidth: '70%',
                  padding: '1rem 1.25rem',
                  backgroundColor: message.role === 'user' ? 'rgba(196, 181, 253, 0.1)' : '#1a1a24',
                  border: `1px solid ${message.role === 'user' ? 'rgba(196, 181, 253, 0.3)' : 'rgba(168, 216, 255, 0.2)'}`,
                  borderRadius: '1rem',
                  color: '#f0f0f5',
                  fontSize: '0.95rem',
                  lineHeight: '1.6'
                }}
              >
                <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{message.content}</p>
                <p style={{ 
                  margin: '0.5rem 0 0 0', 
                  fontSize: '0.75rem', 
                  color: '#9ca3af',
                  textAlign: message.role === 'user' ? 'right' : 'left'
                }}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Sparkles className="h-5 w-5" style={{ color: '#a8d8ff' }} />
              </div>
              <div
                style={{
                  padding: '1rem 1.25rem',
                  backgroundColor: '#1a1a24',
                  border: '1px solid rgba(168, 216, 255, 0.2)',
                  borderRadius: '1rem'
                }}
              >
                <p style={{ color: '#b3b3c4', margin: 0 }}>Thinking...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Prompts */}
        {messages.length === 1 && (
          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ color: '#b3b3c4', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
              Quick start prompts:
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              {quickPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => setInputMessage(prompt)}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: 'rgba(168, 216, 255, 0.1)',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    borderRadius: '9999px',
                    color: '#a8d8ff',
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.2)'
                    e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.5)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.1)'
                    e.currentTarget.style.borderColor = 'rgba(168, 216, 255, 0.3)'
                  }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div style={{ 
          display: 'flex', 
          gap: '1rem',
          padding: '1.5rem',
          backgroundColor: '#1a1a24',
          border: '1px solid rgba(168, 216, 255, 0.2)',
          borderRadius: '1rem'
        }}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask me anything about ML recipes..."
            disabled={loading}
            style={{
              flex: 1,
              backgroundColor: '#0a0a0f',
              border: '1px solid rgba(168, 216, 255, 0.2)',
              borderRadius: '0.5rem',
              padding: '1rem',
              color: '#f0f0f5',
              fontSize: '0.95rem',
              resize: 'none',
              minHeight: '80px',
              fontFamily: 'inherit'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || loading}
            style={{
              padding: '0 2rem',
              background: inputMessage.trim() && !loading 
                ? 'linear-gradient(135deg, rgba(168, 216, 255, 0.2), rgba(196, 181, 253, 0.2))'
                : 'rgba(168, 216, 255, 0.05)',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              borderRadius: '0.75rem',
              color: inputMessage.trim() && !loading ? '#a8d8ff' : '#6b7280',
              cursor: inputMessage.trim() && !loading ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s'
            }}
          >
            <Send className="h-5 w-5" />
          </button>
        </div>

        {/* Helper Text */}
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <p style={{ color: '#6b7280', fontSize: '0.75rem' }}>
            Using {provider.charAt(0).toUpperCase() + provider.slice(1)} - {model}
          </p>
          {!apiKeys[provider] && (
            <p style={{ color: '#fbbf24', fontSize: '0.75rem', marginTop: '0.25rem' }}>
              ⚠️ No API key configured. Configure {provider.toUpperCase()}_API_KEY in your .env file.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}


