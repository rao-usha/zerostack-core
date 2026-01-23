import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

// ============================================================================
// TYPES
// ============================================================================
interface DataConnection {
  id: string
  name: string
  description?: string
  connection_type: string
  host?: string
  port?: number
  database?: string
  username?: string
  status: 'pending' | 'connected' | 'failed' | 'scanning'
  last_connected_at?: string
  last_error?: string
  last_scan_at?: string
  scan_status: 'never' | 'scanning' | 'completed' | 'failed'
  tables_count: number
  total_rows: number
  created_at: string
}

interface TableScan {
  id: string
  connection_id: string
  schema_name: string
  table_name: string
  full_name: string
  row_count: number
  column_count: number
  completeness_score: number
  quality_issues: { severity: string; column: string; message: string }[]
  scanned_at: string
}

interface ConnectionForm {
  name: string
  description: string
  connection_type: string
  host: string
  port: number
  database: string
  username: string
  password: string
}

const CONNECTION_TYPES = [
  { id: 'postgresql', name: 'PostgreSQL', icon: '🐘', defaultPort: 5432 },
  { id: 'mysql', name: 'MySQL', icon: '🐬', defaultPort: 3306 },
  { id: 'snowflake', name: 'Snowflake', icon: '❄️', defaultPort: 443 },
  { id: 'bigquery', name: 'BigQuery', icon: '📊', defaultPort: 443 },
  { id: 's3', name: 'S3 / MinIO', icon: '🪣', defaultPort: 9000 },
]

