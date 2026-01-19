import React, { useState, useEffect, useCallback } from 'react'
import LineageView from '../components/LineageView'
import LineageMiniWidget from '../components/LineageMiniWidget'
import LineageHealthBadge from '../components/LineageHealthBadge'
import LineageImpactAnalysis from '../components/LineageImpactAnalysis'
import { getLineage, getLineageSummary, analyzeImpact } from '../api/client'

/**
 * Lineage Demo Page
 *
 * Shows all lineage components with realistic dummy data or live API data
 * Toggle between Demo mode and Live API mode
 */

// Entity types for lineage
type EntityType = 'dataset' | 'file' | 'file_table' | 'database_table' | 'model' | 'notebook' | 'report'

// Create mock API responses for demo
const mockGetLineage = () => {
  return Promise.resolve({
    center_node: {
      entity_type: 'dataset',
      entity_id: 'center-dataset-id',
      entity_name: 'sales_analytics_master',
      row_count: 2500000,
      column_count: 45,
      depth: 0,
    },
    upstream_nodes: [
      {
        entity_type: 'file',
        entity_id: 'file-1',
        entity_name: 'raw_transactions.csv',
        row_count: 5000000,
        column_count: 12,
        depth: 2,
      },
      {
        entity_type: 'file',
        entity_id: 'file-2',
        entity_name: 'customer_data.xlsx',
        row_count: 150000,
        column_count: 25,
        depth: 2,
      },
      {
        entity_type: 'file_table',
        entity_id: 'ft-1',
        entity_name: 'transactions_cleaned',
        row_count: 4800000,
        column_count: 15,
        depth: 1,
      },
      {
        entity_type: 'file_table',
        entity_id: 'ft-2',
        entity_name: 'customer_enriched',
        row_count: 145000,
        column_count: 30,
        depth: 1,
      },
      {
        entity_type: 'database_table',
        entity_id: 'db-1',
        entity_name: 'product_catalog',
        row_count: 50000,
        column_count: 20,
        depth: 1,
      },
    ],
    downstream_nodes: [
      {
        entity_type: 'dataset',
        entity_id: 'ds-1',
        entity_name: 'monthly_sales_summary',
        row_count: 36000,
        column_count: 15,
        depth: 1,
      },
      {
        entity_type: 'dataset',
        entity_id: 'ds-2',
        entity_name: 'customer_segments',
        row_count: 12000,
        column_count: 8,
        depth: 1,
      },
      {
        entity_type: 'model',
        entity_id: 'model-1',
        entity_name: 'sales_forecast_v3',
        row_count: 2500000,
        column_count: 45,
        depth: 1,
      },
      {
        entity_type: 'model',
        entity_id: 'model-2',
        entity_name: 'churn_prediction',
        row_count: 145000,
        column_count: 30,
        depth: 1,
      },
      {
        entity_type: 'report',
        entity_id: 'report-1',
        entity_name: 'executive_dashboard',
        row_count: 36000,
        column_count: 10,
        depth: 1,
      },
      {
        entity_type: 'notebook',
        entity_id: 'nb-1',
        entity_name: 'adhoc_analysis_q1',
        row_count: 500000,
        column_count: 20,
        depth: 1,
      },
      {
        entity_type: 'dataset',
        entity_id: 'ds-3',
        entity_name: 'product_performance',
        row_count: 24000,
        column_count: 12,
        depth: 2,
      },
      {
        entity_type: 'report',
        entity_id: 'report-2',
        entity_name: 'marketing_insights',
        row_count: 12000,
        column_count: 8,
        depth: 2,
      },
    ],
    edges: [
      {
        id: 'edge-1',
        source_type: 'file',
        source_id: 'file-1',
        source_name: 'raw_transactions.csv',
        target_type: 'file_table',
        target_id: 'ft-1',
        target_name: 'transactions_cleaned',
        edge_type: 'published',
        source_row_count: 5000000,
        target_row_count: 4800000,
        created_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 'edge-2',
        source_type: 'file',
        source_id: 'file-2',
        source_name: 'customer_data.xlsx',
        target_type: 'file_table',
        target_id: 'ft-2',
        target_name: 'customer_enriched',
        edge_type: 'published',
        source_row_count: 150000,
        target_row_count: 145000,
        created_at: '2024-01-15T11:00:00Z',
      },
      {
        id: 'edge-3',
        source_type: 'file_table',
        source_id: 'ft-1',
        source_name: 'transactions_cleaned',
        target_type: 'dataset',
        target_id: 'center-dataset-id',
        target_name: 'sales_analytics_master',
        edge_type: 'joined',
        source_row_count: 4800000,
        target_row_count: 2500000,
        created_at: '2024-01-16T09:15:00Z',
      },
      {
        id: 'edge-4',
        source_type: 'file_table',
        source_id: 'ft-2',
        source_name: 'customer_enriched',
        target_type: 'dataset',
        target_id: 'center-dataset-id',
        target_name: 'sales_analytics_master',
        edge_type: 'joined',
        source_row_count: 145000,
        target_row_count: 2500000,
        created_at: '2024-01-16T09:15:00Z',
      },
      {
        id: 'edge-5',
        source_type: 'database_table',
        source_id: 'db-1',
        source_name: 'product_catalog',
        target_type: 'dataset',
        target_id: 'center-dataset-id',
        target_name: 'sales_analytics_master',
        edge_type: 'joined',
        source_row_count: 50000,
        target_row_count: 2500000,
        created_at: '2024-01-16T09:15:00Z',
      },
      {
        id: 'edge-6',
        source_type: 'dataset',
        source_id: 'center-dataset-id',
        source_name: 'sales_analytics_master',
        target_type: 'dataset',
        target_id: 'ds-1',
        target_name: 'monthly_sales_summary',
        edge_type: 'aggregated',
        source_row_count: 2500000,
        target_row_count: 36000,
        created_at: '2024-01-17T14:20:00Z',
      },
      {
        id: 'edge-7',
        source_type: 'dataset',
        source_id: 'center-dataset-id',
        source_name: 'sales_analytics_master',
        target_type: 'dataset',
        target_id: 'ds-2',
        target_name: 'customer_segments',
        edge_type: 'aggregated',
        source_row_count: 2500000,
        target_row_count: 12000,
        created_at: '2024-01-17T15:00:00Z',
      },
      {
        id: 'edge-8',
        source_type: 'dataset',
        source_id: 'center-dataset-id',
        source_name: 'sales_analytics_master',
        target_type: 'model',
        target_id: 'model-1',
        target_name: 'sales_forecast_v3',
        edge_type: 'trained_on',
        source_row_count: 2500000,
        target_row_count: 2500000,
        created_at: '2024-01-18T10:00:00Z',
      },
      {
        id: 'edge-9',
        source_type: 'dataset',
        source_id: 'center-dataset-id',
        source_name: 'sales_analytics_master',
        target_type: 'model',
        target_id: 'model-2',
        target_name: 'churn_prediction',
        edge_type: 'trained_on',
        source_row_count: 145000,
        target_row_count: 145000,
        created_at: '2024-01-18T11:30:00Z',
      },
      {
        id: 'edge-10',
        source_type: 'dataset',
        source_id: 'ds-1',
        source_name: 'monthly_sales_summary',
        target_type: 'report',
        target_id: 'report-1',
        target_name: 'executive_dashboard',
        edge_type: 'queried_from',
        source_row_count: 36000,
        target_row_count: 36000,
        created_at: '2024-01-19T08:00:00Z',
      },
      {
        id: 'edge-11',
        source_type: 'dataset',
        source_id: 'center-dataset-id',
        source_name: 'sales_analytics_master',
        target_type: 'notebook',
        target_id: 'nb-1',
        target_name: 'adhoc_analysis_q1',
        edge_type: 'queried_from',
        source_row_count: 500000,
        target_row_count: 500000,
        created_at: '2024-01-19T16:45:00Z',
      },
      {
        id: 'edge-12',
        source_type: 'dataset',
        source_id: 'ds-1',
        source_name: 'monthly_sales_summary',
        target_type: 'dataset',
        target_id: 'ds-3',
        target_name: 'product_performance',
        edge_type: 'transformed',
        source_row_count: 36000,
        target_row_count: 24000,
        created_at: '2024-01-20T10:00:00Z',
      },
      {
        id: 'edge-13',
        source_type: 'dataset',
        source_id: 'ds-2',
        source_name: 'customer_segments',
        target_type: 'report',
        target_id: 'report-2',
        target_name: 'marketing_insights',
        edge_type: 'queried_from',
        source_row_count: 12000,
        target_row_count: 12000,
        created_at: '2024-01-20T14:30:00Z',
      },
    ],
    column_mappings: [],
    total_upstream_count: 5,
    total_downstream_count: 8,
    max_depth: 3,
  })
}

