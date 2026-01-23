/**
 * Lineage Full Demo Page
 * 
 * Interactive demo showcasing all lineage features with synthetic data.
 * Includes pre-loaded queries and real-time analysis.
 */
import React, { useState } from 'react';
import { Play, RefreshCw, Database, Sparkles } from 'lucide-react';
import QueryLineageView from '../components/QueryLineageView';
import ColumnLineageGraph from '../components/ColumnLineageGraph';
import MLQueryAnalyzer from '../components/MLQueryAnalyzer';
import { parseColumnLineage, analyzeMLQuery } from '../api/client';

interface DemoQuery {
  id: string;
  name: string;
  category: string;
  sql: string;
  description: string;
  demonstrates: string[];
}

const DEMO_QUERIES: DemoQuery[] = [
  {
    id: 'basic_join',
    name: 'Customer Revenue Analysis',
    category: 'Basic',
    sql: `SELECT 
  c.country,
  COUNT(DISTINCT c.customer_id) as customer_count,
  SUM(s.amount) as total_revenue,
  AVG(s.amount) as avg_order_value
FROM customers_clean c
INNER JOIN sales_clean s ON c.customer_id = s.customer_id
GROUP BY c.country
ORDER BY total_revenue DESC`,
    description: 'Simple JOIN with aggregations - shows table lineage and column transformations',
    demonstrates: ['INNER JOIN', 'Multiple Aggregations', 'GROUP BY', 'Table Lineage']
  },
  {
    id: 'ml_churn',
    name: 'ML Churn Prediction Features',
    category: 'ML',
    sql: `SELECT 
  c.customer_id,
  c.country,
  DATE_PART('day', NOW() - c.signup_date) as days_since_signup,
  COUNT(s.sale_id) as total_orders,
  SUM(s.amount) as total_spent,
  AVG(s.amount) as avg_order_value,
  STDDEV(s.amount) as order_value_stddev,
  DATE_PART('day', NOW() - MAX(s.sale_date)) as days_since_last_purchase,
  LOG(GREATEST(SUM(s.amount), 1)) as log_total_spent,
  CASE 
    WHEN DATE_PART('day', NOW() - MAX(s.sale_date)) > 90 THEN 1
    ELSE 0
  END as is_churned
FROM customers_clean c
LEFT JOIN sales_clean s ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.country, c.signup_date
HAVING COUNT(s.sale_id) > 0`,
    description: 'ML feature engineering - automatically detected as ML query with high confidence',
    demonstrates: ['ML Detection', 'Feature Engineering', 'LOG Transform', 'Statistical Functions', 'Label Creation']
  },
  {
    id: 'timeseries',
    name: 'Sales Forecasting Features',
    category: 'ML',
    sql: `SELECT 
  DATE(sale_date) as date,
  EXTRACT(dow FROM sale_date) as day_of_week,
  EXTRACT(hour FROM sale_date) as hour,
  SUM(amount) as daily_revenue,
  LAG(SUM(amount), 1) OVER (ORDER BY DATE(sale_date)) as prev_day_revenue,
  LAG(SUM(amount), 7) OVER (ORDER BY DATE(sale_date)) as prev_week_revenue,
  AVG(SUM(amount)) OVER (
    ORDER BY DATE(sale_date) 
    ROWS BETWEEN 7 PRECEDING AND CURRENT ROW
  ) as rolling_avg_7d
FROM sales_clean
WHERE sale_date >= '2024-01-01'
GROUP BY DATE(sale_date), sale_date
ORDER BY date`,
    description: 'Time series features with LAG and rolling windows - ideal for forecasting models',
    demonstrates: ['Window Functions', 'LAG Features', 'Rolling Averages', 'Time Series', 'ML Features']
  },
  {
    id: 'column_transform',
    name: 'Data Cleaning Transformations',
    category: 'Column Lineage',
    sql: `SELECT 
  customer_id,
  UPPER(TRIM(name)) as name_normalized,
  LOWER(email) as email_normalized,
  DATE_PART('year', signup_date) as signup_year,
  CASE 
    WHEN country IN ('USA', 'Canada') THEN 'North America'
    WHEN country IN ('UK', 'Germany', 'France') THEN 'Europe'
    ELSE 'Other'
  END as region
FROM raw_customers
WHERE email IS NOT NULL
LIMIT 100`,
    description: 'Multiple column transformations - see exact transformation for each column',
    demonstrates: ['String Functions', 'CASE Statements', 'Column-Level Lineage', 'Data Cleaning']
  },
  {
    id: 'multi_join',
    name: 'Product Performance Report',
    category: 'Advanced',
    sql: `SELECT 
  p.category,
  p.product_name,
  COUNT(s.sale_id) as units_sold,
  SUM(s.amount) as revenue,
  COUNT(DISTINCT c.country) as countries_sold_in
FROM raw_products p
INNER JOIN sales_clean s ON p.product_id = s.product_id
INNER JOIN customers_clean c ON s.customer_id = c.customer_id
WHERE c.country IN ('USA', 'UK', 'Canada')
GROUP BY p.category, p.product_name
HAVING SUM(s.amount) > 1000
ORDER BY revenue DESC`,
    description: '3-table JOIN with complex filters - shows multi-source lineage',
    demonstrates: ['Multi-Table JOIN', 'Complex Filters', 'HAVING Clause', 'Cross-Table Analysis']
  }
];

