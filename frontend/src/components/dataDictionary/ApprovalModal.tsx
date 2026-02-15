/**
 * Approval/Rejection Modal for Data Dictionary entries.
 */
import { Loader2 } from 'lucide-react'
import { ApprovalModalState } from '../../types/dataDictionary'

interface ApprovalModalProps {
  modal: ApprovalModalState
  notes: string
  saving: boolean
  onNotesChange: (notes: string) => void
  onSubmit: () => void
  onCancel: () => void
}

export default function ApprovalModal({
  modal,
  notes,
  saving,
  onNotesChange,
  onSubmit,
  onCancel
}: ApprovalModalProps) {
  if (!modal.isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}
      onClick={onCancel}
    >
      <div
        style={{
          backgroundColor: '#1a1d2e',
          border: '1px solid rgba(168, 216, 255, 0.3)',
          borderRadius: '0.75rem',
          padding: '2rem',
          maxWidth: '500px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: '600',
          marginBottom: '1.5rem',
          color: '#f0f0f5'
        }}>
          {modal.action === 'approve' ? 'Approve Entry' : 'Reject Entry'}
        </h2>

        <div style={{ marginBottom: '1.5rem' }}>
          <label
            htmlFor="approval-notes"
            style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              marginBottom: '0.5rem',
              color: '#a8d8ff'
            }}
          >
            {modal.action === 'approve' ? 'Approval notes (optional)' : 'Rejection reason (optional)'}
          </label>
          <textarea
            id="approval-notes"
            value={notes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder={
              modal.action === 'approve'
                ? 'Add any notes about this approval...'
                : 'Explain why this entry is being rejected...'
            }
            rows={4}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: '#0a0e1a',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              borderRadius: '0.5rem',
              color: '#f0f0f5',
              fontSize: '0.875rem',
              fontFamily: 'inherit',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            disabled={saving}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'rgba(168, 216, 255, 0.1)',
              border: '1px solid rgba(168, 216, 255, 0.3)',
              borderRadius: '0.5rem',
              color: '#a8d8ff',
              fontSize: '0.875rem',
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.5 : 1
            }}
          >
            Cancel
          </button>
          <button
            onClick={onSubmit}
            disabled={saving}
            style={{
              padding: '0.5rem 1rem',
              background: modal.action === 'approve'
                ? 'linear-gradient(90deg, rgba(34, 197, 94, 0.2), rgba(22, 163, 74, 0.2))'
                : 'linear-gradient(90deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2))',
              border: modal.action === 'approve'
                ? '1px solid rgba(34, 197, 94, 0.4)'
                : '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: '0.5rem',
              color: modal.action === 'approve' ? '#22c55e' : '#ef4444',
              fontSize: '0.875rem',
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.5 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {modal.action === 'approve' ? 'Approving...' : 'Rejecting...'}
              </>
            ) : (
              modal.action === 'approve' ? 'Approve' : 'Reject'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
