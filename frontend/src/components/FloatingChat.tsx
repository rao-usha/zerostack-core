import { useState, useRef, useEffect } from 'react'
import { MessageCircle, ChevronRight, ChevronLeft, Send, Bot, User, Sparkles } from 'lucide-react'
import { chatQuery, listDatasets } from '../api/client'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export default function FloatingChat() {
  const [isExpanded, setIsExpanded] = useState(true)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: '👋 Hi! I\'m your AI data assistant. Upload a dataset and ask me anything!\n\n💡 **Try asking**:\n• "Give me an overview"\n• "What trends do you see?"\n• "Show me insights"',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [datasets, setDatasets] = useState<any[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const suggestedQuestions = [
    "Give me an overview",
    "What are the key insights?",
    "Show me trends",
    "Are there correlations?",
    "Recommend next steps"
  ]

  useEffect(() => {
    loadDatasets()
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async (text?: string) => {
    const messageText = text || input
    if (!messageText.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatQuery(messageText, selectedDataset || undefined)
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || 'Failed to get response'}`,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatMessage = (content: string) => {
    // Split by lines
    const lines = content.split('\n')
    
    return (
      <div className="space-y-2">
        {lines.map((line, idx) => {
          // Skip empty lines
          if (!line.trim()) return <div key={idx} className="h-2" />

          // Bold text with **
          let formattedLine = line
          const boldRegex = /\*\*(.*?)\*\*/g
          const parts = []
          let lastIndex = 0
          let match

          while ((match = boldRegex.exec(line)) !== null) {
            // Add text before match
            if (match.index > lastIndex) {
              parts.push(
                <span key={`text-${idx}-${lastIndex}`}>
                  {line.substring(lastIndex, match.index)}
                </span>
              )
            }
            // Add bold text
            parts.push(
              <strong key={`bold-${idx}-${match.index}`} style={{ color: '#a8d8ff', fontWeight: 600 }}>
                {match[1]}
              </strong>
            )
            lastIndex = match.index + match[0].length
          }

          // Add remaining text
          if (lastIndex < line.length) {
            parts.push(
              <span key={`text-${idx}-${lastIndex}`}>
                {line.substring(lastIndex)}
              </span>
            )
          }

          // Render based on line type
          if (line.startsWith('• ')) {
            return (
              <div key={idx} className="flex items-start space-x-2 ml-2">
                <span style={{ color: '#a8d8ff', marginTop: '2px' }}>•</span>
                <span className="flex-1">{parts.length > 0 ? parts : line.substring(2)}</span>
              </div>
            )
          } else if (line.trim().startsWith('-')) {
            return (
              <div key={idx} className="flex items-start space-x-2 ml-4">
                <span style={{ color: '#c4b5fd', marginTop: '2px' }}>→</span>
                <span className="flex-1">{parts.length > 0 ? parts : line.trim().substring(1)}</span>
              </div>
            )
          } else if (line.match(/^\d+\./)) {
            return (
              <div key={idx} className="flex items-start space-x-2 ml-2">
                <span style={{ color: '#a8d8ff', fontWeight: 600 }}>{line.match(/^\d+\./)?.[0]}</span>
                <span className="flex-1">{parts.length > 0 ? parts : line.replace(/^\d+\.\s*/, '')}</span>
              </div>
            )
          } else {
            return (
              <div key={idx}>
                {parts.length > 0 ? parts : line}
              </div>
            )
          }
        })}
      </div>
    )
  }

  return (
    <div
      className={`fixed top-0 right-0 h-screen flex flex-col transition-all duration-300 ease-in-out z-40 ${
        isExpanded ? 'w-96' : 'w-12'
      }`}
      style={{
        backgroundColor: '#1a1a24',
        borderLeft: '1px solid rgba(168, 216, 255, 0.12)'
      }}
    >
      {/* Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="absolute -left-10 top-1/2 -translate-y-1/2 p-2 rounded-l-lg transition-all duration-300"
        style={{
          backgroundColor: 'rgba(168, 216, 255, 0.15)',
          border: '1px solid rgba(168, 216, 255, 0.3)',
          color: '#a8d8ff'
        }}
        aria-label={isExpanded ? 'Collapse chat' : 'Expand chat'}
      >
        {isExpanded ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
      </button>

      {isExpanded ? (
        <>
          {/* Header */}
          <div 
            className="flex items-center space-x-3 p-4"
            style={{
              borderBottom: '1px solid rgba(168, 216, 255, 0.12)',
              background: 'linear-gradient(135deg, rgba(168, 216, 255, 0.08), rgba(196, 181, 253, 0.08))'
            }}
          >
            <div 
              className="h-10 w-10 rounded-full flex items-center justify-center"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                border: '1px solid rgba(168, 216, 255, 0.3)'
              }}
            >
              <Sparkles className="h-5 w-5" style={{ color: '#a8d8ff' }} />
            </div>
            <div>
              <h3 
                className="font-semibold"
                style={{
                  background: 'linear-gradient(90deg, #a8d8ff, #c4b5fd)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text'
                }}
              >
                AI Assistant
              </h3>
              <p className="text-xs" style={{ color: '#b0b8c0' }}>Ask me anything</p>
            </div>
          </div>

          {/* Dataset Selector */}
          {datasets.length > 0 && (
            <div 
              className="p-4"
              style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.08)' }}
            >
              <label className="block text-xs font-medium mb-2" style={{ color: '#a8d8ff' }}>
                Select Dataset (Optional)
              </label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm focus:ring-2"
                style={{
                  backgroundColor: '#13131a',
                  border: '1px solid rgba(168, 216, 255, 0.15)',
                  color: '#f0f0f5'
                }}
              >
                <option value="">All datasets</option>
                {datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.filename} ({dataset.rows} rows)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Suggested Questions */}
          {messages.length <= 1 && (
            <div className="p-4" style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.08)' }}>
              <p className="text-xs font-medium mb-3" style={{ color: '#b0b8c0' }}>Quick questions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(question)}
                    className="text-xs px-3 py-1.5 rounded-full transition-all"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.08)',
                      border: '1px solid rgba(168, 216, 255, 0.15)',
                      color: '#a8d8ff'
                    }}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex items-start space-x-2 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0">
                    <div 
                      className="h-8 w-8 rounded-full flex items-center justify-center"
                      style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.15)',
                        border: '1px solid rgba(168, 216, 255, 0.3)'
                      }}
                    >
                      <Bot className="h-4 w-4" style={{ color: '#a8d8ff' }} />
                    </div>
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-lg px-4 py-3 ${
                    message.role === 'user' ? '' : ''
                  }`}
                  style={message.role === 'user' ? {
                    background: 'linear-gradient(135deg, rgba(168, 216, 255, 0.2), rgba(196, 181, 253, 0.2))',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    color: '#f0f0f5'
                  } : {
                    backgroundColor: '#13131a',
                    border: '1px solid rgba(168, 216, 255, 0.12)',
                    color: '#f0f0f5'
                  }}
                >
                  <div className="text-sm leading-relaxed">
                    {message.role === 'assistant' ? formatMessage(message.content) : message.content}
                  </div>
                  <p className="text-xs mt-2" style={{ color: '#b0b8c0', opacity: 0.7 }}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="flex-shrink-0">
                    <div 
                      className="h-8 w-8 rounded-full flex items-center justify-center"
                      style={{
                        backgroundColor: 'rgba(196, 181, 253, 0.15)',
                        border: '1px solid rgba(196, 181, 253, 0.3)'
                      }}
                    >
                      <User className="h-4 w-4" style={{ color: '#c4b5fd' }} />
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex items-start space-x-2">
                <div className="flex-shrink-0">
                  <div 
                    className="h-8 w-8 rounded-full flex items-center justify-center"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.15)',
                      border: '1px solid rgba(168, 216, 255, 0.3)'
                    }}
                  >
                    <Bot className="h-4 w-4 animate-pulse" style={{ color: '#a8d8ff' }} />
                  </div>
                </div>
                <div 
                  className="rounded-lg px-4 py-3"
                  style={{
                    backgroundColor: '#13131a',
                    border: '1px solid rgba(168, 216, 255, 0.12)'
                  }}
                >
                  <p className="text-sm" style={{ color: '#a8d8ff' }}>Analyzing your question...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div 
            className="p-4"
            style={{
              borderTop: '1px solid rgba(168, 216, 255, 0.12)',
              backgroundColor: '#13131a'
            }}
          >
            <div className="flex flex-col space-y-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about your data..."
                rows={2}
                className="w-full px-3 py-2 rounded-lg text-sm resize-none focus:ring-2"
                style={{
                  backgroundColor: '#1a1a24',
                  border: '1px solid rgba(168, 216, 255, 0.15)',
                  color: '#f0f0f5'
                }}
                disabled={loading}
              />
              <button
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
                className="w-full px-4 py-2.5 rounded-lg flex items-center justify-center space-x-2 transition-all duration-300 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.2), rgba(196, 181, 253, 0.2))',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  color: '#a8d8ff'
                }}
              >
                <Send className="h-4 w-4" />
                <span>Send Message</span>
              </button>
            </div>
          </div>
        </>
      ) : (
        /* Collapsed State */
        <div className="flex flex-col items-center justify-center h-full">
          <div className="transform -rotate-90 whitespace-nowrap">
            <div className="flex items-center space-x-2">
              <MessageCircle className="h-5 w-5" style={{ color: '#a8d8ff' }} />
              <span 
                className="text-sm font-semibold"
                style={{
                  background: 'linear-gradient(90deg, #a8d8ff, #c4b5fd)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text'
                }}
              >
                AI Chat
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
