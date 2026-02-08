/**
 * Expert Review view for Distillation Workbench.
 * Manage review queues and perform quality assessment.
 */
import {
  Plus, ChevronRight, Loader2, Users, Download, Play,
  ThumbsUp, ThumbsDown, AlertCircle
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { ReviewQueue, ReviewItem, Response } from '../../types/distillation'

interface CurrentReviewItem {
  item: ReviewItem
  response: Response
}

interface ReviewViewProps {
  // Data
  reviewQueues: ReviewQueue[]
  selectedQueue: ReviewQueue | null
  reviewItems: ReviewItem[]
  currentReviewItem: CurrentReviewItem | null
  reviewLoading: boolean
  // State
  reviewNotes: string
  setReviewNotes: (notes: string) => void
  reviewScore: string
  setReviewScore: (score: string) => void
  // Actions
  setCreateQueueOpen: (open: boolean) => void
  setSelectedQueue: (queue: ReviewQueue | null) => void
  setReviewItems: (items: ReviewItem[]) => void
  setCurrentReviewItem: (item: CurrentReviewItem | null) => void
  loadReviewItems: (queueId: string) => void
  getNextReviewItem: (queueId: string) => void
  handleAutoPopulateQueue: (queueId: string) => void
  handleExportQueue: (queueId: string, format: string) => void
  handleSubmitReview: (action: string) => void
}

export default function ReviewView({
  reviewQueues,
  selectedQueue,
  reviewItems,
  currentReviewItem,
  reviewLoading,
  reviewNotes,
  setReviewNotes,
  reviewScore,
  setReviewScore,
  setCreateQueueOpen,
  setSelectedQueue,
  setReviewItems,
  setCurrentReviewItem,
  loadReviewItems,
  getNextReviewItem,
  handleAutoPopulateQueue,
  handleExportQueue,
  handleSubmitReview
}: ReviewViewProps) {
  return (
    <div className="rounded-lg p-6" style={{
      backgroundColor: 'rgba(30, 30, 40, 0.8)',
      border: '1px solid rgba(168, 216, 255, 0.2)'
    }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>Expert Review</h2>
        <button
          onClick={() => setCreateQueueOpen(true)}
          className="px-3 py-2 rounded-lg flex items-center space-x-2"
          style={{
            backgroundColor: 'rgba(168, 216, 255, 0.15)',
            border: '1px solid rgba(168, 216, 255, 0.4)',
            color: '#a8d8ff'
          }}
        >
          <Plus className="h-4 w-4" /><span>New Queue</span>
        </button>
      </div>

      {!selectedQueue && !currentReviewItem ? (
        // Queue List
        <div className="space-y-3">
          {reviewQueues.length === 0 ? (
            <p style={{ color: '#b3d9ff' }}>No review queues yet. Create one to start expert review.</p>
          ) : (
            reviewQueues.map(queue => (
              <div
                key={queue.id}
                className="p-4 rounded-lg"
                style={{
                  backgroundColor: 'rgba(20, 20, 30, 0.6)',
                  border: '1px solid rgba(168, 216, 255, 0.1)'
                }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{queue.name}</h3>
                    <p className="text-xs mt-1" style={{ color: '#b3d9ff' }}>
                      {queue.description || 'No description'}
                    </p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">
                        {queue.pending_count || 0} pending
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400">
                        {queue.completed_count || 0} completed
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleAutoPopulateQueue(queue.id)}
                      className="px-2 py-1 rounded text-xs flex items-center space-x-1"
                      style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.2)',
                        border: '1px solid rgba(168, 216, 255, 0.4)',
                        color: '#a8d8ff'
                      }}
                    >
                      <Users className="h-3 w-3" /><span>Populate</span>
                    </button>
                    <button
                      onClick={() => handleExportQueue(queue.id, 'csv')}
                      className="px-2 py-1 rounded text-xs flex items-center space-x-1"
                      style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.2)',
                        border: '1px solid rgba(168, 216, 255, 0.4)',
                        color: '#a8d8ff'
                      }}
                    >
                      <Download className="h-3 w-3" /><span>Export</span>
                    </button>
                    <button
                      onClick={() => {
                        setSelectedQueue(queue)
                        loadReviewItems(queue.id)
                      }}
                      className="px-2 py-1 rounded text-xs"
                      style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.2)',
                        border: '1px solid rgba(168, 216, 255, 0.4)',
                        color: '#a8d8ff'
                      }}
                    >
                      View Items
                    </button>
                    <button
                      onClick={() => getNextReviewItem(queue.id)}
                      className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                      style={{
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        border: '1px solid rgba(16, 185, 129, 0.6)',
                        color: '#10b981'
                      }}
                    >
                      <Play className="h-3 w-3" /><span>Start Review</span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : currentReviewItem ? (
        // Active Review Interface
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => {
                setCurrentReviewItem(null)
                setSelectedQueue(null)
              }}
              className="text-sm flex items-center space-x-1"
              style={{ color: '#a8d8ff' }}
            >
              <ChevronRight className="h-4 w-4 rotate-180" /><span>Back to queues</span>
            </button>
            <span className="text-sm" style={{ color: '#b3d9ff' }}>
              Reviewing: {currentReviewItem.item.id.slice(0, 8)}...
            </span>
          </div>

          {reviewLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" style={{ color: '#a8d8ff' }} />
            </div>
          ) : (
            <>
              {/* Response to Review */}
              <div className="p-4 rounded-lg" style={{
                backgroundColor: 'rgba(20, 20, 30, 0.6)',
                border: '1px solid rgba(168, 216, 255, 0.1)'
              }}>
                {currentReviewItem.response && (
                  <>
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-1 rounded text-xs" style={{
                        backgroundColor: 'rgba(168, 216, 255, 0.2)',
                        color: '#a8d8ff'
                      }}>
                        {currentReviewItem.response.provider} / {currentReviewItem.response.model}
                      </span>
                    </div>
                    <p className="text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>Prompt:</p>
                    <p className="text-sm mb-4 p-2 rounded" style={{
                      backgroundColor: 'rgba(0, 0, 0, 0.3)',
                      color: '#f0f0f5'
                    }}>
                      {currentReviewItem.response.prompt_sent}
                    </p>
                    <p className="text-sm font-medium mb-2" style={{ color: '#a8d8ff' }}>Response:</p>
                    <div className="prose prose-sm prose-invert max-w-none p-2 rounded" style={{
                      backgroundColor: 'rgba(0, 0, 0, 0.3)',
                      color: '#f0f0f5'
                    }}>
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
                        {currentReviewItem.response.response_text}
                      </ReactMarkdown>
                    </div>
                  </>
                )}
              </div>

              {/* Review Controls */}
              <div className="space-y-3">
                <div>
                  <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Quality Score (0-1)</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={reviewScore}
                    onChange={e => setReviewScore(e.target.value)}
                    placeholder="0.8"
                    className="w-32 px-3 py-2 rounded-lg"
                    style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.8)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                  />
                </div>
                <div>
                  <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Review Notes</label>
                  <textarea
                    value={reviewNotes}
                    onChange={e => setReviewNotes(e.target.value)}
                    placeholder="Optional notes about this response..."
                    className="w-full px-3 py-2 rounded-lg"
                    style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.8)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                    rows={2}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-center space-x-4">
                <button
                  onClick={() => handleSubmitReview('rejected')}
                  className="px-4 py-2 rounded-lg flex items-center space-x-2"
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.6)',
                    color: '#ef4444'
                  }}
                >
                  <ThumbsDown className="h-4 w-4" /><span>Reject</span>
                </button>
                <button
                  onClick={() => handleSubmitReview('needs_revision')}
                  className="px-4 py-2 rounded-lg flex items-center space-x-2"
                  style={{
                    backgroundColor: 'rgba(251, 191, 36, 0.2)',
                    border: '1px solid rgba(251, 191, 36, 0.6)',
                    color: '#fbbf24'
                  }}
                >
                  <AlertCircle className="h-4 w-4" /><span>Needs Revision</span>
                </button>
                <button
                  onClick={() => handleSubmitReview('approved')}
                  className="px-4 py-2 rounded-lg flex items-center space-x-2"
                  style={{
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    border: '1px solid rgba(16, 185, 129, 0.6)',
                    color: '#10b981'
                  }}
                >
                  <ThumbsUp className="h-4 w-4" /><span>Approve</span>
                </button>
              </div>
            </>
          )}
        </div>
      ) : selectedQueue && (
        // Queue Items List
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => { setSelectedQueue(null); setReviewItems([]) }}
              className="text-sm flex items-center space-x-1"
              style={{ color: '#a8d8ff' }}
            >
              <ChevronRight className="h-4 w-4 rotate-180" /><span>Back to queues</span>
            </button>
            <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{selectedQueue.name}</h3>
          </div>

          <div className="space-y-2">
            {reviewItems.length === 0 ? (
              <p style={{ color: '#b3d9ff' }}>No items in this queue. Click "Populate" to add items.</p>
            ) : (
              reviewItems.map(item => (
                <div key={item.id} className="p-3 rounded-lg flex items-center justify-between" style={{
                  backgroundColor: 'rgba(20, 20, 30, 0.6)',
                  border: '1px solid rgba(168, 216, 255, 0.1)'
                }}>
                  <div className="flex items-center space-x-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      item.status === 'approved' ? 'bg-green-500/20 text-green-400' :
                      item.status === 'rejected' ? 'bg-red-500/20 text-red-400' :
                      item.status === 'needs_revision' ? 'bg-yellow-500/20 text-yellow-400' :
                      item.status === 'in_review' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>{item.status}</span>
                    {item.review_score !== null && (
                      <span className="text-xs" style={{ color: '#b3d9ff' }}>
                        Score: {item.review_score}
                      </span>
                    )}
                  </div>
                  <span className="text-xs" style={{ color: '#b3d9ff' }}>
                    Priority: {item.priority}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
