import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import { chatQuery, listDatasets, listOntologies, createOntology, addOntologyTerms, publishOntologyVersion, getOntology } from '../api/client'
import ChatUIElements from '../components/ChatUIElements'
import OntologyViewer from '../components/OntologyViewer'
// Markdown rendering simplified

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  responseType?: string
  action?: any
  uiElements?: any[]
  metadata?: any
}

export default function ChatEnhanced() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '👋 Hi! I\'m your AI assistant. I can help you:\n\n📊 **Analyze data** - Upload datasets and get insights\n🗂️ **Build ontologies** - Create knowledge structures for your domain\n\n**Try asking**: "Create a retail support ontology" or "Analyze my data"',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [datasets, setDatasets] = useState<any[]>([])
  const [ontologies, setOntologies] = useState<any[]>([])
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadDatasets()
    loadOntologies()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadDatasets = async () => {
    try {
      const data = await listDatasets()
      setDatasets(data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    }
  }

  const loadOntologies = async () => {
    try {
      const data = await listOntologies()
      setOntologies(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Failed to load ontologies:', error)
      setOntologies([])
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatQuery(input, selectedDataset || undefined)
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
        responseType: response.response_type,
        action: response.action,
        uiElements: response.ui_elements,
        metadata: response.metadata,
      }
      
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || 'Failed to get response'}`,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleUIAction = async (messageIndex: number, action: string, data?: any) => {
    const message = messages[messageIndex]
    
    if (action === 'cancel') {
      // Just add a cancellation message
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '❌ Action cancelled. What would you like to do instead?',
        timestamp: new Date().toISOString(),
      }])
      return
    }

    if (action === 'confirm' && message.action) {
      setLoading(true)
      
      try {
        let result
        const actionType = message.action.type
        const params = message.action.params

        switch (actionType) {
          case 'create_ontology':
            result = await createOntology(
              params.org_id,
              params.name,
              params.description
            )
            await loadOntologies() // Refresh list
            setMessages((prev) => [...prev, {
              role: 'assistant',
              content: `✅ Created ontology **${params.name}**!\n\nOntology ID: \`${result.ontology_id}\`\n\n💡 You can now add terms by saying "add terms for [topic]" or "suggest terms about [topic]"`,
              timestamp: new Date().toISOString(),
            }])
            break

          case 'suggest_terms':
            // Mock AI suggestion for now
            const mockTerms = [
              { term: 'rma', definition: 'Return Merchandise Authorization' },
              { term: 'refund', definition: 'Money returned to customer' },
              { term: 'exchange', definition: 'Product swap' },
            ]
            setMessages((prev) => [...prev, {
              role: 'assistant',
              content: `💡 Here are suggested terms:\n\n${mockTerms.map(t => `• **${t.term}**: ${t.definition}`).join('\n')}\n\nWould you like to add these?`,
              timestamp: new Date().toISOString(),
              action: {
                type: 'add_terms_confirmed',
                params: { terms: mockTerms }
              },
              uiElements: [
                { type: 'button', label: 'Add All Terms', action: 'confirm' },
                { type: 'button', label: 'Cancel', action: 'cancel' }
              ]
            }])
            break

          case 'add_terms_confirmed':
            // Add terms to ontology
            if (data?.ontology_id && params.terms) {
              result = await addOntologyTerms(data.ontology_id, params.terms)
              setMessages((prev) => [...prev, {
                role: 'assistant',
                content: `✅ Added ${result.added} terms to your ontology!\n\nYou can now:\n• View the ontology: "show me the ontology"\n• Add relations: "add relations"\n• Publish: "publish as v1.0"`,
                timestamp: new Date().toISOString(),
              }])
            }
            break

          case 'view_ontology':
            if (params.ontology_id) {
              const ontologyData = await getOntology(params.ontology_id)
              setMessages((prev) => [...prev, {
                role: 'assistant',
                content: `📊 Here's your ontology:`,
                timestamp: new Date().toISOString(),
                responseType: 'visualization',
                metadata: { ontology_id: params.ontology_id, data: ontologyData }
              }])
            }
            break

          case 'publish_version':
            if (params.ontology_id) {
              result = await publishOntologyVersion(
                params.ontology_id,
                params.change_summary
              )
              setMessages((prev) => [...prev, {
                role: 'assistant',
                content: `✅ Published version **${result.version_id}**!\n\nDigest: \`${result.digest}\`\n\nThis version is now immutable and can be referenced by other systems.`,
                timestamp: new Date().toISOString(),
              }])
            }
            break
        }
      } catch (error: any) {
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: `❌ Error: ${error.response?.data?.detail || error.message || 'Action failed'}`,
          timestamp: new Date().toISOString(),
        }])
      } finally {
        setLoading(false)
      }
    }

    // Handle ontology selection
    if (action === 'select' && data?.ontology_id) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `✅ Selected ontology. What would you like to do with it?`,
        timestamp: new Date().toISOString(),
      }])
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user'

    return (
      <div key={index} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
        {!isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-accent-blue to-pastel-purple flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
        )}

        <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-gradient-to-br from-accent-blue to-pastel-purple text-white'
              : 'bg-dark-card border border-pastel-blue/20 text-dark-text'
          }`}>
            {message.content && (
              <div className="whitespace-pre-wrap">{message.content}</div>
            )}

            {/* Render UI Elements */}
            {message.uiElements && message.uiElements.length > 0 && (
              <ChatUIElements
                elements={message.uiElements}
                onAction={(action, data) => handleUIAction(index, action, data)}
                availableOntologies={ontologies}
              />
            )}

            {/* Render Visualization */}
            {message.responseType === 'visualization' && message.metadata?.ontology_id && (
              <div className="mt-3">
                <OntologyViewer ontologyId={message.metadata.ontology_id} />
              </div>
            )}
          </div>

          <div className="text-xs text-dark-muted mt-1">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>

        {isUser && (
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-dark-surface flex items-center justify-center border border-pastel-blue/20">
            <User className="w-5 h-5 text-dark-text" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-bright-purple" />
          AI Chat Assistant
        </h1>
        <p className="mt-2 text-dark-muted">Conversational data analysis and ontology management</p>
      </div>

      {/* Dataset Selector */}
      {datasets.length > 0 && (
        <div className="bg-dark-card rounded-xl shadow-2xl p-4 border border-pastel-blue/20">
          <label className="block text-sm font-medium text-dark-text mb-2">
            Select Dataset (Optional)
          </label>
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            className="w-full px-4 py-2 bg-dark-surface border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-accent-blue focus:border-accent-blue text-dark-text"
          >
            <option value="">No dataset selected</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.filename} ({dataset.rows} rows)
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Chat Messages */}
      <div className="bg-dark-card rounded-xl shadow-2xl flex-1 flex flex-col overflow-hidden border border-pastel-blue/20">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message, index) => renderMessage(message, index))}
          
          {loading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-accent-blue to-pastel-purple flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-dark-card border border-pastel-blue/20 rounded-2xl px-4 py-3">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-pastel-blue/20 p-4 bg-dark-surface">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about your data or ontologies..."
              className="flex-1 px-4 py-3 bg-dark-card border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-accent-blue focus:border-accent-blue text-dark-text placeholder-dark-muted"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-gradient-to-r from-accent-blue to-pastel-purple text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
            >
              <Send className="w-5 h-5" />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


