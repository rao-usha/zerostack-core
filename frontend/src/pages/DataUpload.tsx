import { useState } from 'react'
import { Upload, FileText, CheckCircle2 } from 'lucide-react'
import { uploadDataset, listDatasets } from '../api/client'
import { useNavigate } from 'react-router-dom'

export default function DataUpload() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
      setUploadResult(null)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    setUploading(true)
    setError(null)

    try {
      const result = await uploadDataset(file)
      setUploadResult(result)
      
      // Reload datasets after successful upload
      await listDatasets()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-bright-blue to-bright-purple bg-clip-text text-transparent">Upload Data</h1>
        <p className="mt-2 text-dark-muted">Upload your dataset to get started with analysis</p>
      </div>

      <div className="bg-dark-card rounded-xl shadow-2xl p-8 border border-pastel-blue/20">
        <div className="max-w-2xl mx-auto">
          {/* Upload Area */}
          <div className="border-2 border-dashed border-dark-border rounded-xl p-12 text-center hover:border-pastel-purple transition-all duration-300 bg-dark-surface/50">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".csv"
              onChange={handleFileChange}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              {file ? (
                <div className="space-y-4">
                  <CheckCircle2 className="mx-auto h-12 w-12 text-green-500" />
                  <div>
                    <p className="text-lg font-medium text-dark-text">{file.name}</p>
                    <p className="text-sm text-dark-muted">{(file.size / 1024).toFixed(2)} KB</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="mx-auto h-12 w-12 text-accent-blue" />
                  <div>
                    <p className="text-lg font-medium text-dark-text">
                      Drop your CSV file here or click to browse
                    </p>
                    <p className="text-sm text-dark-muted">Supports CSV files only</p>
                  </div>
                </div>
              )}
            </label>
          </div>

          {file && (
            <div className="mt-6 flex justify-center">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="bg-gradient-to-r from-bright-blue to-bright-purple text-white px-8 py-3 rounded-lg font-medium hover:from-accent-blue/90 hover:to-accent-purple/90 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg transition-all duration-300"
              >
                {uploading ? 'Uploading...' : 'Upload Dataset'}
              </button>
            </div>
          )}

          {error && (
            <div className="mt-4 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {uploadResult && (
            <div className="mt-6 bg-green-500/10 border border-green-500/50 rounded-xl p-6">
              <div className="flex items-start space-x-3">
                <CheckCircle2 className="h-6 w-6 text-green-400 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-green-400">Upload Successful!</h3>
                  <div className="mt-2 space-y-1 text-sm text-dark-text">
                    <p><strong>Dataset ID:</strong> {uploadResult.dataset_id}</p>
                    <p><strong>Rows:</strong> {uploadResult.rows}</p>
                    <p><strong>Columns:</strong> {uploadResult.columns}</p>
                    <p><strong>Columns:</strong> {uploadResult.columns_list.join(', ')}</p>
                  </div>
                  <button
                    onClick={() => navigate('/insights', { state: { datasetId: uploadResult.dataset_id } })}
                    className="mt-4 bg-gradient-to-r from-green-500 to-accent-cyan text-white px-4 py-2 rounded-lg hover:from-green-600 hover:to-accent-cyan/90 shadow-lg transition-all duration-300"
                  >
                    View Insights
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-accent-blue/10 border border-accent-blue/30 rounded-xl p-6">
        <h3 className="font-semibold text-accent-blue mb-2 flex items-center">
          <FileText className="h-5 w-5 mr-2" />
          Upload Guidelines
        </h3>
        <ul className="mt-2 space-y-1 text-sm text-dark-text list-disc list-inside">
          <li>CSV files should have headers in the first row</li>
          <li>Ensure data is clean and properly formatted</li>
          <li>Large datasets may take longer to process</li>
          <li>Your data is processed securely and privately</li>
        </ul>
      </div>
    </div>
  )
}

