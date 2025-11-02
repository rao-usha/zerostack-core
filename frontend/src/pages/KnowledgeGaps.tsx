import { useState, useEffect } from 'react'
import { AlertCircle, Clock, Database, TrendingUp, CheckCircle2 } from 'lucide-react'
import { getKnowledgeGaps, listDatasets } from '../api/client'

export default function KnowledgeGaps() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [gaps, setGaps] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const data = await listDatasets()
      setDatasets(data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedDataset) return

    setLoading(true)
    try {
      const result = await getKnowledgeGaps(selectedDataset)
      setGaps(result)
    } catch (error: any) {
      console.error('Failed to analyze gaps:', error)
      alert(error.response?.data?.detail || 'Failed to identify knowledge gaps')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">Knowledge Gap Analysis</h1>
        <p className="mt-2 text-dark-muted">Identify gaps in your data coverage and knowledge</p>
      </div>

      {/* Controls */}
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-dark-text mb-2">
              Select Dataset
            </label>
            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a dataset...</option>
              {datasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.filename} ({dataset.rows} rows)
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={!selectedDataset || loading}
            className="bg-gradient-to-r from-bright-blue to-bright-purple text-white px-6 py-2 rounded-lg hover:from-accent-blue/90 hover:to-accent-purple/90 disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Identify Gaps'}
          </button>
        </div>
      </div>

      {/* Gaps Report */}
      {gaps && (
        <div className="space-y-6">
          {/* Feature Gaps */}
          {gaps.feature_gaps && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Database className="h-6 w-6 text-red-500" />
                <h2 className="text-xl font-bold text-dark-text">Feature Gaps</h2>
              </div>
              {gaps.feature_gaps.identified_gaps && gaps.feature_gaps.identified_gaps.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                      {gaps.feature_gaps.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded p-4">
                    <p className="font-medium text-red-900 mb-2">Missing Features:</p>
                    <ul className="list-disc list-inside space-y-1 text-red-800">
                      {gaps.feature_gaps.identified_gaps.map((gap: string, index: number) => (
                        <li key={index}>{gap.replace('_', ' ').toUpperCase()}</li>
                      ))}
                    </ul>
                  </div>
                  {gaps.feature_gaps.suggestions && gaps.feature_gaps.suggestions.length > 0 && (
                    <div className="mt-4">
                      <p className="font-medium text-dark-text mb-2">Suggestions:</p>
                      <ul className="space-y-1">
                        {gaps.feature_gaps.suggestions.map((suggestion: string, index: number) => (
                          <li key={index} className="text-sm text-dark-text flex items-start">
                            <span className="text-blue-500 mr-2">→</span>
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-dark-muted">No significant feature gaps identified.</p>
              )}
            </div>
          )}

          {/* Temporal Gaps */}
          {gaps.temporal_gaps && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Clock className="h-6 w-6 text-blue-500" />
                <h2 className="text-xl font-bold text-dark-text">Temporal Coverage</h2>
              </div>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  {gaps.temporal_gaps.has_temporal_data ? (
                    <>
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                      <span className="text-green-700">Temporal data detected</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-5 w-5 text-orange-500" />
                      <span className="text-orange-700">No temporal dimension found</span>
                    </>
                  )}
                </div>
                {gaps.temporal_gaps.date_columns && gaps.temporal_gaps.date_columns.length > 0 && (
                  <div>
                    <p className="text-sm text-dark-muted">Date columns: {gaps.temporal_gaps.date_columns.join(', ')}</p>
                    {gaps.temporal_gaps.time_span_days && (
                      <p className="text-sm text-dark-muted">
                        Time span: {gaps.temporal_gaps.time_span_days} days
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Coverage Gaps */}
          {gaps.coverage_gaps && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <AlertCircle className="h-6 w-6 text-orange-500" />
                <h2 className="text-xl font-bold text-dark-text">Coverage Gaps</h2>
              </div>
              {gaps.coverage_gaps.gaps && gaps.coverage_gaps.gaps.length > 0 ? (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      gaps.coverage_gaps.severity === 'high' 
                        ? 'bg-red-100 text-red-800'
                        : gaps.coverage_gaps.severity === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {gaps.coverage_gaps.severity.toUpperCase()} SEVERITY
                    </span>
                  </div>
                  {gaps.coverage_gaps.gaps.map((gap: any, index: number) => (
                    <div key={index} className="bg-orange-50 border border-orange-200 rounded p-4">
                      <p className="font-medium text-orange-900">{gap.type.replace('_', ' ').toUpperCase()}</p>
                      {gap.columns && (
                        <p className="text-sm text-orange-700 mt-1">
                          Affected columns: {gap.columns.join(', ')}
                        </p>
                      )}
                      {gap.sample_count && (
                        <p className="text-sm text-orange-700 mt-1">
                          Sample count: {gap.sample_count}
                        </p>
                      )}
                      <p className="text-sm text-orange-800 mt-2">{gap.impact}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-dark-muted">No significant coverage gaps identified.</p>
              )}
            </div>
          )}

          {/* Data Diversity */}
          {gaps.data_diversity && Object.keys(gaps.data_diversity).length > 0 && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <h2 className="text-xl font-bold text-dark-text mb-4">Data Diversity Assessment</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-dark-border">
                  <thead className="bg-dark-surface">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase">Column</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase">Unique Values</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase">Diversity Ratio</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase">Assessment</th>
                    </tr>
                  </thead>
                  <tbody className="bg-dark-card divide-y divide-dark-border">
                    {Object.entries(gaps.data_diversity).map(([col, stats]: [string, any]) => (
                      <tr key={col}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-dark-text">{col}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-muted">{stats.unique_values}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-muted">
                          {(stats.diversity_ratio * 100).toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            stats.assessment === 'high'
                              ? 'bg-green-100 text-green-800'
                              : stats.assessment === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {stats.assessment.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Relationship Gaps */}
          {gaps.relationship_gaps && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <TrendingUp className="h-6 w-6 text-purple-500" />
                <h2 className="text-xl font-bold text-dark-text">Relationship Analysis</h2>
              </div>
              <div className="space-y-3">
                {gaps.relationship_gaps.can_analyze_relationships ? (
                  <>
                    <p className="text-dark-text">
                      Strong relationships found: {gaps.relationship_gaps.strong_relationships_found}
                    </p>
                    <p className="text-sm text-dark-muted">
                      {gaps.relationship_gaps.recommendation}
                    </p>
                  </>
                ) : (
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
                    <p className="text-yellow-800">{gaps.relationship_gaps.reason}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {gaps.recommendations && gaps.recommendations.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-blue-900 mb-4">Recommendations</h2>
              <ul className="space-y-2">
                {gaps.recommendations.map((rec: string, index: number) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span className="text-blue-900">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

