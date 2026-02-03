import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

// ============================================================================
// TYPES
// ============================================================================
interface ColumnScan {
  name: string
  data_type: string
  nullable: boolean
  nulls_pct: number
  cardinality: number
  sample_values: any[]
  min_value?: any
  max_value?: any
  mean_value?: number
  is_date?: boolean
  is_numeric?: boolean
}

interface QualityIssue {
  severity: 'warning' | 'error' | 'info'
  column: string
  issue_type: string
  message: string
  suggestion?: string
}

interface TableScanDetail {
  id: string
  connection_id: string
  schema_name: string
  table_name: string
  full_name: string
  row_count: number
  column_count: number
  size_bytes?: number
  columns: ColumnScan[]
  date_column?: string
  date_min?: string
  date_max?: string
  date_span_days?: number
  completeness_score: number
  quality_issues: QualityIssue[]
  sample_rows: Record<string, any>[]
  scanned_at: string
}

interface RequirementCheck {
  requirement_id: string
  name: string
  status: 'met' | 'partial' | 'missing'
  message: string
  details?: string
}

interface RecipeCompatibility {
  recipe_id: string
  recipe_name: string
  description: string
  compatibility_score: number
  status: 'ready' | 'partial' | 'incompatible'
  requirements: RequirementCheck[]
  estimated_quality: string
  suggestion?: string
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function TableExplorerPage() {
  const { scanId } = useParams<{ scanId: string }>()
  const navigate = useNavigate()
  
  // State
  const [scan, setScan] = useState<TableScanDetail | null>(null)
  const [compatibility, setCompatibility] = useState<RecipeCompatibility[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'columns' | 'quality' | 'sample' | 'compatibility'>('overview')
  const [sortColumn, setSortColumn] = useState<string>('name')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  const loadData = useCallback(async () => {
    if (!scanId) return
    
    try {
      setLoading(true)
      const [scanRes, compatRes] = await Promise.all([
        fetch(`/api/v1/data-connections/scans/${scanId}`),
        fetch(`/api/v1/data-connections/scans/${scanId}/compatibility`)
      ])
      
      if (!scanRes.ok) throw new Error('Failed to load table details')
      
      const scanData = await scanRes.json()
      setScan(scanData)
      
      if (compatRes.ok) {
        const compatData = await compatRes.json()
        setCompatibility(compatData.recipes || [])
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load table')
    } finally {
      setLoading(false)
    }
  }, [scanId])

  useEffect(() => {
    loadData()
  }, [loadData])

  // ============================================================================
  // HELPERS
  // ============================================================================
  const formatBytes = (bytes?: number) => {
    if (!bytes) return '—'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`
  }

  const formatDate = (date?: string) => {
    if (!date) return '—'
    return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getQualityColor = (score: number) => {
    if (score >= 90) return '#10b981'
    if (score >= 70) return '#fbbf24'
    return '#ef4444'
  }

  const getNullColor = (percent: number) => {
    if (percent === 0) return '#10b981'
    if (percent < 10) return '#6b7280'
    if (percent < 30) return '#fbbf24'
    return '#ef4444'
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return '#ef4444'
      case 'warning': return '#fbbf24'
      default: return '#6b7280'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return '#10b981'
      case 'partial': return '#fbbf24'
      case 'incompatible': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getCheckIcon = (status: string) => {
    switch (status) {
      case 'met': return '✓'
      case 'partial': return '⚠'
      case 'missing': return '✗'
      default: return '•'
    }
  }

  const getCheckColor = (status: string) => {
    switch (status) {
      case 'met': return '#10b981'
      case 'partial': return '#fbbf24'
      case 'missing': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const sortedColumns = scan?.columns?.slice().sort((a, b) => {
    let aVal: any = a[sortColumn as keyof ColumnScan]
    let bVal: any = b[sortColumn as keyof ColumnScan]
    if (typeof aVal === 'string') aVal = aVal.toLowerCase()
    if (typeof bVal === 'string') bVal = bVal.toLowerCase()
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
    return 0
  }) || []

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  // ============================================================================
  // RENDER
  // ============================================================================
  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingState}>
          <div style={styles.spinner} />
          <p>Loading table details...</p>
        </div>
      </div>
    )
  }

  if (error || !scan) {
    return (
      <div style={styles.container}>
        <div style={styles.errorState}>
          <p>❌ {error || 'Table not found'}</p>
          <button onClick={() => navigate('/data-sources')} style={styles.backButton}>
            ← Back to Data Sources
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <button onClick={() => navigate('/data-sources')} style={styles.backLink}>
            ← Back
          </button>
          <div>
            <h1 style={styles.title}>📊 {scan.full_name}</h1>
            <p style={styles.subtitle}>
              {scan.row_count.toLocaleString()} rows • {scan.column_count} columns • Scanned {formatDate(scan.scanned_at)}
            </p>
          </div>
        </div>
        <button onClick={() => loadData()} style={styles.rescanButton}>
          🔄 Rescan
        </button>
      </header>

      {/* Stats Bar */}
      <div style={styles.statsBar}>
        <div style={styles.statBox}>
          <span style={styles.statNumber}>{scan.row_count.toLocaleString()}</span>
          <span style={styles.statLabel}>Rows</span>
        </div>
        <div style={styles.statBox}>
          <span style={styles.statNumber}>{scan.column_count}</span>
          <span style={styles.statLabel}>Columns</span>
        </div>
        <div style={styles.statBox}>
          <span style={styles.statNumber}>{scan.date_span_days || '—'}</span>
          <span style={styles.statLabel}>Days of History</span>
        </div>
        <div style={styles.statBox}>
          <span style={{ ...styles.statNumber, color: getQualityColor((scan.completeness_score || 0) * 100) }}>
            {((scan.completeness_score || 0) * 100).toFixed(0)}%
          </span>
          <span style={styles.statLabel}>Completeness</span>
        </div>
        <div style={styles.statBox}>
          <span style={styles.statNumber}>{formatBytes(scan.size_bytes)}</span>
          <span style={styles.statLabel}>Size</span>
        </div>
      </div>

      {/* Tabs */}
      <div style={styles.tabBar}>
        {[
          { id: 'overview', label: '📋 Overview' },
          { id: 'columns', label: '📊 Columns' },
          { id: 'quality', label: `⚠️ Quality (${scan.quality_issues.length})` },
          { id: 'sample', label: '🔍 Sample Data' },
          { id: 'compatibility', label: '🤖 ML Compatibility' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              ...styles.tab,
              backgroundColor: activeTab === tab.id ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
              color: activeTab === tab.id ? '#60a5fa' : '#9ca3af',
              borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <main style={styles.main}>
        {/* ================================================================ */}
        {/* OVERVIEW TAB */}
        {/* ================================================================ */}
        {activeTab === 'overview' && (
          <div style={styles.overviewGrid}>
            {/* Time Series Info */}
            {scan.date_column && (
              <section style={styles.card}>
                <h3 style={styles.cardTitle}>📅 Time Series</h3>
                <div style={styles.timeSeriesInfo}>
                  <div style={styles.tsRow}>
                    <span style={styles.tsLabel}>Date Column</span>
                    <span style={styles.tsValue}>{scan.date_column}</span>
                  </div>
                  <div style={styles.tsRow}>
                    <span style={styles.tsLabel}>Date Range</span>
                    <span style={styles.tsValue}>{formatDate(scan.date_min)} → {formatDate(scan.date_max)}</span>
                  </div>
                  <div style={styles.tsRow}>
                    <span style={styles.tsLabel}>Span</span>
                    <span style={styles.tsValue}>{scan.date_span_days} days</span>
                  </div>
                </div>
              </section>
            )}

            {/* Column Type Distribution */}
            <section style={styles.card}>
              <h3 style={styles.cardTitle}>📊 Column Types</h3>
              <div style={styles.typeDistribution}>
                {Object.entries(
                  scan.columns.reduce((acc, col) => {
                    const type = col.data_type.split('(')[0].toLowerCase()
                    acc[type] = (acc[type] || 0) + 1
                    return acc
                  }, {} as Record<string, number>)
                ).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                  <div key={type} style={styles.typeRow}>
                    <span style={styles.typeName}>{type}</span>
                    <div style={styles.typeBarBg}>
                      <div style={{ ...styles.typeBar, width: `${(count / scan.column_count) * 100}%` }} />
                    </div>
                    <span style={styles.typeCount}>{count}</span>
                  </div>
                ))}
              </div>
            </section>

            {/* Quick Quality Summary */}
            <section style={styles.card}>
              <h3 style={styles.cardTitle}>⚡ Quick Summary</h3>
              <div style={styles.summaryList}>
                <div style={styles.summaryItem}>
                  <span style={{ color: '#10b981' }}>✓</span>
                  <span>{scan.columns.filter(c => c.nulls_pct === 0).length} columns have no nulls</span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={{ color: '#fbbf24' }}>⚠</span>
                  <span>{scan.columns.filter(c => c.nulls_pct > 30).length} columns have &gt;30% nulls</span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={{ color: '#6b7280' }}>•</span>
                  <span>{scan.quality_issues.length} quality issues detected</span>
                </div>
                <div style={styles.summaryItem}>
                  <span style={{ color: compatibility.filter(c => c.status === 'ready').length > 0 ? '#10b981' : '#fbbf24' }}>
                    {compatibility.filter(c => c.status === 'ready').length > 0 ? '✓' : '⚠'}
                  </span>
                  <span>
                    {compatibility.filter(c => c.status === 'ready').length} recipes ready,{' '}
                    {compatibility.filter(c => c.status === 'partial').length} partial
                  </span>
                </div>
              </div>
            </section>
          </div>
        )}

        {/* ================================================================ */}
        {/* COLUMNS TAB */}
        {/* ================================================================ */}
        {activeTab === 'columns' && (
          <section style={styles.tableCard}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th} onClick={() => handleSort('name')}>
                    Column {sortColumn === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th style={styles.th} onClick={() => handleSort('data_type')}>
                    Type {sortColumn === 'data_type' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th style={styles.th} onClick={() => handleSort('null_percent')}>
                    Nulls {sortColumn === 'null_percent' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th style={styles.th} onClick={() => handleSort('distinct_count')}>
                    Unique {sortColumn === 'distinct_count' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th style={styles.th}>Range / Sample</th>
                </tr>
              </thead>
              <tbody>
                {sortedColumns.map((col, i) => (
                  <tr key={i} style={styles.tr}>
                    <td style={styles.td}>
                      <strong style={{ color: '#f0f0f5' }}>{col.name}</strong>
                      {col.name === scan.date_column && (
                        <span style={styles.dateTag}>DATE</span>
                      )}
                    </td>
                    <td style={styles.td}>
                      <code style={styles.typeCode}>{col.data_type}</code>
                    </td>
                    <td style={styles.td}>
                      <span style={{ color: getNullColor(col.nulls_pct), fontWeight: col.nulls_pct > 30 ? '600' : '400' }}>
                        {col.nulls_pct.toFixed(1)}%
                        {col.nulls_pct > 30 && ' ⚠'}
                      </span>
                    </td>
                    <td style={styles.td}>{col.cardinality.toLocaleString()}</td>
                    <td style={styles.td}>
                      {col.min_value !== undefined && col.max_value !== undefined ? (
                        <span style={{ color: '#9ca3af', fontSize: '11px' }}>
                          {String(col.min_value).slice(0, 12)} → {String(col.max_value).slice(0, 12)}
                        </span>
                      ) : col.sample_values?.length > 0 ? (
                        <span style={{ color: '#9ca3af', fontSize: '11px' }}>
                          {col.sample_values.slice(0, 3).map(v => String(v).slice(0, 10)).join(', ')}...
                        </span>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* ================================================================ */}
        {/* QUALITY TAB */}
        {/* ================================================================ */}
        {activeTab === 'quality' && (
          <section style={styles.card}>
            <h3 style={styles.cardTitle}>⚠️ Quality Issues</h3>
            
            {scan.quality_issues.length === 0 ? (
              <div style={styles.noIssues}>
                <span style={{ fontSize: '32px' }}>✅</span>
                <p>No quality issues detected!</p>
                <p style={{ color: '#6b7280', fontSize: '12px' }}>This table looks clean and ready for ML.</p>
              </div>
            ) : (
              <div style={styles.issueList}>
                {scan.quality_issues.map((issue, i) => (
                  <div key={i} style={styles.issueCard}>
                    <div style={styles.issueHeader}>
                      <span style={{ 
                        ...styles.issueSeverity, 
                        backgroundColor: `${getSeverityColor(issue.severity)}20`,
                        color: getSeverityColor(issue.severity)
                      }}>
                        {issue.severity.toUpperCase()}
                      </span>
                      <span style={styles.issueColumn}>{issue.column}</span>
                    </div>
                    <p style={styles.issueMessage}>{issue.message}</p>
                    {issue.suggestion && (
                      <p style={styles.issueSuggestion}>💡 {issue.suggestion}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* ================================================================ */}
        {/* SAMPLE DATA TAB */}
        {/* ================================================================ */}
        {activeTab === 'sample' && (
          <section style={styles.tableCard}>
            <div style={styles.sampleHeader}>
              <h3 style={styles.cardTitle}>🔍 Sample Data</h3>
              <span style={{ color: '#6b7280', fontSize: '12px' }}>
                Showing {Math.min(scan.sample_rows?.length || 0, 20)} of {scan.row_count.toLocaleString()} rows
              </span>
            </div>
            
            {!scan.sample_rows || scan.sample_rows.length === 0 ? (
              <div style={styles.noData}>No sample data available</div>
            ) : (
              <div style={styles.sampleTableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      {Object.keys(scan.sample_rows[0]).slice(0, 8).map(key => (
                        <th key={key} style={styles.th}>{key}</th>
                      ))}
                      {Object.keys(scan.sample_rows[0]).length > 8 && (
                        <th style={styles.th}>...</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {scan.sample_rows.slice(0, 20).map((row, i) => (
                      <tr key={i} style={styles.tr}>
                        {Object.entries(row).slice(0, 8).map(([_key, value], j) => (
                          <td key={j} style={styles.td}>
                            <span style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block' }}>
                              {value === null ? <em style={{ color: '#6b7280' }}>null</em> : String(value).slice(0, 30)}
                            </span>
                          </td>
                        ))}
                        {Object.keys(row).length > 8 && (
                          <td style={styles.td}>...</td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {/* ================================================================ */}
        {/* ML COMPATIBILITY TAB */}
        {/* ================================================================ */}
        {activeTab === 'compatibility' && (
          <section style={styles.card}>
            <h3 style={styles.cardTitle}>🤖 ML Recipe Compatibility</h3>
            <p style={styles.cardSubtitle}>
              Based on the table structure and data quality, here's how compatible this data is with different ML recipes.
            </p>
            
            {compatibility.length === 0 ? (
              <div style={styles.noData}>Loading compatibility analysis...</div>
            ) : (
              <div style={styles.recipeList}>
                {compatibility.map((recipe, i) => (
                  <div key={i} style={styles.recipeCard}>
                    <div style={styles.recipeHeader}>
                      <div>
                        <h4 style={styles.recipeName}>{recipe.recipe_name}</h4>
                        <p style={styles.recipeDesc}>{recipe.description}</p>
                      </div>
                      <div style={styles.recipeScore}>
                        <span style={{ 
                          ...styles.statusBadge, 
                          backgroundColor: `${getStatusColor(recipe.status)}20`,
                          color: getStatusColor(recipe.status)
                        }}>
                          {recipe.status === 'ready' ? '✓ Ready' : recipe.status === 'partial' ? '⚠ Partial' : '✗ Incompatible'}
                        </span>
                        <span style={{ fontSize: '20px', fontWeight: '700', color: getStatusColor(recipe.status) }}>
                          {recipe.compatibility_score}%
                        </span>
                      </div>
                    </div>

                    <div style={styles.requirementsList}>
                      {recipe.requirements.map((req, j) => (
                        <div key={j} style={styles.requirementRow}>
                          <span style={{ color: getCheckColor(req.status), marginRight: '8px' }}>
                            {getCheckIcon(req.status)}
                          </span>
                          <span style={{ color: req.status === 'met' ? '#d1d5db' : '#9ca3af' }}>
                            {req.name}
                          </span>
                          {req.details && (
                            <span style={{ color: '#6b7280', fontSize: '11px', marginLeft: '8px' }}>
                              ({req.details})
                            </span>
                          )}
                        </div>
                      ))}
                    </div>

                    {recipe.suggestion && (
                      <div style={styles.recipeSuggestion}>
                        💡 {recipe.suggestion}
                      </div>
                    )}

                    {recipe.status === 'ready' && (
                      <button 
                        onClick={() => navigate(`/forecast?table=${scan.full_name}`)}
                        style={styles.runRecipeButton}
                      >
                        ▶ Run {recipe.recipe_name}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

// ============================================================================
// STYLES
// ============================================================================
const styles: Record<string, React.CSSProperties> = {
  container: { minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  
  // Header
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 32px', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '16px' },
  backLink: { padding: '6px 12px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer' },
  title: { fontSize: '20px', fontWeight: '700', margin: 0 },
  subtitle: { fontSize: '12px', color: '#6b7280', margin: '4px 0 0 0' },
  rescanButton: { padding: '8px 16px', backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', borderRadius: '6px', color: '#60a5fa', fontSize: '13px', cursor: 'pointer' },
  
  // Stats Bar
  statsBar: { display: 'flex', gap: '24px', padding: '16px 32px', borderBottom: '1px solid rgba(255,255,255,0.1)', backgroundColor: '#0f0f14' },
  statBox: { display: 'flex', flexDirection: 'column', gap: '2px' },
  statNumber: { fontSize: '18px', fontWeight: '700', color: '#f0f0f5' },
  statLabel: { fontSize: '11px', color: '#6b7280' },
  
  // Tabs
  tabBar: { display: 'flex', gap: '4px', padding: '0 32px', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  tab: { padding: '12px 16px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: '500', transition: 'all 0.2s' },
  
  // Main
  main: { padding: '24px 32px', maxWidth: '1200px', margin: '0 auto' },
  
  // Cards
  card: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.1)', marginBottom: '16px' },
  cardTitle: { fontSize: '16px', fontWeight: '600', margin: '0 0 16px 0', color: '#f0f0f5' },
  cardSubtitle: { fontSize: '13px', color: '#6b7280', margin: '-12px 0 16px 0' },
  tableCard: { backgroundColor: '#12121a', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', overflow: 'hidden' },
  
  // Overview Grid
  overviewGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' },
  
  // Time Series
  timeSeriesInfo: { display: 'flex', flexDirection: 'column', gap: '12px' },
  tsRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  tsLabel: { fontSize: '12px', color: '#6b7280' },
  tsValue: { fontSize: '13px', color: '#d1d5db', fontWeight: '500' },
  
  // Type Distribution
  typeDistribution: { display: 'flex', flexDirection: 'column', gap: '8px' },
  typeRow: { display: 'flex', alignItems: 'center', gap: '10px' },
  typeName: { fontSize: '12px', color: '#9ca3af', width: '80px' },
  typeBarBg: { flex: 1, height: '8px', backgroundColor: '#1a1a24', borderRadius: '4px' },
  typeBar: { height: '100%', backgroundColor: '#3b82f6', borderRadius: '4px' },
  typeCount: { fontSize: '12px', color: '#6b7280', width: '30px', textAlign: 'right' },
  
  // Summary
  summaryList: { display: 'flex', flexDirection: 'column', gap: '10px' },
  summaryItem: { display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#d1d5db' },
  
  // Table
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', padding: '12px 14px', fontSize: '11px', color: '#6b7280', fontWeight: '500', borderBottom: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', userSelect: 'none' },
  tr: { borderBottom: '1px solid rgba(255,255,255,0.05)' },
  td: { padding: '10px 14px', fontSize: '12px', color: '#9ca3af' },
  typeCode: { backgroundColor: '#1a1a24', padding: '2px 6px', borderRadius: '3px', fontSize: '11px', color: '#a78bfa' },
  dateTag: { marginLeft: '8px', padding: '2px 6px', backgroundColor: 'rgba(59, 130, 246, 0.2)', borderRadius: '3px', fontSize: '9px', color: '#60a5fa' },
  
  // Quality Issues
  noIssues: { textAlign: 'center', padding: '40px' },
  issueList: { display: 'flex', flexDirection: 'column', gap: '12px' },
  issueCard: { backgroundColor: '#0f0f14', borderRadius: '8px', padding: '14px' },
  issueHeader: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' },
  issueSeverity: { padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: '600' },
  issueColumn: { fontSize: '12px', color: '#d1d5db', fontWeight: '500' },
  issueMessage: { fontSize: '13px', color: '#9ca3af', margin: 0 },
  issueSuggestion: { fontSize: '12px', color: '#10b981', margin: '8px 0 0 0', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '8px 10px', borderRadius: '4px' },
  
  // Sample Data
  sampleHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  sampleTableWrapper: { overflowX: 'auto' },
  noData: { padding: '40px', textAlign: 'center', color: '#6b7280' },
  
  // Recipe Compatibility
  recipeList: { display: 'flex', flexDirection: 'column', gap: '16px' },
  recipeCard: { backgroundColor: '#0f0f14', borderRadius: '8px', padding: '16px' },
  recipeHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' },
  recipeName: { fontSize: '14px', fontWeight: '600', margin: 0, color: '#f0f0f5' },
  recipeDesc: { fontSize: '12px', color: '#6b7280', margin: '4px 0 0 0' },
  recipeScore: { display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' },
  statusBadge: { padding: '4px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: '600' },
  requirementsList: { display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' },
  requirementRow: { display: 'flex', alignItems: 'center', fontSize: '12px' },
  recipeSuggestion: { fontSize: '12px', color: '#fbbf24', backgroundColor: 'rgba(251, 191, 36, 0.1)', padding: '10px 12px', borderRadius: '6px', marginTop: '8px' },
  runRecipeButton: { marginTop: '12px', padding: '8px 16px', backgroundColor: '#10b981', border: 'none', borderRadius: '6px', color: '#fff', fontSize: '13px', fontWeight: '600', cursor: 'pointer', width: '100%' },
  
  // Loading & Error
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' },
  spinner: { width: '32px', height: '32px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' },
  errorState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#ef4444' },
  backButton: { marginTop: '16px', padding: '10px 20px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer' }
}
