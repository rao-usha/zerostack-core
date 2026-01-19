import { useState, useEffect } from 'react';
import Toast from '../components/Toast';

interface DatasetVersion {
  id: string;
  highlighted_dataset_id: string;
  version_label: string;
  manifest_uri: string;
  storage_uri: string;
  file_count: number | null;
  total_bytes: number | null;
  created_at: string;
}

interface HighlightedDataset {
  id: string;
  display_name: string;
  description: string | null;
  tags: string[];
  source_type: string;
  availability_state: string;
  license_notes: string | null;
  created_at: string;
  updated_at: string;
  latest_version: DatasetVersion | null;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function HighlightedDatasets() {
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);
  const [datasets, setDatasets] = useState<HighlightedDataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/v1/highlighted-datasets`);
      if (!response.ok) throw new Error('Failed to fetch datasets');
      const data = await response.json();
      setDatasets(data.datasets);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (datasetId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/highlighted-datasets/${datasetId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_refresh: false })
      });
      const data = await response.json();
      setToast({ message: data.message, type: 'success' });
      fetchDatasets();
    } catch (err) {
      setToast({ message: 'Failed to resolve dataset', type: 'error' });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async (datasetId: string) => {
    if (uploadFiles.length === 0) {
      setToast({ message: 'Please select files to upload', type: 'warning' });
      return;
    }

    setUploading(true);
    try {
      // Upload each file
      for (let i = 0; i < uploadFiles.length; i++) {
        const file = uploadFiles[i];
        setUploadProgress(`Uploading ${file.name} (${i + 1}/${uploadFiles.length})...`);
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(
          `${API_BASE}/api/v1/highlighted-datasets/${datasetId}/upload?version_label=v1`,
          { method: 'POST', body: formData }
        );
        
        if (!response.ok) throw new Error(`Failed to upload ${file.name}`);
      }

      // Complete the upload
      setUploadProgress('Finalizing upload...');
      const completeResponse = await fetch(
        `${API_BASE}/api/v1/highlighted-datasets/${datasetId}/upload/complete`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ version_label: 'v1' })
        }
      );

      if (!completeResponse.ok) throw new Error('Failed to complete upload');
      
      const result = await completeResponse.json();
      setToast({ message: result.message, type: 'success' });
      setUploadFiles([]);
      setSelectedDataset(null);
      fetchDatasets();
    } catch (err) {
      setToast({ message: err instanceof Error ? err.message : 'Upload failed', type: 'error' });
    } finally {
      setUploading(false);
      setUploadProgress('');
    }
  };

  const formatBytes = (bytes: number | null) => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'AVAILABLE': return 'bg-green-100 text-green-800';
      case 'NOT_PRESENT': return 'bg-yellow-100 text-yellow-800';
      case 'INGESTING': return 'bg-blue-100 text-blue-800';
      case 'ERROR': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button onClick={fetchDatasets} className="mt-2 text-red-600 underline">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Highlighted Datasets</h1>
          <p className="text-gray-600 mt-1">
            Curated datasets for ML model training and evaluation
          </p>
        </div>
        <button
          onClick={fetchDatasets}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      {/* Dataset Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {datasets.map((dataset) => (
          <div
            key={dataset.id}
            className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden"
          >
            <div className="p-5">
              <div className="flex items-start justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {dataset.display_name}
                </h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStateColor(dataset.availability_state)}`}>
                  {dataset.availability_state}
                </span>
              </div>
              
              <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                {dataset.description || 'No description'}
              </p>

              {/* Tags */}
              <div className="mt-3 flex flex-wrap gap-1">
                {dataset.tags.slice(0, 4).map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                  >
                    {tag}
                  </span>
                ))}
                {dataset.tags.length > 4 && (
                  <span className="px-2 py-0.5 text-xs text-gray-500">
                    +{dataset.tags.length - 4} more
                  </span>
                )}
              </div>

              {/* Version Info */}
              {dataset.latest_version && (
                <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
                  <div className="flex justify-between">
                    <span>Version: {dataset.latest_version.version_label}</span>
                    <span>{dataset.latest_version.file_count} files</span>
                  </div>
                  <div className="mt-1">
                    Size: {formatBytes(dataset.latest_version.total_bytes)}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="px-5 py-3 bg-gray-50 border-t border-gray-100 flex gap-2">
              {dataset.availability_state === 'AVAILABLE' ? (
                <button
                  onClick={() => handleResolve(dataset.id)}
                  className="flex-1 px-3 py-1.5 text-sm font-medium text-indigo-700 bg-indigo-50 rounded hover:bg-indigo-100"
                >
                  View Details
                </button>
              ) : dataset.availability_state === 'NOT_PRESENT' ? (
                <>
                  <button
                    onClick={() => setSelectedDataset(selectedDataset === dataset.id ? null : dataset.id)}
                    className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700"
                  >
                    Upload Data
                  </button>
                  <button
                    onClick={() => handleResolve(dataset.id)}
                    className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                  >
                    Resolve
                  </button>
                </>
              ) : (
                <span className="text-sm text-gray-500">
                  {dataset.availability_state === 'INGESTING' ? 'Processing...' : 'Check status'}
                </span>
              )}
            </div>

            {/* Upload Panel */}
            {selectedDataset === dataset.id && (
              <div className="px-5 py-4 bg-indigo-50 border-t border-indigo-100">
                <p className="text-sm text-indigo-800 mb-3">
                  Upload CSV files for this dataset:
                </p>
                <input
                  type="file"
                  multiple
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-indigo-100 file:text-indigo-700 hover:file:bg-indigo-200"
                />
                {uploadFiles.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-gray-600 mb-2">
                      Selected: {uploadFiles.map(f => f.name).join(', ')}
                    </p>
                    <button
                      onClick={() => handleUpload(dataset.id)}
                      disabled={uploading}
                      className="w-full px-3 py-2 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {uploading ? uploadProgress : 'Upload Files'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {datasets.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No highlighted datasets found.</p>
          <p className="text-sm text-gray-400 mt-1">
            Run the seed script to create sample datasets.
          </p>
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
  );
}
