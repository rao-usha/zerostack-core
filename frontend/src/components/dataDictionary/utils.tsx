/**
 * Shared utilities for Data Dictionary components.
 */
import React from 'react'

/**
 * Render a state badge with appropriate styling.
 */
export function renderStateBadge(state: string): React.ReactNode {
  const colors = {
    draft: { bg: 'rgba(168, 216, 255, 0.1)', text: '#a8d8ff', border: 'rgba(168, 216, 255, 0.3)' },
    pending_approval: { bg: 'rgba(251, 191, 36, 0.1)', text: '#fbbf24', border: 'rgba(251, 191, 36, 0.3)' },
    published: { bg: 'rgba(34, 197, 94, 0.1)', text: '#22c55e', border: 'rgba(34, 197, 94, 0.3)' }
  }
  const color = colors[state as keyof typeof colors] || colors.draft
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '0.75rem',
      fontWeight: '500',
      backgroundColor: color.bg,
      color: color.text,
      border: `1px solid ${color.border}`,
      display: 'inline-block',
      textTransform: 'capitalize'
    }}>
      {state.replace('_', ' ')}
    </span>
  )
}
