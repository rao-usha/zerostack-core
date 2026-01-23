import {
  CheckCircle,
  XCircle,
  Settings,
  Clock,
  Activity
} from 'lucide-react';

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

interface SLAStatusCardProps {
  status: SLAStatus;
  onConfigure: () => void;
}

export default function SLAStatusCard({ status, onConfigure }: SLAStatusCardProps) {
  const StatusIcon = status.is_compliant ? CheckCircle : XCircle;
  const statusColor = status.is_compliant ? 'text-green-400' : 'text-red-400';
  const statusBg = status.is_compliant ? 'bg-green-900/20' : 'bg-red-900/20';
  const statusBorder = status.is_compliant ? 'border-green-500/30' : 'border-red-500/30';

  return (
    <div className={`bg-dark-surface border border-dark-border rounded-lg p-6 h-full`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">SLA Status</h3>
        <button
          onClick={onConfigure}
          className="p-1 text-gray-500 hover:text-gray-300 rounded"
          title="Configure SLA"
        >
          <Settings size={14} />
        </button>
      </div>

      {/* Main status */}
      <div className={`p-4 rounded-lg ${statusBg} border ${statusBorder} mb-4`}>
        <div className="flex items-center gap-3">
          <StatusIcon className={`h-8 w-8 ${statusColor}`} />
          <div>
            <div className={`font-semibold ${statusColor}`}>
              {status.is_compliant ? 'SLA Compliant' : 'SLA Breach'}
            </div>
            <p className="text-xs text-gray-400 mt-0.5">{status.message}</p>
          </div>
        </div>
      </div>

      {/* Thresholds */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Clock size={14} />
            P95 Latency
          </div>
          <div className="flex items-center gap-2">
            {status.latency_compliant ? (
              <CheckCircle size={14} className="text-green-400" />
            ) : (
              <XCircle size={14} className="text-red-400" />
            )}
            <span className={`text-sm font-medium ${status.latency_compliant ? 'text-green-400' : 'text-red-400'}`}>
              {status.current_p95_ms !== null
                ? `${status.current_p95_ms.toFixed(1)}ms`
                : '-'
              }
            </span>
            <span className="text-xs text-gray-500">
              / {status.sla_config.max_latency_p95_ms}ms
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Activity size={14} />
            Error Rate
          </div>
          <div className="flex items-center gap-2">
            {status.error_rate_compliant ? (
              <CheckCircle size={14} className="text-green-400" />
            ) : (
              <XCircle size={14} className="text-red-400" />
            )}
            <span className={`text-sm font-medium ${status.error_rate_compliant ? 'text-green-400' : 'text-red-400'}`}>
              {status.current_error_rate !== null
                ? `${status.current_error_rate.toFixed(2)}%`
                : '-'
              }
            </span>
            <span className="text-xs text-gray-500">
              / {status.sla_config.max_error_rate_percent}%
            </span>
          </div>
        </div>
      </div>

      {/* Alerting status */}
      <div className="mt-4 pt-4 border-t border-dark-border">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">Alerting</span>
          <span className={status.sla_config.alerting_enabled ? 'text-green-400' : 'text-gray-500'}>
            {status.sla_config.alerting_enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
      </div>
    </div>
  );
}
