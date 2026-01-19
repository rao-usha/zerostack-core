import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  FileText,
  Calendar,
  Database,
  Eye,
  Upload,
  CheckCircle2,
  Clock,
  Hash,
} from 'lucide-react'
import {
  getFileAssetDetail,
  previewFileTable,
  publishFileTable,
  FileAssetDetail as FileAssetDetailType,
  FileTable,
} from '../api/client'
import DataTable from '../components/DataTable'
import { useToast } from '../contexts/ToastContext'

export default function FileAssetDetail() {
  const { assetId } = useParams<{ assetId: string }>()
  const navigate = useNavigate()
  const toast = useToast()

  const [detail, setDetail] = useState<FileAssetDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'versions' | 'tables'>('tables')
  
  // Table preview state
  const [selectedTable, setSelectedTable] = useState<FileTable | null>(null)
  const [previewData, setPreviewData] = useState<any>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [publishing, setPublishing] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (assetId) {
      loadDetail()
    }
  }, [assetId])

  const loadDetail = async () => {
    try {
      setLoading(true)
      const data = await getFileAssetDetail(assetId!)
      setDetail(data)
      
      // Auto-select first table if available
      if (data.latest_tables.length > 0 && !selectedTable) {
        handleTableSelect(data.latest_tables[0])
      }
    } catch (err) {
      toast.error('Failed to load asset details')
    } finally {
      setLoading(false)
    }
  }

  const handleTableSelect = async (table: FileTable) => {
    setSelectedTable(table)
    setLoadingPreview(true)
    try {
      const data = await previewFileTable(table.id, 100, 0)
      setPreviewData(data)
    } catch (err) {
      toast.error('Failed to load table preview')
    } finally {
      setLoadingPreview(false)
    }
  }

  const handlePublish = async (tableId: string) => {
    setPublishing(prev => ({ ...prev, [tableId]: true }))
    try {
      await publishFileTable(tableId)
      await loadDetail() // Reload to get updated publish status
      toast.success('Table published successfully')
    } catch (err) {
      toast.error('Failed to publish table')
    } finally {
      setPublishing(prev => ({ ...prev, [tableId]: false }))
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  if (loading) {
    return (
      <div style={{
        padding: '2rem',
        backgroundColor: '#0f0f17',
        minHeight: '100vh',
        color: '#f0f0f5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        Loading...
      </div>
    )
  }

  if (!detail) {
    return (
      <div style={{
        padding: '2rem',
        backgroundColor: '#0f0f17',
        minHeight: '100vh',
        color: '#f0f0f5',
      }}>
        <p>File not found</p>
      </div>
    )
  }

  const { asset, versions, latest_tables } = detail

  return (
    <div style={{
      padding: '2rem',
      backgroundColor: '#0f0f17',
      minHeight: '100vh',
      color: '#f0f0f5'
    }}>
      {/* Back Button */}
      <button
        onClick={() => navigate('/files/inventory')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.5rem 1rem',
          backgroundColor: 'transparent',
          color: '#a8d8ff',
          border: '1px solid rgba(168, 216, 255, 0.3)',
          borderRadius: '0.5rem',
          cursor: 'pointer',
          marginBottom: '2rem',
        }}
      >
        <ArrowLeft size={20} />
        Back to Inventory
      </button>

      {/* File Header */}
      <div style={{
        padding: '2rem',
        backgroundColor: '#1a1a24',
        border: '1px solid rgba(168, 216, 255, 0.2)',
        borderRadius: '0.75rem',
        marginBottom: '2rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'start', gap: '1rem' }}>
          <FileText size={48} style={{ color: '#a8d8ff' }} />
          <div style={{ flex: 1 }}>
            <h1 style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              marginBottom: '0.5rem',
              color: '#f0f0f5'
            }}>
              {asset.file_name}
            </h1>
            <p style={{ color: '#8ab3cc', marginBottom: '1rem' }}>
              {asset.location_name} • {asset.relative_path}
            </p>

            {/* Stats Grid */}
            {asset.latest_version && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '1rem',
                marginTop: '1.5rem',
              }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#b0b8c0', marginBottom: '0.25rem' }}>
                    File Size
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#f0f0f5' }}>
                    {formatFileSize(asset.latest_version.size_bytes)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#b0b8c0', marginBottom: '0.25rem' }}>
                    Total Rows
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#f0f0f5' }}>
                    {asset.latest_version.row_count_estimate?.toLocaleString() || 'N/A'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#b0b8c0', marginBottom: '0.25rem' }}>
                    Tables/Sheets
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#f0f0f5' }}>
                    {asset.latest_version.table_count}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#b0b8c0', marginBottom: '0.25rem' }}>
                    Versions
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#f0f0f5' }}>
                    {asset.version_count}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        marginBottom: '1.5rem',
        borderBottom: '1px solid rgba(168, 216, 255, 0.2)',
      }}>
        <button
          onClick={() => setActiveTab('tables')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: 'transparent',
            color: activeTab === 'tables' ? '#a8d8ff' : '#b0b8c0',
            border: 'none',
            borderBottom: activeTab === 'tables' ? '2px solid #a8d8ff' : '2px solid transparent',
            cursor: 'pointer',
            fontWeight: '600',
          }}
        >
          Tables
        </button>
        <button
          onClick={() => setActiveTab('versions')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: 'transparent',
            color: activeTab === 'versions' ? '#a8d8ff' : '#b0b8c0',
            border: 'none',
            borderBottom: activeTab === 'versions' ? '2px solid #a8d8ff' : '2px solid transparent',
            cursor: 'pointer',
            fontWeight: '600',
          }}
        >
          Version History
        </button>
      </div>

      {/* Tables Tab */}
      {activeTab === 'tables' && (
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          {/* Table List */}
          <div style={{ width: '300px', flexShrink: 0 }}>
            <h3 style={{
              fontSize: '1rem',
              fontWeight: '600',
              marginBottom: '1rem',
              color: '#f0f0f5'
            }}>
              Available Tables
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {latest_tables.map(table => (
                <div
                  key={table.id}
                  onClick={() => handleTableSelect(table)}
                  style={{
                    padding: '1rem',
                    backgroundColor: selectedTable?.id === table.id
                      ? 'rgba(168, 216, 255, 0.15)'
                      : '#1a1a24',
                    border: selectedTable?.id === table.id
                      ? '1px solid #a8d8ff'
                      : '1px solid rgba(168, 216, 255, 0.2)',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    if (selectedTable?.id !== table.id) {
                      e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.05)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedTable?.id !== table.id) {
                      e.currentTarget.style.backgroundColor = '#1a1a24'
                    }
                  }}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '0.5rem',
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                    }}>
                      <Database size={16} style={{ color: '#a8d8ff' }} />
                      <span style={{ fontWeight: '600', color: '#f0f0f5' }}>
                        {table.table_name}
                      </span>
                    </div>
                    {table.is_published && (
                      <CheckCircle2 size={16} style={{ color: '#22c55e' }} />
                    )}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#b0b8c0' }}>
                    {table.row_count.toLocaleString()} rows × {table.column_count} cols
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Table Preview */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {selectedTable ? (
              <div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem',
                }}>
                  <h3 style={{
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: '#f0f0f5',
                  }}>
                    {selectedTable.table_name}
                  </h3>
                  {!selectedTable.is_published ? (
                    <button
                      onClick={() => handlePublish(selectedTable.id)}
                      disabled={publishing[selectedTable.id]}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.75rem 1.5rem',
                        backgroundColor: '#a8d8ff',
                        color: '#0f0f17',
                        border: 'none',
                        borderRadius: '0.5rem',
                        fontWeight: '600',
                        cursor: publishing[selectedTable.id] ? 'not-allowed' : 'pointer',
                        opacity: publishing[selectedTable.id] ? 0.6 : 1,
                      }}
                    >
                      <Upload size={16} />
                      {publishing[selectedTable.id] ? 'Publishing...' : 'Publish to Datasets'}
                    </button>
                  ) : (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.75rem 1.5rem',
                      backgroundColor: 'rgba(34, 197, 94, 0.15)',
                      border: '1px solid rgba(34, 197, 94, 0.3)',
                      borderRadius: '0.5rem',
                      color: '#22c55e',
                      fontWeight: '600',
                    }}>
                      <CheckCircle2 size={16} />
                      Published
                    </div>
                  )}
                </div>

                {loadingPreview ? (
                  <div style={{
                    textAlign: 'center',
                    padding: '4rem',
                    backgroundColor: '#1a1a24',
                    borderRadius: '0.75rem',
                    color: '#b0b8c0',
                  }}>
                    Loading preview...
                  </div>
                ) : previewData ? (
                  <div>
                    <DataTable
                      columns={previewData.columns.map((col: any) => ({
                        header: col.name,
                        accessorKey: col.name,
                      }))}
                      data={previewData.rows.map((row: any[]) => {
                        const obj: any = {}
                        previewData.columns.forEach((col: any, idx: number) => {
                          obj[col.name] = row[idx]
                        })
                        return obj
                      })}
                    />
                    <div style={{
                      marginTop: '1rem',
                      fontSize: '0.875rem',
                      color: '#b0b8c0',
                    }}>
                      Showing first {previewData.rows.length} of {previewData.total_rows.toLocaleString()} rows
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '4rem',
                backgroundColor: '#1a1a24',
                borderRadius: '0.75rem',
                color: '#b0b8c0',
              }}>
                <Eye size={64} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
                <p>Select a table to preview its data</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Versions Tab */}
      {activeTab === 'versions' && (
        <div>
          <h3 style={{
            fontSize: '1.25rem',
            fontWeight: '600',
            marginBottom: '1.5rem',
            color: '#f0f0f5'
          }}>
            Version History
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {versions.map((version, idx) => (
              <div
                key={version.id}
                style={{
                  padding: '1.5rem',
                  backgroundColor: '#1a1a24',
                  border: idx === 0
                    ? '1px solid rgba(34, 197, 94, 0.3)'
                    : '1px solid rgba(168, 216, 255, 0.2)',
                  borderRadius: '0.75rem',
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'start',
                  marginBottom: '1rem',
                }}>
                  <div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      marginBottom: '0.5rem',
                    }}>
                      <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#f0f0f5' }}>
                        Version {versions.length - idx}
                      </h4>
                      {idx === 0 && (
                        <span style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: 'rgba(34, 197, 94, 0.15)',
                          border: '1px solid rgba(34, 197, 94, 0.3)',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          color: '#22c55e',
                        }}>
                          Current
                        </span>
                      )}
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      fontSize: '0.875rem',
                      color: '#8ab3cc',
                    }}>
                      <Calendar size={14} />
                      Modified: {formatDate(version.modified_at)}
                    </div>
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.875rem',
                    color: '#8ab3cc',
                  }}>
                    <Clock size={14} />
                    Detected: {formatDate(version.detected_at)}
                  </div>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                  gap: '1rem',
                  padding: '1rem',
                  backgroundColor: 'rgba(168, 216, 255, 0.05)',
                  borderRadius: '0.5rem',
                }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#b0b8c0', marginBottom: '0.25rem' }}>
                      Size
                    </div>
                    <div style={{ fontWeight: '600', color: '#f0f0f5' }}>
                      {formatFileSize(version.size_bytes)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#b0b8c0', marginBottom: '0.25rem' }}>
                      Rows
                    </div>
                    <div style={{ fontWeight: '600', color: '#f0f0f5' }}>
                      {version.row_count_estimate?.toLocaleString() || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#b0b8c0', marginBottom: '0.25rem' }}>
                      Tables
                    </div>
                    <div style={{ fontWeight: '600', color: '#f0f0f5' }}>
                      {version.table_count}
                    </div>
                  </div>
                  <div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: '#b0b8c0',
                      marginBottom: '0.25rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                    }}>
                      <Hash size={12} />
                      Content Hash
                    </div>
                    <div style={{
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      color: '#f0f0f5',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}>
                      {version.content_hash.substring(0, 16)}...
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
