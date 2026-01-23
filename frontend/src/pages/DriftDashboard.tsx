import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Activity,
  CheckCircle,
  XCircle,
  Bell,
  BellOff,
  RefreshCw,
  Plus,
  Trash2,
  Eye,
  Filter
} from 'lucide-react';
import Toast from '../components/Toast';

interface DriftCheck {
  id: string;
  name: string;
  description: string | null;
  metric: string;
  threshold: number;
  comparison: string;
  recipe_id: string | null;
  asset_id: string | null;
  baseline_value: number | null;
  latest_value: number | null;
  is_breached: boolean;
  is_active: boolean;
  check_frequency: string;
  last_checked_at: string | null;
  created_at: string;
}

interface DriftAlert {
  id: string;
  drift_check_id: string;
  run_id: string | null;
  severity: string;
  baseline_value: number | null;
  current_value: number | null;
  change_percent: number | null;
  message: string | null;
  acknowledged: boolean;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  triggered_at: string;
}

interface DriftSummary {
  total_checks: number;
  active_checks: number;
  breached_checks: number;
  total_alerts: number;
  unacknowledged_alerts: number;
  critical_alerts: number;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function DriftDashboard() {
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);

  const [summary, setSummary] = useState<DriftSummary | null>(null);
  const [checks, setChecks] = useState<DriftCheck[]>([]);
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [showActiveOnly, setShowActiveOnly] = useState(false);
  const [showBreachedOnly, setShowBreachedOnly] = useState(false);
  const [showUnacknowledgedOnly, setShowUnacknowledgedOnly] = useState(true);

