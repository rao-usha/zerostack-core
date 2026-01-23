import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

// ============================================================================
// TYPES
// ============================================================================
interface Dataset {
  id: string
  name: string
  description?: string
  source_notebook_id?: string
  source_cell_id?: string
  source_query?: string
  storage_uri?: string
  storage_format: string
  row_count?: number
  column_count?: number
  size_bytes?: number
  columns: { name: string; type: string }[]
  created_by?: string
  created_at: string
  updated_at: string
}

interface PreviewData {
  columns: string[]
  rows: Record<string, any>[]
  total_rows: number
  showing: number
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function DatasetsPage() {
  const navigate = useNavigate()
  
  // State
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null)
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [downloading, setDownloading] = useState<string | null>(null)

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  const loadDatasets = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      
      const res = await fetch(`/api/v1/notebooks/datasets?${params}`)
      if (!res.ok) throw new Error('Failed to load datasets')
      const data = await res.json()
      setDatasets(data.datasets || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => {
    loadDatasets()
  }, [loadDatasets])

  const loadPreview = async (dataset: Dataset) => {
    setSelectedDataset(dataset)
    setPreviewLoading(true)
    setPreviewData(null)
    
    try {
      const res = await fetch(`/api/v1/notebooks/datasets/${dataset.id}/preview?limit=50`)
      if (!res.ok) throw new Error('Failed to load preview')
      const data = await res.json()
      setPreviewData(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setPreviewLoading(false)
    }
  }

  // ============================================================================
  // ACTIONS
  // ============================================================================
  const downloadDataset = async (dataset: Dataset) => {
    setDownloading(dataset.id)
    try {
      const res = await fetch(`/api/v1/notebooks/datasets/${dataset.id}/download`)
      if (!res.ok) throw new Error('Failed to get download URL')
      const data = await res.json()
      
      // Open download URL in new tab
      window.open(data.download_url, '_blank')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setDownloading(null)
    }
  }

  const deleteDataset = async (dataset: Dataset) => {
    if (!confirm(`Delete dataset "${dataset.name}"? This will also delete the stored data.`)) return
    
    try {
      const res = await fetch(`/api/v1/notebooks/datasets/${dataset.id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete')
      
      if (selectedDataset?.id === dataset.id) {
        setSelectedDataset(null)
        setPreviewData(null)
      }
      await loadDatasets()
    } catch (err: any) {
      setError(err.message)
    }
  }

  // ============================================================================
  // HELPERS
  // ============================================================================
  const formatBytes = (bytes?: number) => {
    if (!bytes) return '—'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatNumber = (n?: number) => {
    if (!n) return '—'
    return n.toLocaleString()
  }

  // ============================================================================
  // RENDER
  // ============================================================================
  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingState}>
          <div style={styles.spinner} />
          <p>Loading datasets...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>📊 Datasets</h1>
          <p style={styles.subtitle}>
            Browse and manage datasets created from SQL notebooks
          </p>
        </div>
        
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search datasets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <button onClick={() => navigate('/notebooks')} style={styles.secondaryButton}>
            📓 Go to Notebooks
          </button>
        </div>
      </header>

      {error && (
        <div style={styles.errorBanner}>
          {error}
          <button onClick={() => setError(null)} style={styles.errorClose}>×</button>
        </div>
      )}

      {/* Main Content */}
      <main style={styles.main}>
        <div style={styles.layout}>
          {/* Dataset List */}
          <div style={styles.listPanel}>
            <div style={styles.panelHeader}>
              <span>{datasets.length} dataset{datasets.length !== 1 ? 's' : ''}</span>
            </div>
            
            {datasets.length === 0 ? (
              <div style={styles.emptyState}>
                <div style={styles.emptyIcon}>📊</div>
                <p>No datasets yet</p>
                <p style={styles.emptySubtext}>
                  Create datasets by saving SQL query results from notebooks
                </p>
                <button onClick={() => navigate('/notebooks')} style={styles.primaryButton}>
                  Open Notebooks
                </button>
              </div>
            ) : (
              <div style={styles.datasetList}>
                {datasets.map(ds => (
                  <div
                    key={ds.id}
                    style={{
                      ...styles.datasetCard,
                      borderColor: selectedDataset?.id === ds.id ? '#3b82f6' : 'rgba(255,255,255,0.1)'
                    }}
                    onClick={() => loadPreview(ds)}
                  >
                    <div style={styles.cardHeader}>
                      <h3 style={styles.cardTitle}>{ds.name}</h3>
                      <span style={styles.formatBadge}>{ds.storage_format?.toUpperCase()}</span>
                    </div>
                    
                    {ds.description && (
                      <p style={styles.cardDescription}>{ds.description}</p>
                    )}
                    
                    <div style={styles.cardStats}>
                      <span>{formatNumber(ds.row_count)} rows</span>
                      <span>•</span>
                      <span>{ds.column_count} cols</span>
                      <span>•</span>
                      <span>{formatBytes(ds.size_bytes)}</span>
                    </div>
                    
                    <div style={styles.cardFooter}>
                      <span style={styles.cardDate}>{formatDate(ds.created_at)}</span>
                      <div style={styles.cardActions}>
                        <button
                          onClick={(e) => { e.stopPropagation(); downloadDataset(ds) }}
                          disabled={downloading === ds.id || !ds.storage_uri}
                          style={styles.iconBtn}
                          title="Download"
                        >
                          {downloading === ds.id ? '⏳' : '⬇'}
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); deleteDataset(ds) }}
                          style={{ ...styles.iconBtn, color: '#ef4444' }}
                          title="Delete"
                        >
                          🗑
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Preview Panel */}
          <div style={styles.previewPanel}>
            {selectedDataset ? (
              <>
                <div style={styles.previewHeader}>
                  <div>
                    <h2 style={styles.previewTitle}>{selectedDataset.name}</h2>
                    <p style={styles.previewSubtitle}>
                      {formatNumber(selectedDataset.row_count)} rows • {selectedDataset.column_count} columns • {formatBytes(selectedDataset.size_bytes)}
                    </p>
                  </div>
                  <button
                    onClick={() => downloadDataset(selectedDataset)}
                    disabled={downloading === selectedDataset.id || !selectedDataset.storage_uri}
                    style={styles.downloadBtn}
                  >
                    {downloading === selectedDataset.id ? 'Getting URL...' : `⬇ Download ${selectedDataset.storage_format?.toUpperCase()}`}
                  </button>
                </div>

                {/* Source Query */}
                {selectedDataset.source_query && (
                  <div style={styles.querySection}>
                    <h4 style={styles.sectionTitle}>Source Query</h4>
                    <pre style={styles.queryCode}>{selectedDataset.source_query}</pre>
                  </div>
                )}

                {/* Data Preview */}
                <div style={styles.dataSection}>
                  <h4 style={styles.sectionTitle}>
                    Data Preview 
                    {previewData && <span style={styles.previewCount}> (showing {previewData.showing} of {formatNumber(previewData.total_rows)})</span>}
                  </h4>
                  
                  {previewLoading ? (
                    <div style={styles.loadingPreview}>
                      <div style={styles.spinner} />
                      Loading preview...
                    </div>
                  ) : previewData ? (
                    <div style={styles.tableContainer}>
                      <table style={styles.table}>
                        <thead>
                          <tr>
                            {previewData.columns.map((col, i) => (
                              <th key={i} style={styles.th}>{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewData.rows.map((row, i) => (
                            <tr key={i} style={styles.tr}>
                              {previewData.columns.map((col, j) => (
                                <td key={j} style={styles.td}>
                                  {row[col] === null ? (
                                    <em style={{ color: '#6b7280' }}>null</em>
                                  ) : typeof row[col] === 'object' ? (
                                    JSON.stringify(row[col]).slice(0, 50)
                                  ) : (
                                    String(row[col]).slice(0, 100)
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div style={styles.noPreview}>Click a dataset to preview</div>
                  )}
                </div>

                {/* Columns */}
                {selectedDataset.columns && selectedDataset.columns.length > 0 && (
                  <div style={styles.columnsSection}>
                    <h4 style={styles.sectionTitle}>Columns ({selectedDataset.columns.length})</h4>
                    <div style={styles.columnsList}>
                      {selectedDataset.columns.map((col, i) => (
                        <div key={i} style={styles.columnItem}>
                          <span style={styles.columnName}>{col.name}</span>
                          <span style={styles.columnType}>{col.type}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div style={styles.noSelection}>
                <div style={styles.noSelectionIcon}>👈</div>
                <p>Select a dataset to preview</p>
              </div>
            )}
          </div>
        </div>
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
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 32px', borderBottom: '1px solid rgba(255,255,255,0.1)', flexWrap: 'wrap', gap: '16px' },
  title: { fontSize: '24px', fontWeight: '700', margin: 0 },
  subtitle: { fontSize: '13px', color: '#9ca3af', margin: '4px 0 0 0' },
  headerActions: { display: 'flex', gap: '12px', alignItems: 'center' },
  searchInput: { padding: '8px 12px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '13px', width: '200px' },
  primaryButton: { padding: '10px 20px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '8px', color: '#fff', fontWeight: '600', fontSize: '14px', cursor: 'pointer' },
  secondaryButton: { padding: '10px 20px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px', color: '#9ca3af', fontSize: '14px', cursor: 'pointer' },
  
  // Main Layout
  main: { padding: '24px 32px' },
  layout: { display: 'grid', gridTemplateColumns: '380px 1fr', gap: '24px', alignItems: 'start' },
  
  // List Panel
  listPanel: { backgroundColor: '#12121a', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', overflow: 'hidden' },
  panelHeader: { padding: '12px 16px', borderBottom: '1px solid rgba(255,255,255,0.1)', fontSize: '12px', color: '#6b7280' },
  datasetList: { maxHeight: 'calc(100vh - 260px)', overflow: 'auto' },
  datasetCard: { padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)', cursor: 'pointer', borderLeft: '3px solid transparent', transition: 'background-color 0.15s' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' },
  cardTitle: { fontSize: '14px', fontWeight: '600', margin: 0 },
  formatBadge: { fontSize: '10px', padding: '2px 6px', backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', borderRadius: '4px' },
  cardDescription: { fontSize: '12px', color: '#9ca3af', margin: '0 0 8px 0', lineHeight: '1.4' },
  cardStats: { display: 'flex', gap: '6px', fontSize: '11px', color: '#6b7280', marginBottom: '8px' },
  cardFooter: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  cardDate: { fontSize: '11px', color: '#6b7280' },
  cardActions: { display: 'flex', gap: '4px' },
  iconBtn: { width: '24px', height: '24px', backgroundColor: 'transparent', border: 'none', cursor: 'pointer', fontSize: '12px', opacity: 0.6 },
  
  // Preview Panel
  previewPanel: { backgroundColor: '#12121a', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', padding: '20px', minHeight: '500px' },
  previewHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' },
  previewTitle: { fontSize: '18px', fontWeight: '600', margin: 0 },
  previewSubtitle: { fontSize: '12px', color: '#9ca3af', margin: '4px 0 0 0' },
  downloadBtn: { padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontSize: '13px', fontWeight: '500', cursor: 'pointer' },
  
  // Sections
  querySection: { marginBottom: '20px' },
  dataSection: { marginBottom: '20px' },
  columnsSection: { marginBottom: '20px' },
  sectionTitle: { fontSize: '12px', color: '#9ca3af', margin: '0 0 8px 0', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.5px' },
  previewCount: { fontWeight: '400', textTransform: 'none', letterSpacing: '0' },
  queryCode: { backgroundColor: '#0f0f14', padding: '12px', borderRadius: '6px', fontSize: '12px', fontFamily: 'monospace', color: '#d1d5db', overflow: 'auto', maxHeight: '120px', margin: 0, whiteSpace: 'pre-wrap' },
  
  // Table
  tableContainer: { maxHeight: '300px', overflow: 'auto', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.1)' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: '12px' },
  th: { textAlign: 'left', padding: '8px 10px', backgroundColor: '#0a0a0f', color: '#9ca3af', fontWeight: '500', position: 'sticky', top: 0 },
  tr: { borderBottom: '1px solid rgba(255,255,255,0.05)' },
  td: { padding: '6px 10px', color: '#d1d5db', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  
  // Columns List
  columnsList: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '6px' },
  columnItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', backgroundColor: '#0f0f14', borderRadius: '4px' },
  columnName: { fontSize: '12px', color: '#f0f0f5' },
  columnType: { fontSize: '10px', color: '#6b7280' },
  
  // States
  emptyState: { textAlign: 'center', padding: '60px 32px' },
  emptyIcon: { fontSize: '48px', marginBottom: '12px' },
  emptySubtext: { fontSize: '12px', color: '#6b7280', marginTop: '4px', marginBottom: '16px' },
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' },
  spinner: { width: '24px', height: '24px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' },
  loadingPreview: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px', color: '#9ca3af', fontSize: '13px' },
  noPreview: { padding: '40px', textAlign: 'center', color: '#6b7280', fontSize: '13px' },
  noSelection: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '400px', color: '#6b7280' },
  noSelectionIcon: { fontSize: '32px', marginBottom: '12px' },
  
  // Error
  errorBanner: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 32px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontSize: '13px' },
  errorClose: { background: 'none', border: 'none', color: '#ef4444', fontSize: '18px', cursor: 'pointer' }
}
