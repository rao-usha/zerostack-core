import { Plus, Trash2, AlertCircle } from 'lucide-react'
import type { ConditionOperator, GenerationCondition } from '../api/client'

interface ColumnInfo {
  name: string
  dtype: string
  unique_values?: any[]
}

interface ConditionBuilderProps {
  columns: ColumnInfo[]
  conditions: GenerationCondition[]
  onChange: (conditions: GenerationCondition[]) => void
}

const OPERATORS: { value: ConditionOperator; label: string; description: string }[] = [
  { value: 'eq', label: '=', description: 'Equals' },
  { value: 'ne', label: '!=', description: 'Not equals' },
  { value: 'gt', label: '>', description: 'Greater than' },
  { value: 'gte', label: '>=', description: 'Greater or equal' },
  { value: 'lt', label: '<', description: 'Less than' },
  { value: 'lte', label: '<=', description: 'Less or equal' },
  { value: 'in', label: 'IN', description: 'In list' },
  { value: 'not_in', label: 'NOT IN', description: 'Not in list' },
  { value: 'between', label: 'BETWEEN', description: 'Between min and max' },
]

const NUMERIC_OPERATORS: ConditionOperator[] = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'between', 'in', 'not_in']
const CATEGORICAL_OPERATORS: ConditionOperator[] = ['eq', 'ne', 'in', 'not_in']

function isNumericType(dtype: string): boolean {
  return ['int64', 'float64', 'int32', 'float32', 'int', 'float', 'number'].some(t =>
    dtype.toLowerCase().includes(t)
  )
}

function getValidOperators(dtype: string): ConditionOperator[] {
  return isNumericType(dtype) ? NUMERIC_OPERATORS : CATEGORICAL_OPERATORS
}

interface ConditionRowProps {
  condition: GenerationCondition
  index: number
  columns: ColumnInfo[]
  onUpdate: (index: number, condition: GenerationCondition) => void
  onRemove: (index: number) => void
}

function ConditionRow({ condition, index, columns, onUpdate, onRemove }: ConditionRowProps) {
  const selectedColumn = columns.find(c => c.name === condition.column)
  const validOperators = selectedColumn ? getValidOperators(selectedColumn.dtype) : OPERATORS.map(o => o.value)
  const isNumeric = selectedColumn ? isNumericType(selectedColumn.dtype) : false

  const handleColumnChange = (columnName: string) => {
    const col = columns.find(c => c.name === columnName)
    const newOperator = col && !getValidOperators(col.dtype).includes(condition.operator)
      ? 'eq'
      : condition.operator
    onUpdate(index, { ...condition, column: columnName, operator: newOperator, value: '' })
  }

  const handleOperatorChange = (operator: ConditionOperator) => {
    let newValue = condition.value
    // Reset value when switching to/from between or in operators
    if (operator === 'between' && !Array.isArray(condition.value)) {
      newValue = ['', '']
    } else if ((operator === 'in' || operator === 'not_in') && !Array.isArray(condition.value)) {
      newValue = []
    } else if (!['between', 'in', 'not_in'].includes(operator) && Array.isArray(condition.value)) {
      newValue = ''
    }
    onUpdate(index, { ...condition, operator, value: newValue })
  }

  const handleValueChange = (value: any) => {
    onUpdate(index, { ...condition, value })
  }

  const renderValueInput = () => {
    if (condition.operator === 'between') {
      const [min, max] = Array.isArray(condition.value) ? condition.value : ['', '']
      return (
        <div className="flex items-center gap-2">
          <input
            type={isNumeric ? 'number' : 'text'}
            value={min}
            onChange={(e) => handleValueChange([e.target.value, max])}
            placeholder="Min"
            className="flex-1 px-3 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text text-sm focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-dark-muted">to</span>
          <input
            type={isNumeric ? 'number' : 'text'}
            value={max}
            onChange={(e) => handleValueChange([min, e.target.value])}
            placeholder="Max"
            className="flex-1 px-3 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text text-sm focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )
    }

    if (condition.operator === 'in' || condition.operator === 'not_in') {
      const values = Array.isArray(condition.value) ? condition.value : []

      // If we have unique values from the column, show checkboxes
      if (selectedColumn?.unique_values && selectedColumn.unique_values.length <= 20) {
        return (
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border border-pastel-blue/20 rounded-lg bg-dark-surface">
            {selectedColumn.unique_values.map((uv: any) => (
              <label key={String(uv)} className="flex items-center gap-1 text-sm text-dark-text cursor-pointer">
                <input
                  type="checkbox"
                  checked={values.includes(uv)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      handleValueChange([...values, uv])
                    } else {
                      handleValueChange(values.filter((v: any) => v !== uv))
                    }
                  }}
                  className="rounded border-pastel-blue/20"
                />
                {String(uv)}
              </label>
            ))}
          </div>
        )
      }

      // Otherwise, show a comma-separated input
      return (
        <input
          type="text"
          value={values.join(', ')}
          onChange={(e) => handleValueChange(e.target.value.split(',').map(v => v.trim()).filter(v => v))}
          placeholder="value1, value2, value3"
          className="w-full px-3 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text text-sm focus:ring-2 focus:ring-blue-500"
        />
      )
    }

    // Single value - show dropdown if unique values available
    if (selectedColumn?.unique_values && selectedColumn.unique_values.length <= 50 && !isNumeric) {
      return (
        <select
          value={condition.value || ''}
          onChange={(e) => handleValueChange(e.target.value)}
          className="w-full px-3 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text text-sm focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select value...</option>
          {selectedColumn.unique_values.map((uv: any) => (
            <option key={String(uv)} value={uv}>{String(uv)}</option>
          ))}
        </select>
      )
    }

    return (
      <input
        type={isNumeric ? 'number' : 'text'}
        value={condition.value || ''}
        onChange={(e) => handleValueChange(isNumeric ? parseFloat(e.target.value) || e.target.value : e.target.value)}
        placeholder="Enter value"
        className="w-full px-3 py-2 border border-pastel-blue/20 rounded-lg bg-dark-surface text-dark-text text-sm focus:ring-2 focus:ring-blue-500"
      />
    )
  }

  return (
    <div className="flex items-start gap-3 p-3 bg-dark-surface rounded-lg border border-pastel-blue/10">
      {/* Column selector */}
      <div className="flex-1 min-w-0">
        <label className="block text-xs text-dark-muted mb-1">Column</label>
        <select
          value={condition.column}
          onChange={(e) => handleColumnChange(e.target.value)}
          className="w-full px-3 py-2 border border-pastel-blue/20 rounded-lg bg-dark-card text-dark-text text-sm focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select column...</option>
          {columns.map(col => (
            <option key={col.name} value={col.name}>
              {col.name} ({col.dtype})
            </option>
          ))}
        </select>
      </div>

      {/* Operator selector */}
      <div className="w-28">
        <label className="block text-xs text-dark-muted mb-1">Operator</label>
        <select
          value={condition.operator}
          onChange={(e) => handleOperatorChange(e.target.value as ConditionOperator)}
          className="w-full px-3 py-2 border border-pastel-blue/20 rounded-lg bg-dark-card text-dark-text text-sm focus:ring-2 focus:ring-blue-500"
        >
          {OPERATORS.filter(op => validOperators.includes(op.value)).map(op => (
            <option key={op.value} value={op.value} title={op.description}>
              {op.label}
            </option>
          ))}
        </select>
      </div>

      {/* Value input */}
      <div className="flex-1 min-w-0">
        <label className="block text-xs text-dark-muted mb-1">Value</label>
        {renderValueInput()}
      </div>

      {/* Remove button */}
      <button
        onClick={() => onRemove(index)}
        className="mt-6 p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
        title="Remove condition"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  )
}

