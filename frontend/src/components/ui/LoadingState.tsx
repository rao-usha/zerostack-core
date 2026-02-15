/**
 * Reusable loading state components.
 */
import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  return (
    <Loader2
      className={`animate-spin ${sizeClasses[size]} ${className}`}
      style={{ color: '#a8d8ff' }}
    />
  )
}

interface LoadingOverlayProps {
  message?: string
}

export function LoadingOverlay({ message }: LoadingOverlayProps) {
  return (
    <div
      className="absolute inset-0 flex items-center justify-center z-10"
      style={{ backgroundColor: 'rgba(13, 13, 20, 0.8)' }}
    >
      <div className="text-center">
        <LoadingSpinner size="lg" />
        {message && (
          <p className="mt-4 text-sm" style={{ color: '#b0b8c0' }}>
            {message}
          </p>
        )}
      </div>
    </div>
  )
}

interface LoadingPageProps {
  message?: string
}

export function LoadingPage({ message = 'Loading...' }: LoadingPageProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4" style={{ color: '#b0b8c0' }}>
          {message}
        </p>
      </div>
    </div>
  )
}

interface LoadingInlineProps {
  message?: string
}

export function LoadingInline({ message }: LoadingInlineProps) {
  return (
    <div className="flex items-center gap-2 py-2">
      <LoadingSpinner size="sm" />
      {message && (
        <span className="text-sm" style={{ color: '#b0b8c0' }}>
          {message}
        </span>
      )}
    </div>
  )
}

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
}

export function Skeleton({
  className = '',
  variant = 'text',
  width,
  height,
}: SkeletonProps) {
  const baseClasses = 'animate-pulse'

  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  }

  const style: React.CSSProperties = {
    backgroundColor: 'rgba(168, 216, 255, 0.1)',
    width: width,
    height: height,
  }

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  )
}

interface SkeletonTableProps {
  rows?: number
  columns?: number
}

export function SkeletonTable({ rows = 5, columns = 4 }: SkeletonTableProps) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex gap-4 pb-3 border-b" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="flex-1 h-4" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4 py-2">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="flex-1 h-4" />
          ))}
        </div>
      ))}
    </div>
  )
}

interface SkeletonCardProps {
  hasImage?: boolean
}

export function SkeletonCard({ hasImage = false }: SkeletonCardProps) {
  return (
    <div
      className="rounded-xl p-4"
      style={{
        backgroundColor: '#1a1a24',
        border: '1px solid rgba(168, 216, 255, 0.1)',
      }}
    >
      {hasImage && (
        <Skeleton variant="rectangular" className="w-full h-32 mb-4" />
      )}
      <Skeleton className="w-3/4 h-5 mb-3" />
      <Skeleton className="w-full h-4 mb-2" />
      <Skeleton className="w-2/3 h-4" />
    </div>
  )
}

export default LoadingSpinner
