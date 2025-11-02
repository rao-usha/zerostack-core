import { useState, useRef, useEffect } from 'react'
import { Send, MessageCircle, Bot, User } from 'lucide-react'
import { chatQuery } from '../api/client'
import { listDatasets } from '../api/client'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I can help you analyze your data, answer questions about your datasets, and provide insights. Upload a dataset and ask me anything!',
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [datasets, setDatasets] = useState<any[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

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

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">AI Chat Assistant</h1>
        <p className="mt-2 text-dark-muted">Ask questions about your data and get instant answers</p>
      </div>

      {/* Dataset Selector */}
      <div className="bg-dark-card rounded-xl shadow-2xl p-4 border border-pastel-blue/20">
        <label className="block text-sm font-medium text-dark-text mb-2">
          Select Dataset (Optional)
        </label>
        <select
          value={selectedDataset}
          onChange={(e) => setSelectedDataset(e.target.value)}
          className="w-full px-4 py-2 bg-dark-surface border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-accent-blue focus:border-accent-blue text-dark-text"
        >
          <option value="">No dataset selected (general questions)</option>
          {datasets.map((dataset) => (
            <option key={dataset.id} value={dataset.id}>
              {dataset.filename} ({dataset.rows} rows)
            </option>
          ))}
        </select>
      </div>

      {/* Chat Messages */}
      <div className="bg-dark-card rounded-xl shadow-2xl flex-1 flex flex-col overflow-hidden border border-pastel-blue/20">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex items-start space-x-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                </div>
              )}
              <div
                className={`max-w-3xl rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-bright-blue to-bright-purple text-white'
                    : 'bg-dark-surface text-dark-text border border-pastel-blue/20'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs mt-2 opacity-70">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
              {message.role === 'user' && (
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 rounded-full bg-dark-surface border border-pastel-blue/20 flex items-center justify-center">
                    <User className="h-5 w-5 text-accent-blue" />
                  </div>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
                  <Bot className="h-5 w-5 text-white animate-pulse" />
                </div>
              </div>
              <div className="bg-dark-surface rounded-lg px-4 py-3 border border-pastel-blue/20">
                <p className="text-sm text-dark-muted">Thinking...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-dark-border p-4 bg-dark-surface">
          <div className="flex space-x-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your data..."
              className="flex-1 px-4 py-2 bg-dark-card border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-accent-blue focus:border-accent-blue text-dark-text placeholder-dark-muted"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-gradient-to-r from-bright-blue to-bright-purple text-white px-6 py-2 rounded-lg hover:from-accent-blue/90 hover:to-accent-purple/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 shadow-lg transition-all duration-300"
            >
              <Send className="h-5 w-5" />
              <span>Send</span>
            </button>
          </div>
          <p className="mt-2 text-xs text-dark-muted">
            Try asking: "What columns are in my dataset?" or "Show me the average values"
          </p>
        </div>
      </div>
    </div>
  )
}