  // Create check modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCheck, setNewCheck] = useState({
    name: '',
    metric: '',
    threshold: 0.1,
    comparison: 'percentage_both',
    description: '',
    check_frequency: 'on_run'
  });

  useEffect(() => {
    fetchAll();
  }, [showActiveOnly, showBreachedOnly, showUnacknowledgedOnly]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      await Promise.all([fetchSummary(), fetchChecks(), fetchAlerts()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    const response = await fetch(`${API_BASE}/api/v1/drift/summary`);
    if (!response.ok) throw new Error('Failed to fetch summary');
    const data = await response.json();
    setSummary(data);
  };

  const fetchChecks = async () => {
    const params = new URLSearchParams();
    if (showActiveOnly) params.append('is_active', 'true');
    if (showBreachedOnly) params.append('is_breached', 'true');

    const response = await fetch(`${API_BASE}/api/v1/drift/checks?${params}`);
    if (!response.ok) throw new Error('Failed to fetch checks');
    const data = await response.json();
    setChecks(data);
  };

  const fetchAlerts = async () => {
    const params = new URLSearchParams();
    if (showUnacknowledgedOnly) params.append('unacknowledged_only', 'true');

    const response = await fetch(`${API_BASE}/api/v1/drift/alerts?${params}`);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    const data = await response.json();
    setAlerts(data);
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/drift/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to acknowledge alert');
      setToast({ message: 'Alert acknowledged', type: 'success' });
      fetchAll();
    } catch (err) {
      setToast({ message: 'Failed to acknowledge alert', type: 'error' });
    }
  };

  const acknowledgeAllAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/drift/alerts/acknowledge-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('Failed to acknowledge alerts');
      const data = await response.json();
      setToast({ message: data.message, type: 'success' });
      fetchAll();
    } catch (err) {
      setToast({ message: 'Failed to acknowledge alerts', type: 'error' });
    }
  };

  const createCheck = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/drift/checks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCheck)
      });
      if (!response.ok) throw new Error('Failed to create check');
      setToast({ message: 'Check created successfully', type: 'success' });
      setShowCreateModal(false);
      setNewCheck({
        name: '',
        metric: '',
        threshold: 0.1,
        comparison: 'percentage_both',
        description: '',
        check_frequency: 'on_run'
      });
      fetchAll();
    } catch (err) {
      setToast({ message: 'Failed to create check', type: 'error' });
    }
  };

  const deleteCheck = async (checkId: string) => {
    if (!confirm('Are you sure you want to delete this check?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/v1/drift/checks/${checkId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete check');
      setToast({ message: 'Check deleted', type: 'success' });
      fetchAll();
    } catch (err) {
      setToast({ message: 'Failed to delete check', type: 'error' });
    }
  };

  const toggleCheckActive = async (check: DriftCheck) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/drift/checks/${check.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !check.is_active })
      });
      if (!response.ok) throw new Error('Failed to update check');
      setToast({
        message: `Check ${check.is_active ? 'disabled' : 'enabled'}`,
        type: 'success'
      });
      fetchAll();
    } catch (err) {
      setToast({ message: 'Failed to update check', type: 'error' });
    }
  };

  const formatValue = (value: number | null) => {
    if (value === null) return 'N/A';
    return value.toFixed(4);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading && !summary) {
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
        <button onClick={fetchAll} className="mt-2 text-red-400 underline">
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
          <h1 className="text-2xl font-bold text-gray-100">Drift Detection</h1>
          <p className="text-gray-400 mt-1">
            Monitor metrics and detect distribution drift in your ML models
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchAll}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-surface border border-dark-border rounded-lg hover:bg-dark-border flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 flex items-center gap-2"
          >
            <Plus size={16} />
            New Check
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Active Checks</p>
                <p className="text-2xl font-bold text-gray-100 mt-1">
                  {summary.active_checks}
                </p>
              </div>
              <div className="p-3 bg-indigo-900/30 rounded-lg">
                <Activity className="h-6 w-6 text-indigo-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              of {summary.total_checks} total
            </p>
          </div>

          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Breached</p>
                <p className={`text-2xl font-bold mt-1 ${summary.breached_checks > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {summary.breached_checks}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${summary.breached_checks > 0 ? 'bg-red-900/30' : 'bg-green-900/30'}`}>
                {summary.breached_checks > 0 ? (
                  <XCircle className="h-6 w-6 text-red-400" />
                ) : (
                  <CheckCircle className="h-6 w-6 text-green-400" />
                )}
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              checks exceeded threshold
            </p>
          </div>

          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Unacknowledged</p>
                <p className={`text-2xl font-bold mt-1 ${summary.unacknowledged_alerts > 0 ? 'text-yellow-400' : 'text-gray-100'}`}>
                  {summary.unacknowledged_alerts}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${summary.unacknowledged_alerts > 0 ? 'bg-yellow-900/30' : 'bg-dark-border'}`}>
                <Bell className="h-6 w-6 text-yellow-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              of {summary.total_alerts} total alerts
            </p>
          </div>

          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Critical Alerts</p>
                <p className={`text-2xl font-bold mt-1 ${summary.critical_alerts > 0 ? 'text-red-400' : 'text-gray-100'}`}>
                  {summary.critical_alerts}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${summary.critical_alerts > 0 ? 'bg-red-900/30' : 'bg-dark-border'}`}>
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              requiring immediate attention
            </p>
          </div>
        </div>
      )}

      {/* Alerts Section */}
      <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
        <div className="p-4 border-b border-dark-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
            <Bell size={20} />
            Alerts
          </h2>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={showUnacknowledgedOnly}
                onChange={(e) => setShowUnacknowledgedOnly(e.target.checked)}
                className="rounded border-gray-600 bg-dark-bg text-indigo-600 focus:ring-indigo-500"
              />
              Unacknowledged only
            </label>
            {alerts.length > 0 && (
              <button
                onClick={acknowledgeAllAlerts}
                className="px-3 py-1.5 text-sm font-medium text-gray-300 bg-dark-border rounded hover:bg-gray-600"
              >
                Acknowledge All
              </button>
            )}
          </div>
        </div>

        {alerts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <BellOff className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No alerts to display</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {alerts.map((alert) => (
              <div key={alert.id} className="p-4 hover:bg-dark-bg/50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded border ${getSeverityColor(alert.severity)}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-400">
                        {formatDate(alert.triggered_at)}
                      </span>
                    </div>
                    <p className="text-gray-200">{alert.message || 'Drift detected'}</p>
                    <div className="mt-2 text-sm text-gray-400 flex gap-4">
                      <span>Baseline: {formatValue(alert.baseline_value)}</span>
                      <span>Current: {formatValue(alert.current_value)}</span>
                      {alert.change_percent !== null && (
                        <span className={alert.change_percent > 0 ? 'text-red-400' : 'text-green-400'}>
                          {alert.change_percent > 0 ? '+' : ''}{alert.change_percent.toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => acknowledgeAlert(alert.id)}
                      className="px-3 py-1.5 text-sm font-medium text-indigo-400 bg-indigo-900/30 rounded hover:bg-indigo-900/50"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Drift Checks Section */}
      <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
        <div className="p-4 border-b border-dark-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
            <Activity size={20} />
            Drift Checks
          </h2>
          <div className="flex items-center gap-3">
            <Filter size={16} className="text-gray-500" />
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={showActiveOnly}
                onChange={(e) => setShowActiveOnly(e.target.checked)}
                className="rounded border-gray-600 bg-dark-bg text-indigo-600 focus:ring-indigo-500"
              />
              Active only
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={showBreachedOnly}
                onChange={(e) => setShowBreachedOnly(e.target.checked)}
                className="rounded border-gray-600 bg-dark-bg text-indigo-600 focus:ring-indigo-500"
              />
              Breached only
            </label>
          </div>
        </div>

        {checks.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No drift checks configured</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-4 py-2 text-sm font-medium text-indigo-400 border border-indigo-400 rounded hover:bg-indigo-900/30"
            >
              Create your first check
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-bg text-gray-400 text-sm">
                <tr>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">Metric</th>
                  <th className="px-4 py-3 text-left">Threshold</th>
                  <th className="px-4 py-3 text-left">Baseline</th>
                  <th className="px-4 py-3 text-left">Latest</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Last Checked</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border">
                {checks.map((check) => (
                  <tr key={check.id} className="hover:bg-dark-bg/50">
                    <td className="px-4 py-3">
                      <div>
                        <span className="font-medium text-gray-200">{check.name}</span>
                        {check.description && (
                          <p className="text-xs text-gray-500 mt-0.5">{check.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{check.metric}</td>
                    <td className="px-4 py-3 text-gray-300">
                      {(check.threshold * 100).toFixed(1)}%
                      <span className="text-xs text-gray-500 ml-1">({check.comparison})</span>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{formatValue(check.baseline_value)}</td>
                    <td className="px-4 py-3 text-gray-300">{formatValue(check.latest_value)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {check.is_breached ? (
                          <span className="flex items-center gap-1 text-red-400">
                            <XCircle size={16} />
                            Breached
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-green-400">
                            <CheckCircle size={16} />
                            Normal
                          </span>
                        )}
                        {!check.is_active && (
                          <span className="text-xs text-gray-500">(disabled)</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-sm">
                      {formatDate(check.last_checked_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => toggleCheckActive(check)}
                          className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-dark-border rounded"
                          title={check.is_active ? 'Disable' : 'Enable'}
                        >
                          {check.is_active ? <Eye size={16} /> : <Eye size={16} className="opacity-50" />}
                        </button>
                        <button
                          onClick={() => deleteCheck(check.id)}
                          className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-dark-border rounded"
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Check Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-surface rounded-lg border border-dark-border w-full max-w-md mx-4">
            <div className="p-4 border-b border-dark-border">
              <h3 className="text-lg font-semibold text-gray-100">Create Drift Check</h3>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                <input
                  type="text"
                  value={newCheck.name}
                  onChange={(e) => setNewCheck({ ...newCheck, name: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g., RMSE Drift Check"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Metric Name</label>
                <input
                  type="text"
                  value={newCheck.metric}
                  onChange={(e) => setNewCheck({ ...newCheck, metric: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g., rmse, accuracy, f1_score"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Threshold (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newCheck.threshold * 100}
                    onChange={(e) => setNewCheck({ ...newCheck, threshold: parseFloat(e.target.value) / 100 })}
                    className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Comparison</label>
                  <select
                    value={newCheck.comparison}
                    onChange={(e) => setNewCheck({ ...newCheck, comparison: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="percentage_both">Both directions</option>
                    <option value="percentage_increase">Increase only</option>
                    <option value="percentage_decrease">Decrease only</option>
                    <option value="absolute">Absolute</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Check Frequency</label>
                <select
                  value={newCheck.check_frequency}
                  onChange={(e) => setNewCheck({ ...newCheck, check_frequency: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="on_run">On each run</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description (optional)</label>
                <textarea
                  value={newCheck.description}
                  onChange={(e) => setNewCheck({ ...newCheck, description: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  rows={2}
                  placeholder="Brief description of this check"
                />
              </div>
            </div>
            <div className="p-4 border-t border-dark-border flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-border rounded hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={createCheck}
                disabled={!newCheck.name || !newCheck.metric}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                Create Check
              </button>
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
  );
}
