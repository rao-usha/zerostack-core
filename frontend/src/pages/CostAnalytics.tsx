import { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  Clock,
  Server,
  Cpu,
  Plus,
  RefreshCw,
  PieChart,
  BarChart3,
  AlertTriangle,
  Target
} from 'lucide-react';
import Toast from '../components/Toast';

interface CostSummary {
  total_cost_usd: number;
  total_runs: number;
  average_cost_per_run: number;
  total_runtime_hours: number;
  period_start: string;
  period_end: string;
}

interface ProviderCost {
  provider: string;
  total_cost_usd: number;
  run_count: number;
  total_runtime_hours: number;
  average_cost_per_run: number;
}

interface ModelCost {
  model_name: string;
  model_id: string;
  total_cost_usd: number;
  run_count: number;
  total_runtime_hours: number;
}

interface CostTrend {
  period_start: string;
  period_end: string;
  total_cost_usd: number;
  run_count: number;
  average_cost_per_run: number;
}

interface Budget {
  id: string;
  name: string;
  budget_amount_usd: number;
  period: string;
  alert_threshold_percent: number;
  scope_type: string;
  scope_id: string | null;
  is_active: boolean;
}

interface BudgetStatus {
  budget_id: string;
  budget_name: string;
  budget_amount_usd: number;
  current_spend_usd: number;
  percent_used: number;
  remaining_usd: number;
  is_exceeded: boolean;
  alert_triggered: boolean;
  period_start: string;
  period_end: string;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function CostAnalytics() {
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null>(null);

  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [providerCosts, setProviderCosts] = useState<ProviderCost[]>([]);
  const [modelCosts, setModelCosts] = useState<ModelCost[]>([]);
  const [trends, setTrends] = useState<CostTrend[]>([]);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [budgetStatuses, setBudgetStatuses] = useState<Map<string, BudgetStatus>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Time period filter
  const [periodDays, setPeriodDays] = useState(30);

  // Create budget modal
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [newBudget, setNewBudget] = useState({
    name: '',
    budget_amount_usd: 100,
    period: 'monthly',
    alert_threshold_percent: 80,
    scope_type: 'global',
    scope_id: ''
  });

  useEffect(() => {
    fetchAll();
  }, [periodDays]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchSummary(),
        fetchProviderCosts(),
        fetchModelCosts(),
        fetchTrends(),
        fetchBudgets()
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    const end = new Date().toISOString();
    const start = new Date(Date.now() - periodDays * 24 * 60 * 60 * 1000).toISOString();

    const response = await fetch(`${API_BASE}/api/v1/cost-analytics/summary?start=${start}&end=${end}`);
    if (!response.ok) throw new Error('Failed to fetch summary');
    const data = await response.json();
    setSummary(data);
  };

  const fetchProviderCosts = async () => {
    const end = new Date().toISOString();
    const start = new Date(Date.now() - periodDays * 24 * 60 * 60 * 1000).toISOString();

    const response = await fetch(`${API_BASE}/api/v1/cost-analytics/by-provider?start=${start}&end=${end}`);
    if (!response.ok) throw new Error('Failed to fetch provider costs');
    const data = await response.json();
    setProviderCosts(data);
  };

  const fetchModelCosts = async () => {
    const end = new Date().toISOString();
    const start = new Date(Date.now() - periodDays * 24 * 60 * 60 * 1000).toISOString();

    const response = await fetch(`${API_BASE}/api/v1/cost-analytics/by-model?start=${start}&end=${end}`);
    if (!response.ok) throw new Error('Failed to fetch model costs');
    const data = await response.json();
    setModelCosts(data);
  };

  const fetchTrends = async () => {
    const periods = periodDays <= 7 ? 7 : periodDays <= 30 ? 30 : 12;
    const granularity = periodDays <= 7 ? 'daily' : periodDays <= 30 ? 'daily' : 'weekly';

    const response = await fetch(`${API_BASE}/api/v1/cost-analytics/trends?periods=${periods}&granularity=${granularity}`);
    if (!response.ok) throw new Error('Failed to fetch trends');
    const data = await response.json();
    setTrends(data.reverse()); // Show oldest to newest
  };

  const fetchBudgets = async () => {
    const response = await fetch(`${API_BASE}/api/v1/cost-analytics/budgets`);
    if (!response.ok) throw new Error('Failed to fetch budgets');
    const data = await response.json();
    setBudgets(data);

    // Fetch status for each budget
    const statuses = new Map<string, BudgetStatus>();
    for (const budget of data) {
      try {
        const statusResponse = await fetch(`${API_BASE}/api/v1/cost-analytics/budgets/${budget.id}/status`);
        if (statusResponse.ok) {
          const status = await statusResponse.json();
          statuses.set(budget.id, status);
        }
      } catch (e) {
        // Ignore individual budget status errors
      }
    }
    setBudgetStatuses(statuses);
  };

  const createBudget = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/cost-analytics/budgets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newBudget,
          scope_id: newBudget.scope_id || null
        })
      });
      if (!response.ok) throw new Error('Failed to create budget');
      setToast({ message: 'Budget created successfully', type: 'success' });
      setShowBudgetModal(false);
      setNewBudget({
        name: '',
        budget_amount_usd: 100,
        period: 'monthly',
        alert_threshold_percent: 80,
        scope_type: 'global',
        scope_id: ''
      });
      fetchBudgets();
    } catch (err) {
      setToast({ message: 'Failed to create budget', type: 'error' });
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  // Calculate max for chart scaling
  const maxTrendCost = Math.max(...trends.map(t => t.total_cost_usd), 0.01);

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
          <h1 className="text-2xl font-bold text-gray-100">Cost Analytics</h1>
          <p className="text-gray-400 mt-1">
            Track and analyze your ML compute spending
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="px-3 py-2 text-sm bg-dark-surface border border-dark-border rounded-lg text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button
            onClick={fetchAll}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-surface border border-dark-border rounded-lg hover:bg-dark-border flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
          <button
            onClick={() => setShowBudgetModal(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 flex items-center gap-2"
          >
            <Plus size={16} />
            New Budget
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Spend</p>
                <p className="text-2xl font-bold text-gray-100 mt-1">
                  {formatCurrency(summary.total_cost_usd)}
                </p>
              </div>
              <div className="p-3 bg-green-900/30 rounded-lg">
                <DollarSign className="h-6 w-6 text-green-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Last {periodDays} days
            </p>
          </div>

          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Runs</p>
                <p className="text-2xl font-bold text-gray-100 mt-1">
                  {summary.total_runs}
                </p>
              </div>
              <div className="p-3 bg-blue-900/30 rounded-lg">
                <Cpu className="h-6 w-6 text-blue-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Avg {formatCurrency(summary.average_cost_per_run)} per run
            </p>
          </div>

          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Compute Hours</p>
                <p className="text-2xl font-bold text-gray-100 mt-1">
                  {summary.total_runtime_hours.toFixed(1)}h
                </p>
              </div>
              <div className="p-3 bg-purple-900/30 rounded-lg">
                <Clock className="h-6 w-6 text-purple-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              GPU runtime
            </p>
          </div>

          <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Projected Monthly</p>
                <p className="text-2xl font-bold text-gray-100 mt-1">
                  {formatCurrency(summary.total_cost_usd / periodDays * 30)}
                </p>
              </div>
              <div className="p-3 bg-yellow-900/30 rounded-lg">
                <TrendingUp className="h-6 w-6 text-yellow-400" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Based on current rate
            </p>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cost Trend Chart */}
        <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <BarChart3 size={16} />
            Cost Trend
          </h3>
          {trends.length > 0 ? (
            <div className="h-48">
              <div className="flex items-end gap-1 h-full">
                {trends.map((trend, i) => (
                  <div
                    key={i}
                    className="flex-1 flex flex-col items-center gap-1"
                  >
                    <div
                      className="w-full bg-indigo-500/70 rounded-t hover:bg-indigo-400/70 transition-colors"
                      style={{
                        height: `${(trend.total_cost_usd / maxTrendCost) * 100}%`,
                        minHeight: trend.total_cost_usd > 0 ? '4px' : '0'
                      }}
                      title={`${formatCurrency(trend.total_cost_usd)} - ${trend.run_count} runs`}
                    />
                    <span className="text-xs text-gray-500 truncate w-full text-center">
                      {formatDate(trend.period_start)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>

        {/* Cost by Provider */}
        <div className="bg-dark-surface rounded-lg border border-dark-border p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2">
            <PieChart size={16} />
            Cost by Provider
          </h3>
          {providerCosts.length > 0 ? (
            <div className="space-y-3">
              {providerCosts.map((provider, i) => {
                const totalCost = providerCosts.reduce((sum, p) => sum + p.total_cost_usd, 0);
                const percentage = totalCost > 0 ? (provider.total_cost_usd / totalCost) * 100 : 0;
                const colors = ['bg-indigo-500', 'bg-cyan-500', 'bg-purple-500', 'bg-green-500'];

                return (
                  <div key={provider.provider} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <Server size={14} className="text-gray-400" />
                        <span className="text-gray-300 capitalize">{provider.provider}</span>
                      </div>
                      <span className="text-gray-400">{formatCurrency(provider.total_cost_usd)}</span>
                    </div>
                    <div className="h-2 bg-dark-bg rounded-full overflow-hidden">
                      <div
                        className={`h-full ${colors[i % colors.length]} rounded-full`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{provider.run_count} runs</span>
                      <span>{provider.total_runtime_hours.toFixed(1)}h</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500">
              No provider data
            </div>
          )}
        </div>
      </div>

      {/* Budget Status */}
      {budgets.length > 0 && (
        <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
          <div className="p-4 border-b border-dark-border">
            <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <Target size={20} />
              Budget Status
            </h3>
          </div>
          <div className="divide-y divide-dark-border">
            {budgets.map((budget) => {
              const status = budgetStatuses.get(budget.id);
              if (!status) return null;

              return (
                <div key={budget.id} className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-200">{budget.name}</span>
                      <span className="px-2 py-0.5 text-xs rounded bg-dark-border text-gray-400">
                        {budget.period}
                      </span>
                      {status.is_exceeded && (
                        <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded bg-red-900/30 text-red-400">
                          <AlertTriangle size={10} />
                          Exceeded
                        </span>
                      )}
                      {status.alert_triggered && !status.is_exceeded && (
                        <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded bg-yellow-900/30 text-yellow-400">
                          <AlertTriangle size={10} />
                          Alert
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-gray-100">
                        {formatCurrency(status.current_spend_usd)}
                      </span>
                      <span className="text-gray-500"> / {formatCurrency(status.budget_amount_usd)}</span>
                    </div>
                  </div>
                  <div className="h-3 bg-dark-bg rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        status.is_exceeded ? 'bg-red-500' :
                        status.alert_triggered ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(status.percent_used, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-gray-500">
                    <span>{status.percent_used.toFixed(1)}% used</span>
                    <span>{formatCurrency(status.remaining_usd)} remaining</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Cost by Model */}
      {modelCosts.length > 0 && (
        <div className="bg-dark-surface rounded-lg border border-dark-border overflow-hidden">
          <div className="p-4 border-b border-dark-border">
            <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <Cpu size={20} />
              Cost by Model
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-bg text-gray-400 text-sm">
                <tr>
                  <th className="px-4 py-3 text-left">Model</th>
                  <th className="px-4 py-3 text-right">Total Cost</th>
                  <th className="px-4 py-3 text-right">Runs</th>
                  <th className="px-4 py-3 text-right">Runtime</th>
                  <th className="px-4 py-3 text-right">Avg Cost/Run</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border">
                {modelCosts.map((model) => (
                  <tr key={model.model_id} className="hover:bg-dark-bg/50">
                    <td className="px-4 py-3 text-gray-300">{model.model_name}</td>
                    <td className="px-4 py-3 text-right text-gray-300">
                      {formatCurrency(model.total_cost_usd)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400">{model.run_count}</td>
                    <td className="px-4 py-3 text-right text-gray-400">
                      {model.total_runtime_hours.toFixed(1)}h
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400">
                      {formatCurrency(model.total_cost_usd / model.run_count)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Budget Modal */}
      {showBudgetModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-surface rounded-lg border border-dark-border w-full max-w-md mx-4">
            <div className="p-4 border-b border-dark-border">
              <h3 className="text-lg font-semibold text-gray-100">Create Budget</h3>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                <input
                  type="text"
                  value={newBudget.name}
                  onChange={(e) => setNewBudget({ ...newBudget, name: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g., Monthly ML Budget"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Amount (USD)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={newBudget.budget_amount_usd}
                    onChange={(e) => setNewBudget({ ...newBudget, budget_amount_usd: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Period</label>
                  <select
                    value={newBudget.period}
                    onChange={(e) => setNewBudget({ ...newBudget, period: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Alert Threshold (%)
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={newBudget.alert_threshold_percent}
                  onChange={(e) => setNewBudget({ ...newBudget, alert_threshold_percent: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Scope</label>
                <select
                  value={newBudget.scope_type}
                  onChange={(e) => setNewBudget({ ...newBudget, scope_type: e.target.value })}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="global">Global (all spending)</option>
                  <option value="provider">By Provider</option>
                  <option value="model">By Model</option>
                </select>
              </div>
              {newBudget.scope_type !== 'global' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    {newBudget.scope_type === 'provider' ? 'Provider Name' : 'Model ID'}
                  </label>
                  <input
                    type="text"
                    value={newBudget.scope_id}
                    onChange={(e) => setNewBudget({ ...newBudget, scope_id: e.target.value })}
                    className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder={newBudget.scope_type === 'provider' ? 'e.g., runpod' : 'e.g., model-123'}
                  />
                </div>
              )}
            </div>
            <div className="p-4 border-t border-dark-border flex justify-end gap-3">
              <button
                onClick={() => setShowBudgetModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-border rounded hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={createBudget}
                disabled={!newBudget.name || newBudget.budget_amount_usd <= 0}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                Create Budget
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
