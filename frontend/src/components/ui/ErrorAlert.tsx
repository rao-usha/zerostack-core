/**
 * Reusable error alert components for displaying errors consistently.
 */
import { AlertCircle, AlertTriangle, XCircle, RefreshCw, X } from 'lucide-react'
import { ReactNode } from 'react'

type ErrorSeverity = 'error' | 'warning' | 'info'

interface ErrorAlertProps {
  title?: string
  message: string
  severity?: ErrorSeverity
  onRetry?: () => void
  onDismiss?: () => void
  details?: string
  className?: string
}

const severityStyles = {
  error: {
    bg: 'rgba(255, 107, 107, 0.1)',
    border: 'rgba(255, 107, 107, 0.3)',
    color: '#ff6b6b',
    Icon: XCircle,
  },
  warning: {
    bg: 'rgba(251, 191, 36, 0.1)',
    border: 'rgba(251, 191, 36, 0.3)',
    color: '#fbbf24',
    Icon: AlertTriangle,
  },
  info: {
    bg: 'rgba(168, 216, 255, 0.1)',
    border: 'rgba(168, 216, 255, 0.3)',
    color: '#a8d8ff',
    Icon: AlertCircle,
  },
}

export function ErrorAlert({
  title,
  message,
  severity = 'error',
  onRetry,
  onDismiss,
  details,
  className = '',
}: ErrorAlertProps) {
  const styles = severityStyles[severity]
  const Icon = styles.Icon

  return (
    <div
      className={`rounded-lg p-4 ${className}`}
      style={{
        backgroundColor: styles.bg,
        border: `1px solid ${styles.border}`,
      }}
    >
      <div className="flex items-start gap-3">
        <Icon
          className="h-5 w-5 flex-shrink-0 mt-0.5"
          style={{ color: styles.color }}
        />
        <div className="flex-1 min-w-0">
          {title && (
            <h4
              className="font-semibold mb-1"
              style={{ color: styles.color }}
            >
              {title}
            </h4>
          )}
          <p className="text-sm" style={{ color: '#b0b8c0' }}>
            {message}
          </p>
          {details && (
            <p
              className="text-xs mt-2 font-mono break-all"
              style={{ color: '#8090a0' }}
            >
              {details}
            </p>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-1.5 mt-3 text-sm px-3 py-1.5 rounded transition-colors"
              style={{
                backgroundColor: 'rgba(168, 216, 255, 0.15)',
                color: '#a8d8ff',
              }}
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry
            </button>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 rounded hover:bg-white/10 transition-colors"
            style={{ color: '#8090a0' }}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

interface ErrorBannerProps {
  message: string
  onDismiss?: () => void
  onRetry?: () => void
}

export function ErrorBanner({ message, onDismiss, onRetry }: ErrorBannerProps) {
  return (
    <div
      className="w-full px-4 py-3 flex items-center justify-between gap-4"
      style={{
        backgroundColor: 'rgba(255, 107, 107, 0.15)',
        borderBottom: '1px solid rgba(255, 107, 107, 0.3)',
      }}
    >
      <div className="flex items-center gap-2">
        <XCircle className="h-4 w-4 flex-shrink-0" style={{ color: '#ff6b6b' }} />
        <span className="text-sm" style={{ color: '#ff6b6b' }}>
          {message}
        </span>
      </div>
      <div className="flex items-center gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-sm px-2 py-1 rounded transition-colors hover:bg-white/10"
            style={{ color: '#ff6b6b' }}
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 rounded hover:bg-white/10 transition-colors"
            style={{ color: '#ff6b6b' }}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

interface InlineErrorProps {
  message: string
}

export function InlineError({ message }: InlineErrorProps) {
  return (
    <p className="text-sm flex items-center gap-1.5" style={{ color: '#ff6b6b' }}>
      <AlertCircle className="h-3.5 w-3.5" />
      {message}
    </p>
  )
}

interface PageErrorProps {
  title?: string
  message: string
  onRetry?: () => void
  children?: ReactNode
}

export function PageError({
  title = 'Error',
  message,
  onRetry,
  children,
}: PageErrorProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px] p-8">
      <div
        className="max-w-md w-full rounded-xl p-8 text-center"
        style={{
          backgroundColor: '#1a1a24',
          border: '1px solid rgba(255, 107, 107, 0.3)',
        }}
      >
        <XCircle
          className="h-12 w-12 mx-auto mb-4"
          style={{ color: '#ff6b6b' }}
        />
        <h2
          className="text-xl font-bold mb-2"
          style={{ color: '#ff6b6b' }}
        >
          {title}
        </h2>
        <p className="mb-6" style={{ color: '#b0b8c0' }}>
          {message}
        </p>
        {children}
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors mx-auto"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.15)',
              color: '#a8d8ff',
              border: '1px solid rgba(168, 216, 255, 0.3)',
            }}
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
        )}
      </div>
    </div>
  )
}

export default ErrorAlert
