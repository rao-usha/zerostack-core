/**
 * Error Boundary component for catching unhandled React errors.
 * Prevents the entire app from crashing when a component fails.
 */
import { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo })
    this.props.onError?.(error, errorInfo)

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div
            className="max-w-md w-full rounded-xl p-8 text-center"
            style={{
              backgroundColor: '#1a1a24',
              border: '1px solid rgba(255, 107, 107, 0.3)',
            }}
          >
            <AlertTriangle
              className="h-16 w-16 mx-auto mb-4"
              style={{ color: '#ff6b6b' }}
            />
            <h2
              className="text-2xl font-bold mb-2"
              style={{ color: '#ff6b6b' }}
            >
              Something went wrong
            </h2>
            <p className="mb-6" style={{ color: '#b0b8c0' }}>
              An unexpected error occurred. Please try again or return to the home page.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div
                className="mb-6 p-4 rounded-lg text-left overflow-auto max-h-40"
                style={{
                  backgroundColor: 'rgba(255, 107, 107, 0.1)',
                  fontSize: '0.75rem',
                }}
              >
                <p className="font-mono text-red-400 break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.15)',
                  color: '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                }}
              >
                <RefreshCw className="h-4 w-4" />
                Try Again
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors"
                style={{
                  backgroundColor: 'rgba(196, 181, 253, 0.15)',
                  color: '#c4b5fd',
                  border: '1px solid rgba(196, 181, 253, 0.3)',
                }}
              >
                <Home className="h-4 w-4" />
                Go Home
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
