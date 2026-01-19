import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileText,
  Filter,
  Search,
  AlertCircle,
  Calendar,
  FolderOpen,
  ChevronRight,
} from 'lucide-react'
import {
  listFileAssets,
  listFileLocations,
  FileAsset,
  FileLocation,
} from '../api/client'

export default function FileInventory() {
  const navigate = useNavigate()
  const [assets, setAssets] = useState<FileAsset[]>([])
  const [locations, setLocations] = useState<FileLocation[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showOnlyChanges, setShowOnlyChanges] = useState(false)

  useEffect(() => {
    loadData()
  }, [selectedLocation])

  const loadData = async () => {
    try {
      setLoading(true)
      const [assetsData, locationsData] = await Promise.all([
        listFileAssets(selectedLocation === 'all' ? undefined : selectedLocation),
        listFileLocations(),
      ])
      setAssets(assetsData)
      setLocations(locationsData)
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         asset.relative_path.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesChanges = !showOnlyChanges || asset.has_changes
    return matchesSearch && matchesChanges
  })

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  return (
    <div style={{
      padding: '2rem',
      backgroundColor: '#0f0f17',
      minHeight: '100vh',
      color: '#f0f0f5'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{
          fontSize: '2rem',
          fontWeight: 'bold',
          marginBottom: '0.5rem',
          color: '#f0f0f5'
        }}>
          File Inventory
        </h1>
        <p style={{ color: '#b0b8c0' }}>
          Browse and manage all discovered files across locations
        </p>
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        marginBottom: '2rem',
        flexWrap: 'wrap',
      }}>
        {/* Search */}
        <div style={{ flex: '1', minWidth: '300px' }}>
          <div style={{ position: 'relative' }}>
            <Search 
              size={20} 
              style={{ 
                position: 'absolute', 
                left: '0.75rem', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: '#b0b8c0'
              }} 
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search files..."
              style={{
                width: '100%',
                padding: '0.75rem 0.75rem 0.75rem 2.75rem',
                backgroundColor: '#1a1a24',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                borderRadius: '0.5rem',
                color: '#f0f0f5',
                fontSize: '1rem',
              }}
            />
          </div>
        </div>

        {/* Location Filter */}
        <div style={{ position: 'relative' }}>
          <Filter 
            size={20} 
            style={{ 
              position: 'absolute', 
              left: '0.75rem', 
              top: '50%', 
              transform: 'translateY(-50%)',
              color: '#b0b8c0',
              pointerEvents: 'none'
            }} 
          />
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            style={{
              padding: '0.75rem 1rem 0.75rem 2.75rem',
              backgroundColor: '#1a1a24',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              borderRadius: '0.5rem',
              color: '#f0f0f5',
              fontSize: '1rem',
              cursor: 'pointer',
            }}
          >
            <option value="all">All Locations</option>
            {locations.map(loc => (
              <option key={loc.id} value={loc.id}>{loc.name}</option>
            ))}
          </select>
        </div>

        {/* Show Changes Only */}
        <label style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1rem',
          backgroundColor: '#1a1a24',
          border: '1px solid rgba(168, 216, 255, 0.3)',
          borderRadius: '0.5rem',
          cursor: 'pointer',
          userSelect: 'none',
        }}>
          <input
            type="checkbox"
            checked={showOnlyChanges}
            onChange={(e) => setShowOnlyChanges(e.target.checked)}
            style={{ cursor: 'pointer' }}
          />
          <span style={{ fontSize: '0.875rem', color: '#b0b8c0' }}>
            Show changes only
          </span>
        </label>
      </div>

      {/* Results Count */}
      <div style={{
        marginBottom: '1rem',
        fontSize: '0.875rem',
        color: '#b0b8c0',
      }}>
        {filteredAssets.length} file{filteredAssets.length !== 1 ? 's' : ''} found
      </div>

      {/* Files List */}
      {loading ? (
        <div style={{
          textAlign: 'center',
          padding: '4rem',
          color: '#b0b8c0'
        }}>
          Loading files...
        </div>
      ) : filteredAssets.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '4rem',
          backgroundColor: '#1a1a24',
          borderRadius: '0.75rem',
          border: '1px solid rgba(168, 216, 255, 0.2)',
        }}>
          <FileText size={64} style={{
            margin: '0 auto 1rem',
            opacity: 0.5,
            color: '#a8d8ff'
          }} />
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: '600',
            marginBottom: '0.5rem',
            color: '#f0f0f5'
          }}>
            No Files Found
          </h2>
          <p style={{ color: '#b0b8c0' }}>
            {searchQuery || showOnlyChanges
              ? 'Try adjusting your filters'
              : 'Scan a location to discover files'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filteredAssets.map((asset) => (
            <div
              key={asset.id}
              onClick={() => navigate(`/files/assets/${asset.id}`)}
              style={{
                padding: '1.5rem',
                backgroundColor: '#1a1a24',
                border: asset.has_changes
                  ? '1px solid rgba(34, 197, 94, 0.3)'
                  : '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(168, 216, 255, 0.05)'
                e.currentTarget.style.borderColor = '#a8d8ff'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#1a1a24'
                e.currentTarget.style.borderColor = asset.has_changes
                  ? 'rgba(34, 197, 94, 0.3)'
                  : 'rgba(168, 216, 255, 0.2)'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'start',
              }}>
                <div style={{ flex: 1 }}>
                  {/* File Name & Location */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    marginBottom: '0.75rem',
                  }}>
                    <FileText size={24} style={{ color: '#a8d8ff' }} />
                    <div>
                      <h3 style={{
                        fontSize: '1.125rem',
                        fontWeight: '600',
                        color: '#f0f0f5',
                        marginBottom: '0.25rem',
                      }}>
                        {asset.file_name}
                      </h3>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem',
                        color: '#8ab3cc',
                      }}>
                        <FolderOpen size={14} />
                        {asset.location_name} • {asset.relative_path}
                      </div>
                    </div>
                  </div>

                  {/* Version Info */}
                  {asset.latest_version && (
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                      gap: '1rem',
                      padding: '1rem',
                      backgroundColor: 'rgba(168, 216, 255, 0.05)',
                      borderRadius: '0.5rem',
                    }}>
                      <div>
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#b0b8c0',
                          marginBottom: '0.25rem'
                        }}>
                          File Size
                        </div>
                        <div style={{ color: '#f0f0f5', fontWeight: '600' }}>
                          {formatFileSize(asset.latest_version.size_bytes)}
                        </div>
                      </div>
                      <div>
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#b0b8c0',
                          marginBottom: '0.25rem'
                        }}>
                          Rows
                        </div>
                        <div style={{ color: '#f0f0f5', fontWeight: '600' }}>
                          {asset.latest_version.row_count_estimate?.toLocaleString() || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#b0b8c0',
                          marginBottom: '0.25rem'
                        }}>
                          Tables
                        </div>
                        <div style={{ color: '#f0f0f5', fontWeight: '600' }}>
                          {asset.latest_version.table_count}
                        </div>
                      </div>
                      <div>
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#b0b8c0',
                          marginBottom: '0.25rem'
                        }}>
                          Modified
                        </div>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                          color: '#f0f0f5',
                          fontSize: '0.875rem'
                        }}>
                          <Calendar size={14} />
                          {new Date(asset.latest_version.modified_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                  {asset.has_changes && (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.375rem 0.75rem',
                      backgroundColor: 'rgba(34, 197, 94, 0.15)',
                      border: '1px solid rgba(34, 197, 94, 0.3)',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      color: '#22c55e',
                    }}>
                      <AlertCircle size={14} />
                      New Version
                    </div>
                  )}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    fontSize: '0.75rem',
                    color: '#8ab3cc',
                  }}>
                    {asset.version_count} version{asset.version_count !== 1 ? 's' : ''}
                  </div>
                  <ChevronRight size={20} style={{ color: '#a8d8ff' }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
