import { useState, useEffect } from 'react'
import { CheckCircle2, AlertTriangle, TrendingUp } from 'lucide-react'
import { getDataQuality, listDatasets } from '../api/client'

export default function Quality() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [qualityReport, setQualityReport] = useState<any>(null)
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
      const result = await getDataQuality(selectedDataset)
      setQualityReport(result)
    } catch (error: any) {
      console.error('Failed to analyze quality:', error)
      alert(error.response?.data?.detail || 'Failed to analyze data quality')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100'
    if (score >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">Data Quality Assessment</h1>
        <p className="mt-2 text-dark-muted">Analyze and improve your data quality</p>
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
            {loading ? 'Analyzing...' : 'Analyze Quality'}
          </button>
        </div>
      </div>

      {/* Quality Report */}
      {qualityReport && (
        <div className="space-y-6">
          {/* Overall Score */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-dark-text">Overall Quality Score</h2>
              <div className={`${getScoreBgColor(qualityReport.overall_score)} px-4 py-2 rounded-lg`}>
                <span className={`text-3xl font-bold ${getScoreColor(qualityReport.overall_score)}`}>
                  {qualityReport.overall_score.toFixed(1)}
                </span>
                <span className="text-dark-muted ml-1">/ 100</span>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className={`h-4 rounded-full ${
                  qualityReport.overall_score >= 80
                    ? 'bg-green-500'
                    : qualityReport.overall_score >= 60
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${qualityReport.overall_score}%` }}
              />
            </div>
          </div>

          {/* Completeness */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <CheckCircle2 className="h-6 w-6 text-blue-500" />
              <h2 className="text-xl font-bold text-dark-text">Completeness</h2>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-dark-muted">Total Missing</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">
                    {qualityReport.completeness.total_missing}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-dark-muted">Completeness %</p>
                  <p className="text-2xl font-bold text-green-600">
                    {qualityReport.completeness.completeness_percentage.toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-dark-muted">Total Cells</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">
                    {qualityReport.completeness.total_cells}
                  </p>
                </div>
              </div>
              {Object.keys(qualityReport.completeness.columns_with_missing || {}).length > 0 && (
                <div>
                  <p className="text-sm font-medium text-dark-text mb-2">Columns with Missing Data:</p>
                  <div className="space-y-2">
                    {Object.entries(qualityReport.completeness.columns_with_missing).map(([col, info]: [string, any]) => (
                      <div key={col} className="flex items-center justify-between bg-dark-surface p-3 rounded">
                        <span className="font-medium text-dark-text">{col}</span>
                        <span className="text-sm text-dark-muted">
                          {info.missing_count} ({info.missing_percentage}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Consistency */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <TrendingUp className="h-6 w-6 text-purple-500" />
              <h2 className="text-xl font-bold text-dark-text">Consistency</h2>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-dark-muted">Duplicate Rows</p>
                <p className="text-2xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">
                  {qualityReport.consistency.duplicate_rows}
                </p>
                <p className="text-sm text-dark-muted">
                  {qualityReport.consistency.duplicate_percentage.toFixed(2)}% of total
                </p>
              </div>
              <div>
                <p className="text-sm text-dark-muted">Consistency Score</p>
                <p className="text-2xl font-bold text-purple-600">
                  {qualityReport.consistency.consistency_score.toFixed(1)}
                </p>
              </div>
            </div>
          </div>

          {/* Accuracy */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-orange-500" />
              <h2 className="text-xl font-bold text-dark-text">Accuracy</h2>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-dark-muted mb-2">Accuracy Score</p>
                <p className="text-2xl font-bold text-orange-600">
                  {qualityReport.accuracy.accuracy_score.toFixed(1)}
                </p>
              </div>
              {qualityReport.accuracy.issues && qualityReport.accuracy.issues.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-dark-text mb-2">Issues Detected:</p>
                  <div className="space-y-2">
                    {qualityReport.accuracy.issues.map((issue: any, index: number) => (
                      <div key={index} className="bg-orange-50 border border-orange-200 rounded p-3">
                        <p className="font-medium text-orange-900">{issue.column}</p>
                        <p className="text-sm text-orange-700">
                          {issue.count} outliers ({issue.percentage.toFixed(1)}%)
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Issues */}
          {qualityReport.issues && qualityReport.issues.length > 0 && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <h2 className="text-xl font-bold text-dark-text mb-4">Identified Issues</h2>
              <div className="space-y-3">
                {qualityReport.issues.map((issue: any, index: number) => (
                  <div
                    key={index}
                    className={`border-l-4 ${
                      issue.severity === 'high'
                        ? 'border-red-500 bg-red-50'
                        : 'border-yellow-500 bg-yellow-50'
                    } p-4 rounded`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-dark-text">{issue.description}</p>
                        <p className="text-sm text-dark-muted mt-1">{issue.recommendation}</p>
                      </div>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          issue.severity === 'high'
                            ? 'bg-red-200 text-red-800'
                            : 'bg-yellow-200 text-yellow-800'
                        }`}
                      >
                        {issue.severity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {qualityReport.recommendations && qualityReport.recommendations.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-blue-900 mb-4">Recommendations</h2>
              <ul className="space-y-2">
                {qualityReport.recommendations.map((rec: string, index: number) => (
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

