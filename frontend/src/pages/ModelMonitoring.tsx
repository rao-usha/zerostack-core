import { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Settings,
  Bell,
  ChevronDown
} from 'lucide-react';
import Toast from '../components/Toast';
import HealthScoreGauge from '../components/HealthScoreGauge';
import LatencyChart from '../components/LatencyChart';
import ErrorRateChart from '../components/ErrorRateChart';
import SLAStatusCard from '../components/SLAStatusCard';

interface ProductionModel {
  model_id: string;
  model_name: string;
  model_family: string;
  health_score: number | null;
  is_sla_compliant: boolean | null;
  current_p95_ms: number | null;
  current_error_rate: number | null;
}

interface HealthScore {
  overall: number;
  latency_score: number;
  error_score: number;
  latency_details: string;
  error_details: string;
}

interface SLAConfig {
  id: string;
  model_id: string;
  max_latency_p95_ms: number;
  max_error_rate_percent: number;
  alerting_enabled: boolean;
}

interface SLAStatus {
  model_id: string;
  is_compliant: boolean;
  latency_compliant: boolean;
  error_rate_compliant: boolean;
  current_p95_ms: number | null;
  current_error_rate: number | null;
  sla_config: SLAConfig;
  message: string;
}

interface LatencyMetric {
  id: string;
  model_id: string;
  recorded_at: string;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  request_count: number;
  window_minutes: number;
}

interface ErrorMetric {
  id: string;
  model_id: string;
  recorded_at: string;
  total_requests: number;
  error_count: number;
  error_rate: number;
  error_types: Record<string, number>;
  window_minutes: number;
}

interface MonitoringSummary {
  model_id: string;
  model_name: string;
  health_score: HealthScore;
  sla_status: SLAStatus | null;
  recent_latency: LatencyMetric[];
  recent_errors: ErrorMetric[];
  active_alerts: number;
  total_requests_24h: number;
}

interface SLAAlert {
  id: string;
  model_id: string;
  model_name: string | null;
  alert_type: string;
  threshold_value: number;
  actual_value: number;
  triggered_at: string;
  resolved_at: string | null;
  acknowledged: boolean;
  acknowledged_by: string | null;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function ModelMonitoring() {
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);

  const [productionModels, setProductionModels] = useState<ProductionModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [alerts, setAlerts] = useState<SLAAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // SLA configuration modal
  const [showSLAModal, setShowSLAModal] = useState(false);
  const [slaConfig, setSlaConfig] = useState({
    max_latency_p95_ms: 500,
    max_error_rate_percent: 1.0,
    alerting_enabled: true
  });

  useEffect(() => {
    fetchProductionModels();
    fetchAlerts();
  }, []);

  useEffect(() => {
    if (selectedModelId) {
      fetchModelSummary(selectedModelId);
    }
  }, [selectedModelId]);