const LineageFullDemo: React.FC = () => {
  const [selectedQuery, setSelectedQuery] = useState<DemoQuery>(DEMO_QUERIES[0]);
  const [analyzing, setAnalyzing] = useState(false);
  const [columnLineage, setColumnLineage] = useState<any>(null);
  const [mlAnalysis, setMLAnalysis] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'query' | 'column' | 'ml'>('query');

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setColumnLineage(null);
    setMLAnalysis(null);

    try {
      // Analyze column lineage
      const colResult = await parseColumnLineage(selectedQuery.sql);
      setColumnLineage(colResult);

      // Analyze ML patterns
      const mlResult = await analyzeMLQuery(selectedQuery.sql);
      setMLAnalysis(mlResult);

      // Auto-switch to ML tab if detected
      if (mlResult.is_ml_related && mlResult.confidence > 0.7) {
        setActiveTab('ml');
      } else if (colResult.transformations && colResult.transformations.length > 0) {
        setActiveTab('column');
      }
    } catch (error) {
      console.error('Analysis error:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const categories = Array.from(new Set(DEMO_QUERIES.map(q => q.category)));

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-800">Lineage System Demo</h1>
          </div>
          <p className="text-gray-600">
            Interactive demonstration of automatic SQL lineage tracking, column-level transformations, and ML query detection
          </p>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Query Selection */}
          <div className="col-span-3 space-y-4">
            <div className="bg-white rounded-lg shadow-md p-4">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <Database className="w-4 h-4" />
                Demo Queries
              </h3>

              {categories.map(category => (
                <div key={category} className="mb-4">
                  <div className="text-xs font-medium text-gray-500 mb-2">{category}</div>
                  {DEMO_QUERIES.filter(q => q.category === category).map(query => (
                    <button
                      key={query.id}
                      onClick={() => setSelectedQuery(query)}
                      className={`w-full text-left px-3 py-2 rounded mb-1 text-sm transition-colors ${
                        selectedQuery.id === query.id
                          ? 'bg-blue-100 text-blue-800 font-medium'
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                    >
                      {query.name}
                    </button>
                  ))}
                </div>
              ))}
            </div>

            {/* Info Box */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4">
              <div className="text-xs font-medium text-purple-800 mb-2">💡 How It Works</div>
              <div className="text-xs text-gray-700 space-y-2">
                <p>1. Select a demo query</p>
                <p>2. Click "Analyze Query"</p>
                <p>3. View automatic lineage</p>
                <p>4. Explore different tabs</p>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-9 space-y-6">
            {/* Query Display */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-800">{selectedQuery.name}</h2>
                  <p className="text-sm text-gray-600 mt-1">{selectedQuery.description}</p>
                </div>
                <button
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {analyzing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Analyze Query
                    </>
                  )}
                </button>
              </div>

              {/* SQL Display */}
              <div className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm font-mono whitespace-pre">{selectedQuery.sql}</pre>
              </div>

              {/* Demonstrates Tags */}
              <div className="mt-4 flex flex-wrap gap-2">
                {selectedQuery.demonstrates.map((feature, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-medium"
                  >
                    {feature}
                  </span>
                ))}
              </div>
            </div>

            {/* Results */}
            {(columnLineage || mlAnalysis) && (
              <div className="bg-white rounded-lg shadow-md">
                {/* Tabs */}
                <div className="flex border-b border-gray-200">
                  <button
                    className={`px-6 py-3 text-sm font-medium transition-colors ${
                      activeTab === 'query'
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                    onClick={() => setActiveTab('query')}
                  >
                    Query Lineage
                  </button>
                  <button
                    className={`px-6 py-3 text-sm font-medium transition-colors ${
                      activeTab === 'column'
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                    onClick={() => setActiveTab('column')}
                  >
                    Column Lineage
                    {columnLineage?.transformations && (
                      <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
                        {columnLineage.transformations.length}
                      </span>
                    )}
                  </button>
                  <button
                    className={`px-6 py-3 text-sm font-medium transition-colors ${
                      activeTab === 'ml'
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                    onClick={() => setActiveTab('ml')}
                  >
                    ML Analysis
                    {mlAnalysis?.is_ml_related && (
                      <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs">
                        {Math.round(mlAnalysis.confidence * 100)}%
                      </span>
                    )}
                  </button>
                </div>

                {/* Tab Content */}
                <div className="p-6">
                  {activeTab === 'query' && columnLineage && (
                    <div className="space-y-4">
                      <div className="text-sm text-gray-600">
                        Basic table-level lineage showing source tables, transformations, and data flow.
                      </div>
                      {/* Here you would render QueryLineageView if you had the data */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="font-medium text-blue-800 mb-2">✓ Lineage Extracted</div>
                        <div className="text-sm text-gray-700">
                          Run this query in Data Explorer to see full table-level lineage with automatic detection!
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'column' && columnLineage && (
                    <div className="space-y-4">
                      <div className="text-sm text-gray-600 mb-4">
                        Column-level lineage showing how each source column transforms into target columns.
                      </div>
                      <ColumnLineageGraph
                        transformations={columnLineage.transformations}
                        compact={false}
                      />
                    </div>
                  )}

                  {activeTab === 'ml' && mlAnalysis && (
                    <div className="space-y-4">
                      <div className="text-sm text-gray-600 mb-4">
                        ML query analysis showing detected features, patterns, and confidence score.
                      </div>
                      <MLQueryAnalyzer analysis={mlAnalysis} />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Placeholder when no analysis */}
            {!columnLineage && !mlAnalysis && !analyzing && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <Sparkles className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-800 mb-2">Ready to Analyze</h3>
                <p className="text-gray-600">
                  Click "Analyze Query" to see automatic lineage tracking in action
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LineageFullDemo;
