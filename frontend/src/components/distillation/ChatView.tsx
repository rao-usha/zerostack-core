/**
 * Interactive Chat view for Distillation Workbench.
 * Allows querying multiple models and banking responses.
 */
import {
  Send, Loader2, ChevronDown, X, Tag, ThumbsUp
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Response, AvailableModel } from '../../types/distillation'

interface ChatViewProps {
  // Chat state
  chatMessage: string
  setChatMessage: (message: string) => void
  selectedModels: string[]
  setSelectedModels: (models: string[]) => void
  chatResponses: Response[]
  chatLoading: boolean
  streamingStatus: string
  streamingContent: Record<string, string>
  activeModel: string | null
  // Model selection
  availableModels: AvailableModel[]
  apiKeys: Record<string, boolean>
  loadingModels: boolean
  // Actions
  handleChat: () => void
  handleBankResponse: (responseId: string) => void
  setTagResponseId: (id: string) => void
  setTagModalOpen: (open: boolean) => void
}

export default function ChatView({
  chatMessage,
  setChatMessage,
  selectedModels,
  setSelectedModels,
  chatResponses,
  chatLoading,
  streamingStatus,
  streamingContent,
  activeModel,
  availableModels,
  apiKeys,
  loadingModels,
  handleChat,
  handleBankResponse,
  setTagResponseId,
  setTagModalOpen
}: ChatViewProps) {
  return (
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
                  onClick={() => setSelectedModels(selectedModels.filter(id => id !== modelId))}
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
                  if (value && value.trim() && !selectedModels.includes(value)) {
                    setSelectedModels([...selectedModels.filter(id => id), value])
                  }
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
  )
}
