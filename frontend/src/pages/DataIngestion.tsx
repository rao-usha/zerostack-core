import { useState, useEffect, useCallback } from 'react';
import {
  Upload,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Trash2,
  Eye,
  Building2,
  Plus,
  Filter,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface IngestedFile {
  id: string;
  deal_id: string | null;
  deal_name: string | null;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  upload_source: string;
  quality_score: number | null;
  row_count: number | null;
  column_count: number | null;
  sheet_count: number;
  detected_categories: string[];
  status: string;
  issue_count: number;
  uploaded_by: string | null;
  uploaded_at: string;
  analyzed_at: string | null;
}

interface Deal {
  id: string;
  name: string;
  target_company: string;
  status: string;
  file_count: number;
  issue_count: number;
  avg_quality_score: number | null;
  created_at: string;
}

interface IssueSummary {
  total: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  unacknowledged: number;
  critical_count: number;
}

export default function DataIngestion() {
  const [files, setFiles] = useState<IngestedFile[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [issueSummary, setIssueSummary] = useState<IssueSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedDeal, setSelectedDeal] = useState<string | null>(null);
  const [expandedFile, setExpandedFile] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // New deal form
  const [showNewDeal, setShowNewDeal] = useState(false);
  const [newDealName, setNewDealName] = useState('');
  const [newDealCompany, setNewDealCompany] = useState('');

  useEffect(() => {
    fetchData();
  }, [selectedDeal]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [filesRes, dealsRes, issuesRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/ingest/files${selectedDeal ? `?deal_id=${selectedDeal}` : ''}`),
        fetch(`${API_BASE}/api/v1/ingest/deals`),
        fetch(`${API_BASE}/api/v1/ingest/issues/summary${selectedDeal ? `?deal_id=${selectedDeal}` : ''}`),
      ]);

      if (filesRes.ok) setFiles(await filesRes.json());
      if (dealsRes.ok) setDeals(await dealsRes.json());
      if (issuesRes.ok) setIssueSummary(await issuesRes.json());
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    await uploadFiles(droppedFiles);
  }, [selectedDeal]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      await uploadFiles(selectedFiles);
    }
  };

  const uploadFiles = async (filesToUpload: File[]) => {
    setUploading(true);
    setError(null);

    for (let i = 0; i < filesToUpload.length; i++) {
      const file = filesToUpload[i];
      setUploadProgress(`Uploading ${file.name} (${i + 1}/${filesToUpload.length})...`);

      const formData = new FormData();
      formData.append('file', file);
      if (selectedDeal) {
        formData.append('deal_id', selectedDeal);
      }

      try {
        const response = await fetch(`${API_BASE}/api/v1/ingest/upload/persist`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Upload failed');
        }
      } catch (err) {
        setError(`Failed to upload ${file.name}: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    }

    setUploading(false);
    setUploadProgress(null);
    fetchData();
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!confirm('Delete this file and all associated issues?')) return;

    try {
      await fetch(`${API_BASE}/api/v1/ingest/files/${fileId}`, { method: 'DELETE' });
      fetchData();
    } catch (err) {
      setError('Failed to delete file');
    }
  };

  const handleCreateDeal = async () => {
    if (!newDealName || !newDealCompany) return;

    try {
      const response = await fetch(`${API_BASE}/api/v1/ingest/deals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newDealName,
          target_company: newDealCompany,
        }),
      });

      if (response.ok) {
        setShowNewDeal(false);
        setNewDealName('');
        setNewDealCompany('');
        fetchData();
      }
    } catch (err) {
      setError('Failed to create deal');
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getQualityColor = (score: number | null) => {
    if (score === null) return 'text-gray-400';
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} className="text-green-400" />;
      case 'failed':
        return <XCircle size={16} className="text-red-400" />;
      default:
        return <RefreshCw size={16} className="text-blue-400 animate-spin" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Data Ingestion</h1>
          <p className="text-gray-400 mt-1">
            Upload and analyze data files for PE due diligence
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowNewDeal(true)}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-surface border border-dark-border rounded-lg hover:bg-dark-border flex items-center gap-2"
          >
            <Plus size={16} />
            New Deal
          </button>
          <button
            onClick={fetchData}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-surface border border-dark-border rounded-lg hover:bg-dark-border flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-sm text-gray-400">Total Files</div>
          <div className="text-2xl font-bold text-gray-100 mt-1">{files.length}</div>
        </div>
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-sm text-gray-400">Active Deals</div>
          <div className="text-2xl font-bold text-gray-100 mt-1">
            {deals.filter(d => d.status === 'active').length}
          </div>
        </div>
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-sm text-gray-400">Open Issues</div>
          <div className="text-2xl font-bold text-yellow-400 mt-1">
            {issueSummary?.unacknowledged || 0}
          </div>
        </div>
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-sm text-gray-400">Critical Issues</div>
          <div className="text-2xl font-bold text-red-400 mt-1">
            {issueSummary?.critical_count || 0}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6">
        {/* Deals Sidebar */}
        <div className="col-span-1 space-y-4">
          <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
            <h3 className="font-medium text-gray-200 mb-3 flex items-center gap-2">
              <Building2 size={16} />
              Deals
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => setSelectedDeal(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                  selectedDeal === null
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-300 hover:bg-dark-border'
                }`}
              >
                All Files
              </button>
              {deals.map(deal => (
                <button
                  key={deal.id}
                  onClick={() => setSelectedDeal(deal.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                    selectedDeal === deal.id
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-300 hover:bg-dark-border'
                  }`}
                >
                  <div className="font-medium">{deal.name}</div>
                  <div className="text-xs opacity-70">
                    {deal.file_count} files • {deal.issue_count} issues
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Issue Summary */}
          {issueSummary && issueSummary.total > 0 && (
            <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
              <h3 className="font-medium text-gray-200 mb-3 flex items-center gap-2">
                <AlertTriangle size={16} />
                Issues by Severity
              </h3>
              <div className="space-y-2">
                {Object.entries(issueSummary.by_severity).map(([severity, count]) => (
                  <div key={severity} className="flex items-center justify-between text-sm">
                    <span className={`capitalize ${
                      severity === 'critical' ? 'text-red-400' :
                      severity === 'high' ? 'text-orange-400' :
                      severity === 'medium' ? 'text-yellow-400' :
                      'text-gray-400'
                    }`}>
                      {severity}
                    </span>
                    <span className="text-gray-300">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="col-span-3 space-y-4">
          {/* Upload Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragOver
                ? 'border-indigo-500 bg-indigo-900/20'
                : 'border-dark-border hover:border-gray-600'
            }`}
          >
            {uploading ? (
              <div className="text-gray-300">
                <RefreshCw size={32} className="mx-auto mb-3 animate-spin text-indigo-400" />
                <p>{uploadProgress}</p>
              </div>
            ) : (
              <>
                <Upload size={32} className="mx-auto mb-3 text-gray-500" />
                <p className="text-gray-300 mb-2">
                  Drag and drop CSV or Excel files here
                </p>
                <p className="text-sm text-gray-500 mb-4">
                  or click to browse
                </p>
                <label className="px-4 py-2 bg-indigo-600 text-white rounded-lg cursor-pointer hover:bg-indigo-700">
                  Select Files
                  <input
                    type="file"
                    multiple
                    accept=".csv,.xlsx,.xls,.tsv"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </label>
              </>
            )}
          </div>

          {error && (
            <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 text-red-400">
              {error}
            </div>
          )}

          {/* Files List */}
          <div className="bg-dark-surface border border-dark-border rounded-lg">
            <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
              <h3 className="font-medium text-gray-200 flex items-center gap-2">
                <FileSpreadsheet size={16} />
                Uploaded Files
              </h3>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Filter size={14} />
                {files.length} files
              </div>
            </div>

            {loading ? (
              <div className="p-8 text-center text-gray-500">
                <RefreshCw size={24} className="mx-auto mb-2 animate-spin" />
                Loading...
              </div>
            ) : files.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No files uploaded yet. Drag and drop to get started.
              </div>
            ) : (
              <div className="divide-y divide-dark-border">
                {files.map(file => (
                  <div key={file.id}>
                    <div
                      className="px-4 py-3 hover:bg-dark-bg/50 cursor-pointer"
                      onClick={() => setExpandedFile(expandedFile === file.id ? null : file.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {expandedFile === file.id ? (
                            <ChevronDown size={16} className="text-gray-500" />
                          ) : (
                            <ChevronRight size={16} className="text-gray-500" />
                          )}
                          {getStatusIcon(file.status)}
                          <div>
                            <div className="font-medium text-gray-200">{file.filename}</div>
                            <div className="text-xs text-gray-500">
                              {formatBytes(file.file_size_bytes)} •{' '}
                              {file.row_count?.toLocaleString() || '?'} rows •{' '}
                              {file.column_count || '?'} columns
                              {file.deal_name && (
                                <span className="ml-2 text-indigo-400">• {file.deal_name}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          {file.detected_categories.length > 0 && (
                            <div className="flex gap-1">
                              {file.detected_categories.slice(0, 3).map(cat => (
                                <span
                                  key={cat}
                                  className="px-2 py-0.5 text-xs bg-dark-border rounded text-gray-300"
                                >
                                  {cat}
                                </span>
                              ))}
                            </div>
                          )}
                          <div className={`text-sm font-medium ${getQualityColor(file.quality_score)}`}>
                            {file.quality_score !== null ? `${file.quality_score.toFixed(0)}%` : '-'}
                          </div>
                          {file.issue_count > 0 && (
                            <span className="px-2 py-0.5 text-xs bg-yellow-900/30 text-yellow-400 rounded">
                              {file.issue_count} issues
                            </span>
                          )}
                          <span className="text-xs text-gray-500">
                            {formatDate(file.uploaded_at)}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteFile(file.id);
                            }}
                            className="p-1 text-gray-500 hover:text-red-400 rounded"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {expandedFile === file.id && (
                      <div className="px-4 py-3 bg-dark-bg/50 border-t border-dark-border">
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">File Type:</span>
                            <span className="ml-2 text-gray-300">{file.file_type}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Sheets:</span>
                            <span className="ml-2 text-gray-300">{file.sheet_count}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Source:</span>
                            <span className="ml-2 text-gray-300 capitalize">{file.upload_source}</span>
                          </div>
                        </div>
                        {file.detected_categories.length > 0 && (
                          <div className="mt-3">
                            <span className="text-gray-500 text-sm">Detected Categories:</span>
                            <div className="flex gap-2 mt-1">
                              {file.detected_categories.map(cat => (
                                <span
                                  key={cat}
                                  className="px-2 py-1 text-xs bg-indigo-900/30 text-indigo-300 rounded"
                                >
                                  {cat}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        <div className="mt-3 flex gap-2">
                          <a
                            href={`${API_BASE}/api/v1/ingest/files/${file.id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1 text-xs bg-dark-border text-gray-300 rounded hover:bg-gray-700 flex items-center gap-1"
                          >
                            <Eye size={12} />
                            View Details
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Deal Modal */}
      {showNewDeal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-200 mb-4">Create New Deal</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Deal Name</label>
                <input
                  type="text"
                  value={newDealName}
                  onChange={(e) => setNewDealName(e.target.value)}
                  placeholder="e.g., Project Alpha"
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Target Company</label>
                <input
                  type="text"
                  value={newDealCompany}
                  onChange={(e) => setNewDealCompany(e.target.value)}
                  placeholder="e.g., Acme Corp"
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-gray-200"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowNewDeal(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateDeal}
                disabled={!newDealName || !newDealCompany}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                Create Deal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
