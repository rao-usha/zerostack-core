import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

interface Run {
  id: string;
  recipe_id: string;
  status: string;
  created_at: string;
  metrics: Record<string, number>;
  estimated_cost_usd: number | null;
  actual_cost_usd: number | null;
  runtime_seconds: number | null;
  gpu_type: string | null;
}

interface ComparisonData {
  runs: Run[];
  metrics_comparison: Record<string, {
    values: { run_id: string; value: number }[];
    min: number | null;
    max: number | null;
  }>;
  cost_comparison: {
    total_estimated: number;
    total_actual: number;
    cheapest_run: string | null;
    most_expensive_run: string | null;
  };
}

export default function RunComparison() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableRuns, setAvailableRuns] = useState<Run[]>([]);
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);

  // Get run IDs from URL
  const runIdsParam = searchParams.get('run_ids');

  // Load available runs on mount
  useEffect(() => {
    loadAvailableRuns();
  }, []);

  // Load comparison when URL has run_ids
  useEffect(() => {
    if (runIdsParam) {
      const ids = runIdsParam.split(',');
      setSelectedRuns(ids);
      if (ids.length >= 2) {
        loadComparison(ids);
      }
    }
  }, [runIdsParam]);

  const loadAvailableRuns = async () => {
    try {
      const response = await fetch('/api/v1/ml-development/runs?limit=50');
      if (response.ok) {
        const data = await response.json();
        setAvailableRuns(data.runs || []);
      }
    } catch (err) {
      console.error('Failed to load runs:', err);
    }
  };

  const loadComparison = async (runIds: string[]) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/v1/ml-development/runs/compare?run_ids=${runIds.join(',')}`);
      if (response.ok) {
        const data = await response.json();
        setComparison(data);
      } else {
        const errData = await response.json();
        setError(errData.detail || 'Failed to load comparison');
      }
    } catch (err) {
      setError('Failed to load comparison');
    } finally {
      setLoading(false);
    }
  };

  const handleRunToggle = (runId: string) => {
    setSelectedRuns(prev => {
      if (prev.includes(runId)) {
        return prev.filter(id => id !== runId);
      }
      if (prev.length >= 5) {
        return prev; // Max 5 runs
      }
      return [...prev, runId];
    });
  };

  const handleCompare = () => {
    if (selectedRuns.length >= 2) {
      setSearchParams({ run_ids: selectedRuns.join(',') });
    }
  };

  const formatValue = (value: number | null | undefined, precision = 2) => {
    if (value === null || value === undefined) return '-';
    return typeof value === 'number' ? value.toFixed(precision) : value;
  };

  const formatCost = (value: number | null | undefined) => {
    if (value === null || value === undefined) return '-';
    return `$${value.toFixed(4)}`;
  };

  const formatDuration = (seconds: number | null | undefined) => {
    if (seconds === null || seconds === undefined) return '-';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const getMetricColor = (runId: string, metric: string) => {
    if (!comparison) return '';
    const metricData = comparison.metrics_comparison[metric];
    if (!metricData) return '';
    
    const runValue = metricData.values.find(v => v.run_id === runId);
    if (!runValue) return '';
    
    if (runValue.value === metricData.max) return 'bg-green-100 text-green-800';
    if (runValue.value === metricData.min) return 'bg-red-100 text-red-800';
    return '';
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Run Comparison</h1>
      
      {/* Run Selection */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Select Runs to Compare</h2>
        <p className="text-sm text-gray-600 mb-4">
          Select 2-5 runs to compare their metrics, costs, and performance.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
          {availableRuns.map(run => (
            <label 
              key={run.id}
              className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedRuns.includes(run.id) 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <input
                type="checkbox"
                checked={selectedRuns.includes(run.id)}
                onChange={() => handleRunToggle(run.id)}
                className="mr-3"
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{run.id}</div>
                <div className="text-xs text-gray-500">
                  {run.status} • {new Date(run.created_at).toLocaleDateString()}
                </div>
              </div>
            </label>
          ))}
        </div>
        
        <button
          onClick={handleCompare}
          disabled={selectedRuns.length < 2}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Compare {selectedRuns.length} Run{selectedRuns.length !== 1 ? 's' : ''}
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading comparison...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && !loading && (
        <div className="space-y-6">
          {/* Overview */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Overview</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-sm text-gray-500 border-b">
                    <th className="pb-3 pr-4">Run ID</th>
                    <th className="pb-3 pr-4">Recipe</th>
                    <th className="pb-3 pr-4">Status</th>
                    <th className="pb-3 pr-4">GPU</th>
                    <th className="pb-3 pr-4">Duration</th>
                    <th className="pb-3 pr-4">Estimated</th>
                    <th className="pb-3">Actual</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.runs.map(run => (
                    <tr key={run.id} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-mono text-sm">
                        <a href={`/runs/${run.id}`} className="text-blue-600 hover:underline">
                          {run.id.slice(0, 12)}...
                        </a>
                      </td>
                      <td className="py-3 pr-4 text-sm">{run.recipe_id}</td>
                      <td className="py-3 pr-4">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          run.status === 'succeeded' ? 'bg-green-100 text-green-800' :
                          run.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-sm">{run.gpu_type || '-'}</td>
                      <td className="py-3 pr-4 text-sm">{formatDuration(run.runtime_seconds)}</td>
                      <td className="py-3 pr-4 text-sm">{formatCost(run.estimated_cost_usd)}</td>
                      <td className={`py-3 text-sm ${
                        comparison.cost_comparison.cheapest_run === run.id ? 'text-green-600 font-semibold' :
                        comparison.cost_comparison.most_expensive_run === run.id ? 'text-red-600 font-semibold' :
                        ''
                      }`}>
                        {formatCost(run.actual_cost_usd)}
                        {comparison.cost_comparison.cheapest_run === run.id && ' 💰'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Metrics Comparison */}
          {Object.keys(comparison.metrics_comparison).length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Metrics Comparison</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 border-b">
                      <th className="pb-3 pr-4">Metric</th>
                      {comparison.runs.map(run => (
                        <th key={run.id} className="pb-3 pr-4 font-mono text-xs">
                          {run.id.slice(0, 8)}
                        </th>
                      ))}
                      <th className="pb-3 pr-4">Min</th>
                      <th className="pb-3">Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(comparison.metrics_comparison).map(([metric, data]) => (
                      <tr key={metric} className="border-b last:border-0">
                        <td className="py-3 pr-4 font-medium">{metric}</td>
                        {comparison.runs.map(run => {
                          const value = data.values.find(v => v.run_id === run.id)?.value;
                          return (
                            <td 
                              key={run.id} 
                              className={`py-3 pr-4 text-sm ${getMetricColor(run.id, metric)}`}
                            >
                              {formatValue(value, 4)}
                            </td>
                          );
                        })}
                        <td className="py-3 pr-4 text-sm text-gray-500">{formatValue(data.min, 4)}</td>
                        <td className="py-3 text-sm text-gray-500">{formatValue(data.max, 4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 flex items-center gap-4 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <span className="w-4 h-4 bg-green-100 rounded"></span> Best
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-4 h-4 bg-red-100 rounded"></span> Worst
                </span>
              </div>
            </div>
          )}

          {/* Cost Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Cost Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-500">Total Estimated</div>
                <div className="text-2xl font-bold">{formatCost(comparison.cost_comparison.total_estimated)}</div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-500">Total Actual</div>
                <div className="text-2xl font-bold">{formatCost(comparison.cost_comparison.total_actual)}</div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="text-sm text-green-600">Cheapest Run</div>
                <div className="text-lg font-mono">{comparison.cost_comparison.cheapest_run?.slice(0, 12) || '-'}</div>
              </div>
              <div className="p-4 bg-red-50 rounded-lg">
                <div className="text-sm text-red-600">Most Expensive</div>
                <div className="text-lg font-mono">{comparison.cost_comparison.most_expensive_run?.slice(0, 12) || '-'}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
