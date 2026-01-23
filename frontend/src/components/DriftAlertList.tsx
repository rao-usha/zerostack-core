import { useState } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Check,
  Clock,
  ChevronDown,
  ChevronUp,
  Filter
} from 'lucide-react';

interface DriftAlert {
  id: string;
  drift_check_id: string;
  check_name?: string;
  metric?: string;
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

interface DriftAlertListProps {
  alerts: DriftAlert[];
  onAcknowledge?: (alertId: string) => void;
  onAcknowledgeAll?: () => void;
  showFilters?: boolean;
  maxHeight?: string;
  compact?: boolean;
}

export default function DriftAlertList({
  alerts,
  onAcknowledge,
  onAcknowledgeAll,
  showFilters = true,
  maxHeight = '400px',
  compact = false
}: DriftAlertListProps) {
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());

  const toggleExpanded = (id: string) => {
    const next = new Set(expandedAlerts);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setExpandedAlerts(next);
  };

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    if (severityFilter !== 'all' && alert.severity !== severityFilter) return false;
    if (!showAcknowledged && alert.acknowledged) return false;
    return true;
  });

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle size={16} className="text-red-400" />;
      case 'warning':
        return <AlertCircle size={16} className="text-yellow-400" />;
      default:
        return <AlertCircle size={16} className="text-gray-400" />;
    }
  };

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-900/30 text-red-400 border-red-500/30';
      case 'warning':
        return 'bg-yellow-900/30 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-gray-800 text-gray-400 border-gray-600';
    }
  };

  const unacknowledgedCount = alerts.filter(a => !a.acknowledged).length;
  const criticalCount = alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length;

  if (alerts.length === 0) {
    return (
      <div className="bg-dark-surface rounded-lg border border-dark-border p-6 text-center">
        <Check size={32} className="mx-auto text-green-400 mb-2" />
        <p className="text-gray-400">No drift alerts</p>
        <p className="text-sm text-gray-500">All metrics are within acceptable ranges</p>
      </div>
    );
  }

  return (
    <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
      {/* Header */}
      <div className="p-3 border-b border-dark-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-medium text-gray-200">
            Drift Alerts
            {unacknowledgedCount > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-yellow-900/30 text-yellow-400">
                {unacknowledgedCount} unacknowledged
              </span>
            )}
            {criticalCount > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-red-900/30 text-red-400">
                {criticalCount} critical
              </span>
            )}
          </h3>
        </div>

        {onAcknowledgeAll && unacknowledgedCount > 0 && (
          <button
            onClick={onAcknowledgeAll}
            className="px-3 py-1 text-xs font-medium text-gray-300 bg-dark-border rounded hover:bg-gray-600"
          >
            Acknowledge All
          </button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="p-2 border-b border-dark-border bg-dark-bg/50 flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Filter size={12} />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-dark-bg border border-dark-border rounded px-2 py-1 text-gray-300 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="all">All severity</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
            </select>
          </div>

          <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={showAcknowledged}
              onChange={(e) => setShowAcknowledged(e.target.checked)}
              className="rounded border-gray-600 bg-dark-bg text-indigo-600 focus:ring-indigo-500"
            />
            Show acknowledged
          </label>
        </div>
      )}

      {/* Alert List */}
      <div
        className="overflow-y-auto divide-y divide-dark-border"
        style={{ maxHeight }}
      >
        {filteredAlerts.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No alerts match the current filters
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`${alert.acknowledged ? 'opacity-60' : ''} hover:bg-dark-bg/50 transition-colors`}
            >
              <div
                className={`p-3 flex items-start gap-3 cursor-pointer ${compact ? 'py-2' : ''}`}
                onClick={() => toggleExpanded(alert.id)}
              >
                {/* Severity Icon */}
                <div className="mt-0.5">
                  {getSeverityIcon(alert.severity)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-1.5 py-0.5 text-xs font-medium rounded border ${getSeverityBadgeClass(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    {alert.check_name && (
                      <span className="text-sm text-gray-300 truncate">
                        {alert.check_name}
                      </span>
                    )}
                    {alert.acknowledged && (
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <Check size={10} />
                        Acknowledged
                      </span>
                    )}
                  </div>

                  <p className={`text-gray-300 ${compact ? 'text-xs' : 'text-sm'} truncate`}>
                    {alert.message || 'Drift threshold exceeded'}
                  </p>

                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {formatDate(alert.triggered_at)}
                    </span>
                    {alert.change_percent !== null && (
                      <span className={alert.change_percent > 0 ? 'text-red-400' : 'text-green-400'}>
                        {alert.change_percent > 0 ? '+' : ''}{alert.change_percent.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>

                {/* Expand/Actions */}
                <div className="flex items-center gap-2">
                  {!alert.acknowledged && onAcknowledge && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onAcknowledge(alert.id);
                      }}
                      className="p-1.5 text-gray-400 hover:text-indigo-400 hover:bg-indigo-900/30 rounded transition-colors"
                      title="Acknowledge"
                    >
                      <Check size={14} />
                    </button>
                  )}
                  <button className="p-1 text-gray-500">
                    {expandedAlerts.has(alert.id) ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedAlerts.has(alert.id) && (
                <div className="px-3 pb-3 pl-9 border-t border-dark-border/50 bg-dark-bg/30">
                  <div className="pt-3 grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-gray-500">Baseline Value:</span>
                      <span className="ml-2 text-gray-300">
                        {alert.baseline_value?.toFixed(4) ?? 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Current Value:</span>
                      <span className="ml-2 text-gray-300">
                        {alert.current_value?.toFixed(4) ?? 'N/A'}
                      </span>
                    </div>
                    {alert.metric && (
                      <div>
                        <span className="text-gray-500">Metric:</span>
                        <span className="ml-2 text-gray-300">{alert.metric}</span>
                      </div>
                    )}
                    {alert.run_id && (
                      <div>
                        <span className="text-gray-500">Run ID:</span>
                        <span className="ml-2 text-gray-300 font-mono text-xs">
                          {alert.run_id.slice(0, 8)}...
                        </span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">Alert ID:</span>
                      <span className="ml-2 text-gray-300 font-mono text-xs">
                        {alert.id.slice(0, 8)}...
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Triggered:</span>
                      <span className="ml-2 text-gray-300">
                        {new Date(alert.triggered_at).toLocaleString()}
                      </span>
                    </div>
                    {alert.acknowledged && alert.acknowledged_at && (
                      <>
                        <div>
                          <span className="text-gray-500">Acknowledged:</span>
                          <span className="ml-2 text-gray-300">
                            {new Date(alert.acknowledged_at).toLocaleString()}
                          </span>
                        </div>
                        {alert.acknowledged_by && (
                          <div>
                            <span className="text-gray-500">By:</span>
                            <span className="ml-2 text-gray-300">{alert.acknowledged_by}</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer Summary */}
      <div className="p-2 border-t border-dark-border bg-dark-bg/50 text-xs text-gray-500 text-center">
        Showing {filteredAlerts.length} of {alerts.length} alerts
      </div>
    </div>
  );
}
