import { ReactNode, useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'
import { LucideIcon } from 'lucide-react'

interface NavGroupProps {
  title: string
  icon: LucideIcon
  children: ReactNode
  defaultExpanded?: boolean
  isActive?: boolean
  storageKey: string
}

export default function NavGroup({
  title,
  icon: Icon,
  children,
  defaultExpanded = false,
  isActive = false,
  storageKey
}: NavGroupProps) {
  const [isExpanded, setIsExpanded] = useState(() => {
    const stored = localStorage.getItem(`nav-group-${storageKey}`)
    if (stored !== null) {
      return stored === 'true'
    }
    return defaultExpanded
  })

  // Auto-expand when a child becomes active
  useEffect(() => {
    if (isActive && !isExpanded) {
      setIsExpanded(true)
    }
  }, [isActive])

  // Persist state to localStorage
  useEffect(() => {
    localStorage.setItem(`nav-group-${storageKey}`, String(isExpanded))
  }, [isExpanded, storageKey])

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded)
  }

  return (
    <div className="mb-1">
      <button
        onClick={toggleExpanded}
        className="w-full flex items-center justify-between px-4 py-3 rounded-lg transition-all duration-200 hover:bg-dark-border/30"
        style={isActive ? {
          background: 'rgba(168, 216, 255, 0.08)',
          color: '#a8d8ff'
        } : {
          color: '#c0c0c8'
        }}
      >
        <div className="flex items-center space-x-3">
          <Icon className="h-5 w-5" />
          <span className="font-semibold text-sm">{title}</span>
        </div>
        <ChevronDown
          className={`h-4 w-4 transition-transform duration-200 ${
            isExpanded ? 'rotate-0' : '-rotate-90'
          }`}
        />
      </button>

      <div
        className={`overflow-hidden transition-all duration-200 ease-in-out ${
          isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="pl-3 mt-1 space-y-1">
          {children}
        </div>
      </div>
    </div>
  )
}
