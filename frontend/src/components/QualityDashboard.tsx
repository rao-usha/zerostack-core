import { useState, useEffect } from 'react'
import {
  BarChart3,
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Loader2,
  RefreshCw,
} from 'lucide-react'
import {
  getSyntheticQualityDashboard,
  getSyntheticDistributions,
  getSyntheticPrivacyRisk,
  type QualityDashboard as QualityDashboardData,
  type DistributionComparison,
  type PrivacyRiskAssessment,
} from '../api/client'

interface QualityDashboardProps {
  datasetId: string
  initialQualityScore?: number
}

type ScoreRating = 'excellent' | 'good' | 'fair' | 'poor'

function getScoreRating(score: number): ScoreRating {
  if (score >= 0.95) return 'excellent'
  if (score >= 0.85) return 'good'
  if (score >= 0.7) return 'fair'
  return 'poor'
}

function getScoreColor(rating: ScoreRating): string {
  switch (rating) {
    case 'excellent': return 'text-green-500'
    case 'good': return 'text-blue-500'
    case 'fair': return 'text-yellow-500'
    case 'poor': return 'text-red-500'
  }
}

function getScoreBgColor(rating: ScoreRating): string {
  switch (rating) {
    case 'excellent': return 'bg-green-500/20'
    case 'good': return 'bg-blue-500/20'
    case 'fair': return 'bg-yellow-500/20'
    case 'poor': return 'bg-red-500/20'
  }
}

function getRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'low': return 'text-green-500'
    case 'medium': return 'text-yellow-500'
    case 'high': return 'text-red-500'
    default: return 'text-dark-muted'
  }
}

function getRiskBgColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'low': return 'bg-green-500/20'
    case 'medium': return 'bg-yellow-500/20'
    case 'high': return 'bg-red-500/20'
    default: return 'bg-dark-surface'
  }
}

interface ScoreCardProps {
  title: string
  score: number | null | undefined
  icon: React.ReactNode
  description?: string
}

