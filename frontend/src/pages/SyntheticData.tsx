import { useState, useEffect, useCallback } from 'react'
import Toast from '../components/Toast'
import ConditionBuilder from '../components/ConditionBuilder'
import QualityDashboard from '../components/QualityDashboard'
import { Database, Sparkles, Upload, FileSpreadsheet, Settings, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react'
import {
  generateSyntheticData,
  generateConditionalSyntheticData,
  listDatasets,
  type GenerationCondition,
  type ConditionalGenerateResponse
} from '../api/client'

type SourceMode = 'dataset' | 'upload'
type SynthesizerType = 'gaussian_copula' | 'ctgan' | 'tvae'

interface ColumnInfo {
  name: string
  dtype: string
  unique_values?: any[]
}

export default function SyntheticData() {
  const [toast, setToast] = useState<{
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
  } | null>(null)

  // Source selection
  const [sourceMode, setSourceMode] = useState<SourceMode>('upload')
  const [datasets, setDatasets] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>('')

  // File upload
  const [file, setFile] = useState<File | null>(null)
  const [columns, setColumns] = useState<ColumnInfo[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)

  // Generation settings
  const [numRows, setNumRows] = useState<number>(1000)
  const [synthesizer, setSynthesizer] = useState<SynthesizerType>('gaussian_copula')
  const [conditions, setConditions] = useState<GenerationCondition[]>([])
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [oversampleFactor, setOversampleFactor] = useState<number>(2.0)
  const [maxTries, setMaxTries] = useState<number>(100)

  // Results
  const [syntheticResult, setSyntheticResult] = useState<ConditionalGenerateResponse | any>(null)
  const [loading, setLoading] = useState(false)
  const [warnings, setWarnings] = useState<string[]>([])

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

  // Parse CSV to extract column info
  const parseFileColumns = useCallback(async (file: File) => {
    return new Promise<ColumnInfo[]>((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        const lines = text.split('\n').filter(line => line.trim())
        if (lines.length < 2) {
          resolve([])
          return
        }

        const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''))
        const sampleRows = lines.slice(1, Math.min(101, lines.length))

        const columnInfo: ColumnInfo[] = headers.map((name, colIdx) => {
          const values = sampleRows.map(row => {
            const cells = row.split(',')
            return cells[colIdx]?.trim().replace(/^["']|["']$/g, '')
          }).filter(v => v !== undefined && v !== '')

          // Detect type
          let dtype = 'object'
          const numericValues = values.filter(v => !isNaN(parseFloat(v)))
          if (numericValues.length > values.length * 0.8) {
            dtype = values.some(v => v.includes('.')) ? 'float64' : 'int64'
          }

          // Get unique values for categorical columns
          let unique_values: any[] | undefined
          if (dtype === 'object') {
            const uniqueSet = new Set(values)
            if (uniqueSet.size <= 50) {
              unique_values = Array.from(uniqueSet).sort()
            }
          }

          return { name, dtype, unique_values }
        })

        resolve(columnInfo)
      }
      reader.readAsText(file.slice(0, 100000)) // Read first 100KB for analysis
    })
  }, [])

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile)
    setConditions([])
    setWarnings([])
    setSyntheticResult(null)

    // Parse columns
    const cols = await parseFileColumns(selectedFile)
    setColumns(cols)

    if (cols.length === 0) {
      setToast({ message: 'Could not parse CSV file. Please check the format.', type: 'error' })
    }
  }

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.name.endsWith('.csv') || droppedFile.type === 'text/csv')) {
      await handleFileSelect(droppedFile)
    } else {
      setToast({ message: 'Please upload a CSV file', type: 'error' })
    }
  }, [parseFileColumns])

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      await handleFileSelect(selectedFile)
    }
  }

  const handleGenerate = async () => {
    if (sourceMode === 'dataset' && !selectedDataset) {
      setToast({ message: 'Please select a dataset', type: 'error' })
      return
    }
    if (sourceMode === 'upload' && !file) {
      setToast({ message: 'Please upload a file', type: 'error' })
      return
    }

    setLoading(true)
    setWarnings([])

    try {
      let result: any

      if (sourceMode === 'upload' && file) {
        // Use conditional generation API
        result = await generateConditionalSyntheticData(
          file,
          {
            num_rows: numRows,
            synthesizer,
            conditions,
            oversample_factor: conditions.length > 0 ? oversampleFactor : undefined,
            max_tries_per_batch: conditions.length > 0 ? maxTries : undefined,
          },
          (progress) => setUploadProgress(progress)
        )

        if (result.warnings && result.warnings.length > 0) {
          setWarnings(result.warnings)
        }
      } else {
        // Use legacy dataset-based generation
        result = await generateSyntheticData(selectedDataset, numRows)
      }

      setSyntheticResult(result)
      setToast({ message: 'Synthetic data generated successfully!', type: 'success' })
    } catch (error: any) {
      console.error('Failed to generate synthetic data:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to generate synthetic data'
      setToast({ message: errorMessage, type: 'error' })
    } finally {
      setLoading(false)
      setUploadProgress(0)
    }
  }

  const hasRangeConditions = conditions.some(c =>
    ['gt', 'gte', 'lt', 'lte', 'ne', 'not_in', 'between'].includes(c.operator)
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">
          Synthetic Data Generation
        </h1>
        <p className="mt-2 text-dark-muted">
          Generate synthetic data that preserves statistical properties of your original dataset
        </p>
      </div>

      {/* Source Selection */}
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setSourceMode('upload')}
            className={`flex-1 py-3 px-4 rounded-lg border-2 transition-all ${
              sourceMode === 'upload'
                ? 'border-bright-blue bg-bright-blue/10 text-bright-blue'
                : 'border-pastel-blue/20 text-dark-muted hover:border-pastel-blue/40'
            }`}
          >
            <Upload className="h-5 w-5 mx-auto mb-2" />
            <span className="block font-medium">Upload CSV</span>
            <span className="text-xs opacity-75">With conditional generation</span>
          </button>
          <button
            onClick={() => setSourceMode('dataset')}
            className={`flex-1 py-3 px-4 rounded-lg border-2 transition-all ${
              sourceMode === 'dataset'
                ? 'border-bright-blue bg-bright-blue/10 text-bright-blue'
                : 'border-pastel-blue/20 text-dark-muted hover:border-pastel-blue/40'
            }`}
          >
            <Database className="h-5 w-5 mx-auto mb-2" />
            <span className="block font-medium">Existing Dataset</span>
            <span className="text-xs opacity-75">From your library</span>
          </button>
        </div>

        {sourceMode === 'upload' ? (
          <div className="space-y-4">
            {/* File Upload Zone */}
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                isDragging
                  ? 'border-bright-blue bg-bright-blue/10'
                  : file
                  ? 'border-green-500/50 bg-green-500/5'
                  : 'border-pastel-blue/20 hover:border-pastel-blue/40'
              }`}
            >
              {file ? (
                <div className="space-y-2">
                  <FileSpreadsheet className="h-12 w-12 mx-auto text-green-500" />
                  <p className="text-dark-text font-medium">{file.name}</p>
                  <p className="text-sm text-dark-muted">
                    {(file.size / 1024).toFixed(1)} KB · {columns.length} columns detected
                  </p>
                  <button
                    onClick={() => {
                      setFile(null)
                      setColumns([])
                      setConditions([])
                    }}
                    className="text-sm text-red-400 hover:text-red-300"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-12 w-12 mx-auto text-dark-muted" />
                  <p className="text-dark-text">Drop your CSV file here</p>
                  <p className="text-sm text-dark-muted">or</p>
                  <label className="inline-block">
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileInput}
                      className="hidden"
                    />
                    <span className="px-4 py-2 bg-bright-blue/20 text-bright-blue rounded-lg cursor-pointer hover:bg-bright-blue/30 transition-colors">
                      Browse files
                    </span>
                  </label>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-dark-text mb-2">
              Select Source Dataset
            </label>
            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a dataset...</option>
              {datasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.filename} ({dataset.rows} rows)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Condition Builder (only for upload mode) */}
      {sourceMode === 'upload' && (
        <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
          <ConditionBuilder
            columns={columns}
            conditions={conditions}
            onChange={setConditions}
          />
        </div>
      )}

      {/* Generation Settings */}
      <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-text mb-2">
                Number of Rows to Generate
              </label>
              <input
                type="number"
                value={numRows}
                onChange={(e) => setNumRows(parseInt(e.target.value) || 1000)}
                min={10}
                max={100000}
                step={100}
                className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-sm text-dark-muted">
                Generate between 10 and 100,000 rows
              </p>
            </div>

            {sourceMode === 'upload' && (
              <div>
                <label className="block text-sm font-medium text-dark-text mb-2">
                  Synthesizer Algorithm
                </label>
                <select
                  value={synthesizer}
                  onChange={(e) => setSynthesizer(e.target.value as SynthesizerType)}
                  className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text focus:ring-2 focus:ring-blue-500"
                >
                  <option value="gaussian_copula">Gaussian Copula (Recommended)</option>
                  <option value="ctgan">CTGAN (Deep Learning)</option>
                  <option value="tvae">TVAE (Variational Autoencoder)</option>
                </select>
                <p className="mt-1 text-sm text-dark-muted">
                  {synthesizer === 'gaussian_copula' && 'Fast and efficient for most use cases'}
                  {synthesizer === 'ctgan' && 'Better for complex distributions, slower'}
                  {synthesizer === 'tvae' && 'Good for mixed data types, moderate speed'}
                </p>
              </div>
            )}
          </div>

          {/* Advanced Options */}
          {sourceMode === 'upload' && conditions.length > 0 && (
            <div>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-sm text-dark-muted hover:text-dark-text transition-colors"
              >
                <Settings className="h-4 w-4" />
                Advanced Options
                {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>

              {showAdvanced && (
                <div className="mt-4 p-4 bg-dark-surface rounded-lg border border-pastel-blue/10 space-y-4">
                  {hasRangeConditions && (
                    <div>
                      <label className="block text-sm font-medium text-dark-text mb-2">
                        Oversample Factor
                      </label>
                      <input
                        type="number"
                        value={oversampleFactor}
                        onChange={(e) => setOversampleFactor(parseFloat(e.target.value) || 2.0)}
                        min={1.0}
                        max={10.0}
                        step={0.5}
                        className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg bg-dark-card text-dark-text focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="mt-1 text-sm text-dark-muted">
                        Generate extra rows before filtering (for range conditions)
                      </p>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-dark-text mb-2">
                      Max Tries Per Batch
                    </label>
                    <input
                      type="number"
                      value={maxTries}
                      onChange={(e) => setMaxTries(parseInt(e.target.value) || 100)}
                      min={10}
                      max={1000}
                      step={10}
                      className="w-full px-4 py-2 border border-pastel-blue/20 rounded-lg bg-dark-card text-dark-text focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="mt-1 text-sm text-dark-muted">
                      Maximum attempts to generate matching rows
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={(sourceMode === 'dataset' && !selectedDataset) || (sourceMode === 'upload' && !file) || loading}
            className="w-full bg-gradient-to-r from-bright-blue to-bright-purple text-white px-6 py-3 rounded-lg hover:from-accent-blue/90 hover:to-accent-purple/90 disabled:opacity-50 flex items-center justify-center space-x-2 transition-all"
          >
            {loading ? (
              <>
                <Sparkles className="h-5 w-5 animate-pulse" />
                <span>
                  {uploadProgress > 0 && uploadProgress < 100
                    ? `Uploading ${uploadProgress}%...`
                    : 'Generating...'}
                </span>
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                <span>
                  Generate Synthetic Data
                  {conditions.length > 0 && ` (${conditions.length} condition${conditions.length > 1 ? 's' : ''})`}
                </span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-yellow-500">Warnings</h3>
              <ul className="mt-1 text-sm text-yellow-400 space-y-1">
                {warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

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
                <p className="text-sm text-dark-muted">
                  {syntheticResult.job_id ? 'Job ID' : 'Dataset ID'}
                </p>
                <p className="text-lg font-semibold text-dark-text">
                  {(syntheticResult.job_id || syntheticResult.synthetic_dataset_id)?.slice(0, 8)}...
                </p>
              </div>
              <div>
                <p className="text-sm text-dark-muted">Rows Generated</p>
                <p className="text-2xl font-bold text-green-600">
                  {(syntheticResult.num_rows || 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-dark-muted">Columns</p>
                <p className="text-2xl font-bold text-accent-blue">
                  {syntheticResult.columns?.length || 0}
                </p>
              </div>
            </div>
          </div>

          {/* Preview */}
          {syntheticResult.preview && syntheticResult.preview.length > 0 && (
            <div className="bg-dark-card rounded-xl shadow-2xl border border-pastel-blue/20 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-dark-text">Data Preview</h2>
                <span className="text-sm text-dark-muted">
                  First {Math.min(50, syntheticResult.preview.length)} rows
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-dark-border">
                  <thead className="bg-dark-surface">
                    <tr>
                      {syntheticResult.columns?.map((col: any) => {
                        const colName = typeof col === 'string' ? col : col.name
                        return (
                          <th
                            key={colName}
                            className="px-4 py-3 text-left text-xs font-medium text-dark-muted uppercase"
                          >
                            {colName}
                          </th>
                        )
                      })}
                    </tr>
                  </thead>
                  <tbody className="bg-dark-card divide-y divide-dark-border">
                    {syntheticResult.preview.slice(0, 50).map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-dark-surface">
                        {syntheticResult.columns?.map((col: any) => {
                          const colName = typeof col === 'string' ? col : col.name
                          return (
                            <td key={colName} className="px-4 py-3 text-sm text-dark-text">
                              {row[colName] !== null && row[colName] !== undefined
                                ? typeof row[colName] === 'number'
                                  ? Number.isInteger(row[colName])
                                    ? row[colName]
                                    : row[colName].toFixed(2)
                                  : String(row[colName])
                                : '-'}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Quality Dashboard */}
          {syntheticResult.synthetic_dataset_id && (
            <QualityDashboard
              datasetId={syntheticResult.synthetic_dataset_id}
              initialQualityScore={syntheticResult.quality_score}
            />
          )}

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
              {conditions.length > 0 && (
                <p>
                  • Generated data matches your specified conditions ({conditions.length} applied)
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