const mockGetLineageSummary = () => {
  return Promise.resolve({
    entity_type: 'dataset',
    entity_id: 'center-dataset-id',
    entity_name: 'sales_analytics_master',
    upstream_count: 5,
    downstream_count: 8,
    total_upstream_count: 5,
    total_downstream_count: 8,
    immediate_sources: [
      'transactions_cleaned',
      'customer_enriched',
      'product_catalog',
    ],
    immediate_targets: [
      'monthly_sales_summary',
      'sales_forecast_v3',
      'churn_prediction',
      'executive_dashboard',
    ],
    is_stale: false,
    last_refreshed_at: '2024-01-20T15:00:00Z',
  })
}

const mockAnalyzeImpact = () => {
  return Promise.resolve({
    entity_type: 'dataset',
    entity_id: 'center-dataset-id',
    entity_name: 'sales_analytics_master',
    affected_downstream_count: 8,
    affected_entities: [
      {
        entity_type: 'dataset',
        entity_name: 'monthly_sales_summary',
        row_count: 36000,
        depth: 1,
      },
      {
        entity_type: 'model',
        entity_name: 'sales_forecast_v3',
        row_count: 2500000,
        depth: 1,
      },
      {
        entity_type: 'model',
        entity_name: 'churn_prediction',
        row_count: 145000,
        depth: 1,
      },
      {
        entity_type: 'report',
        entity_name: 'executive_dashboard',
        row_count: 36000,
        depth: 2,
      },
    ],
    risk_level: 'high',
    recommendations: [
      '⚠️ 2 ML model(s) may need retraining',
      '📊 2 report(s) may need refresh',
      '💾 2 downstream dataset(s) affected',
      '🔔 Notify data science team before making changes',
    ],
  })
}

