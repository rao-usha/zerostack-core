import React, { useState, useEffect } from 'react'
import { 
  FolderOpen, 
  Plus, 
  RefreshCw, 
  Trash2, 
  CheckCircle2, 
  XCircle,
  Folder,
  Clock,
  FileText,
  Cloud,
  HardDrive,
  Link2,
} from 'lucide-react'
import {
  listFileLocations,
  createFileLocation,
  scanFileLocation,
  deleteFileLocation,
  FileLocation,
  getGDriveAuthUrl,
  listGDriveAccounts,
  ExternalAccount,
} from '../api/client'

export default function FileLocations() {
  const [locations, setLocations] = useState<FileLocation[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  
  // Form state
  const [locationType, setLocationType] = useState<'local' | 'gdrive'>('local')
  const [locationName, setLocationName] = useState('')
  const [localPath, setLocalPath] = useState('')
  const [gdriveFolderId, setGdriveFolderId] = useState('')
  const [gdriveIncludeShared, setGdriveIncludeShared] = useState(true)
  const [selectedAccount, setSelectedAccount] = useState<string>('')
  
  // Google Drive state
  const [gdriveAccounts, setGdriveAccounts] = useState<ExternalAccount[]>([])
  const [connectingGDrive, setConnectingGDrive] = useState(false)
  
  const [creating, setCreating] = useState(false)
  const [scanning, setScanning] = useState<Record<string, boolean>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [locationsData, accountsData] = await Promise.all([
        listFileLocations(),
        listGDriveAccounts().catch(() => []), // Gracefully handle if not configured
      ])
      setLocations(locationsData)
      setGdriveAccounts(accountsData)
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleConnectGDrive = async () => {
    try {
      setConnectingGDrive(true)
      const { auth_url } = await getGDriveAuthUrl()
      // Open OAuth flow in new window
      window.open(auth_url, '_blank', 'width=600,height=700')
      
      // Poll for new accounts (simple MVP approach)
      setTimeout(async () => {
        const accounts = await listGDriveAccounts()
        setGdriveAccounts(accounts)
        if (accounts.length > 0) {
          setSelectedAccount(accounts[accounts.length - 1].id)
        }
      }, 5000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to connect Google Drive')
    } finally {
      setConnectingGDrive(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      if (locationType === 'local') {
        await createFileLocation(locationName, 'local', localPath)
      } else {
        await createFileLocation(
          locationName,
          'gdrive',
          undefined,
          gdriveFolderId,
          gdriveIncludeShared,
          selectedAccount
        )
      }
      
      // Reset form
      setLocationName('')
      setLocalPath('')
      setGdriveFolderId('')
      setShowCreateForm(false)
      await loadData()
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create location')
    } finally {
      setCreating(false)
    }
  }

  const handleScan = async (locationId: string) => {
    setScanning(prev => ({ ...prev, [locationId]: true }))
    try {
      await scanFileLocation(locationId)
      await loadData()
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to scan location')
    } finally {
      setScanning(prev => ({ ...prev, [locationId]: false }))
    }
  }

  const handleDelete = async (locationId: string) => {
    if (!confirm('Are you sure you want to delete this location?')) return
    
    try {
      await deleteFileLocation(locationId)
      await loadData()
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete location')
    }
  }

  return (
    <div style={{ 
      padding: '2rem', 
      backgroundColor: '#0f0f17', 
      minHeight: '100vh',
      color: '#f0f0f5'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '2rem' 
      }}>
        <div>
          <h1 style={{ 
            fontSize: '2rem', 
            fontWeight: 'bold', 
            marginBottom: '0.5rem',
            color: '#f0f0f5'
          }}>
            File Locations
          </h1>
          <p style={{ color: '#b0b8c0' }}>
            Configure local folders or Google Drive folders to scan for data files
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
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
            cursor: 'pointer',
          }}
        >
          <Plus size={20} />
          Add Location
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div style={{
          padding: '1rem',
          marginBottom: '1rem',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '0.5rem',
          color: '#fca5a5',
        }}>
          {error}
        </div>
      )}

      {/* Create Form */}
      {showCreateForm && (
        <div style={{
          padding: '1.5rem',
          marginBottom: '2rem',
          backgroundColor: '#1a1a24',
          border: '1px solid rgba(168, 216, 255, 0.2)',
          borderRadius: '0.75rem',
        }}>
          <h2 style={{ 
            fontSize: '1.25rem', 
            fontWeight: '600', 
            marginBottom: '1rem',
            color: '#a8d8ff'
          }}>
            Create New Location
          </h2>
          
          <form onSubmit={handleCreate}>
            {/* Location Type Selector */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem', 
                color: '#b0b8c0',
                fontSize: '0.875rem'
              }}>
                Location Type
              </label>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setLocationType('local')}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    padding: '1rem',
                    backgroundColor: locationType === 'local' 
                      ? 'rgba(168, 216, 255, 0.15)' 
                      : 'rgba(168, 216, 255, 0.05)',
                    border: locationType === 'local'
                      ? '2px solid #a8d8ff'
                      : '1px solid rgba(168, 216, 255, 0.3)',
                    borderRadius: '0.5rem',
                    color: locationType === 'local' ? '#a8d8ff' : '#f0f0f5',
                    cursor: 'pointer',
                    fontWeight: '600',
                  }}
                >
                  <HardDrive size={20} />
                  Local Folder
                </button>
                <button
                  type="button"
                  onClick={() => setLocationType('gdrive')}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    padding: '1rem',
                    backgroundColor: locationType === 'gdrive' 
                      ? 'rgba(168, 216, 255, 0.15)' 
                      : 'rgba(168, 216, 255, 0.05)',
                    border: locationType === 'gdrive'
                      ? '2px solid #a8d8ff'
                      : '1px solid rgba(168, 216, 255, 0.3)',
                    borderRadius: '0.5rem',
                    color: locationType === 'gdrive' ? '#a8d8ff' : '#f0f0f5',
                    cursor: 'pointer',
                    fontWeight: '600',
                  }}
                >
                  <Cloud size={20} />
                  Google Drive
                </button>
              </div>
            </div>

            {/* Location Name */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem', 
                color: '#b0b8c0',
                fontSize: '0.875rem'
              }}>
                Name
              </label>
              <input
                type="text"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                placeholder="My Data Folder"
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  backgroundColor: '#0f0f17',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.5rem',
                  color: '#f0f0f5',
                  fontSize: '1rem',
                }}
              />
            </div>

            {/* Local Path Input */}
            {locationType === 'local' && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '0.5rem', 
                  color: '#b0b8c0',
                  fontSize: '0.875rem'
                }}>
                  Local Path
                </label>
                <input
                  type="text"
                  value={localPath}
                  onChange={(e) => setLocalPath(e.target.value)}
                  placeholder="C:\Users\YourName\Desktop\data-files"
                  required
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    backgroundColor: '#0f0f17',
                    border: '1px solid rgba(168, 216, 255, 0.3)',
                    borderRadius: '0.5rem',
                    color: '#f0f0f5',
                    fontSize: '1rem',
                  }}
                />
                <p style={{ 
                  marginTop: '0.5rem', 
                  fontSize: '0.75rem', 
                  color: '#8ab3cc' 
                }}>
                  Path must be within the configured FILES_ROOT directory
                </p>
              </div>
            )}

            {/* Google Drive Inputs */}
            {locationType === 'gdrive' && (
              <>
                {/* Connected Account */}
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    color: '#b0b8c0',
                    fontSize: '0.875rem'
                  }}>
                    Google Account
                  </label>
                  {gdriveAccounts.length === 0 ? (
                    <button
                      type="button"
                      onClick={handleConnectGDrive}
                      disabled={connectingGDrive}
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        padding: '0.75rem',
                        backgroundColor: 'rgba(168, 216, 255, 0.1)',
                        border: '1px solid rgba(168, 216, 255, 0.3)',
                        borderRadius: '0.5rem',
                        color: '#a8d8ff',
                        cursor: connectingGDrive ? 'not-allowed' : 'pointer',
                        fontWeight: '600',
                      }}
                    >
                      <Link2 size={20} />
                      {connectingGDrive ? 'Connecting...' : 'Connect Google Drive'}
                    </button>
                  ) : (
                    <div>
                      <select
                        value={selectedAccount}
                        onChange={(e) => setSelectedAccount(e.target.value)}
                        required
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          backgroundColor: '#0f0f17',
                          border: '1px solid rgba(168, 216, 255, 0.3)',
                          borderRadius: '0.5rem',
                          color: '#f0f0f5',
                          fontSize: '1rem',
                        }}
                      >
                        <option value="">Select account...</option>
                        {gdriveAccounts.map(acc => (
                          <option key={acc.id} value={acc.id}>
                            {acc.account_email}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={handleConnectGDrive}
                        style={{
                          marginTop: '0.5rem',
                          fontSize: '0.75rem',
                          color: '#a8d8ff',
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          textDecoration: 'underline',
                        }}
                      >
                        Connect another account
                      </button>
                    </div>
                  )}
                </div>

                {/* Folder ID */}
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    color: '#b0b8c0',
                    fontSize: '0.875rem'
                  }}>
                    Folder ID
                  </label>
                  <input
                    type="text"
                    value={gdriveFolderId}
                    onChange={(e) => setGdriveFolderId(e.target.value)}
                    placeholder="1a2B3c4D5e6F7g8H9i0J"
                    required
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      backgroundColor: '#0f0f17',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      borderRadius: '0.5rem',
                      color: '#f0f0f5',
                      fontSize: '1rem',
                    }}
                  />
                  <p style={{ 
                    marginTop: '0.5rem', 
                    fontSize: '0.75rem', 
                    color: '#8ab3cc' 
                  }}>
                    Copy folder ID from Google Drive URL: drive.google.com/drive/folders/<strong>[ID]</strong>
                  </p>
                </div>

                {/* Include Shared Drives */}
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    cursor: 'pointer',
                    userSelect: 'none',
                  }}>
                    <input
                      type="checkbox"
                      checked={gdriveIncludeShared}
                      onChange={(e) => setGdriveIncludeShared(e.target.checked)}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '0.875rem', color: '#b0b8c0' }}>
                      Include Shared Drives
                    </span>
                  </label>
                </div>
              </>
            )}

            {/* Submit Buttons */}
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                type="submit"
                disabled={creating || (locationType === 'gdrive' && (!selectedAccount || !gdriveFolderId))}
                style={{
                  padding: '0.75rem 1.5rem',
                  backgroundColor: '#a8d8ff',
                  color: '#0f0f17',
                  border: 'none',
                  borderRadius: '0.5rem',
                  fontWeight: '600',
                  cursor: creating ? 'not-allowed' : 'pointer',
                  opacity: creating || (locationType === 'gdrive' && (!selectedAccount || !gdriveFolderId)) ? 0.6 : 1,
                }}
              >
                {creating ? 'Creating...' : 'Create Location'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false)
                  setLocationName('')
                  setLocalPath('')
                  setGdriveFolderId('')
                }}
                style={{
                  padding: '0.75rem 1.5rem',
                  backgroundColor: 'rgba(168, 216, 255, 0.1)',
                  color: '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                  borderRadius: '0.5rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Locations List */}
      {loading ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '4rem', 
          color: '#b0b8c0' 
        }}>
          Loading locations...
        </div>
      ) : locations.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '4rem',
          backgroundColor: '#1a1a24',
          borderRadius: '0.75rem',
          border: '1px solid rgba(168, 216, 255, 0.2)',
        }}>
          <FolderOpen size={64} style={{ 
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
            No Locations Yet
          </h2>
          <p style={{ color: '#b0b8c0', marginBottom: '1.5rem' }}>
            Add your first file location to start scanning for data files
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.5rem',
              backgroundColor: '#a8d8ff',
              color: '#0f0f17',
              border: 'none',
              borderRadius: '0.5rem',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            <Plus size={20} />
            Add First Location
          </button>
        </div>
      ) : (
        <div style={{ 
          display: 'grid', 
          gap: '1rem', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))' 
        }}>
          {locations.map((location) => (
            <div
              key={location.id}
              style={{
                padding: '1.5rem',
                backgroundColor: '#1a1a24',
                border: '1px solid rgba(168, 216, 255, 0.2)',
                borderRadius: '0.75rem',
              }}
            >
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'start',
                marginBottom: '1rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {location.type === 'local' ? (
                    <HardDrive size={24} style={{ color: '#a8d8ff' }} />
                  ) : (
                    <Cloud size={24} style={{ color: '#a8d8ff' }} />
                  )}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <h3 style={{ 
                        fontSize: '1.125rem', 
                        fontWeight: '600',
                        color: '#f0f0f5'
                      }}>
                        {location.name}
                      </h3>
                      <span style={{
                        fontSize: '0.625rem',
                        padding: '0.125rem 0.5rem',
                        backgroundColor: location.type === 'local' 
                          ? 'rgba(168, 216, 255, 0.15)'
                          : 'rgba(196, 181, 253, 0.15)',
                        color: location.type === 'local' ? '#a8d8ff' : '#c4b5fd',
                        borderRadius: '9999px',
                        fontWeight: '600',
                        textTransform: 'uppercase',
                      }}>
                        {location.type}
                      </span>
                    </div>
                    <p style={{ 
                      fontSize: '0.875rem', 
                      color: '#8ab3cc',
                      marginTop: '0.25rem'
                    }}>
                      {location.type === 'local' 
                        ? location.local_path 
                        : `${location.gdrive_account_email} • ${location.gdrive_folder_id}`}
                    </p>
                  </div>
                </div>
                {location.is_active ? (
                  <CheckCircle2 size={20} style={{ color: '#22c55e' }} />
                ) : (
                  <XCircle size={20} style={{ color: '#ef4444' }} />
                )}
              </div>

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr', 
                gap: '0.75rem',
                marginBottom: '1rem',
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
                    Files
                  </div>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.5rem' 
                  }}>
                    <FileText size={16} style={{ color: '#a8d8ff' }} />
                    <span style={{ 
                      fontSize: '1.25rem', 
                      fontWeight: '600',
                      color: '#f0f0f5'
                    }}>
                      {location.file_count}
                    </span>
                  </div>
                </div>
                <div>
                  <div style={{ 
                    fontSize: '0.75rem', 
                    color: '#b0b8c0', 
                    marginBottom: '0.25rem' 
                  }}>
                    Last Scanned
                  </div>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '0.5rem' 
                  }}>
                    <Clock size={16} style={{ color: '#a8d8ff' }} />
                    <span style={{ 
                      fontSize: '0.875rem',
                      color: '#f0f0f5'
                    }}>
                      {location.last_scanned_at 
                        ? new Date(location.last_scanned_at).toLocaleDateString()
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  onClick={() => handleScan(location.id)}
                  disabled={scanning[location.id]}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    padding: '0.625rem',
                    backgroundColor: '#a8d8ff',
                    color: '#0f0f17',
                    border: 'none',
                    borderRadius: '0.5rem',
                    fontWeight: '600',
                    cursor: scanning[location.id] ? 'not-allowed' : 'pointer',
                    opacity: scanning[location.id] ? 0.6 : 1,
                  }}
                >
                  <RefreshCw 
                    size={16} 
                    style={{ 
                      animation: scanning[location.id] ? 'spin 1s linear infinite' : 'none'
                    }} 
                  />
                  {scanning[location.id] ? 'Scanning...' : 'Scan Now'}
                </button>
                <button
                  onClick={() => handleDelete(location.id)}
                  style={{
                    padding: '0.625rem',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    color: '#fca5a5',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '0.5rem',
                    cursor: 'pointer',
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  )
}
