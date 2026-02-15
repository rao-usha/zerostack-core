/**
 * Reusable empty state component for displaying "no data" scenarios.
 */
import { ReactNode } from 'react'
import {
  Database,
  FileText,
  Folder,
  Inbox,
  Search,
  Table,
  LucideIcon,
} from 'lucide-react'

type EmptyStateVariant =
  | 'default'
  | 'search'
  | 'table'
  | 'files'
  | 'folder'
  | 'database'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: LucideIcon
  variant?: EmptyStateVariant
  action?: {
    label: string
    onClick: () => void
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  children?: ReactNode
  compact?: boolean
}

const variantIcons: Record<EmptyStateVariant, LucideIcon> = {
  default: Inbox,
  search: Search,
  table: Table,
  files: FileText,
  folder: Folder,
  database: Database,
}

export function EmptyState({
  title,
  description,
  icon,
  variant = 'default',
  action,
  secondaryAction,
  children,
  compact = false,
}: EmptyStateProps) {
  const Icon = icon || variantIcons[variant]

  if (compact) {
    return (
      <div className="py-8 text-center">
        <Icon
          className="h-8 w-8 mx-auto mb-2 opacity-50"
          style={{ color: '#a8d8ff' }}
        />
        <p className="text-sm font-medium" style={{ color: '#b0b8c0' }}>
          {title}
        </p>
        {description && (
          <p className="text-xs mt-1" style={{ color: '#8090a0' }}>
            {description}
          </p>
        )}
        {action && (
          <button
            onClick={action.onClick}
            className="mt-3 text-sm px-3 py-1.5 rounded-lg transition-colors"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.15)',
              color: '#a8d8ff',
            }}
          >
            {action.label}
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center min-h-[300px] p-8">
      <div
        className="max-w-md w-full rounded-xl p-8 text-center"
        style={{
          backgroundColor: '#1a1a24',
          border: '1px solid rgba(168, 216, 255, 0.15)',
        }}
      >
        <Icon
          className="h-16 w-16 mx-auto mb-4 opacity-50"
          style={{ color: '#a8d8ff' }}
        />
        <h3
          className="text-xl font-semibold mb-2"
          style={{ color: '#f0f0f5' }}
        >
          {title}
        </h3>
        {description && (
          <p className="mb-6" style={{ color: '#b0b8c0' }}>
            {description}
          </p>
        )}
        {children}
        {(action || secondaryAction) && (
          <div className="flex gap-3 justify-center mt-6">
            {action && (
              <button
                onClick={action.onClick}
                className="px-4 py-2 rounded-lg transition-colors"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.15)',
                  color: '#a8d8ff',
                  border: '1px solid rgba(168, 216, 255, 0.3)',
                }}
              >
                {action.label}
              </button>
            )}
            {secondaryAction && (
              <button
                onClick={secondaryAction.onClick}
                className="px-4 py-2 rounded-lg transition-colors"
                style={{
                  backgroundColor: 'transparent',
                  color: '#b0b8c0',
                  border: '1px solid rgba(176, 184, 192, 0.3)',
                }}
              >
                {secondaryAction.label}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

interface NoResultsProps {
  query?: string
  onClear?: () => void
}

export function NoResults({ query, onClear }: NoResultsProps) {
  return (
    <EmptyState
      variant="search"
      title="No results found"
      description={
        query
          ? `No results match "${query}". Try adjusting your search.`
          : 'Try adjusting your filters or search terms.'
      }
      action={onClear ? { label: 'Clear search', onClick: onClear } : undefined}
      compact
    />
  )
}

interface NoDataProps {
  resource: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function NoData({ resource, action }: NoDataProps) {
  return (
    <EmptyState
      variant="table"
      title={`No ${resource} yet`}
      description={`Get started by creating your first ${resource.toLowerCase()}.`}
      action={action}
    />
  )
}

export default EmptyState