const DEFAULT_FORM: ConnectionForm = {
  name: '',
  description: '',
  connection_type: 'postgresql',
  host: '',
  port: 5432,
  database: '',
  username: '',
  password: ''
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function DataSourcesPage() {
  const navigate = useNavigate()
  
  // State
  const [connections, setConnections] = useState<DataConnection[]>([])
  const [tables, setTables] = useState<Record<string, TableScan[]>>({})
  const [expandedConnection, setExpandedConnection] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Modal state
  const [showAddModal, setShowAddModal] = useState(false)
  const [form, setForm] = useState<ConnectionForm>(DEFAULT_FORM)
  const [formStep, setFormStep] = useState<'type' | 'config'>('type')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [saving, setSaving] = useState(false)
  
  // Scanning state
  const [scanning, setScanning] = useState<Record<string, boolean>>({})
  const [loadingTables, setLoadingTables] = useState<Record<string, boolean>>({})

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  const loadConnections = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/data-connections')
      if (!res.ok) throw new Error('Failed to load connections')
      const data = await res.json()
      setConnections(data.connections || [])
    } catch (err: any) {
      setError(err.message || 'Failed to load data sources')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadTables = useCallback(async (connectionId: string) => {
    setLoadingTables(prev => ({ ...prev, [connectionId]: true }))
    try {
      console.log('Loading tables for connection:', connectionId)
      const res = await fetch(`/api/v1/data-connections/${connectionId}/tables`)
      if (!res.ok) {
        console.error('Tables API error:', res.status, res.statusText)
        throw new Error('Failed to load tables')
      }
      const data = await res.json()
      console.log('Tables loaded:', Array.isArray(data) ? data.length : 0, 'tables')
      // API returns array directly, not wrapped in { tables: [...] }
      const tableData = Array.isArray(data) ? data : []
      setTables(prev => ({ ...prev, [connectionId]: tableData }))
    } catch (err: any) {
      console.error('Failed to load tables:', err)
      setError(`Failed to load tables: ${err.message}`)
    } finally {
      setLoadingTables(prev => ({ ...prev, [connectionId]: false }))
    }
  }, [])

  useEffect(() => {
    loadConnections()
    // Refresh every 10 seconds if any connection is scanning
    const interval = setInterval(() => {
      if (Object.values(scanning).some(s => s)) {
        loadConnections()
      }
    }, 10000)
    return () => clearInterval(interval)
  }, [loadConnections, scanning])

  // Load tables when expanding a connection
  useEffect(() => {
    if (expandedConnection) {
      // Always load tables when expanding (in case they changed)
      loadTables(expandedConnection)
    }
  }, [expandedConnection, loadTables])

  // ============================================================================
  // ACTIONS
  // ============================================================================
  const testConnection = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await fetch('/api/v1/data-connections/quick-scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          connection_type: form.connection_type,
          host: form.host,
          port: form.port,
          database: form.database,
          username: form.username,
          password: form.password
        })
      })
      const data = await res.json()
      if (res.ok) {
        setTestResult({ success: true, message: `Connected! Found ${data.tables_count || 0} tables.` })
      } else {
        setTestResult({ success: false, message: data.detail || 'Connection failed' })
      }
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || 'Connection test failed' })
    } finally {
      setTesting(false)
    }
  }

  const saveConnection = async () => {
    setSaving(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/data-connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to save connection')
      }
      setShowAddModal(false)
      setForm(DEFAULT_FORM)
      setFormStep('type')
      setTestResult(null)
      await loadConnections()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const deleteConnection = async (id: string) => {
    if (!confirm('Delete this connection? This cannot be undone.')) return
    try {
      const res = await fetch(`/api/v1/data-connections/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete')
      await loadConnections()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const scanConnection = async (id: string) => {
    setScanning(prev => ({ ...prev, [id]: true }))
    try {
      const res = await fetch(`/api/v1/data-connections/${id}/scan`, { method: 'POST' })
      if (!res.ok) throw new Error('Failed to start scan')
      // Refresh to show scanning status
      await loadConnections()
      // Poll for completion
      const pollInterval = setInterval(async () => {
        const checkRes = await fetch(`/api/v1/data-connections/${id}`)
        const conn = await checkRes.json()
        if (conn.scan_status !== 'scanning') {
          clearInterval(pollInterval)
          setScanning(prev => ({ ...prev, [id]: false }))
          await loadConnections()
          if (expandedConnection === id) {
            await loadTables(id)
          }
        }
      }, 3000)
    } catch (err: any) {
      setError(err.message)
      setScanning(prev => ({ ...prev, [id]: false }))
    }
  }

  const testExistingConnection = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/data-connections/${id}/test`, { method: 'POST' })
      const data = await res.json()
      if (res.ok && data.success) {
        await loadConnections()
      } else {
        setError(data.message || 'Connection test failed')
      }
    } catch (err: any) {
      setError(err.message)
    }
  }

  // ============================================================================
  // HELPERS
  // ============================================================================
  const getTypeInfo = (type: string) => CONNECTION_TYPES.find(t => t.id === type) || { icon: '📁', name: type }
  
  const formatDate = (date?: string) => {
    if (!date) return 'Never'
    return new Date(date).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return '#10b981'
      case 'scanning': return '#fbbf24'
      case 'failed': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getQualityColor = (score: number) => {
    if (score >= 90) return '#10b981'
    if (score >= 70) return '#fbbf24'
    return '#ef4444'
  }

  // ============================================================================
  // RENDER
  // ============================================================================
  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingState}>
          <div style={styles.spinner} />
          <p>Loading data sources...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>🔌 Data Sources</h1>
          <p style={styles.subtitle}>
            Connect to databases and file storage to scan for ML-ready data
          </p>
        </div>
        <button onClick={() => setShowAddModal(true)} style={styles.primaryButton}>
          + Add Connection
        </button>
      </header>

      {error && (
        <div style={styles.errorBanner}>
          {error}
          <button onClick={() => setError(null)} style={styles.errorClose}>×</button>
        </div>
      )}

      {/* Main Content */}
      <main style={styles.main}>
        {connections.length === 0 ? (
          /* Empty State */
          <section style={styles.emptyState}>
            <div style={styles.emptyIcon}>🔌</div>
            <h2 style={styles.emptyTitle}>No Data Sources</h2>
            <p style={styles.emptyText}>
              Connect your databases to discover ML-ready tables and assess data quality.
            </p>
            <button onClick={() => setShowAddModal(true)} style={styles.primaryButton}>
              + Add Your First Connection
            </button>
          </section>
        ) : (
          /* Connection List */
          <div style={styles.connectionList}>
            {connections.map(conn => (
              <div key={conn.id} style={styles.connectionCard}>
                {/* Connection Header */}
                <div style={styles.connectionHeader}>
                  <div style={styles.connectionInfo}>
                    <span style={styles.connectionIcon}>{getTypeInfo(conn.connection_type).icon}</span>
                    <div>
                      <h3 style={styles.connectionName}>{conn.name}</h3>
                      <p style={styles.connectionMeta}>
                        {getTypeInfo(conn.connection_type).name} • {conn.host}:{conn.port}/{conn.database}
                      </p>
                    </div>
                  </div>
                  
                  <div style={styles.connectionStatus}>
                    <div style={{ ...styles.statusDot, backgroundColor: getStatusColor(conn.status) }} />
                    <span style={{ color: getStatusColor(conn.status), fontSize: '12px', textTransform: 'capitalize' }}>
                      {conn.status}
                    </span>
                  </div>
                </div>

                {/* Connection Stats */}
                <div style={styles.connectionStats}>
                  <div style={styles.statItem}>
                    <span style={styles.statValue}>{conn.tables_count}</span>
                    <span style={styles.statLabel}>Tables</span>
                  </div>
                  <div style={styles.statItem}>
                    <span style={styles.statValue}>{conn.total_rows.toLocaleString()}</span>
                    <span style={styles.statLabel}>Rows</span>
                  </div>
                  <div style={styles.statItem}>
                    <span style={styles.statValue}>{formatDate(conn.last_scan_at)}</span>
                    <span style={styles.statLabel}>Last Scan</span>
                  </div>
                </div>

                {/* Connection Actions */}
                <div style={styles.connectionActions}>
                  <button 
                    onClick={() => testExistingConnection(conn.id)} 
                    style={styles.actionBtn}
                  >
                    🔌 Test
                  </button>
                  <button 
                    onClick={() => scanConnection(conn.id)}
                    disabled={scanning[conn.id]}
                    style={{ ...styles.actionBtn, opacity: scanning[conn.id] ? 0.6 : 1 }}
                  >
                    {scanning[conn.id] ? '⏳ Scanning...' : '🔍 Scan'}
                  </button>
                  <button 
                    onClick={() => setExpandedConnection(expandedConnection === conn.id ? null : conn.id)}
                    style={{ ...styles.actionBtn, backgroundColor: expandedConnection === conn.id ? 'rgba(59, 130, 246, 0.2)' : undefined }}
                  >
                    📋 {expandedConnection === conn.id ? 'Hide' : 'View'} Tables
                  </button>
                  <button 
                    onClick={() => deleteConnection(conn.id)}
                    style={{ ...styles.actionBtn, color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                  >
                    🗑️
                  </button>
                </div>

                {/* Expanded Table List */}
                {expandedConnection === conn.id && (
                  <div style={styles.tableList}>
                    {loadingTables[conn.id] ? (
                      <div style={styles.tableLoading}>Loading tables...</div>
                    ) : !tables[conn.id] || tables[conn.id].length === 0 ? (
                      <div style={styles.tableLoading}>
                        {conn.tables_count > 0 
                          ? `Found ${conn.tables_count} tables. Loading...` 
                          : 'No tables scanned yet. Click "Scan" to discover tables.'}
                      </div>
                    ) : (
                      <table style={styles.table}>
                        <thead>
                          <tr>
                            <th style={styles.tableHeader}>Table</th>
                            <th style={styles.tableHeader}>Rows</th>
                            <th style={styles.tableHeader}>Columns</th>
                            <th style={styles.tableHeader}>Quality</th>
                            <th style={styles.tableHeader}>Issues</th>
                            <th style={styles.tableHeader}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tables[conn.id].map(table => (
                            <tr key={table.id} style={styles.tableRow}>
                              <td style={styles.tableCell}>
                                <strong style={{ color: '#f0f0f5' }}>{table.full_name}</strong>
                              </td>
                              <td style={styles.tableCell}>{table.row_count.toLocaleString()}</td>
                              <td style={styles.tableCell}>{table.column_count}</td>
                              <td style={styles.tableCell}>
                                <span style={{ 
                                  color: getQualityColor((table.completeness_score || 0) * 100),
                                  fontWeight: '600'
                                }}>
                                  {((table.completeness_score || 0) * 100).toFixed(0)}%
                                </span>
                              </td>
                              <td style={styles.tableCell}>
                                {(table.quality_issues?.length || 0) > 0 ? (
                                  <span style={{ color: '#fbbf24' }}>
                                    ⚠ {table.quality_issues.length}
                                  </span>
                                ) : (
                                  <span style={{ color: '#10b981' }}>✓</span>
                                )}
                              </td>
                              <td style={styles.tableCell}>
                                <button
                                  onClick={() => navigate(`/data-sources/tables/${table.id}`)}
                                  style={styles.exploreBtn}
                                >
                                  Explore →
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Quick Add Section */}
        <section style={styles.quickAddSection}>
          <h3 style={styles.quickAddTitle}>+ Add New Connection</h3>
          <div style={styles.quickAddTypes}>
            {CONNECTION_TYPES.map(type => (
              <button
                key={type.id}
                onClick={() => {
                  setForm({ ...DEFAULT_FORM, connection_type: type.id, port: type.defaultPort })
                  setFormStep('config')
                  setShowAddModal(true)
                }}
                style={styles.quickAddType}
              >
                <span style={styles.quickAddIcon}>{type.icon}</span>
                <span>{type.name}</span>
              </button>
            ))}
          </div>
        </section>
      </main>

      {/* Add Connection Modal */}
      {showAddModal && (
        <div style={styles.modalOverlay} onClick={() => setShowAddModal(false)}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={{ margin: 0, color: '#f0f0f5' }}>
                {formStep === 'type' ? '+ Add Connection' : `${getTypeInfo(form.connection_type).icon} ${getTypeInfo(form.connection_type).name} Connection`}
              </h2>
              <button onClick={() => { setShowAddModal(false); setFormStep('type'); setTestResult(null) }} style={styles.modalClose}>×</button>
            </div>

            <div style={styles.modalBody}>
              {formStep === 'type' ? (
                /* Type Selection */
                <div style={styles.typeGrid}>
                  {CONNECTION_TYPES.map(type => (
                    <button
                      key={type.id}
                      onClick={() => {
                        setForm({ ...DEFAULT_FORM, connection_type: type.id, port: type.defaultPort })
                        setFormStep('config')
                      }}
                      style={styles.typeCard}
                    >
                      <span style={{ fontSize: '32px' }}>{type.icon}</span>
                      <span style={{ fontWeight: '600', color: '#f0f0f5' }}>{type.name}</span>
                    </button>
                  ))}
                </div>
              ) : (
                /* Configuration Form */
                <div style={styles.form}>
                  <div style={styles.formRow}>
                    <label style={styles.formLabel}>Connection Name</label>
                    <input
                      type="text"
                      value={form.name}
                      onChange={e => setForm({ ...form, name: e.target.value })}
                      placeholder="My Database"
                      style={styles.formInput}
                    />
                  </div>

                  <div style={styles.formRow}>
                    <label style={styles.formLabel}>Description (optional)</label>
                    <input
                      type="text"
                      value={form.description}
                      onChange={e => setForm({ ...form, description: e.target.value })}
                      placeholder="Production analytics database"
                      style={styles.formInput}
                    />
                  </div>

                  <div style={styles.formGrid}>
                    <div style={styles.formRow}>
                      <label style={styles.formLabel}>Host</label>
                      <input
                        type="text"
                        value={form.host}
                        onChange={e => setForm({ ...form, host: e.target.value })}
                        placeholder="localhost"
                        style={styles.formInput}
                      />
                    </div>
                    <div style={styles.formRow}>
                      <label style={styles.formLabel}>Port</label>
                      <input
                        type="number"
                        value={form.port}
                        onChange={e => setForm({ ...form, port: parseInt(e.target.value) || 0 })}
                        style={styles.formInput}
                      />
                    </div>
                  </div>

                  <div style={styles.formRow}>
                    <label style={styles.formLabel}>Database</label>
                    <input
                      type="text"
                      value={form.database}
                      onChange={e => setForm({ ...form, database: e.target.value })}
                      placeholder="mydb"
                      style={styles.formInput}
                    />
                  </div>

                  <div style={styles.formGrid}>
                    <div style={styles.formRow}>
                      <label style={styles.formLabel}>Username</label>
                      <input
                        type="text"
                        value={form.username}
                        onChange={e => setForm({ ...form, username: e.target.value })}
                        placeholder="admin"
                        style={styles.formInput}
                      />
                    </div>
                    <div style={styles.formRow}>
                      <label style={styles.formLabel}>Password</label>
                      <input
                        type="password"
                        value={form.password}
                        onChange={e => setForm({ ...form, password: e.target.value })}
                        placeholder="••••••••"
                        style={styles.formInput}
                      />
                    </div>
                  </div>

                  {/* Test Result */}
                  {testResult && (
                    <div style={{
                      ...styles.testResult,
                      backgroundColor: testResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      borderColor: testResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
                      color: testResult.success ? '#10b981' : '#ef4444'
                    }}>
                      {testResult.success ? '✓' : '✗'} {testResult.message}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div style={styles.modalFooter}>
              {formStep === 'config' && (
                <button onClick={() => setFormStep('type')} style={styles.modalSecondary}>
                  ← Back
                </button>
              )}
              <div style={{ flex: 1 }} />
              <button onClick={() => { setShowAddModal(false); setFormStep('type'); setTestResult(null) }} style={styles.modalCancel}>
                Cancel
              </button>
              {formStep === 'config' && (
                <>
                  <button 
                    onClick={testConnection} 
                    disabled={testing || !form.host || !form.database}
                    style={{ ...styles.modalSecondary, opacity: testing || !form.host || !form.database ? 0.6 : 1 }}
                  >
                    {testing ? 'Testing...' : '🔌 Test'}
                  </button>
                  <button 
                    onClick={saveConnection}
                    disabled={saving || !form.name || !form.host || !form.database}
                    style={{ ...styles.modalSubmit, opacity: saving || !form.name || !form.host || !form.database ? 0.6 : 1 }}
                  >
                    {saving ? 'Saving...' : 'Save Connection'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// STYLES
// ============================================================================
const styles: Record<string, React.CSSProperties> = {
  container: { minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  
  // Header
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 32px', borderBottom: '1px solid rgba(255,255,255,0.1)', flexWrap: 'wrap', gap: '16px' },
  title: { fontSize: '24px', fontWeight: '700', margin: 0 },
  subtitle: { fontSize: '13px', color: '#9ca3af', margin: '4px 0 0 0' },
  primaryButton: { padding: '10px 20px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '8px', color: '#fff', fontWeight: '600', fontSize: '14px', cursor: 'pointer' },
  
  // Main
  main: { padding: '24px 32px', maxWidth: '1200px', margin: '0 auto' },
  
  // Connection List
  connectionList: { display: 'flex', flexDirection: 'column', gap: '16px' },
  connectionCard: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.1)' },
  connectionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' },
  connectionInfo: { display: 'flex', alignItems: 'center', gap: '12px' },
  connectionIcon: { fontSize: '28px' },
  connectionName: { fontSize: '16px', fontWeight: '600', margin: 0, color: '#f0f0f5' },
  connectionMeta: { fontSize: '12px', color: '#6b7280', margin: '2px 0 0 0' },
  connectionStatus: { display: 'flex', alignItems: 'center', gap: '6px' },
  statusDot: { width: '8px', height: '8px', borderRadius: '50%' },
  
  // Stats
  connectionStats: { display: 'flex', gap: '24px', padding: '12px 0', borderTop: '1px solid rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.05)', marginBottom: '12px' },
  statItem: { display: 'flex', flexDirection: 'column', gap: '2px' },
  statValue: { fontSize: '16px', fontWeight: '600', color: '#f0f0f5' },
  statLabel: { fontSize: '11px', color: '#6b7280' },
  
  // Actions
  connectionActions: { display: 'flex', gap: '8px', flexWrap: 'wrap' },
  actionBtn: { padding: '6px 12px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#d1d5db', fontSize: '12px', cursor: 'pointer' },
  
  // Table List
  tableList: { marginTop: '16px', backgroundColor: '#0f0f14', borderRadius: '8px', overflow: 'hidden' },
  tableLoading: { padding: '24px', textAlign: 'center', color: '#6b7280', fontSize: '13px' },
  table: { width: '100%', borderCollapse: 'collapse' },
  tableHeader: { textAlign: 'left', padding: '10px 14px', fontSize: '11px', color: '#6b7280', fontWeight: '500', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  tableRow: { borderBottom: '1px solid rgba(255,255,255,0.05)' },
  tableCell: { padding: '10px 14px', fontSize: '12px', color: '#9ca3af' },
  exploreBtn: { padding: '4px 10px', backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', borderRadius: '4px', color: '#60a5fa', fontSize: '11px', cursor: 'pointer' },
  
  // Quick Add
  quickAddSection: { marginTop: '32px', backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px dashed rgba(255,255,255,0.2)' },
  quickAddTitle: { fontSize: '14px', fontWeight: '600', color: '#9ca3af', margin: '0 0 16px 0' },
  quickAddTypes: { display: 'flex', gap: '12px', flexWrap: 'wrap' },
  quickAddType: { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#d1d5db', fontSize: '13px', cursor: 'pointer' },
  quickAddIcon: { fontSize: '18px' },
  
  // Empty
  emptyState: { textAlign: 'center', padding: '60px 32px', backgroundColor: '#12121a', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.2)' },
  emptyIcon: { fontSize: '48px', marginBottom: '12px' },
  emptyTitle: { fontSize: '20px', fontWeight: '600', margin: '0 0 8px 0' },
  emptyText: { fontSize: '13px', color: '#9ca3af', margin: '0 0 20px 0', maxWidth: '360px', marginLeft: 'auto', marginRight: 'auto' },
  
  // Modal
  modalOverlay: { position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { backgroundColor: '#12121a', borderRadius: '12px', width: '90%', maxWidth: '520px', border: '1px solid rgba(255,255,255,0.1)' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  modalClose: { background: 'none', border: 'none', color: '#6b7280', fontSize: '20px', cursor: 'pointer' },
  modalBody: { padding: '20px' },
  modalFooter: { display: 'flex', gap: '10px', padding: '16px 20px', borderTop: '1px solid rgba(255,255,255,0.1)' },
  modalCancel: { padding: '8px 16px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', cursor: 'pointer' },
  modalSecondary: { padding: '8px 16px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#d1d5db', cursor: 'pointer' },
  modalSubmit: { padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: '600', cursor: 'pointer' },
  
  // Type Grid
  typeGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '12px' },
  typeCard: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '20px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', cursor: 'pointer' },
  
  // Form
  form: { display: 'flex', flexDirection: 'column', gap: '16px' },
  formRow: { display: 'flex', flexDirection: 'column', gap: '6px' },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  formLabel: { fontSize: '12px', fontWeight: '500', color: '#9ca3af' },
  formInput: { padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '14px' },
  testResult: { padding: '10px 14px', borderRadius: '6px', border: '1px solid', fontSize: '13px' },
  
  // Loading
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' },
  spinner: { width: '32px', height: '32px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' },
  
  // Error
  errorBanner: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 32px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontSize: '13px' },
  errorClose: { background: 'none', border: 'none', color: '#ef4444', fontSize: '18px', cursor: 'pointer' },
}
