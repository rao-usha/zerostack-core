import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

// ============================================================================
// TYPES
// ============================================================================
interface Notebook {
  id: string
  name: string
  description?: string
  folder: string
  tags: string[]
  default_connection_id?: string
  cell_count: number
  created_at: string
  updated_at: string
}

interface DataConnection {
  id: string
  name: string
  connection_type: string
  database: string
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function NotebooksListPage() {
  const navigate = useNavigate()
  
  // State
  const [notebooks, setNotebooks] = useState<Notebook[]>([])
  const [connections, setConnections] = useState<DataConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newConnection, setNewConnection] = useState('')
  const [creating, setCreating] = useState(false)

  // ============================================================================
  // DATA LOADING
  // ============================================================================
  const loadNotebooks = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/notebooks')
      if (!res.ok) throw new Error('Failed to load notebooks')
      const data = await res.json()
      setNotebooks(data.notebooks || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const loadConnections = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/data-connections')
      if (res.ok) {
        const data = await res.json()
        setConnections(data.connections || [])
      }
    } catch (err) {
      console.error('Failed to load connections:', err)
    }
  }, [])

  useEffect(() => {
    loadNotebooks()
    loadConnections()
  }, [loadNotebooks, loadConnections])

  // ============================================================================
  // ACTIONS
  // ============================================================================
  const createNotebook = async () => {
    if (!newName.trim()) return
    
    setCreating(true)
    try {
      const res = await fetch('/api/v1/notebooks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newName,
          default_connection_id: newConnection || undefined
        })
      })
      if (!res.ok) throw new Error('Failed to create notebook')
      const data = await res.json()
      navigate(`/notebooks/${data.id}`)
    } catch (err: any) {
      setError(err.message)
      setCreating(false)
    }
  }

  const deleteNotebook = async (id: string, name: string) => {
    if (!confirm(`Delete notebook "${name}"? This cannot be undone.`)) return
    
    try {
      const res = await fetch(`/api/v1/notebooks/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete')
      await loadNotebooks()
    } catch (err: any) {
      setError(err.message)
    }
  }

  // ============================================================================
  // HELPERS
  // ============================================================================
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getConnectionName = (id?: string) => {
    if (!id) return null
    const conn = connections.find(c => c.id === id)
    return conn ? conn.name : null
  }

  // ============================================================================
  // RENDER
  // ============================================================================
  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingState}>
          <div style={styles.spinner} />
          <p>Loading notebooks...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>📓 SQL Notebooks</h1>
          <p style={styles.subtitle}>
            Query your data sources, transform data, and save datasets
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} style={styles.primaryButton}>
          + New Notebook
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
        {notebooks.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>📓</div>
            <h2 style={styles.emptyTitle}>No Notebooks</h2>
            <p style={styles.emptyText}>
              Create your first notebook to start querying data and building datasets.
            </p>
            <button onClick={() => setShowCreate(true)} style={styles.primaryButton}>
              + Create Your First Notebook
            </button>
          </div>
        ) : (
          <div style={styles.notebookGrid}>
            {notebooks.map(nb => (
              <div
                key={nb.id}
                style={styles.notebookCard}
                onClick={() => navigate(`/notebooks/${nb.id}`)}
              >
                <div style={styles.cardHeader}>
                  <h3 style={styles.cardTitle}>📓 {nb.name}</h3>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteNotebook(nb.id, nb.name) }}
                    style={styles.deleteBtn}
                  >
                    🗑
                  </button>
                </div>
                
                {nb.description && (
                  <p style={styles.cardDescription}>{nb.description}</p>
                )}
                
                <div style={styles.cardStats}>
                  <span>{nb.cell_count} cells</span>
                  {getConnectionName(nb.default_connection_id) && (
                    <>
                      <span>•</span>
                      <span>🔌 {getConnectionName(nb.default_connection_id)}</span>
                    </>
                  )}
                </div>
                
                <div style={styles.cardFooter}>
                  <span style={styles.cardDate}>Updated {formatDate(nb.updated_at)}</span>
                </div>
              </div>
            ))}
            
            {/* New Notebook Card */}
            <div
              style={{ ...styles.notebookCard, ...styles.newCard }}
              onClick={() => setShowCreate(true)}
            >
              <div style={styles.newCardContent}>
                <span style={styles.newCardIcon}>+</span>
                <span>New Notebook</span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showCreate && (
        <div style={styles.modalOverlay} onClick={() => setShowCreate(false)}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <h2 style={{ margin: '0 0 16px 0', color: '#f0f0f5' }}>+ New Notebook</h2>
            
            <div style={styles.formField}>
              <label style={styles.formLabel}>Name</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="My Analysis"
                style={styles.formInput}
                autoFocus
              />
            </div>
            
            <div style={styles.formField}>
              <label style={styles.formLabel}>Default Data Connection</label>
              <select
                value={newConnection}
                onChange={(e) => setNewConnection(e.target.value)}
                style={styles.formSelect}
              >
                <option value="">Select later...</option>
                {connections.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.database})
                  </option>
                ))}
              </select>
            </div>
            
            <div style={styles.modalActions}>
              <button onClick={() => setShowCreate(false)} style={styles.modalCancel}>
                Cancel
              </button>
              <button
                onClick={createNotebook}
                disabled={!newName.trim() || creating}
                style={{ ...styles.modalSubmit, opacity: !newName.trim() || creating ? 0.6 : 1 }}
              >
                {creating ? 'Creating...' : 'Create Notebook'}
              </button>
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
  
  // Notebook Grid
  notebookGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' },
  notebookCard: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', transition: 'border-color 0.2s, transform 0.2s' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' },
  cardTitle: { fontSize: '16px', fontWeight: '600', margin: 0, color: '#f0f0f5' },
  deleteBtn: { padding: '4px 8px', backgroundColor: 'transparent', border: 'none', cursor: 'pointer', opacity: 0.5, fontSize: '14px' },
  cardDescription: { fontSize: '13px', color: '#9ca3af', margin: '0 0 12px 0', lineHeight: '1.4' },
  cardStats: { display: 'flex', gap: '8px', fontSize: '12px', color: '#6b7280', marginBottom: '12px' },
  cardFooter: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  cardDate: { fontSize: '11px', color: '#6b7280' },
  
  // New Card
  newCard: { border: '2px dashed rgba(59, 130, 246, 0.3)', backgroundColor: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '150px' },
  newCardContent: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: '#60a5fa' },
  newCardIcon: { fontSize: '32px' },
  
  // Empty State
  emptyState: { textAlign: 'center', padding: '60px 32px', backgroundColor: '#12121a', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.2)' },
  emptyIcon: { fontSize: '48px', marginBottom: '12px' },
  emptyTitle: { fontSize: '20px', fontWeight: '600', margin: '0 0 8px 0' },
  emptyText: { fontSize: '13px', color: '#9ca3af', margin: '0 0 20px 0', maxWidth: '360px', marginLeft: 'auto', marginRight: 'auto' },
  
  // Loading/Error
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' },
  spinner: { width: '32px', height: '32px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' },
  errorBanner: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 32px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontSize: '13px' },
  errorClose: { background: 'none', border: 'none', color: '#ef4444', fontSize: '18px', cursor: 'pointer' },
  
  // Modal
  modalOverlay: { position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { backgroundColor: '#12121a', borderRadius: '12px', padding: '24px', width: '90%', maxWidth: '450px', border: '1px solid rgba(255,255,255,0.1)' },
  formField: { marginBottom: '16px' },
  formLabel: { display: 'block', fontSize: '12px', fontWeight: '500', color: '#9ca3af', marginBottom: '6px' },
  formInput: { width: '100%', padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '14px' },
  formSelect: { width: '100%', padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '14px' },
  modalActions: { display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' },
  modalCancel: { padding: '10px 16px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', cursor: 'pointer' },
  modalSubmit: { padding: '10px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: '600', cursor: 'pointer' }
}
