import { useState, useEffect } from 'react'
import { TrendingUp, Activity, BarChart3 } from 'lucide-react'
import { buildPredictiveModel, listDatasets, getDataset } from '../api/client'

export default function Models() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [datasetInfo, setDatasetInfo] = useState<any>(null)
  const [targetColumn, setTargetColumn] = useState<string>('')
  const [modelType, setModelType] = useState<string>('regression')
  const [modelResult, setModelResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadDatasets()
  }, [])

  useEffect(() => {
    if (selectedDataset) {
      loadDatasetInfo()
    }
  }, [selectedDataset])

  const loadDatasets = async () => {
    try {
      const data = await listDatasets()
      setDatasets(data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    }
  }

  const loadDatasetInfo = async () => {
    try {
      const info = await getDataset(selectedDataset)
      setDatasetInfo(info)
      if (info.columns_list && info.columns_list.length > 0) {
        // Auto-select first numeric column if available
        setTargetColumn(info.columns_list[0])
      }
    } catch (error) {
      console.error('Failed to load dataset info:', error)
    }
  }

  const handleBuildModel = async () => {
    if (!selectedDataset || !targetColumn) return

    setLoading(true)
    try {
      const result = await buildPredictiveModel(selectedDataset, targetColumn, modelType)
      setModelResult(result)
    } catch (error: any) {
      console.error('Failed to build model:', error)
      alert(error.response?.data?.detail || 'Failed to build model')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">Predictive Models</h1>
        <p className="mt-2 text-dark-muted">Build and analyze predictive models from your data</p>
      </div>

      {/* Controls */}
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="space-y-4">
          <div>
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

          {datasetInfo && (
            <>
              <div>
                <label className="block text-sm font-medium text-dark-text mb-2">
                  Target Column (what to predict)
                </label>
                <select
                  value={targetColumn}
                  onChange={(e) => setTargetColumn(e.target.value)}
                  className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select target column...</option>
                  {datasetInfo.columns_list?.map((col: string) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-text mb-2">
                  Model Type
                </label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="regression">Regression (for numeric predictions)</option>
                  <option value="classification">Classification (for categories)</option>
                </select>
              </div>
            </>
          )}

          <button
            onClick={handleBuildModel}
            disabled={!selectedDataset || !targetColumn || loading}
            className="bg-gradient-to-r from-bright-blue to-bright-purple text-white px-6 py-2 rounded-lg hover:from-accent-blue/90 hover:to-accent-purple/90 disabled:opacity-50"
          >
            {loading ? 'Building Model...' : 'Build Predictive Model'}
          </button>
        </div>
      </div>

      {/* Model Results */}
      {modelResult && (
        <div className="space-y-6">
          {/* Model Performance */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Activity className="h-6 w-6 text-green-500" />
              <h2 className="text-xl font-bold text-dark-text">Model Performance</h2>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-dark-muted">Model Type</p>
                <p className="text-2xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent capitalize">
                  {modelResult.model_type}
                </p>
              </div>
              <div>
                <p className="text-sm text-dark-muted">
                  {modelResult.model_type === 'classification' ? 'Accuracy' : 'R² Score'}
                </p>
                <p className="text-2xl font-bold text-green-600">
                  {modelResult.model_type === 'classification'
                    ? (modelResult.accuracy * 100).toFixed(2) + '%'
                    : modelResult.r2_score.toFixed(3)}
                </p>
              </div>
            </div>
            <div className="mt-4">
              <p className="text-sm text-dark-muted mb-2">Target Column</p>
              <p className="font-medium text-dark-text">{modelResult.target_column}</p>
            </div>
          </div>

          {/* Feature Importance */}
          {modelResult.feature_importance && Object.keys(modelResult.feature_importance).length > 0 && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <BarChart3 className="h-6 w-6 text-blue-500" />
                <h2 className="text-xl font-bold text-dark-text">Feature Importance</h2>
              </div>
              <div className="space-y-3">
                {Object.entries(modelResult.feature_importance)
                  .sort(([, a]: [string, any], [, b]: [string, any]) => b - a)
                  .map(([feature, importance]: [string, any]) => (
                    <div key={feature}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-dark-text">{feature}</span>
                        <span className="text-sm text-dark-muted">
                          {(importance * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-bright-blue to-bright-purple h-2 rounded-full"
                          style={{ width: `${importance * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Interpretation */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-2">Model Interpretation</h3>
            <div className="space-y-2 text-sm text-blue-800">
              {modelResult.model_type === 'classification' ? (
                <>
                  <p>
                    The model achieved {modelResult.accuracy * 100}% accuracy in predicting{' '}
                    {modelResult.target_column}.
                  </p>
                  <p>
                    Features are ranked by their importance in making predictions. Higher
                    importance means the feature has more influence on the outcome.
                  </p>
                </>
              ) : (
                <>
                  <p>
                    The model explains {(modelResult.r2_score * 100).toFixed(1)}% of the variance
                    in {modelResult.target_column} (R² = {modelResult.r2_score.toFixed(3)}).
                  </p>
                  <p>
                    Features are ranked by their importance. Use this information to understand
                    which factors most strongly influence {modelResult.target_column}.
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

