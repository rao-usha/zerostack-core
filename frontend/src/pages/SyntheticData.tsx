import { useState, useEffect } from 'react'
import { Database, Download, Sparkles } from 'lucide-react'
import { generateSyntheticData, listDatasets, getDataset } from '../api/client'

export default function SyntheticData() {
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [numRows, setNumRows] = useState<number>(1000)
  const [syntheticResult, setSyntheticResult] = useState<any>(null)
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

  const handleGenerate = async () => {
    if (!selectedDataset) return

    setLoading(true)
    try {
      const result = await generateSyntheticData(selectedDataset, numRows)
      setSyntheticResult(result)
    } catch (error: any) {
      console.error('Failed to generate synthetic data:', error)
      alert(error.response?.data?.detail || 'Failed to generate synthetic data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">Synthetic Data Generation</h1>
        <p className="mt-2 text-dark-muted">
          Generate synthetic data that preserves statistical properties of your original dataset
        </p>
      </div>

      {/* Controls */}
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-text mb-2">
              Select Source Dataset
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

          <div>
            <label className="block text-sm font-medium text-dark-text mb-2">
              Number of Rows to Generate
            </label>
            <input
              type="number"
              value={numRows}
              onChange={(e) => setNumRows(parseInt(e.target.value) || 1000)}
              min={100}
              max={10000}
              step={100}
              className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-sm text-dark-muted">
              Generate between 100 and 10,000 rows
            </p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!selectedDataset || loading}
            className="bg-gradient-to-r from-bright-blue to-bright-purple text-white px-6 py-2 rounded-lg hover:from-accent-blue/90 hover:to-accent-purple/90 disabled:opacity-50 flex items-center space-x-2"
          >
            {loading ? (
              <>
                <Sparkles className="h-5 w-5 animate-pulse" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Database className="h-5 w-5" />
                <span>Generate Synthetic Data</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {syntheticResult && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Sparkles className="h-6 w-6 text-purple-500" />
              <h2 className="text-xl font-bold text-dark-text">Synthetic Dataset Generated</h2>
            </div>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-dark-muted">Dataset ID</p>
                <p className="text-lg font-semibold text-dark-text">
                  {syntheticResult.synthetic_dataset_id.slice(0, 8)}...
                </p>
              </div>
              <div>
                <p className="text-sm text-dark-muted">Rows Generated</p>
                <p className="text-2xl font-bold text-green-600">
                  {syntheticResult.num_rows.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-dark-muted">Columns</p>
                <p className="text-2xl font-bold text-accent-blue">
                  {syntheticResult.columns.length}
                </p>
              </div>
            </div>
          </div>

          {/* Preview */}
          <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-dark-text">Data Preview</h2>
              <span className="text-sm text-dark-muted">First 50 rows</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-dark-border">
                <thead className="bg-dark-surface">
                  <tr>
                    {syntheticResult.columns.map((col: string) => (
                      <th
                        key={col}
                        className="px-4 py-3 text-left text-xs font-medium text-dark-muted uppercase"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-dark-card divide-y divide-dark-border">
                  {syntheticResult.preview.map((row: any, idx: number) => (
                    <tr key={idx} className="hover:bg-dark-surface">
                      {syntheticResult.columns.map((col: string) => (
                        <td key={col} className="px-4 py-3 text-sm text-dark-text">
                          {row[col] !== null && row[col] !== undefined
                            ? typeof row[col] === 'number'
                              ? row[col].toFixed(2)
                              : String(row[col])
                            : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Information */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-2 flex items-center">
              <Sparkles className="h-5 w-5 mr-2" />
              About Synthetic Data
            </h3>
            <div className="mt-2 space-y-2 text-sm text-blue-800">
              <p>
                • The synthetic data preserves statistical properties, distributions, and
                correlations from your original dataset
              </p>
              <p>
                • No real data is included - completely synthetic and privacy-safe
              </p>
              <p>
                • Use for testing, development, or sharing without privacy concerns
              </p>
              <p>
                • The synthetic dataset is saved and can be used for further analysis or modeling
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

