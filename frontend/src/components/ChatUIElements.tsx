import { Check, X, Edit2, ChevronDown } from 'lucide-react'
import { useState } from 'react'

interface ButtonElement {
  type: 'button'
  label: string
  action: string
}

interface DropdownElement {
  type: 'dropdown'
  id: string
  label: string
  source: string
  options?: Array<{value: string, label: string}>
}

interface ToggleElement {
  type: 'toggle'
  options: string[]
  default: string
}

type UIElement = ButtonElement | DropdownElement | ToggleElement

interface ChatUIElementsProps {
  elements: UIElement[]
  onAction: (action: string, data?: any) => void
  availableOntologies?: Array<{id: string, name: string}>
}

export default function ChatUIElements({ elements, onAction, availableOntologies = [] }: ChatUIElementsProps) {
  const [selectedOntology, setSelectedOntology] = useState('')
  const [selectedToggle, setSelectedToggle] = useState('')

  const renderButton = (element: ButtonElement) => {
    const iconMap: {[key: string]: any} = {
      confirm: Check,
      cancel: X,
      edit_name: Edit2,
      edit_count: Edit2,
    }
    
    const Icon = iconMap[element.action]
    
    const colorMap: {[key: string]: string} = {
      confirm: 'bg-accent-blue hover:bg-accent-blue/80',
      cancel: 'bg-dark-muted hover:bg-dark-muted/80',
      default: 'bg-pastel-purple hover:bg-pastel-purple/80'
    }
    
    const colorClass = colorMap[element.action] || colorMap.default

    return (
      <button
        key={element.label}
        onClick={() => onAction(element.action)}
        className={`inline-flex items-center gap-2 px-4 py-2 ${colorClass} rounded-lg transition-all text-white font-medium shadow-lg hover:shadow-xl`}
      >
        {Icon && <Icon className="w-4 h-4" />}
        {element.label}
      </button>
    )
  }

  const renderDropdown = (element: DropdownElement) => {
    const options = element.source === 'ontologies' ? availableOntologies : (element.options || [])
    
    return (
      <div key={element.id} className="flex flex-col gap-2 min-w-[250px]">
        <label className="text-sm font-medium text-dark-text">{element.label}</label>
        <div className="relative">
          <select
            value={selectedOntology}
            onChange={(e) => {
              setSelectedOntology(e.target.value)
              onAction('select', { ontology_id: e.target.value })
            }}
            className="w-full px-4 py-2 bg-dark-surface border border-pastel-blue/20 rounded-lg focus:ring-2 focus:ring-accent-blue focus:border-accent-blue text-dark-text appearance-none pr-10"
          >
            <option value="">Select an option...</option>
            {options.map((opt: any) => (
              <option key={opt.id || opt.value} value={opt.id || opt.value}>
                {opt.name || opt.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-muted pointer-events-none" />
        </div>
      </div>
    )
  }

  const renderToggle = (element: ToggleElement) => {
    const [active, setActive] = useState(element.default || element.options[0])

    return (
      <div key="toggle" className="inline-flex items-center gap-1 bg-dark-surface rounded-lg p-1">
        {element.options.map((option) => (
          <button
            key={option}
            onClick={() => {
              setActive(option)
              onAction('toggle_view', { view: option })
            }}
            className={`px-4 py-2 rounded-md transition-all font-medium ${
              active === option
                ? 'bg-accent-blue text-white shadow-md'
                : 'text-dark-muted hover:text-dark-text'
            }`}
          >
            {option}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-3 mt-3">
      {elements.map((element) => {
        switch (element.type) {
          case 'button':
            return renderButton(element)
          case 'dropdown':
            return renderDropdown(element)
          case 'toggle':
            return renderToggle(element)
          default:
            return null
        }
      })}
    </div>
  )
}


