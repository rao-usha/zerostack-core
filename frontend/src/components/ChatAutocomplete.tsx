import { useState, useEffect, useRef, useCallback, KeyboardEvent } from 'react'
import { Send, Loader2, Table2, Columns, Database, Tag } from 'lucide-react'

interface Suggestion {
  value: string
  type: 'table' | 'column' | 'schema' | 'command' | 'recent'
  context?: string // e.g., "from bls_ces_employment"
  icon?: React.ReactNode
}

interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string | null
  tool_name?: string | null
  tool_input?: any
  tool_output?: any
}

interface ChatAutocompleteProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  disabled?: boolean
  placeholder?: string
  messages: Message[]
}

// Common commands/phrases that can be autocompleted
const COMMAND_SUGGESTIONS: Suggestion[] = [
  { value: 'Show me all tables', type: 'command' },
  { value: 'Which tables have data dictionaries?', type: 'command' },
  { value: 'Explain the', type: 'command' },
  { value: 'Tell me about', type: 'command' },
  { value: 'What columns are in', type: 'command' },
  { value: 'Profile the', type: 'command' },
  { value: 'Sample rows from', type: 'command' },
  { value: 'Update the description for', type: 'command' },
]

export default function ChatAutocomplete({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = 'Ask about your data... (Tab to autocomplete)',
  messages
}: ChatAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [contextItems, setContextItems] = useState<Suggestion[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // Extract context from messages
  useEffect(() => {
    const items: Suggestion[] = []
    const seen = new Set<string>()

    for (const message of messages) {
      // Extract from tool outputs
      if (message.tool_output?.success && message.tool_output?.data) {
        const data = message.tool_output.data

        // Extract tables from discover_assets, list_tables, etc.
        if (data.assets) {
          for (const asset of data.assets) {
            const key = `table:${asset.schema}.${asset.table}`
            if (!seen.has(key)) {
              seen.add(key)
              items.push({
                value: `${asset.schema}.${asset.table}`,
                type: 'table',
                context: asset.business_name || asset.description?.substring(0, 50),
                icon: <Table2 size={14} />
              })
              // Also add just the table name
              if (!seen.has(`table:${asset.table}`)) {
                seen.add(`table:${asset.table}`)
                items.push({
                  value: asset.table,
                  type: 'table',
                  context: `in ${asset.schema}`,
                  icon: <Table2 size={14} />
                })
              }
            }
          }
        }

        // Extract from documented_tables (list_documented_tables)
        if (data.documented_tables) {
          for (const t of data.documented_tables) {
            const key = `table:${t.schema}.${t.table}`
            if (!seen.has(key)) {
              seen.add(key)
              items.push({
                value: `${t.schema}.${t.table}`,
                type: 'table',
                context: `${t.columns_documented} columns documented`,
                icon: <Table2 size={14} />
              })
            }
          }
        }

        // Extract columns from get_asset_documentation, explain_table
        if (data.column_definitions) {
          for (const col of data.column_definitions) {
            const key = `column:${col.column_name}`
            if (!seen.has(key)) {
              seen.add(key)
              items.push({
                value: col.column_name,
                type: 'column',
                context: col.business_name || col.description?.substring(0, 40),
                icon: <Columns size={14} />
              })
            }
          }
        }

        // Extract columns from raw structure
        if (data.columns) {
          for (const col of data.columns) {
            const colName = col.name || col.column_name
            if (colName) {
              const key = `column:${colName}`
              if (!seen.has(key)) {
                seen.add(key)
                items.push({
                  value: colName,
                  type: 'column',
                  context: col.type || col.data_type,
                  icon: <Columns size={14} />
                })
              }
            }
          }
        }

        // Extract from raw_structure.columns
        if (data.raw_structure?.columns) {
          for (const col of data.raw_structure.columns) {
            const key = `column:${col.name}`
            if (!seen.has(key)) {
              seen.add(key)
              items.push({
                value: col.name,
                type: 'column',
                context: col.type,
                icon: <Columns size={14} />
              })
            }
          }
        }

        // Extract schemas
        if (data.schemas) {
          for (const schema of data.schemas) {
            const schemaName = schema.name || schema
            const key = `schema:${schemaName}`
            if (!seen.has(key)) {
              seen.add(key)
              items.push({
                value: schemaName,
                type: 'schema',
                icon: <Database size={14} />
              })
            }
          }
        }

        // Extract from single table context
        if (data.table && typeof data.table === 'string') {
          const key = `table:${data.table}`
          if (!seen.has(key)) {
            seen.add(key)
            items.push({
              value: data.table,
              type: 'table',
              icon: <Table2 size={14} />
            })
          }
        }
      }

      // Extract table mentions from tool inputs
      if (message.tool_input) {
        const input = message.tool_input
        if (input.table && input.schema) {
          const fullName = `${input.schema}.${input.table}`
          const key = `table:${fullName}`
          if (!seen.has(key)) {
            seen.add(key)
            items.push({
              value: fullName,
              type: 'table',
              icon: <Table2 size={14} />
            })
          }
        }
        if (input.column) {
          const key = `column:${input.column}`
          if (!seen.has(key)) {
            seen.add(key)
            items.push({
              value: input.column,
              type: 'column',
              icon: <Columns size={14} />
            })
          }
        }
      }
    }

    setContextItems(items)
  }, [messages])

  // Filter suggestions based on input
  const updateSuggestions = useCallback((inputValue: string) => {
    if (!inputValue.trim()) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    const words = inputValue.split(/\s+/)
    const lastWord = words[words.length - 1].toLowerCase()
    const inputLower = inputValue.toLowerCase()

    // If the last word is very short, don't show suggestions yet
    if (lastWord.length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    const matches: Suggestion[] = []
    const addedValues = new Set<string>()

    // First, check for context items that match the last word
    for (const item of contextItems) {
      if (item.value.toLowerCase().includes(lastWord) && !addedValues.has(item.value)) {
        matches.push(item)
        addedValues.add(item.value)
      }
    }

    // Then check command suggestions that match the full input
    for (const cmd of COMMAND_SUGGESTIONS) {
      if (cmd.value.toLowerCase().startsWith(inputLower) && !addedValues.has(cmd.value)) {
        matches.push(cmd)
        addedValues.add(cmd.value)
      }
    }

    // Sort by type priority: tables first, then columns, then commands
    matches.sort((a, b) => {
      const priority = { table: 0, column: 1, schema: 2, recent: 3, command: 4 }
      return (priority[a.type] || 5) - (priority[b.type] || 5)
    })

    setSuggestions(matches.slice(0, 8))
    setShowSuggestions(matches.length > 0)
    setSelectedIndex(0)
  }, [contextItems])

  // Update suggestions when input changes
  useEffect(() => {
    updateSuggestions(value)
  }, [value, updateSuggestions])

  // Apply the selected suggestion
  const applySuggestion = (suggestion: Suggestion) => {
    const words = value.split(/\s+/)
    
    // For command suggestions, replace the entire input
    if (suggestion.type === 'command') {
      onChange(suggestion.value + ' ')
    } else {
      // For other suggestions, replace just the last word
      words[words.length - 1] = suggestion.value
      onChange(words.join(' ') + ' ')
    }
    
    setShowSuggestions(false)
    inputRef.current?.focus()
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        onSend()
      }
      return
    }

    switch (e.key) {
      case 'Tab':
        e.preventDefault()
        if (suggestions.length > 0) {
          applySuggestion(suggestions[selectedIndex])
        }
        break
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (suggestions.length > 0 && selectedIndex < suggestions.length) {
          applySuggestion(suggestions[selectedIndex])
        } else {
          onSend()
        }
        break
      case 'Escape':
        setShowSuggestions(false)
        break
    }
  }

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current && 
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'table': return 'Table'
      case 'column': return 'Column'
      case 'schema': return 'Schema'
      case 'command': return 'Command'
      default: return ''
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'table': return '#a8d8ff'
      case 'column': return '#c4b5fd'
      case 'schema': return '#ffc4e5'
      case 'command': return '#6ee7b7'
      default: return '#8ab3cc'
    }
  }

  return (
    <div className="relative">
      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute bottom-full left-0 right-0 mb-2 rounded-lg overflow-hidden shadow-lg"
          style={{
            backgroundColor: '#0f1419',
            border: '1px solid rgba(168, 216, 255, 0.3)',
            maxHeight: '300px',
            overflowY: 'auto'
          }}
        >
          <div className="px-3 py-2 text-xs" style={{ 
            color: '#8ab3cc',
            borderBottom: '1px solid rgba(168, 216, 255, 0.1)'
          }}>
            Press <kbd className="px-1.5 py-0.5 rounded text-xs" style={{
              backgroundColor: 'rgba(168, 216, 255, 0.1)',
              color: '#a8d8ff'
            }}>Tab</kbd> to complete • <kbd className="px-1.5 py-0.5 rounded text-xs" style={{
              backgroundColor: 'rgba(168, 216, 255, 0.1)',
              color: '#a8d8ff'
            }}>↑↓</kbd> to navigate
          </div>
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.type}-${suggestion.value}`}
              className="px-3 py-2 cursor-pointer flex items-center justify-between gap-2"
              style={{
                backgroundColor: index === selectedIndex 
                  ? 'rgba(168, 216, 255, 0.15)' 
                  : 'transparent',
                borderLeft: index === selectedIndex 
                  ? `3px solid ${getTypeColor(suggestion.type)}` 
                  : '3px solid transparent'
              }}
              onClick={() => applySuggestion(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span style={{ color: getTypeColor(suggestion.type) }}>
                  {suggestion.icon || <Tag size={14} />}
                </span>
                <span className="font-medium truncate" style={{ color: '#f0f0f5' }}>
                  {suggestion.value}
                </span>
                {suggestion.context && (
                  <span className="text-xs truncate" style={{ color: '#6a8399' }}>
                    {suggestion.context}
                  </span>
                )}
              </div>
              <span 
                className="text-xs px-2 py-0.5 rounded flex-shrink-0"
                style={{ 
                  backgroundColor: `${getTypeColor(suggestion.type)}20`,
                  color: getTypeColor(suggestion.type)
                }}
              >
                {getTypeLabel(suggestion.type)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="flex gap-3">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => updateSuggestions(value)}
          disabled={disabled}
          placeholder={placeholder}
          className="flex-1 px-4 py-3 rounded-xl focus:outline-none transition-all"
          style={{
            backgroundColor: '#0a0e1a',
            border: '1px solid rgba(168, 216, 255, 0.3)',
            color: '#f0f0f5'
          }}
        />
        <button
          onClick={onSend}
          disabled={!value.trim() || disabled}
          className="px-6 py-3 rounded-xl transition-all duration-200"
          style={!value.trim() || disabled ? {
            backgroundColor: 'rgba(168, 216, 255, 0.1)',
            border: '1px solid rgba(168, 216, 255, 0.2)',
            color: '#6a8399',
            cursor: 'not-allowed'
          } : {
            background: 'linear-gradient(90deg, rgba(168, 216, 255, 0.2), rgba(196, 181, 253, 0.2))',
            border: '1px solid rgba(168, 216, 255, 0.4)',
            color: '#a8d8ff'
          }}
        >
          {disabled ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <Send size={20} />
          )}
        </button>
      </div>

      {/* Context indicator */}
      {contextItems.length > 0 && (
        <div className="flex items-center gap-2 mt-2 text-xs" style={{ color: '#6a8399' }}>
          <span>Context:</span>
          <span style={{ color: '#a8d8ff' }}>
            {contextItems.filter(i => i.type === 'table').length} tables
          </span>
          <span>•</span>
          <span style={{ color: '#c4b5fd' }}>
            {contextItems.filter(i => i.type === 'column').length} columns
          </span>
          <span className="ml-auto" style={{ color: '#8ab3cc' }}>
            Type to see suggestions
          </span>
        </div>
      )}
    </div>
  )
}
