import { useEffect } from 'react'
import { X, CheckCircle, AlertCircle, Info, XCircle } from 'lucide-react'

interface ToastProps {
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  onClose: () => void
  duration?: number
  inline?: boolean // When true, doesn't use fixed positioning (for use in ToastProvider)
}

export default function Toast({ message, type, onClose, duration = 5000, inline = false }: ToastProps) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration)
      return () => clearTimeout(timer)
    }
  }, [duration, onClose])

  const colors = {
    success: { bg: 'rgba(34, 197, 94, 0.1)', border: '#22c55e', text: '#22c55e' },
    error: { bg: 'rgba(239, 68, 68, 0.1)', border: '#ef4444', text: '#ef4444' },
    warning: { bg: 'rgba(251, 191, 36, 0.1)', border: '#fbbf24', text: '#fbbf24' },
    info: { bg: 'rgba(168, 216, 255, 0.1)', border: '#a8d8ff', text: '#a8d8ff' }
  }

  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info
  }

  const Icon = icons[type]
  const color = colors[type]

  return (
    <div
      style={{
        ...(inline ? {} : { position: 'fixed', top: '1rem', right: '1rem', zIndex: 9999 }),
        minWidth: '300px',
        maxWidth: '500px',
        padding: '1rem',
        backgroundColor: color.bg,
        border: `1px solid ${color.border}`,
        borderRadius: '0.5rem',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        animation: 'slideIn 0.3s ease-out'
      }}
    >
      <Icon size={20} style={{ color: color.text, flexShrink: 0, marginTop: '2px' }} />
      <p style={{ flex: 1, color: color.text, fontSize: '0.875rem', lineHeight: '1.5' }}>
        {message}
      </p>
      <button
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: color.text,
          cursor: 'pointer',
          padding: 0,
          flexShrink: 0
        }}
      >
        <X size={16} />
      </button>
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  )
}
