import { useState, useEffect } from 'react';

interface RunStatus {
  id: string;
  status: string;
  started_at?: string;
  finished_at?: string;
  metrics_json?: Record<string, any>;
  compute_target?: string;
  gpu_type?: string;
  runtime_seconds?: number;
}

interface LiveRunStatusProps {
  runId: string;
  onComplete?: (run: RunStatus) => void;
  onClose?: () => void;
}

export default function LiveRunStatus({ runId, onComplete, onClose }: LiveRunStatusProps) {
  const [run, setRun] = useState<RunStatus | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial fetch
    fetchRunStatus();
    
    // Poll every 3 seconds while running
    const pollInterval = setInterval(() => {
      fetchRunStatus();
    }, 3000);

    // Update elapsed time every second
    const elapsedInterval = setInterval(() => {
      setElapsed(prev => prev + 1);
    }, 1000);

    return () => {
      clearInterval(pollInterval);
      clearInterval(elapsedInterval);
    };
  }, [runId]);

  const fetchRunStatus = async () => {
    try {
      const response = await fetch(`/api/v1/ml-development/runs/${runId}`);
      if (response.ok) {
        const data = await response.json();
        setRun(data);
        
        // If completed, stop polling
        if (data.status === 'succeeded' || data.status === 'failed') {
          onComplete?.(data);
        }
      }
    } catch (error) {
      console.error('Failed to fetch run status:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatElapsed = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      queued: '#f59e0b',
      scheduled: '#3b82f6',
      running: '#8b5cf6',
      succeeded: '#10b981',
      failed: '#ef4444'
    };
    return colors[status] || '#6b7280';
  };

  const isActive = run?.status === 'queued' || run?.status === 'running' || run?.status === 'scheduled';

  if (loading) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <div className="bg-gray-900 rounded-lg p-4 shadow-xl border border-gray-700 animate-pulse">
          <div className="h-4 w-32 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!run) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80">
      <div 
        className="rounded-lg shadow-2xl border overflow-hidden"
        style={{ 
          backgroundColor: '#1a1a24',
          borderColor: `${getStatusColor(run.status)}40`
        }}
      >
        {/* Header */}
        <div 
          className="px-4 py-3 flex items-center justify-between"
          style={{ backgroundColor: `${getStatusColor(run.status)}20` }}
        >
          <div className="flex items-center gap-2">
            {isActive && (
              <div className="relative">
                <div 
                  className="w-3 h-3 rounded-full animate-ping absolute"
                  style={{ backgroundColor: getStatusColor(run.status), opacity: 0.5 }}
                />
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getStatusColor(run.status) }}
                />
              </div>
            )}
            {!isActive && (
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getStatusColor(run.status) }}
              />
            )}
            <span className="font-semibold text-white text-sm">
              {run.status === 'succeeded' ? '✓ Run Complete' : 
               run.status === 'failed' ? '✗ Run Failed' :
               'Run in Progress'}
            </span>
          </div>
          {onClose && (
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          )}
        </div>

        {/* Body */}
        <div className="p-4 space-y-3">
          {/* Run ID */}
          <div>
            <p className="text-gray-500 text-xs uppercase mb-1">Run ID</p>
            <code className="text-gray-300 text-sm font-mono">{run.id}</code>
          </div>

          {/* Progress / Timer */}
          {isActive && (
            <div>
              <p className="text-gray-500 text-xs uppercase mb-1">Elapsed Time</p>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-mono text-white">{formatElapsed(elapsed)}</span>
                {run.compute_target === 'runpod' && run.gpu_type && (
                  <span className="text-xs px-2 py-1 bg-purple-900/50 text-purple-300 rounded">
                    🚀 {run.gpu_type}
                  </span>
                )}
              </div>
              {/* Progress bar animation */}
              <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full animate-pulse"
                  style={{ 
                    backgroundColor: getStatusColor(run.status),
                    width: '100%',
                    animation: 'progress 2s ease-in-out infinite'
                  }}
                />
              </div>
            </div>
          )}

          {/* Completed Results */}
          {run.status === 'succeeded' && run.metrics_json && Object.keys(run.metrics_json).length > 0 && (
            <div className="grid grid-cols-2 gap-2">
              {run.metrics_json.mae !== undefined && (
                <div className="bg-blue-900/30 rounded p-2">
                  <p className="text-blue-400 text-xs uppercase">MAE</p>
                  <p className="text-white font-bold">{Number(run.metrics_json.mae).toFixed(4)}</p>
                </div>
              )}
              {run.metrics_json.rmse !== undefined && (
                <div className="bg-purple-900/30 rounded p-2">
                  <p className="text-purple-400 text-xs uppercase">RMSE</p>
                  <p className="text-white font-bold">{Number(run.metrics_json.rmse).toFixed(4)}</p>
                </div>
              )}
              {run.runtime_seconds !== undefined && (
                <div className="bg-green-900/30 rounded p-2">
                  <p className="text-green-400 text-xs uppercase">Duration</p>
                  <p className="text-white font-bold">{run.runtime_seconds.toFixed(1)}s</p>
                </div>
              )}
            </div>
          )}

          {/* Failed Message */}
          {run.status === 'failed' && (
            <div className="bg-red-900/30 rounded p-2">
              <p className="text-red-400 text-sm">
                Run failed. Check logs for details.
              </p>
            </div>
          )}

          {/* View Details Link */}
          <a 
            href={`/model-development/runs/${run.id}`}
            className="block text-center text-sm py-2 px-4 bg-gray-800 hover:bg-gray-700 rounded text-gray-300 hover:text-white transition-colors"
          >
            View Full Details →
          </a>
        </div>
      </div>

      <style>{`
        @keyframes progress {
          0%, 100% { opacity: 0.5; transform: translateX(-100%); }
          50% { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