function ScoreCard({ title, score, icon, description }: ScoreCardProps) {
  const displayScore = score ?? 0
  const rating = getScoreRating(displayScore)
  const percentage = Math.round(displayScore * 100)

  return (
    <div className="bg-dark-surface rounded-lg p-4 border border-pastel-blue/10">
      <div className="flex items-center gap-2 mb-2">
        <span className={getScoreColor(rating)}>{icon}</span>
        <span className="text-sm font-medium text-dark-text">{title}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className={`text-3xl font-bold ${getScoreColor(rating)}`}>
          {score !== null && score !== undefined ? `${percentage}%` : 'N/A'}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded-full ${getScoreBgColor(rating)} ${getScoreColor(rating)} capitalize`}>
          {rating}
        </span>
      </div>
      {description && (
        <p className="mt-2 text-xs text-dark-muted">{description}</p>
      )}
    </div>
  )
}

interface DistributionBarProps {
  label: string
  realValue: number
  syntheticValue: number
  maxValue: number
}

function DistributionBar({ label, realValue, syntheticValue, maxValue }: DistributionBarProps) {
  const realWidth = maxValue > 0 ? (realValue / maxValue) * 100 : 0
  const synthWidth = maxValue > 0 ? (syntheticValue / maxValue) * 100 : 0

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-dark-muted">
        <span className="truncate max-w-[100px]">{label}</span>
        <span>R: {realValue.toFixed(0)} | S: {syntheticValue.toFixed(0)}</span>
      </div>
      <div className="space-y-0.5">
        <div className="h-2 bg-dark-card rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full"
            style={{ width: `${realWidth}%` }}
          />
        </div>
        <div className="h-2 bg-dark-card rounded-full overflow-hidden">
          <div
            className="h-full bg-purple-500 rounded-full"
            style={{ width: `${synthWidth}%` }}
          />
        </div>
      </div>
    </div>
  )
}

export default function QualityDashboard({ datasetId, initialQualityScore }: QualityDashboardProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dashboard, setDashboard] = useState<QualityDashboardData | null>(null)
  const [distributions, setDistributions] = useState<DistributionComparison | null>(null)
  const [privacyRisk, setPrivacyRisk] = useState<PrivacyRiskAssessment | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [loadingPrivacy, setLoadingPrivacy] = useState(false)

  useEffect(() => {
    loadDashboard()
  }, [datasetId])

  const loadDashboard = async () => {
    setLoading(true)
    setError(null)

    try {
      // Load main dashboard data
      const dashboardData = await getSyntheticQualityDashboard(datasetId)
      setDashboard(dashboardData)

      // Load distribution data for charts
      const distData = await getSyntheticDistributions(datasetId)
      setDistributions(distData)
    } catch (err: any) {
      console.error('Failed to load quality dashboard:', err)
      setError(err.response?.data?.detail || 'Failed to load quality metrics')
    } finally {
      setLoading(false)
    }
  }

  const loadPrivacyRisk = async () => {
    if (privacyRisk || loadingPrivacy) return

    setLoadingPrivacy(true)
    try {
      const risk = await getSyntheticPrivacyRisk(datasetId)
      setPrivacyRisk(risk)
    } catch (err: any) {
      console.error('Failed to load privacy risk:', err)
    } finally {
      setLoadingPrivacy(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="h-6 w-6 animate-spin text-bright-blue" />
          <span className="text-dark-muted">Loading quality metrics...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="flex items-center gap-3 text-red-400">
          <XCircle className="h-5 w-5" />
          <span>{error}</span>
          <button
            onClick={loadDashboard}
            className="ml-auto flex items-center gap-1 text-sm text-bright-blue hover:text-bright-blue/80"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
        </div>
      </div>
    )
  }

  const qualityReport = dashboard?.quality_report
  const overallScore = qualityReport?.overall_score ?? initialQualityScore

  return (
    <div className="space-y-4">
      {/* Main Quality Card */}
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-6 w-6 text-bright-purple" />
            <h2 className="text-xl font-bold text-dark-text">Quality Metrics</h2>
          </div>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-sm text-dark-muted hover:text-dark-text"
          >
            {showDetails ? 'Hide' : 'Show'} Details
            {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>

        {/* Score Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <ScoreCard
            title="Overall Score"
            score={overallScore}
            icon={<TrendingUp className="h-5 w-5" />}
            description="Combined quality metric"
          />
          <ScoreCard
            title="Statistical Fidelity"
            score={qualityReport?.statistical_fidelity_score}
            icon={<BarChart3 className="h-5 w-5" />}
            description="Distribution similarity"
          />
          <ScoreCard
            title="Correlation"
            score={qualityReport?.correlation_score}
            icon={<TrendingUp className="h-5 w-5" />}
            description="Relationship preservation"
          />
          <ScoreCard
            title="Privacy"
            score={qualityReport?.privacy_score}
            icon={<Shield className="h-5 w-5" />}
            description="Re-identification risk"
          />
        </div>

        {/* Summary Stats */}
        {dashboard?.summary_stats && (
          <div className="flex items-center gap-6 text-sm text-dark-muted border-t border-pastel-blue/10 pt-4">
            <div>
              <span className="text-dark-text font-medium">{dashboard.summary_stats.real_rows.toLocaleString()}</span> source rows
            </div>
            <div>
              <span className="text-dark-text font-medium">{dashboard.summary_stats.synthetic_rows.toLocaleString()}</span> synthetic rows
            </div>
            <div>
              <span className="text-dark-text font-medium">{dashboard.summary_stats.total_columns}</span> columns
            </div>
          </div>
        )}
      </div>

      {/* Detailed Views (expandable) */}
      {showDetails && (
        <>
          {/* Distribution Comparison */}
          {distributions && (distributions.numeric_columns.length > 0 || distributions.categorical_columns.length > 0) && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <h3 className="text-lg font-semibold text-dark-text mb-4 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-500" />
                Distribution Comparison
              </h3>
              <div className="flex items-center gap-4 mb-4 text-xs text-dark-muted">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-blue-500" />
                  <span>Real Data</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-purple-500" />
                  <span>Synthetic Data</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Numeric columns */}
                {distributions.numeric_columns.slice(0, 4).map((col) => {
                  const maxCount = Math.max(
                    ...col.real_counts,
                    ...col.synthetic_counts
                  )
                  return (
                    <div key={col.column_name} className="space-y-2">
                      <h4 className="text-sm font-medium text-dark-text">{col.column_name}</h4>
                      <div className="space-y-1">
                        {col.bins.slice(0, -1).map((bin, i) => (
                          <DistributionBar
                            key={i}
                            label={`${bin.toFixed(1)}`}
                            realValue={col.real_counts[i]}
                            syntheticValue={col.synthetic_counts[i]}
                            maxValue={maxCount}
                          />
                        ))}
                      </div>
                    </div>
                  )
                })}

                {/* Categorical columns */}
                {distributions.categorical_columns.slice(0, 4).map((col) => {
                  const maxCount = Math.max(
                    ...col.real_counts,
                    ...col.synthetic_counts
                  )
                  return (
                    <div key={col.column_name} className="space-y-2">
                      <h4 className="text-sm font-medium text-dark-text">{col.column_name}</h4>
                      <div className="space-y-1">
                        {col.categories.slice(0, 6).map((cat, i) => (
                          <DistributionBar
                            key={i}
                            label={String(cat)}
                            realValue={col.real_counts[i]}
                            syntheticValue={col.synthetic_counts[i]}
                            maxValue={maxCount}
                          />
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Privacy Risk Assessment */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-dark-text flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-500" />
                Privacy Risk Assessment
              </h3>
              {!privacyRisk && (
                <button
                  onClick={loadPrivacyRisk}
                  disabled={loadingPrivacy}
                  className="flex items-center gap-1 text-sm text-bright-blue hover:text-bright-blue/80 disabled:opacity-50"
                >
                  {loadingPrivacy ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4" />
                      Analyze Privacy
                    </>
                  )}
                </button>
              )}
            </div>

            {privacyRisk ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-dark-muted">Overall Risk:</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskBgColor(privacyRisk.assessment.overall_risk)} ${getRiskColor(privacyRisk.assessment.overall_risk)} capitalize`}>
                    {privacyRisk.assessment.overall_risk}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-dark-surface rounded-lg">
                    <div className="text-xs text-dark-muted mb-1">Uniqueness Risk</div>
                    <div className={`text-sm font-medium ${getRiskColor(privacyRisk.assessment.uniqueness_risk.level)}`}>
                      {privacyRisk.assessment.uniqueness_risk.level}
                    </div>
                    {privacyRisk.assessment.uniqueness_risk.quasi_identifiers.length > 0 && (
                      <div className="mt-1 text-xs text-dark-muted">
                        QIDs: {privacyRisk.assessment.uniqueness_risk.quasi_identifiers.slice(0, 3).join(', ')}
                      </div>
                    )}
                  </div>

                  <div className="p-3 bg-dark-surface rounded-lg">
                    <div className="text-xs text-dark-muted mb-1">Similarity Risk</div>
                    <div className={`text-sm font-medium ${getRiskColor(privacyRisk.assessment.similarity_risk.level)}`}>
                      {privacyRisk.assessment.similarity_risk.level}
                    </div>
                    <div className="mt-1 text-xs text-dark-muted">
                      {privacyRisk.assessment.similarity_risk.close_matches} close matches
                    </div>
                  </div>

                  <div className="p-3 bg-dark-surface rounded-lg">
                    <div className="text-xs text-dark-muted mb-1">Outlier Risk</div>
                    <div className={`text-sm font-medium ${getRiskColor(privacyRisk.assessment.outlier_risk.level)}`}>
                      {privacyRisk.assessment.outlier_risk.level}
                    </div>
                    <div className="mt-1 text-xs text-dark-muted">
                      {privacyRisk.assessment.outlier_risk.extreme_values} extreme values
                    </div>
                  </div>
                </div>

                {privacyRisk.assessment.recommendations.length > 0 && (
                  <div className="mt-4">
                    <div className="text-xs text-dark-muted mb-2">Recommendations:</div>
                    <ul className="space-y-1">
                      {privacyRisk.assessment.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-dark-text">
                          <Info className="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6 text-dark-muted">
                <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Click "Analyze Privacy" to assess re-identification risks</p>
              </div>
            )}
          </div>

          {/* Recommendations & Warnings */}
          {qualityReport && (qualityReport.recommendations.length > 0 || qualityReport.warnings.length > 0) && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <h3 className="text-lg font-semibold text-dark-text mb-4">Recommendations & Warnings</h3>

              {qualityReport.warnings.length > 0 && (
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-yellow-500 mb-2">
                    <AlertTriangle className="h-4 w-4" />
                    <span className="text-sm font-medium">Warnings</span>
                  </div>
                  <ul className="space-y-1 pl-6">
                    {qualityReport.warnings.map((warning, i) => (
                      <li key={i} className="text-sm text-yellow-400 list-disc">{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {qualityReport.recommendations.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 text-blue-500 mb-2">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Recommendations</span>
                  </div>
                  <ul className="space-y-1 pl-6">
                    {qualityReport.recommendations.map((rec, i) => (
                      <li key={i} className="text-sm text-dark-text list-disc">{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
