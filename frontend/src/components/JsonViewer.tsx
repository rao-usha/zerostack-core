import { useState } from 'react'
import { ChevronRight, ChevronDown } from 'lucide-react'

interface JsonViewerProps {
  data: any
  level?: number
}

function JsonViewer({ data, level = 0 }: JsonViewerProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())

  const toggleKey = (key: string) => {
    const newExpanded = new Set(expandedKeys)
    if (newExpanded.has(key)) {
      newExpanded.delete(key)
    } else {
      newExpanded.add(key)
    }
    setExpandedKeys(newExpanded)
  }

  const renderValue = (value: any, key?: string, path: string = ''): JSX.Element => {
    const fullPath = key ? `${path}.${key}` : path
    const isExpanded = expandedKeys.has(fullPath)

    if (value === null) {
      return <span style={{ color: '#fca5a5' }}>null</span>
    }

    if (value === undefined) {
      return <span style={{ color: '#fca5a5' }}>undefined</span>
    }

    if (typeof value === 'string') {
      return <span style={{ color: '#86efac' }}>"{value}"</span>
    }

    if (typeof value === 'number') {
      return <span style={{ color: '#fbbf24' }}>{value}</span>
    }

    if (typeof value === 'boolean') {
      return <span style={{ color: '#a78bfa' }}>{value.toString()}</span>
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <span style={{ color: '#b3d9ff' }}>[]</span>
      }
      return (
        <div className="ml-4">
          <button
            onClick={() => toggleKey(fullPath)}
            className="flex items-center space-x-1 mb-1"
            style={{ color: '#a8d8ff' }}
          >
            {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            <span className="text-xs font-mono">[{value.length}]</span>
          </button>
          {isExpanded && (
            <div className="ml-4 space-y-1">
              {value.map((item, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span style={{ color: '#b3d9ff' }}>[{idx}]:</span>
                  <div className="flex-1">{renderValue(item, undefined, `${fullPath}[${idx}]`)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }

    if (typeof value === 'object') {
      const keys = Object.keys(value)
      if (keys.length === 0) {
        return <span style={{ color: '#b3d9ff' }}>{'{}'}</span>
      }
      return (
        <div className="ml-4">
          <button
            onClick={() => toggleKey(fullPath)}
            className="flex items-center space-x-1 mb-1"
            style={{ color: '#a8d8ff' }}
          >
            {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
            <span className="text-xs font-mono">{'{'}{keys.length} keys{'}'}</span>
          </button>
          {isExpanded && (
            <div className="ml-4 space-y-1">
              {keys.map((k) => (
                <div key={k} className="flex items-start space-x-2">
                  <span className="font-mono text-xs" style={{ color: '#a8d8ff' }}>"{k}":</span>
                  <div className="flex-1">{renderValue(value[k], k, fullPath)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }

    return <span>{String(value)}</span>
  }

  return (
    <div className="font-mono text-xs" style={{ color: '#f0f0f5' }}>
      {renderValue(data)}
    </div>
  )
}

export default JsonViewer

