/**
 * Response Bank view for Distillation Workbench.
 * Search, filter, and manage banked responses.
 */
import {
  Search, Filter, Loader2, Trash2, Tag, ThumbsUp
} from 'lucide-react'
import { Response, Domain, Topic } from '../../types/distillation'

interface BankViewProps {
  // Data
  responses: Response[]
  domains: Domain[]
  topics: Topic[]
  loading: boolean
  // Search state
  searchQuery: string
  setSearchQuery: (query: string) => void
  filterProvider: string
  setFilterProvider: (provider: string) => void
  // Actions
  searchResponses: () => void
  handleDeleteResponse: (responseId: string) => void
  handleUpdateResponse: (responseId: string, updates: { domain_id?: string | null; topic_id?: string | null; quality_rating?: number | null }) => void
  handleBankResponse: (responseId: string) => void
  setTagResponseId: (id: string) => void
  setTagModalOpen: (open: boolean) => void
}

export default function BankView({
  responses,
  domains,
  topics,
  loading,
  searchQuery,
  setSearchQuery,
  filterProvider,
  setFilterProvider,
  searchResponses,
  handleDeleteResponse,
  handleUpdateResponse,
  handleBankResponse,
  setTagResponseId,
  setTagModalOpen
}: BankViewProps) {
  return (
    <div className="rounded-lg p-6" style={{
      backgroundColor: 'rgba(30, 30, 40, 0.8)',
      border: '1px solid rgba(168, 216, 255, 0.2)'
    }}>
      <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Response Bank</h2>

      {/* Search and Filters */}
      <div className="space-y-3 mb-4">
        <div className="flex flex-wrap gap-2">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: '#b3d9ff' }} />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search responses..."
              className="w-full pl-10 pr-4 py-2 rounded-lg text-sm"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            />
          </div>
          <select
            value={filterProvider}
            onChange={e => setFilterProvider(e.target.value)}
            className="px-3 py-2 rounded-lg text-sm"
            style={{
              backgroundColor: 'rgba(20, 20, 30, 0.8)',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              color: '#f0f0f5'
            }}
          >
            <option value="">All Providers</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="xai">xAI</option>
          </select>
          <button
            onClick={searchResponses}
            className="px-4 py-2 rounded-lg flex items-center space-x-2"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.2)',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              color: '#a8d8ff'
            }}
          >
            <Filter className="h-4 w-4" /><span>Search</span>
          </button>
        </div>
      </div>

      {/* Response List */}
      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin" style={{ color: '#a8d8ff' }} />
        </div>
      ) : responses.length === 0 ? (
        <p style={{ color: '#b3d9ff' }}>No responses found. Use Interactive Chat to capture knowledge.</p>
      ) : (
        <div className="space-y-3">
          {responses.map(response => (
            <div key={response.id} className="p-4 rounded-lg" style={{
              backgroundColor: 'rgba(20, 20, 30, 0.6)',
              border: '1px solid rgba(168, 216, 255, 0.1)'
            }}>
              {/* Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-1 rounded text-xs" style={{
                    backgroundColor: 'rgba(168, 216, 255, 0.2)',
                    color: '#a8d8ff'
                  }}>
                    {response.provider} / {response.model}
                  </span>
                  {response.quality_rating && (
                    <span className="flex items-center text-xs" style={{ color: '#fbbf24' }}>
                      {'★'.repeat(response.quality_rating)}{'☆'.repeat(5 - response.quality_rating)}
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs" style={{ color: '#b3d9ff' }}>
                    {new Date(response.created_at).toLocaleString()}
                  </span>
                  <button
                    onClick={() => handleDeleteResponse(response.id)}
                    className="p-1 rounded hover:bg-red-500/20 text-red-400"
                    title="Delete response"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Content */}
              <p className="text-sm text-gray-400 mb-2 line-clamp-1">
                <strong>Prompt:</strong> {response.prompt_sent}
              </p>
              <p className="text-sm line-clamp-3 mb-3" style={{ color: '#f0f0f5' }}>
                {response.response_text}
              </p>

              {/* Organization Row */}
              <div className="flex flex-wrap items-center gap-2 mb-2 pb-2" style={{ borderBottom: '1px solid rgba(168, 216, 255, 0.1)' }}>
                <select
                  value={response.domain_id || ''}
                  onChange={e => handleUpdateResponse(response.id, { domain_id: e.target.value || null })}
                  className="px-2 py-1 rounded text-xs"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.2)',
                    color: '#b3d9ff'
                  }}
                >
                  <option value="">No Domain</option>
                  {domains.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>

                <select
                  value={response.topic_id || ''}
                  onChange={e => handleUpdateResponse(response.id, { topic_id: e.target.value || null })}
                  className="px-2 py-1 rounded text-xs"
                  style={{
                    backgroundColor: 'rgba(20, 20, 30, 0.8)',
                    border: '1px solid rgba(168, 216, 255, 0.2)',
                    color: '#b3d9ff'
                  }}
                >
                  <option value="">No Topic</option>
                  {topics.filter(t => !response.domain_id || t.domain_id === response.domain_id).map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>

                {/* Rating */}
                <div className="flex items-center space-x-1">
                  {[1, 2, 3, 4, 5].map(rating => (
                    <button
                      key={rating}
                      onClick={() => handleUpdateResponse(response.id, { quality_rating: rating })}
                      className="text-sm hover:scale-110 transition-transform"
                      style={{ color: (response.quality_rating || 0) >= rating ? '#fbbf24' : '#4b5563' }}
                    >
                      ★
                    </button>
                  ))}
                </div>

                {/* Tags display */}
                {response.tags && response.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {response.tags.map(tag => (
                      <span key={tag.id} className="px-1.5 py-0.5 rounded text-xs" style={{
                        backgroundColor: tag.color ? `${tag.color}30` : 'rgba(168, 216, 255, 0.1)',
                        color: tag.color || '#a8d8ff'
                      }}>
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2">
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
                  <ThumbsUp className="h-3 w-3" /><span>Bank</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