  const fetchProductionModels = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/v1/model-monitoring/production-models`);
      if (!response.ok) throw new Error('Failed to fetch production models');
      const data = await response.json();
      setProductionModels(data.models || []);

      // Select first model if none selected
      if (data.models?.length > 0 && !selectedModelId) {
        setSelectedModelId(data.models[0].model_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchModelSummary = async (modelId: string) => {
    try {
      setLoadingSummary(true);
      const response = await fetch(`${API_BASE}/api/v1/model-monitoring/${modelId}/summary`);
      if (!response.ok) throw new Error('Failed to fetch summary');
      const data = await response.json();
      setSummary(data);

      // Update SLA config from summary
      if (data.sla_status?.sla_config) {
        setSlaConfig({
          max_latency_p95_ms: data.sla_status.sla_config.max_latency_p95_ms,
          max_error_rate_percent: data.sla_status.sla_config.max_error_rate_percent,
          alerting_enabled: data.sla_status.sla_config.alerting_enabled
        });
      }
    } catch (err) {
      setToast({ message: 'Failed to fetch model summary', type: 'error' });
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/model-monitoring/alerts`);
      if (!response.ok) throw new Error('Failed to fetch alerts');
      const data = await response.json();
      setAlerts(data);
    } catch (err) {
      // Silent fail - alerts are secondary
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/model-monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acknowledged_by: 'user' })
      });
      if (!response.ok) throw new Error('Failed to acknowledge');

      setAlerts(alerts.map(a =>
        a.id === alertId ? { ...a, acknowledged: true } : a
      ));
      setToast({ message: 'Alert acknowledged', type: 'success' });
    } catch (err) {
      setToast({ message: 'Failed to acknowledge alert', type: 'error' });
    }
  };

  const updateSLA = async () => {
    if (!selectedModelId) return;

    try {
      const response = await fetch(`${API_BASE}/api/v1/model-monitoring/${selectedModelId}/sla`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(slaConfig)
      });
      if (!response.ok) throw new Error('Failed to update SLA');

      setShowSLAModal(false);
      setToast({ message: 'SLA configuration updated', type: 'success' });
      fetchModelSummary(selectedModelId);
    } catch (err) {
      setToast({ message: 'Failed to update SLA', type: 'error' });
    }
  };

  const formatNumber = (n: number | null | undefined) => {
    if (n === null || n === undefined) return '-';
    return n.toLocaleString();
  };

  const formatPercent = (n: number | null | undefined) => {
    if (n === null || n === undefined) return '-';
    return `${n.toFixed(2)}%`;
  };

  const formatRelativeTime = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return d.toLocaleDateString();
  };

  if (loading && productionModels.length === 0) {
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
        <button onClick={fetchProductionModels} className="mt-2 text-red-400 underline">
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
          <h1 className="text-2xl font-bold text-gray-100">Model Monitoring</h1>
          <p className="text-gray-400 mt-1">
            Track health, latency, and errors for production models
          </p>
        </div>
        <div className="flex items-center gap-3">
          {selectedModelId && (
            <button
              onClick={() => setShowSLAModal(true)}
              className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-surface border border-dark-border rounded-lg hover:bg-dark-border flex items-center gap-2"
            >
              <Settings size={16} />
              Configure SLA
            </button>
          )}
          <button
            onClick={() => {
              fetchProductionModels();
              if (selectedModelId) fetchModelSummary(selectedModelId);
              fetchAlerts();
            }}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-surface border border-dark-border rounded-lg hover:bg-dark-border flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      {/* Model Selector */}
      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-400">Select Model:</label>
        <div className="relative">
          <select
            value={selectedModelId || ''}
            onChange={(e) => setSelectedModelId(e.target.value || null)}
            className="appearance-none px-4 py-2 pr-10 bg-dark-surface border border-dark-border rounded-lg text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 min-w-[300px]"
          >
            <option value="">Select a production model...</option>
            {productionModels.map(m => (
              <option key={m.model_id} value={m.model_id}>
                {m.model_name} ({m.model_family})
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 pointer-events-none" />
        </div>

        {/* Quick stats for selected model */}
        {selectedModelId && !loadingSummary && summary && (
          <div className="flex items-center gap-4 ml-4">
            <div className={`flex items-center gap-1.5 text-sm ${
              summary.sla_status?.is_compliant ? 'text-green-400' : 'text-red-400'
            }`}>
              {summary.sla_status?.is_compliant ? (
                <CheckCircle size={14} />
              ) : (
                <XCircle size={14} />
              )}
              {summary.sla_status?.is_compliant ? 'SLA Compliant' : 'SLA Breach'}
            </div>
            {summary.active_alerts > 0 && (
              <div className="flex items-center gap-1.5 text-sm text-yellow-400">
                <Bell size={14} />
                {summary.active_alerts} active alert{summary.active_alerts > 1 ? 's' : ''}
              </div>
            )}
          </div>
        )}
      </div>

      {/* No Models Message */}
      {productionModels.length === 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-8 text-center">
          <Activity className="h-12 w-12 text-gray-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-200">No Production Models</h3>
          <p className="text-gray-400 mt-2">
            Promote a model to production in the Model Registry to start monitoring.
          </p>
        </div>
      )}

      {/* Main Content */}
      {selectedModelId && (
        <>
          {loadingSummary ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          ) : summary ? (
            <div className="grid grid-cols-12 gap-6">
              {/* Health Score */}
              <div className="col-span-4">
                <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
                  <h3 className="text-sm font-medium text-gray-400 mb-4">Health Score</h3>
                  <HealthScoreGauge
                    overall={summary.health_score.overall}
                    latencyScore={summary.health_score.latency_score}
                    errorScore={summary.health_score.error_score}
                    latencyDetails={summary.health_score.latency_details}
                    errorDetails={summary.health_score.error_details}
                  />
                </div>
              </div>

              {/* SLA Status */}
              <div className="col-span-4">
                {summary.sla_status && (
                  <SLAStatusCard
                    status={summary.sla_status}
                    onConfigure={() => setShowSLAModal(true)}
                  />
                )}
              </div>

              {/* Quick Stats */}
              <div className="col-span-4 space-y-4">
                <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
                  <div className="text-sm text-gray-400">Total Requests (24h)</div>
                  <div className="text-2xl font-bold text-gray-100 mt-1">
                    {formatNumber(summary.total_requests_24h)}
                  </div>
                </div>
                <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
                  <div className="text-sm text-gray-400">Current P95 Latency</div>
                  <div className="text-2xl font-bold text-gray-100 mt-1 flex items-center gap-2">
                    {summary.sla_status?.current_p95_ms
                      ? `${summary.sla_status.current_p95_ms.toFixed(1)}ms`
                      : '-'}
                    {summary.sla_status?.current_p95_ms && summary.sla_status.sla_config && (
                      summary.sla_status.current_p95_ms <= summary.sla_status.sla_config.max_latency_p95_ms
                        ? <TrendingDown className="h-5 w-5 text-green-400" />
                        : <TrendingUp className="h-5 w-5 text-red-400" />
                    )}
                  </div>
                </div>
                <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
                  <div className="text-sm text-gray-400">Current Error Rate</div>
                  <div className="text-2xl font-bold text-gray-100 mt-1 flex items-center gap-2">
                    {formatPercent(summary.sla_status?.current_error_rate)}
                    {summary.sla_status?.current_error_rate !== null && summary.sla_status?.sla_config && (
                      (summary.sla_status.current_error_rate || 0) <= summary.sla_status.sla_config.max_error_rate_percent
                        ? <TrendingDown className="h-5 w-5 text-green-400" />
                        : <TrendingUp className="h-5 w-5 text-red-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Latency Chart */}
              <div className="col-span-6">
                <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
                  <h3 className="text-sm font-medium text-gray-400 mb-4">Latency Over Time (24h)</h3>
                  <LatencyChart
                    data={summary.recent_latency}
                    threshold={summary.sla_status?.sla_config?.max_latency_p95_ms}
                  />
                </div>
              </div>

              {/* Error Rate Chart */}
              <div className="col-span-6">
                <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
                  <h3 className="text-sm font-medium text-gray-400 mb-4">Error Rate Over Time (24h)</h3>
                  <ErrorRateChart
                    data={summary.recent_errors}
                    threshold={summary.sla_status?.sla_config?.max_error_rate_percent}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-dark-surface border border-dark-border rounded-lg p-8 text-center">
              <Activity className="h-12 w-12 text-gray-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-200">No Monitoring Data</h3>
              <p className="text-gray-400 mt-2">
                Start recording metrics to see monitoring data.
              </p>
            </div>
          )}
        </>
      )}

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-400" />
            Active SLA Alerts
          </h3>
          <div className="space-y-3">
            {alerts.filter(a => !a.acknowledged).map(alert => (
              <div
                key={alert.id}
                className="flex items-center justify-between p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    alert.alert_type === 'latency'
                      ? 'bg-orange-900/30 text-orange-400'
                      : 'bg-red-900/30 text-red-400'
                  }`}>
                    <Clock size={16} />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-200">
                      {alert.model_name || alert.model_id}
                    </div>
                    <div className="text-xs text-gray-400">
                      {alert.alert_type === 'latency'
                        ? `P95 latency ${alert.actual_value.toFixed(1)}ms exceeds threshold ${alert.threshold_value}ms`
                        : `Error rate ${alert.actual_value.toFixed(2)}% exceeds threshold ${alert.threshold_value}%`
                      }
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">
                    {formatRelativeTime(alert.triggered_at)}
                  </span>
                  <button
                    onClick={() => acknowledgeAlert(alert.id)}
                    className="px-3 py-1 text-xs font-medium text-yellow-400 bg-yellow-900/30 rounded hover:bg-yellow-900/50"
                  >
                    Acknowledge
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SLA Configuration Modal */}
      {showSLAModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-surface rounded-lg border border-dark-border w-full max-w-md mx-4">
            <div className="p-4 border-b border-dark-border">
              <h3 className="text-lg font-semibold text-gray-100">Configure SLA</h3>
              <p className="text-sm text-gray-400 mt-1">
                Set thresholds for latency and error rate alerts
              </p>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max P95 Latency (ms)
                </label>
                <input
                  type="number"
                  value={slaConfig.max_latency_p95_ms}
                  onChange={(e) => setSlaConfig({ ...slaConfig, max_latency_p95_ms: parseInt(e.target.value) || 500 })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Alert when P95 latency exceeds this value
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Error Rate (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={slaConfig.max_error_rate_percent}
                  onChange={(e) => setSlaConfig({ ...slaConfig, max_error_rate_percent: parseFloat(e.target.value) || 1.0 })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Alert when error rate exceeds this percentage
                </p>
              </div>
              <div>
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    type="checkbox"
                    checked={slaConfig.alerting_enabled}
                    onChange={(e) => setSlaConfig({ ...slaConfig, alerting_enabled: e.target.checked })}
                    className="rounded border-dark-border"
                  />
                  Enable alerting
                </label>
              </div>
            </div>
            <div className="p-4 border-t border-dark-border flex justify-end gap-3">
              <button
                onClick={() => setShowSLAModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-border rounded hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={updateSLA}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700"
              >
                Save Configuration
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