// Context to provide mock or live data to child components
export const LineageDataContext = React.createContext<{
  useLiveData: boolean
  getLineageData: (entityType: string, entityId: string) => Promise<any>
  getLineageSummaryData: (entityType: string, entityId: string) => Promise<any>
  getImpactData: (entityType: string, entityId: string) => Promise<any>
}>({
  useLiveData: false,
  getLineageData: mockGetLineage,
  getLineageSummaryData: mockGetLineageSummary,
  getImpactData: mockAnalyzeImpact,
})

const LineageDemo: React.FC = () => {
  const [useLiveData, setUseLiveData] = useState(false)
  const [liveEntityType, setLiveEntityType] = useState<EntityType>('dataset')
  const [liveEntityId, setLiveEntityId] = useState('')
  const [liveEntityName, setLiveEntityName] = useState('')
  const [liveDataError, setLiveDataError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [liveStats, setLiveStats] = useState<{
    upstreamCount: number
    downstreamCount: number
    totalRows: number
    totalEdges: number
  } | null>(null)

  // Get lineage data - either from mock or live API
  const getLineageData = useCallback(async (entityType: string, entityId: string) => {
    if (!useLiveData) {
      return mockGetLineage()
    }
    try {
      const data = await getLineage(entityType, entityId, { direction: 'both', maxDepth: 3 })
      return data
    } catch (error) {
      console.error('Failed to fetch lineage:', error)
      throw error
    }
  }, [useLiveData])

  // Get lineage summary - either from mock or live API
  const getLineageSummaryData = useCallback(async (entityType: string, entityId: string) => {
    if (!useLiveData) {
      return mockGetLineageSummary()
    }
    try {
      const data = await getLineageSummary(entityType, entityId)
      return data
    } catch (error) {
      console.error('Failed to fetch lineage summary:', error)
      throw error
    }
  }, [useLiveData])

  // Get impact analysis - either from mock or live API
  const getImpactData = useCallback(async (entityType: string, entityId: string) => {
    if (!useLiveData) {
      return mockAnalyzeImpact()
    }
    try {
      const data = await analyzeImpact(entityType, entityId)
      return data
    } catch (error) {
      console.error('Failed to fetch impact analysis:', error)
      throw error
    }
  }, [useLiveData])

  // Load live data when entity changes
  useEffect(() => {
    if (useLiveData && liveEntityId) {
      setIsLoading(true)
      setLiveDataError(null)
      getLineageData(liveEntityType, liveEntityId)
        .then((data) => {
          setLiveStats({
            upstreamCount: data.total_upstream_count || data.upstream_nodes?.length || 0,
            downstreamCount: data.total_downstream_count || data.downstream_nodes?.length || 0,
            totalRows: data.center_node?.row_count || 0,
            totalEdges: data.edges?.length || 0,
          })
          setLiveEntityName(data.center_node?.entity_name || liveEntityId)
        })
        .catch((err) => {
          setLiveDataError(err.message || 'Failed to load lineage data')
          setLiveStats(null)
        })
        .finally(() => setIsLoading(false))
    }
  }, [useLiveData, liveEntityType, liveEntityId, getLineageData])

  // Demo stats (static)
  const demoStats = {
    upstreamCount: 5,
    downstreamCount: 8,
    totalRows: 2500000,
    totalEdges: 13,
  }

  const stats = useLiveData && liveStats ? liveStats : demoStats
  const currentEntityType = useLiveData ? liveEntityType : 'dataset'
  const currentEntityId = useLiveData ? liveEntityId : 'center-dataset-id'
  const currentEntityName = useLiveData ? liveEntityName : 'sales_analytics_master'

  return (
    <LineageDataContext.Provider value={{
      useLiveData,
      getLineageData,
      getLineageSummaryData,
      getImpactData,
    }}>
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Data Lineage Explorer
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                {useLiveData ? 'Connected to live API' : 'Demo mode with sample data'}
              </p>
            </div>
            {/* Mode Toggle */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium ${!useLiveData ? 'text-blue-600' : 'text-gray-400'}`}>
                  Demo
                </span>
                <button
                  onClick={() => setUseLiveData(!useLiveData)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    useLiveData ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      useLiveData ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`text-sm font-medium ${useLiveData ? 'text-green-600' : 'text-gray-400'}`}>
                  Live API
                </span>
              </div>
            </div>
          </div>

          {/* Live API Entity Selector */}
          {useLiveData && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex flex-wrap items-end gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entity Type
                  </label>
                  <select
                    value={liveEntityType}
                    onChange={(e) => setLiveEntityType(e.target.value as EntityType)}
                    className="block w-40 rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 text-sm"
                  >
                    <option value="dataset">Dataset</option>
                    <option value="file">File</option>
                    <option value="file_table">File Table</option>
                    <option value="database_table">Database Table</option>
                    <option value="model">Model</option>
                    <option value="notebook">Notebook</option>
                    <option value="report">Report</option>
                  </select>
                </div>
                <div className="flex-1 min-w-64">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entity ID (UUID)
                  </label>
                  <input
                    type="text"
                    value={liveEntityId}
                    onChange={(e) => setLiveEntityId(e.target.value)}
                    placeholder="Enter entity UUID..."
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 text-sm"
                  />
                </div>
                {isLoading && (
                  <div className="flex items-center gap-2 text-green-600">
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span className="text-sm">Loading...</span>
                  </div>
                )}
              </div>
              {liveDataError && (
                <div className="mt-2 text-sm text-red-600">
                  Error: {liveDataError}
                </div>
              )}
              {!liveEntityId && (
                <p className="mt-2 text-sm text-gray-500">
                  Enter an entity ID to load live lineage data from the API
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="text-4xl font-bold text-blue-600">{stats.upstreamCount}</div>
            <div className="text-sm text-gray-600 mt-1">Upstream Sources</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="text-4xl font-bold text-purple-600">{stats.downstreamCount}</div>
            <div className="text-sm text-gray-600 mt-1">Downstream Targets</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="text-4xl font-bold text-green-600">
              {stats.totalRows >= 1000000
                ? `${(stats.totalRows / 1000000).toFixed(1)}M`
                : stats.totalRows >= 1000
                ? `${(stats.totalRows / 1000).toFixed(1)}K`
                : stats.totalRows}
            </div>
            <div className="text-sm text-gray-600 mt-1">Total Rows</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="text-4xl font-bold text-orange-600">{stats.totalEdges}</div>
            <div className="text-sm text-gray-600 mt-1">Total Flows</div>
          </div>
        </div>

        {/* Mini Widgets Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Mini Widget</h3>
            <LineageMiniWidget
              entityType={currentEntityType}
              entityId={currentEntityId}
            />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Health Badge</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 truncate max-w-48">{currentEntityName}</span>
                  <LineageHealthBadge
                    entityType={currentEntityType}
                    entityId={currentEntityId}
                    showDetails={true}
                  />
                </div>
                {!useLiveData && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">monthly_summary</span>
                    <LineageHealthBadge
                      entityType="dataset"
                      entityId="ds-1"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Quick Info</h3>
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
              {useLiveData ? (
                <div className="text-sm text-gray-700 space-y-2">
                  <div>Entity: <span className="font-medium">{currentEntityName || 'Not selected'}</span></div>
                  <div>Type: <span className="font-medium capitalize">{currentEntityType.replace('_', ' ')}</span></div>
                  <div>Upstream: <span className="font-medium">{stats.upstreamCount}</span></div>
                  <div>Downstream: <span className="font-medium">{stats.downstreamCount}</span></div>
                </div>
              ) : (
                <div className="text-sm text-gray-700 space-y-2">
                  <div>2 CSV files</div>
                  <div>2 File tables</div>
                  <div>1 Database table</div>
                  <div>3 Datasets</div>
                  <div>2 ML Models</div>
                  <div>2 Reports</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Lineage View */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Full Lineage Explorer
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            {useLiveData && !liveEntityId ? (
              <span className="text-amber-600">Enter an entity ID above to view lineage</span>
            ) : (
              <>Try switching between <strong>Table</strong>, <strong>Flow (Sankey)</strong>,
              and <strong>Timeline</strong> views. In Flow view, adjust the controls to see how it stays clean!</>
            )}
          </p>
          {(!useLiveData || liveEntityId) && (
            <LineageView
              entityType={currentEntityType}
              entityId={currentEntityId}
              entityName={currentEntityName}
            />
          )}
        </div>

        {/* Impact Analysis */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Impact Analysis
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            See what would be affected if you change this {currentEntityType.replace('_', ' ')}
          </p>
          {(!useLiveData || liveEntityId) && (
            <LineageImpactAnalysis
              entityType={currentEntityType}
              entityId={currentEntityId}
              entityName={currentEntityName}
            />
          )}
        </div>

        {/* Instructions */}
        <div className={`border rounded-lg p-6 ${useLiveData ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'}`}>
          <h3 className={`font-semibold mb-3 ${useLiveData ? 'text-green-900' : 'text-blue-900'}`}>
            {useLiveData ? 'Live Mode Tips:' : 'Demo Mode Tips:'}
          </h3>
          <ul className={`space-y-2 text-sm ${useLiveData ? 'text-green-800' : 'text-blue-800'}`}>
            {useLiveData ? (
              <>
                <li>Enter a valid UUID for the entity you want to explore</li>
                <li>Select the correct entity type (dataset, file, model, etc.)</li>
                <li>The API will fetch real lineage relationships from your database</li>
                <li>Impact analysis shows actual downstream dependencies</li>
              </>
            ) : (
              <>
                <li>Switch to <strong>Flow</strong> view and adjust "Max Flows" slider</li>
                <li>Click on a node in the Sankey diagram to focus</li>
                <li>Toggle "Group by Type" to see the difference</li>
                <li>Use the threshold slider to hide small flows</li>
                <li>Check the Timeline view to see chronological order</li>
              </>
            )}
          </ul>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 py-8">
          <p>
            {useLiveData
              ? 'Connected to live lineage API'
              : 'Viewing demo data. Toggle to Live API mode to explore real lineage!'}
          </p>
          <p className="mt-2">
            <a href="/data-explorer" className="text-blue-600 hover:text-blue-800">
              Go to Data Explorer
            </a>
            {' | '}
            <a href="/files" className="text-blue-600 hover:text-blue-800">
              Go to Files
            </a>
            {' | '}
            <a href="/lineage-full-demo" className="text-blue-600 hover:text-blue-800">
              SQL Lineage Demo
            </a>
          </p>
        </div>
      </div>
    </div>
    </LineageDataContext.Provider>
  )
}

export default LineageDemo
