/**
 * Model Comparison view for Distillation Workbench.
 * Compare responses from multiple models and vote on quality.
 */
import {
  Eye, EyeOff, ChevronRight, Loader2, Check, Award
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Comparison, ComparisonDetail } from '../../types/distillation'

interface CompareViewProps {
  // Data
  comparisons: Comparison[]
  selectedComparison: ComparisonDetail | null
  comparisonLoading: boolean
  // State
  blindMode: boolean
  setBlindMode: (blind: boolean) => void
  selectedWinner: string | null
  setSelectedWinner: (winner: string | null) => void
  setSelectedComparison: (comp: ComparisonDetail | null) => void
  // Actions
  loadComparisonDetails: (comparisonId: string) => void
  handleSubmitVote: () => void
}

export default function CompareView({
  comparisons,
  selectedComparison,
  comparisonLoading,
  blindMode,
  setBlindMode,
  selectedWinner,
  setSelectedWinner,
  setSelectedComparison,
  loadComparisonDetails,
  handleSubmitVote
}: CompareViewProps) {
  return (
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
  )
}