export default function ConditionBuilder({ columns, conditions, onChange }: ConditionBuilderProps) {
  const addCondition = () => {
    const newCondition: GenerationCondition = {
      column: columns.length > 0 ? columns[0].name : '',
      operator: 'eq',
      value: '',
    }
    onChange([...conditions, newCondition])
  }

  const updateCondition = (index: number, condition: GenerationCondition) => {
    const newConditions = [...conditions]
    newConditions[index] = condition
    onChange(newConditions)
  }

  const removeCondition = (index: number) => {
    onChange(conditions.filter((_, i) => i !== index))
  }

  // Validate conditions
  const getValidationErrors = (): string[] => {
    const errors: string[] = []
    conditions.forEach((cond, i) => {
      if (!cond.column) {
        errors.push(`Condition ${i + 1}: Select a column`)
      }
      if (cond.operator === 'between') {
        const [min, max] = Array.isArray(cond.value) ? cond.value : ['', '']
        if (!min || !max) {
          errors.push(`Condition ${i + 1}: Both min and max values required for BETWEEN`)
        }
      } else if (cond.operator === 'in' || cond.operator === 'not_in') {
        if (!Array.isArray(cond.value) || cond.value.length === 0) {
          errors.push(`Condition ${i + 1}: At least one value required for ${cond.operator.toUpperCase()}`)
        }
      } else if (!cond.value && cond.value !== 0) {
        errors.push(`Condition ${i + 1}: Value is required`)
      }
    })
    return errors
  }

  const errors = getValidationErrors()

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-dark-text">Generation Conditions</h3>
        <button
          onClick={addCondition}
          disabled={columns.length === 0}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-bright-blue/20 text-bright-blue hover:bg-bright-blue/30 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="h-4 w-4" />
          Add Condition
        </button>
      </div>

      {columns.length === 0 ? (
        <div className="text-center py-8 text-dark-muted">
          <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>Upload a file first to define conditions</p>
        </div>
      ) : conditions.length === 0 ? (
        <div className="text-center py-8 border-2 border-dashed border-pastel-blue/20 rounded-lg">
          <p className="text-dark-muted">No conditions defined</p>
          <p className="text-sm text-dark-muted mt-1">
            Add conditions to generate data matching specific criteria
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {conditions.map((condition, index) => (
            <ConditionRow
              key={index}
              condition={condition}
              index={index}
              columns={columns}
              onUpdate={updateCondition}
              onRemove={removeCondition}
            />
          ))}
        </div>
      )}

      {errors.length > 0 && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-red-400">
              {errors.map((error, i) => (
                <p key={i}>{error}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {conditions.length > 0 && errors.length === 0 && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
          <p className="text-sm text-green-400">
            {conditions.length} condition{conditions.length > 1 ? 's' : ''} configured
          </p>
        </div>
      )}
    </div>
  )
}
