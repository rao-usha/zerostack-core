import { useState, useEffect } from 'react';
import {
  ChevronUp,
  ChevronDown,
  RefreshCw,
  Search,
  Filter,
  Clock,
  User,
  History
} from 'lucide-react';
import Toast from '../components/Toast';
import ModelPromotionDialog from '../components/ModelPromotionDialog';

interface MLModel {
  id: string;
  name: string;
  model_family: string;
  recipe_id: string;
  recipe_version_id: string;
  status: string;
  owner: string | null;
  created_at: string;
  updated_at: string;
}

interface PromotionRecord {
  id: string;
  model_id: string;
  from_status: string;
  to_status: string;
  promoted_by: string | null;
  promotion_notes: string | null;
  promoted_at: string;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

const STATUS_COLUMNS = ['draft', 'staging', 'production', 'retired'];

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  draft: { bg: 'bg-gray-800', border: 'border-gray-600', text: 'text-gray-300' },
  staging: { bg: 'bg-yellow-900/30', border: 'border-yellow-600', text: 'text-yellow-400' },
  production: { bg: 'bg-green-900/30', border: 'border-green-600', text: 'text-green-400' },
  retired: { bg: 'bg-red-900/30', border: 'border-red-600', text: 'text-red-400' }
};

export default function ModelRegistry() {
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);

  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [familyFilter, setFamilyFilter] = useState<string>('all');

  // Promotion dialog
  const [promotionModel, setPromotionModel] = useState<MLModel | null>(null);
  const [promotionDirection, setPromotionDirection] = useState<'promote' | 'demote'>('promote');

  // Expanded model for history
  const [expandedModel, setExpandedModel] = useState<string | null>(null);
  const [promotionHistory, setPromotionHistory] = useState<PromotionRecord[]>([]);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/v1/ml-development/models?limit=500`);
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      setModels(data.models);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchPromotionHistory = async (modelId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ml-development/models/${modelId}/promotion-history`);
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      setPromotionHistory(data);
    } catch (err) {
      setToast({ message: 'Failed to fetch promotion history', type: 'error' });
    }
  };

  const handleExpandModel = async (modelId: string) => {
    if (expandedModel === modelId) {
      setExpandedModel(null);
      setPromotionHistory([]);
    } else {
      setExpandedModel(modelId);
      await fetchPromotionHistory(modelId);
    }
  };

  const handlePromotionComplete = () => {
    fetchModels();
    setPromotionModel(null);
    setToast({ message: 'Model status updated successfully', type: 'success' });
  };

  const openPromotionDialog = (model: MLModel, direction: 'promote' | 'demote') => {
    setPromotionModel(model);
    setPromotionDirection(direction);
  };

  const getNextStatus = (currentStatus: string): string | null => {
    const idx = STATUS_COLUMNS.indexOf(currentStatus);
    if (idx < STATUS_COLUMNS.length - 1) {
      return STATUS_COLUMNS[idx + 1];
    }
    return null;
  };

  const getPrevStatus = (currentStatus: string): string | null => {
    const idx = STATUS_COLUMNS.indexOf(currentStatus);
    if (idx > 0) {
      return STATUS_COLUMNS[idx - 1];
    }
    return null;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatRelativeTime = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`;
    return formatDate(dateStr);
  };

  // Filter models
  const filteredModels = models.filter(model => {
    if (searchTerm && !model.name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (familyFilter !== 'all' && model.model_family !== familyFilter) {
      return false;
    }
    return true;
  });

  // Group by status
  const modelsByStatus = STATUS_COLUMNS.reduce((acc, status) => {
    acc[status] = filteredModels.filter(m => m.status === status);
    return acc;
  }, {} as Record<string, MLModel[]>);

  // Get unique model families for filter
  const modelFamilies = [...new Set(models.map(m => m.model_family))];

  if (loading && models.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
        <p className="text-red-400">Error: {error}</p>
        <button onClick={fetchModels} className="mt-2 text-red-400 underline">
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
          <h1 className="text-2xl font-bold text-gray-100">Model Registry</h1>
          <p className="text-gray-400 mt-1">
            Manage model lifecycle from draft to production
          </p>
        </div>
        <button
          onClick={fetchModels}
          className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-surface border border-dark-border rounded-lg hover:bg-dark-border flex items-center gap-2"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search models..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-surface border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-500" />
          <select
            value={familyFilter}
            onChange={(e) => setFamilyFilter(e.target.value)}
            className="px-3 py-2 bg-dark-surface border border-dark-border rounded-lg text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All families</option>
            {modelFamilies.map(family => (
              <option key={family} value={family}>{family}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-4 gap-4">
        {STATUS_COLUMNS.map(status => (
          <div key={status} className="space-y-3">
            {/* Column Header */}
            <div className={`p-3 rounded-lg ${STATUS_COLORS[status].bg} border ${STATUS_COLORS[status].border}`}>
              <div className="flex items-center justify-between">
                <h3 className={`font-medium capitalize ${STATUS_COLORS[status].text}`}>
                  {status}
                </h3>
                <span className="text-sm text-gray-500">
                  {modelsByStatus[status].length}
                </span>
              </div>
            </div>

            {/* Model Cards */}
            <div className="space-y-2 min-h-[200px]">
              {modelsByStatus[status].map(model => (
                <div
                  key={model.id}
                  className="bg-dark-surface border border-dark-border rounded-lg overflow-hidden"
                >
                  {/* Card Header */}
                  <div
                    className="p-3 cursor-pointer hover:bg-dark-bg/50"
                    onClick={() => handleExpandModel(model.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-200 truncate">{model.name}</h4>
                        <p className="text-xs text-gray-500 mt-1">{model.model_family}</p>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {/* Promote/Demote buttons */}
                        {status !== 'retired' && getNextStatus(status) && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              openPromotionDialog(model, 'promote');
                            }}
                            className="p-1 text-green-400 hover:bg-green-900/30 rounded"
                            title={`Promote to ${getNextStatus(status)}`}
                          >
                            <ChevronUp size={16} />
                          </button>
                        )}
                        {getPrevStatus(status) && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              openPromotionDialog(model, 'demote');
                            }}
                            className="p-1 text-red-400 hover:bg-red-900/30 rounded"
                            title={`Demote to ${getPrevStatus(status)}`}
                          >
                            <ChevronDown size={16} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Card Details */}
                    <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock size={10} />
                        {formatRelativeTime(model.updated_at)}
                      </span>
                      {model.owner && (
                        <span className="flex items-center gap-1">
                          <User size={10} />
                          {model.owner}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedModel === model.id && (
                    <div className="border-t border-dark-border p-3 bg-dark-bg/50">
                      <div className="text-xs space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Recipe ID:</span>
                          <span className="text-gray-300 font-mono">{model.recipe_id.slice(0, 12)}...</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Created:</span>
                          <span className="text-gray-300">{formatDate(model.created_at)}</span>
                        </div>
                      </div>

                      {/* Promotion History */}
                      {promotionHistory.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-dark-border">
                          <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                            <History size={12} />
                            Promotion History
                          </div>
                          <div className="space-y-2 max-h-32 overflow-y-auto">
                            {promotionHistory.slice(0, 5).map(record => (
                              <div
                                key={record.id}
                                className="text-xs flex items-center gap-2"
                              >
                                <span className="text-gray-500">{formatRelativeTime(record.promoted_at)}</span>
                                <span className={STATUS_COLORS[record.from_status]?.text || 'text-gray-400'}>
                                  {record.from_status}
                                </span>
                                <span className="text-gray-500">→</span>
                                <span className={STATUS_COLORS[record.to_status]?.text || 'text-gray-400'}>
                                  {record.to_status}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {modelsByStatus[status].length === 0 && (
                <div className="text-center py-8 text-gray-500 text-sm">
                  No models
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Status Legend */}
      <div className="flex items-center gap-6 text-sm text-gray-400">
        <span className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-gray-600" />
          Draft - In development
        </span>
        <span className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-yellow-600" />
          Staging - Testing/validation
        </span>
        <span className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-600" />
          Production - Live
        </span>
        <span className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-600" />
          Retired - Deprecated
        </span>
      </div>

      {/* Promotion Dialog */}
      {promotionModel && (
        <ModelPromotionDialog
          model={promotionModel}
          direction={promotionDirection}
          onClose={() => setPromotionModel(null)}
          onSuccess={handlePromotionComplete}
        />
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
