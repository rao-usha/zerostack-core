import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Network, Plus, Eye, GitBranch, Sparkles } from 'lucide-react'
import { chatQuery, listOntologies, getOntology } from '../api/client'
import ChatUIElements from '../components/ChatUIElements'
import OntologyViewer from '../components/OntologyViewer'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  response_type?: string
  action?: string
  ui_elements?: any[]
  metadata?: any
}

export default function Ontology() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [ontologyCount, setOntologyCount] = useState<number | null>(null)
  const [sessionId] = useState(`ont-${Date.now()}`)
  const [currentOntologyId, setCurrentOntologyId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [showWelcome, setShowWelcome] = useState(true)

  // Load ontology count on mount
  useEffect(() => {
    loadOntologyCount()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadOntologyCount = async () => {
    try {
      const ontologies = await listOntologies('demo')
      setOntologyCount(ontologies.length)
    } catch (error) {
      console.error('Failed to load ontologies:', error)
      setOntologyCount(0)
    }
  }

  const handleActionCard = async (action: string) => {
    setShowWelcome(false)
    let queryText = ''
    
    switch(action) {
      case 'build_new':
        queryText = 'I want to create a new ontology'
        break
      case 'view_existing':
        queryText = 'Show me my existing ontologies'
        break
      case 'extend':
        queryText = 'I want to extend an existing ontology'
        break
    }

    if (queryText) {
      await handleSend(queryText)
    }
  }

  const handleSend = async (text?: string, action?: string, payload?: any) => {
    const queryToSend = text || input.trim()
    if (!queryToSend && !action) return

    if (!action) {
      // Add user message
      const userMessage: Message = {
        role: 'user',
        content: queryToSend,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, userMessage])
      setInput('')
      setShowWelcome(false)
    }

    setIsLoading(true)

    try {
      const response = await chatQuery(queryToSend, undefined, sessionId, action, payload)
      
      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response || '',
        timestamp: response.timestamp || new Date().toISOString(),
        response_type: response.response_type,
        action: response.action,
        ui_elements: response.ui_elements,
        metadata: response.metadata,
      }
      
      setMessages(prev => [...prev, assistantMessage])

      // If this response contains an ontology view, update current ID
      if (response.metadata?.ontology?.id) {
        setCurrentOntologyId(response.metadata.ontology.id)
      }

      // Refresh ontology count after actions
      if (action && (action.includes('create') || action.includes('confirm'))) {
        await loadOntologyCount()
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-lg" style={{
            background: 'linear-gradient(135deg, rgba(168, 216, 255, 0.2), rgba(196, 181, 253, 0.2))',
            border: '1px solid rgba(168, 216, 255, 0.4)'
          }}>
            <Network className="h-7 w-7" style={{ color: '#a8d8ff' }} />
          </div>
          <div>
            <h1 className="text-3xl font-bold" style={{ color: '#f0f0f5' }}>
              Ontology Workbench
            </h1>
            <p className="text-sm" style={{ color: '#b3d9ff' }}>
              Build, extend, and manage knowledge ontologies
            </p>
          </div>
        </div>
        {ontologyCount !== null && (
          <div className="px-4 py-2 rounded-lg border" style={{
            background: 'rgba(168, 216, 255, 0.1)',
            borderColor: 'rgba(168, 216, 255, 0.3)',
            color: '#a8d8ff'
          }}>
            <span className="font-semibold">{ontologyCount}</span> {ontologyCount === 1 ? 'Ontology' : 'Ontologies'}
          </div>
        )}
      </div>

      {/* Welcome Screen */}
      {showWelcome && messages.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center space-y-8 pb-32">
          <div className="text-center space-y-4">
            <div className="flex justify-center">
              <div className="p-4 rounded-2xl" style={{
                background: 'linear-gradient(135deg, rgba(168, 216, 255, 0.15), rgba(196, 181, 253, 0.15))',
                border: '1px solid rgba(168, 216, 255, 0.3)'
              }}>
                <Sparkles className="h-12 w-12" style={{ color: '#a8d8ff' }} />
              </div>
            </div>
            <h2 className="text-2xl font-semibold" style={{ color: '#f0f0f5' }}>
              Let's build an ontology or extend an ontology
            </h2>
            <p className="text-base" style={{ color: '#94a3b8' }}>
              I'll help you create structured knowledge representations through natural conversation
            </p>
          </div>

          {/* Action Cards */}
          <div className="grid grid-cols-3 gap-4 w-full max-w-4xl">
            <button
              onClick={() => handleActionCard('build_new')}
              className="p-6 rounded-xl border-2 transition-all duration-200 hover:scale-105"
              style={{
                background: 'linear-gradient(135deg, rgba(168, 216, 255, 0.1), rgba(196, 181, 253, 0.1))',
                borderColor: 'rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            >
              <Plus className="h-8 w-8 mb-3" style={{ color: '#a8d8ff' }} />
              <h3 className="text-lg font-semibold mb-2">Build New</h3>
              <p className="text-sm" style={{ color: '#94a3b8' }}>
                Create a fresh ontology from scratch
              </p>
            </button>

            <button
              onClick={() => handleActionCard('view_existing')}
              className="p-6 rounded-xl border-2 transition-all duration-200 hover:scale-105"
              style={{
                background: 'linear-gradient(135deg, rgba(196, 181, 253, 0.1), rgba(255, 196, 229, 0.1))',
                borderColor: 'rgba(196, 181, 253, 0.3)',
                color: '#f0f0f5'
              }}
            >
              <Eye className="h-8 w-8 mb-3" style={{ color: '#c4b5fd' }} />
              <h3 className="text-lg font-semibold mb-2">View Existing</h3>
              <p className="text-sm" style={{ color: '#94a3b8' }}>
                Browse and interrogate your ontologies
              </p>
            </button>

            <button
              onClick={() => handleActionCard('extend')}
              className="p-6 rounded-xl border-2 transition-all duration-200 hover:scale-105"
              style={{
                background: 'linear-gradient(135deg, rgba(255, 196, 229, 0.1), rgba(168, 216, 255, 0.1))',
                borderColor: 'rgba(255, 196, 229, 0.3)',
                color: '#f0f0f5'
              }}
            >
              <GitBranch className="h-8 w-8 mb-3" style={{ color: '#ffc4e5' }} />
              <h3 className="text-lg font-semibold mb-2">Extend</h3>
              <p className="text-sm" style={{ color: '#94a3b8' }}>
                Add terms and relations to existing ones
              </p>
            </button>
          </div>
        </div>
      )}

      {/* Chat Messages */}
      {(!showWelcome || messages.length > 0) && (
        <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
          {messages.map((message, index) => {
            const isUser = message.role === 'user'
            return (
              <div key={index} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex items-start space-x-3 max-w-4xl ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  {/* Avatar */}
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    isUser 
                      ? 'bg-gradient-to-br from-accent-blue to-pastel-purple' 
                      : 'bg-dark-card border border-pastel-blue/30'
                  }`}>
                    {isUser ? (
                      <User className="h-5 w-5 text-white" />
                    ) : (
                      <Bot className="h-5 w-5" style={{ color: '#a8d8ff' }} />
                    )}
                  </div>

                  {/* Message Content */}
                  <div className={`rounded-2xl px-4 py-3 ${
                    isUser
                      ? 'bg-gradient-to-br from-accent-blue to-pastel-purple text-white'
                      : 'bg-dark-card border border-pastel-blue/20 text-dark-text'
                  }`}>
                    {message.content && (
                      <div className="whitespace-pre-wrap">{message.content}</div>
                    )}

                    {message.ui_elements && message.ui_elements.length > 0 && (
                      <ChatUIElements
                        elements={message.ui_elements}
                        onAction={(action, payload) => {
                          // If confirm, include the message action data
                          if (action === 'confirm' && message.action) {
                            handleSend(undefined, 'confirm', message.action)
                          } else {
                            handleSend(undefined, action, payload)
                          }
                        }}
                        currentOntologyId={currentOntologyId}
                      />
                    )}

                    {message.response_type === 'ontology_view' && message.metadata?.ontology && (
                      <OntologyViewer ontology={message.metadata.ontology} />
                    )}
                  </div>
                </div>
              </div>
            )
          })}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-4xl">
                <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-dark-card border border-pastel-blue/30">
                  <Bot className="h-5 w-5" style={{ color: '#a8d8ff' }} />
                </div>
                <div className="rounded-2xl px-4 py-3 bg-dark-card border border-pastel-blue/20">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#a8d8ff' }}></div>
                    <div className="w-2 h-2 rounded-full animate-pulse delay-75" style={{ backgroundColor: '#c4b5fd' }}></div>
                    <div className="w-2 h-2 rounded-full animate-pulse delay-150" style={{ backgroundColor: '#ffc4e5' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input Area */}
      <div className="border-t pt-4" style={{ borderColor: 'rgba(168, 216, 255, 0.2)' }}>
        <div className="flex items-end space-x-4">
          <div className="flex-1 rounded-xl border-2 p-2" style={{
            borderColor: 'rgba(168, 216, 255, 0.3)',
            background: 'rgba(30, 34, 45, 0.5)'
          }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe what you'd like to do with ontologies..."
              className="w-full bg-transparent resize-none outline-none placeholder-gray-500"
              style={{ 
                color: '#f0f0f5',
                minHeight: '48px',
                maxHeight: '200px',
              }}
              rows={1}
            />
          </div>
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="p-4 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
            style={{
              background: input.trim() && !isLoading
                ? 'linear-gradient(90deg, #a8d8ff, #c4b5fd)'
                : 'rgba(168, 216, 255, 0.2)',
              color: input.trim() && !isLoading ? '#1e222d' : '#94a3b8'
            }}
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

