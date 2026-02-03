import React, { useState, useEffect } from 'react'
import { getLineageSummary, analyzeImpact } from '../api/client'

interface LineageHealthBadgeProps {
  entityType: string
  entityId: string
  showDetails?: boolean
}

/**
 * Lineage Health Badge - Shows health status with visual indicators
 * Displays: freshness, dependencies, risk level
 */
const LineageHealthBadge: React.FC<LineageHealthBadgeProps> = ({ 
  entityType, 
  entityId,
  showDetails = false
}) => {
  const [health, setHealth] = useState<any>(null)
  const [impact, setImpact] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadHealth()
  }, [entityType, entityId])

  const loadHealth = async () => {
    try {
      setLoading(true)
      const [summaryData, impactData] = await Promise.all([
        getLineageSummary(entityType, entityId),
        analyzeImpact(entityType, entityId).catch(() => null)
      ])
      setHealth(summaryData)
      setImpact(impactData)
    } catch (err) {
      console.error('Failed to load health:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-full animate-pulse">
        <div className="w-4 h-4 bg-gray-300 rounded-full"></div>
        <div className="w-20 h-3 bg-gray-300 rounded"></div>
      </div>
    )
  }

  if (!health) return null

  // Calculate health score
  const hasUpstream = health.upstream_count > 0
  const hasDownstream = health.downstream_count > 0
  const isStale = health.is_stale
  const riskLevel = impact?.risk_level || 'low'

  let statusColor = 'green'
  let statusIcon = '✓'
  let statusText = 'Healthy'

  if (isStale) {
    statusColor = 'yellow'
    statusIcon = '⚠'
    statusText = 'Stale Data'
  } else if (riskLevel === 'high') {
    statusColor = 'orange'
    statusIcon = '⚡'
    statusText = 'High Impact'
  } else if (!hasUpstream && hasDownstream) {
    statusColor = 'blue'
    statusIcon = '📍'
    statusText = 'Data Source'
  } else if (hasUpstream && !hasDownstream) {
    statusColor = 'purple'
    statusIcon = '🎯'
    statusText = 'End Point'
  }

  const colorClasses = {
    green: 'bg-green-100 text-green-800 border-green-200',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    orange: 'bg-orange-100 text-orange-800 border-orange-200',
    blue: 'bg-blue-100 text-blue-800 border-blue-200',
    purple: 'bg-purple-100 text-purple-800 border-purple-200',
  }

  return (
    <div className="inline-block">
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${colorClasses[statusColor as keyof typeof colorClasses]}`}>
        <span className="text-sm">{statusIcon}</span>
        <span className="text-xs font-medium">{statusText}</span>
        {showDetails && (
          <span className="text-xs opacity-75">
            {health.upstream_count}⬆ {health.downstream_count}⬇
          </span>
        )}
      </div>

      {showDetails && impact && (
        <div className="mt-2 text-xs text-gray-600">
          {impact.affected_downstream_count > 0 && (
            <div>⚡ {impact.affected_downstream_count} entities affected by changes</div>
          )}
        </div>
      )}
    </div>
  )
}

export default LineageHealthBadge
