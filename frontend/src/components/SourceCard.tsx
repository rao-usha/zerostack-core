import { useState } from 'react'
import { Database, Table as TableIcon, FileText, Zap, Loader2, TrendingUp } from 'lucide-react'
import { DataSourceSummary, quickAnalyzeSource } from '../api/client'

interface SourceCardProps {
  source: DataSourceSummary
  onSourceClick: (sourceName: string) => void
  databaseName?: string
}

export default function SourceCard({ source, onSourceClick, databaseName }: SourceCardProps) {
  const [analyzing, setAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<string | null>(source.description || null)
  const [showAnalysis, setShowAnalysis] = useState(false)

  const handleQuickAnalysis = async (e: React.MouseEvent) => {
    e.stopPropagation() // Prevent card click
    setAnalyzing(true)
    setShowAnalysis(true)
    try {
      const result = await quickAnalyzeSource(source.source_name, databaseName)
      setAnalysis(result.analysis)
    } catch (error) {
      console.error('Failed to analyze source:', error)
      setAnalysis('Failed to generate analysis. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer overflow-hidden"
      onClick={() => onSourceClick(source.source_name)}
    >
      {/* Card Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              <Database className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{source.source_name}</h3>
              <p className="text-sm text-gray-500">
                {source.schemas.join(', ')}
              </p>
            </div>
          </div>
          
          {/* Quick Analysis Button */}
          <button
            onClick={handleQuickAnalysis}
            disabled={analyzing}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg hover:from-purple-600 hover:to-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Quick LLM Analysis"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>Analyze</span>
              </>
            )}
          </button>
        </div>
        
        {/* Analysis Result */}
        {showAnalysis && analysis && (
          <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="flex items-start gap-2">
              <TrendingUp className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-gray-700 whitespace-pre-wrap">{analysis}</div>
            </div>
          </div>
        )}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 p-6 bg-gray-50">
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <TableIcon className="w-4 h-4 text-gray-400" />
            <span className="text-2xl font-bold text-gray-900">{source.table_count}</span>
          </div>
          <p className="text-xs text-gray-600">Tables</p>
        </div>
        
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <FileText className="w-4 h-4 text-gray-400" />
            <span className="text-2xl font-bold text-gray-900">{source.column_count}</span>
          </div>
          <p className="text-xs text-gray-600">Columns</p>
        </div>
        
        <div className="text-center">
          <div className="mb-1">
            <span className="text-2xl font-bold text-green-600">
              {source.documentation_percentage}%
            </span>
          </div>
          <p className="text-xs text-gray-600">Documented</p>
        </div>
      </div>

      {/* Sample Tables */}
      <div className="px-6 pb-6">
        <p className="text-xs font-medium text-gray-500 mb-2">Sample Tables:</p>
        <div className="flex flex-wrap gap-1">
          {source.sample_tables.slice(0, 3).map((table, idx) => (
            <span
              key={idx}
              className="inline-block px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded"
            >
              {table}
            </span>
          ))}
          {source.sample_tables.length > 3 && (
            <span className="inline-block px-2 py-1 text-xs text-gray-500">
              +{source.sample_tables.length - 3} more
            </span>
          )}
        </div>
      </div>

      {/* Footer */}
      {source.last_updated && (
        <div className="px-6 py-3 bg-gray-100 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Last updated: {new Date(source.last_updated).toLocaleDateString()}
          </p>
        </div>
      )}
    </div>
  )
}
