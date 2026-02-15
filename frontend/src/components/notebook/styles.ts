/**
 * Shared styles for Notebook components.
 */
import React from 'react'

export const styles: Record<string, React.CSSProperties> = {
  container: { minHeight: '100vh', backgroundColor: '#0a0a0f', color: '#f0f0f5', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },

  // Header
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 32px', borderBottom: '1px solid rgba(255,255,255,0.1)', position: 'sticky', top: 0, backgroundColor: '#0a0a0f', zIndex: 100 },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '12px' },
  headerActions: { display: 'flex', alignItems: 'center', gap: '12px' },
  backLink: { padding: '6px 12px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', fontSize: '16px', cursor: 'pointer' },
  title: { fontSize: '18px', fontWeight: '600', margin: 0, cursor: 'pointer' },
  nameInput: { fontSize: '18px', fontWeight: '600', backgroundColor: '#1a1a24', border: '1px solid rgba(59, 130, 246, 0.5)', borderRadius: '4px', padding: '4px 8px', color: '#f0f0f5' },
  connectionSelect: { padding: '8px 12px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '13px', minWidth: '200px' },
  resetButton: { padding: '8px 12px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', fontSize: '13px', cursor: 'pointer' },
  runAllButton: { padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: '600', fontSize: '13px', cursor: 'pointer' },

  // Main
  main: { padding: '24px 32px', maxWidth: '1000px', margin: '0 auto' },

  // Cells
  cell: { marginBottom: '16px', backgroundColor: '#12121a', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', overflow: 'hidden' },
  cellHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', backgroundColor: '#0f0f14', borderBottom: '1px solid rgba(255,255,255,0.1)' },
  cellInfo: { display: 'flex', alignItems: 'center', gap: '10px' },
  cellType: { fontSize: '11px', fontWeight: '600' },
  cellPosition: { fontSize: '11px', color: '#6b7280' },
  cellStatus: { fontSize: '11px' },
  cellActions: { display: 'flex', gap: '6px' },
  cellActionBtn: { width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.05)', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' },
  cellContent: { width: '100%', padding: '12px', backgroundColor: 'transparent', border: 'none', color: '#f0f0f5', fontSize: '13px', lineHeight: '1.5', resize: 'vertical', outline: 'none' },

  // Results
  cellResults: { borderTop: '1px solid rgba(255,255,255,0.1)', backgroundColor: '#0f0f14' },
  resultHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', fontSize: '12px', color: '#10b981', borderBottom: '1px solid rgba(255,255,255,0.05)' },
  resultTable: { maxHeight: '400px', overflow: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: '12px' },
  th: { textAlign: 'left', padding: '8px 10px', backgroundColor: '#0a0a0f', color: '#9ca3af', fontWeight: '500', position: 'sticky', top: 0 },
  tr: { borderBottom: '1px solid rgba(255,255,255,0.05)' },
  td: { padding: '6px 10px', color: '#d1d5db', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  moreRows: { padding: '8px 12px', textAlign: 'center', color: '#6b7280', fontSize: '11px' },
  errorResult: { padding: '12px', color: '#ef4444', fontSize: '13px' },
  runningResult: { padding: '12px', color: '#fbbf24', fontSize: '13px' },
  saveDatasetBtn: { padding: '4px 10px', backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', borderRadius: '4px', color: '#60a5fa', fontSize: '11px', cursor: 'pointer' },

  // Python outputs
  pythonOutputs: { padding: '8px 0' },
  pythonHeader: { padding: '8px 12px', fontSize: '12px', color: '#10b981', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  newVars: { color: '#9ca3af', fontSize: '11px' },
  stdout: { margin: '0 12px 8px', padding: '8px', backgroundColor: '#0a0a0f', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace', color: '#d1d5db', whiteSpace: 'pre-wrap', maxHeight: '200px', overflow: 'auto' },
  stderr: { margin: '0 12px 8px', padding: '8px', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace', color: '#fca5a5', whiteSpace: 'pre-wrap' },
  pythonError: {},
  traceback: { margin: '8px 12px', padding: '8px', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace', color: '#fca5a5', whiteSpace: 'pre-wrap', maxHeight: '300px', overflow: 'auto' },
  outputItem: { margin: '8px 12px' },
  dataframeOutput: {},
  dfName: { fontSize: '12px', fontWeight: '600', color: '#10b981', marginBottom: '4px' },
  dfShape: { fontSize: '11px', color: '#9ca3af', marginBottom: '8px' },
  imageOutput: { padding: '8px', backgroundColor: '#1a1a24', borderRadius: '4px' },
  textOutput: { padding: '8px', backgroundColor: '#0a0a0f', borderRadius: '4px', fontSize: '12px', fontFamily: 'monospace', color: '#d1d5db', whiteSpace: 'pre-wrap' },
  resultValue: { padding: '8px 12px', display: 'flex', gap: '8px', alignItems: 'baseline' },
  resultLabel: { color: '#ef4444', fontSize: '11px', fontWeight: '600' },

  // Variables sidebar
  variablesSidebar: { position: 'fixed', right: '16px', top: '80px', width: '200px', backgroundColor: '#12121a', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', padding: '12px', maxHeight: '400px', overflow: 'auto' },
  sidebarTitle: { fontSize: '12px', fontWeight: '600', color: '#9ca3af', margin: '0 0 8px 0', textTransform: 'uppercase' },
  variableItem: { padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', gap: '2px' },
  varName: { fontSize: '12px', color: '#60a5fa', fontWeight: '500' },
  varType: { fontSize: '10px', color: '#6b7280' },
  varPreview: { fontSize: '11px', color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },

  // Add Cell
  addCellRow: { display: 'flex', gap: '8px', justifyContent: 'center', padding: '16px' },
  addCellButtons: { display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '16px' },
  addCellBtn: { padding: '8px 16px', backgroundColor: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', borderRadius: '6px', color: '#60a5fa', fontSize: '13px', cursor: 'pointer' },

  // Empty/Loading/Error States
  emptyState: { textAlign: 'center', padding: '60px 32px', backgroundColor: '#12121a', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.2)' },
  loadingState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' },
  spinner: { width: '32px', height: '32px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '12px' },
  errorState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#ef4444' },
  backButton: { marginTop: '16px', padding: '10px 20px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  errorBanner: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 32px', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', fontSize: '13px' },
  errorClose: { background: 'none', border: 'none', color: '#ef4444', fontSize: '18px', cursor: 'pointer' },

  // Modal
  modalOverlay: { position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { backgroundColor: '#12121a', borderRadius: '12px', padding: '20px', width: '90%', maxWidth: '400px', border: '1px solid rgba(255,255,255,0.1)' },
  modalInput: { width: '100%', padding: '10px', backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#f0f0f5', fontSize: '14px', marginBottom: '16px' },
  modalActions: { display: 'flex', justifyContent: 'flex-end', gap: '10px' },
  modalCancel: { padding: '8px 16px', backgroundColor: 'transparent', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', color: '#9ca3af', cursor: 'pointer' },
  modalSubmit: { padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '6px', color: '#fff', fontWeight: '600', cursor: 'pointer' },

  // Shortcuts
  shortcuts: { position: 'fixed', bottom: '16px', right: '16px', padding: '8px 12px', backgroundColor: 'rgba(0,0,0,0.8)', borderRadius: '6px', fontSize: '11px', color: '#6b7280' }
}
