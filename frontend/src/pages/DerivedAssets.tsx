import { useState, useEffect } from 'react';
import Toast from '../components/Toast';

interface DerivedAsset {
  id: string;
  source_run_id: string;
  name: string | null;
  asset_type: 'temporal' | 'permanent';
  storage_uri: string;
  manifest_uri: string;
  ttl_expires_at: string | null;
  metrics_json: Record<string, number>;
  tags: string[];
  approval_state: string;
  notes: string | null;
  created_at: string;
  created_by: string | null;
  promoted_at: string | null;
  promoted_by: string | null;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function DerivedAssets() {
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);
  const [assets, setAssets] = useState<DerivedAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'temporal' | 'permanent'>('all');

  useEffect(() => {
    fetchAssets();
  }, []);

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/v1/ml-development/assets`);
      if (!response.ok) throw new Error('Failed to fetch assets');
      const data = await response.json();
      setAssets(data.assets || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handlePromote = async (assetId: string) => {
    if (!confirm('Promote this asset to permanent? This will remove the TTL expiration.')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/ml-development/assets/${assetId}/promote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to promote asset');
      setToast({ message: 'Asset promoted to permanent!', type: 'success' });
      fetchAssets();
    } catch (err) {
      setToast({ message: err instanceof Error ? err.message : 'Failed to promote', type: 'error' });
    }
  };

  const handleDelete = async (assetId: string) => {
    if (!confirm('Delete this asset? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/ml-development/assets/${assetId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete asset');
      setToast({ message: 'Asset deleted', type: 'success' });
      fetchAssets();
    } catch (err) {
      setToast({ message: err instanceof Error ? err.message : 'Failed to delete', type: 'error' });
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTimeRemaining = (expiresAt: string | null) => {
    if (!expiresAt) return null;
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expired';
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (days > 0) return `${days}d ${hours}h remaining`;
    return `${hours}h remaining`;
  };

  const filteredAssets = assets.filter(asset => {
    if (filter === 'all') return true;
    return asset.asset_type === filter;
  });

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
        <button onClick={fetchAssets} className="mt-2 text-red-600 underline">
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
          <h1 className="text-2xl font-bold text-gray-900">Derived Assets</h1>
          <p className="text-gray-600 mt-1">
            Banked results from ML runs - promote temporal assets to preserve them
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as typeof filter)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md"
          >
            <option value="all">All Assets</option>
            <option value="temporal">Temporal</option>
            <option value="permanent">Permanent</option>
          </select>
          <button
            onClick={fetchAssets}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Assets</p>
          <p className="text-2xl font-bold text-gray-900">{assets.length}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Temporal</p>
          <p className="text-2xl font-bold text-yellow-600">
            {assets.filter(a => a.asset_type === 'temporal').length}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Permanent</p>
          <p className="text-2xl font-bold text-green-600">
            {assets.filter(a => a.asset_type === 'permanent').length}
          </p>
        </div>
      </div>

      {/* Asset Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Asset
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Metrics
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Expires
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAssets.map((asset) => (
              <tr key={asset.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {asset.name || `Asset ${asset.id.slice(0, 8)}`}
                    </p>
                    <p className="text-xs text-gray-500">
                      Run: {asset.source_run_id.slice(0, 12)}...
                    </p>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    asset.asset_type === 'permanent' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {asset.asset_type}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(asset.metrics_json || {}).slice(0, 3).map(([key, value]) => (
                      <span key={key} className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                        {key}: {typeof value === 'number' ? value.toFixed(3) : value}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {asset.asset_type === 'temporal' && asset.ttl_expires_at ? (
                    <span className={`text-sm ${
                      new Date(asset.ttl_expires_at) < new Date() 
                        ? 'text-red-600' 
                        : 'text-yellow-600'
                    }`}>
                      {getTimeRemaining(asset.ttl_expires_at)}
                    </span>
                  ) : (
                    <span className="text-sm text-green-600">Never</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(asset.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end gap-2">
                    {asset.asset_type === 'temporal' && (
                      <button
                        onClick={() => handlePromote(asset.id)}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        Promote
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(asset.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredAssets.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No assets found</p>
            <p className="text-sm text-gray-400 mt-1">
              Assets are automatically created when ML runs complete successfully
            </p>
          </div>
        )}
      </div>

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
