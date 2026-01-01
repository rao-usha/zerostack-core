/**
 * Dictionary Semantics Tabs Component
 * Provides Decision Context, Guarantees, and Validation tabs for dictionary entries
 */
import { useState, useEffect } from 'react'
import { Save, X, AlertCircle, Check, Plus, Trash2 } from 'lucide-react'
import {
  getSemantics,
  updateSemantics,
  getGrain,
  updateGrain,
  DecisionContext,
  SemanticGuarantees,
  ValidationState,
  DictionaryGrain
} from '../api/client'

interface Props {
  entryId: string
  onClose?: () => void
}

export default function DictionarySemanticsTabs({ entryId, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<'decision' | 'guarantees' | 'validation' | 'grain'>('decision')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Semantics state
  const [decisionContext, setDecisionContext] = useState<DecisionContext>({})
  const [semanticGuarantees, setSemanticGuarantees] = useState<SemanticGuarantees>({})
  const [validationState, setValidationState] = useState<ValidationState>({})
  
  // Grain state
  const [grain, setGrain] = useState<Partial<DictionaryGrain> | null>(null)

  useEffect(() => {
    loadData()
  }, [entryId])

  const loadData = async () => {
    try {
      setLoading(true)
      const [semantics, grainData] = await Promise.all([
        getSemantics(entryId),
        getGrain(entryId)
      ])
      
      setDecisionContext(semantics.decision_context || {})
      setSemanticGuarantees(semantics.semantic_guarantees || {})
      setValidationState(semantics.validation_state || {})
      setGrain(grainData)
    } catch (err: any) {
      console.error('Failed to load semantics:', err)
      setError('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const saveSemantics = async () => {
    try {
      setSaving(true)
      setError(null)
      await updateSemantics(entryId, {
        decision_context: decisionContext,
        semantic_guarantees: semanticGuarantees,
        validation_state: validationState,
        create_version: false
      })
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const saveGrain = async () => {
    if (!grain || !grain.entity) {
      setError('Entity is required for grain')
      return
    }

    try {
      setSaving(true)
      setError(null)
      await updateGrain(entryId, {
        entity: grain.entity,
        primary_key: grain.primary_key,
        time_grain: grain.time_grain,
        natural_key: grain.natural_key,
        notes: grain.notes
      })
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save grain')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: '#0a0a0f' }}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'rgba(168, 216, 255, 0.2)' }}>
        <h2 className="text-xl font-semibold" style={{ color: '#f0f0f5' }}>
          Entry Semantics
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 rounded hover:bg-gray-800"
            style={{ color: '#a8d8ff' }}
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b" style={{ borderColor: 'rgba(168, 216, 255, 0.2)' }}>
        {[
          { id: 'decision', label: 'Decision Context' },
          { id: 'guarantees', label: 'Guarantees' },
          { id: 'validation', label: 'Validation' },
          { id: 'grain', label: 'Grain' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-b-2'
                : 'hover:bg-gray-800'
            }`}
            style={{
              color: activeTab === tab.id ? '#a8d8ff' : '#b0b8c0',
              borderColor: activeTab === tab.id ? '#a8d8ff' : 'transparent'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4 p-3 rounded flex items-center gap-2" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}>
            <AlertCircle className="h-5 w-5" />
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 rounded flex items-center gap-2" style={{ backgroundColor: 'rgba(34, 197, 94, 0.1)', color: '#22c55e' }}>
            <Check className="h-5 w-5" />
            Saved successfully
          </div>
        )}

        {activeTab === 'decision' && (
          <DecisionContextTab
            context={decisionContext}
            onChange={setDecisionContext}
          />
        )}

        {activeTab === 'guarantees' && (
          <GuaranteesTab
            guarantees={semanticGuarantees}
            onChange={setSemanticGuarantees}
          />
        )}

        {activeTab === 'validation' && (
          <ValidationTab
            validation={validationState}
            onChange={setValidationState}
          />
        )}

        {activeTab === 'grain' && (
          <GrainTab
            grain={grain}
            onChange={setGrain}
          />
        )}
      </div>

      {/* Footer */}
      <div className="flex justify-end gap-3 p-4 border-t" style={{ borderColor: 'rgba(168, 216, 255, 0.2)' }}>
        <button
          onClick={activeTab === 'grain' ? saveGrain : saveSemantics}
          disabled={saving}
          className="px-4 py-2 rounded flex items-center gap-2 font-medium transition-colors disabled:opacity-50"
          style={{ backgroundColor: '#a8d8ff', color: '#0a0a0f' }}
        >
          <Save className="h-4 w-4" />
          {saving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </div>
  )
}

// ==================== Decision Context Tab ====================

function DecisionContextTab({ context, onChange }: { context: DecisionContext; onChange: (c: DecisionContext) => void }) {
  const addItem = (field: 'primary_decisions' | 'secondary_decisions') => {
    onChange({
      ...context,
      [field]: [...(context[field] || []), '']
    })
  }

  const updateItem = (field: 'primary_decisions' | 'secondary_decisions', index: number, value: string) => {
    const items = [...(context[field] || [])]
    items[index] = value
    onChange({ ...context, [field]: items })
  }

  const removeItem = (field: 'primary_decisions' | 'secondary_decisions', index: number) => {
    const items = [...(context[field] || [])]
    items.splice(index, 1)
    onChange({ ...context, [field]: items })
  }

  const addConsumer = () => {
    onChange({
      ...context,
      consumers: [...(context.consumers || []), { role: '' }]
    })
  }

  const updateConsumer = (index: number, field: string, value: string) => {
    const consumers = [...(context.consumers || [])]
    consumers[index] = { ...consumers[index], [field]: value }
    onChange({ ...context, consumers })
  }

  const removeConsumer = (index: number) => {
    const consumers = [...(context.consumers || [])]
    consumers.splice(index, 1)
    onChange({ ...context, consumers })
  }

  return (
    <div className="space-y-6">
      {/* Primary Decisions */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium" style={{ color: '#f0f0f5' }}>
            Primary Decisions
          </label>
          <button
            onClick={() => addItem('primary_decisions')}
            className="text-sm flex items-center gap-1 hover:underline"
            style={{ color: '#a8d8ff' }}
          >
            <Plus className="h-4 w-4" /> Add
          </button>
        </div>
        {(context.primary_decisions || []).map((decision, idx) => (
          <div key={idx} className="flex gap-2 mb-2">
            <input
              type="text"
              value={decision}
              onChange={(e) => updateItem('primary_decisions', idx, e.target.value)}
              className="flex-1 px-3 py-2 rounded border"
              style={{
                backgroundColor: '#1a1a24',
                borderColor: 'rgba(168, 216, 255, 0.2)',
                color: '#f0f0f5'
              }}
              placeholder="e.g., Determine customer eligibility"
            />
            <button
              onClick={() => removeItem('primary_decisions', idx)}
              className="p-2 rounded hover:bg-red-900/20"
              style={{ color: '#ef4444' }}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Secondary Decisions */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium" style={{ color: '#f0f0f5' }}>
            Secondary Decisions
          </label>
          <button
            onClick={() => addItem('secondary_decisions')}
            className="text-sm flex items-center gap-1 hover:underline"
            style={{ color: '#a8d8ff' }}
          >
            <Plus className="h-4 w-4" /> Add
          </button>
        </div>
        {(context.secondary_decisions || []).map((decision, idx) => (
          <div key={idx} className="flex gap-2 mb-2">
            <input
              type="text"
              value={decision}
              onChange={(e) => updateItem('secondary_decisions', idx, e.target.value)}
              className="flex-1 px-3 py-2 rounded border"
              style={{
                backgroundColor: '#1a1a24',
                borderColor: 'rgba(168, 216, 255, 0.2)',
                color: '#f0f0f5'
              }}
              placeholder="e.g., Calculate discount tier"
            />
            <button
              onClick={() => removeItem('secondary_decisions', idx)}
              className="p-2 rounded hover:bg-red-900/20"
              style={{ color: '#ef4444' }}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Consumers */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium" style={{ color: '#f0f0f5' }}>
            Consumers
          </label>
          <button
            onClick={addConsumer}
            className="text-sm flex items-center gap-1 hover:underline"
            style={{ color: '#a8d8ff' }}
          >
            <Plus className="h-4 w-4" /> Add
          </button>
        </div>
        {(context.consumers || []).map((consumer, idx) => (
          <div key={idx} className="flex gap-2 mb-2 p-3 rounded border" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
            <div className="flex-1 space-y-2">
              <input
                type="text"
                value={consumer.role}
                onChange={(e) => updateConsumer(idx, 'role', e.target.value)}
                className="w-full px-3 py-2 rounded border"
                style={{
                  backgroundColor: '#1a1a24',
                  borderColor: 'rgba(168, 216, 255, 0.2)',
                  color: '#f0f0f5'
                }}
                placeholder="Role (e.g., Data Analyst)"
              />
              <input
                type="text"
                value={consumer.team || ''}
                onChange={(e) => updateConsumer(idx, 'team', e.target.value)}
                className="w-full px-3 py-2 rounded border"
                style={{
                  backgroundColor: '#1a1a24',
                  borderColor: 'rgba(168, 216, 255, 0.2)',
                  color: '#f0f0f5'
                }}
                placeholder="Team (optional)"
              />
              <input
                type="text"
                value={consumer.system || ''}
                onChange={(e) => updateConsumer(idx, 'system', e.target.value)}
                className="w-full px-3 py-2 rounded border"
                style={{
                  backgroundColor: '#1a1a24',
                  borderColor: 'rgba(168, 216, 255, 0.2)',
                  color: '#f0f0f5'
                }}
                placeholder="System (optional)"
              />
            </div>
            <button
              onClick={() => removeConsumer(idx)}
              className="p-2 rounded hover:bg-red-900/20"
              style={{ color: '#ef4444' }}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Decision Frequency */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Decision Frequency
        </label>
        <select
          value={context.decision_frequency || ''}
          onChange={(e) => onChange({ ...context, decision_frequency: e.target.value })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
        >
          <option value="">Select frequency</option>
          <option value="real_time">Real-time</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="ad_hoc">Ad-hoc</option>
        </select>
      </div>

      {/* Downside if Wrong */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Downside if Wrong
        </label>
        <textarea
          value={context.downside_if_wrong || ''}
          onChange={(e) => onChange({ ...context, downside_if_wrong: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="Describe the impact of incorrect data..."
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Notes
        </label>
        <textarea
          value={context.notes || ''}
          onChange={(e) => onChange({ ...context, notes: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="Additional context..."
        />
      </div>
    </div>
  )
}

// ==================== Guarantees Tab ====================

function GuaranteesTab({ guarantees, onChange }: { guarantees: SemanticGuarantees; onChange: (g: SemanticGuarantees) => void }) {
  const addInvariant = () => {
    onChange({
      ...guarantees,
      invariants: [...(guarantees.invariants || []), '']
    })
  }

  const updateInvariant = (index: number, value: string) => {
    const invariants = [...(guarantees.invariants || [])]
    invariants[index] = value
    onChange({ ...guarantees, invariants })
  }

  const removeInvariant = (index: number) => {
    const invariants = [...(guarantees.invariants || [])]
    invariants.splice(index, 1)
    onChange({ ...guarantees, invariants })
  }

  const addFailureMode = () => {
    onChange({
      ...guarantees,
      known_failure_modes: [...(guarantees.known_failure_modes || []), '']
    })
  }

  const updateFailureMode = (index: number, value: string) => {
    const modes = [...(guarantees.known_failure_modes || [])]
    modes[index] = value
    onChange({ ...guarantees, known_failure_modes: modes })
  }

  const removeFailureMode = (index: number) => {
    const modes = [...(guarantees.known_failure_modes || [])]
    modes.splice(index, 1)
    onChange({ ...guarantees, known_failure_modes: modes })
  }

  return (
    <div className="space-y-6">
      {/* Invariants */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium" style={{ color: '#f0f0f5' }}>
            Invariants
          </label>
          <button
            onClick={addInvariant}
            className="text-sm flex items-center gap-1 hover:underline"
            style={{ color: '#a8d8ff' }}
          >
            <Plus className="h-4 w-4" /> Add
          </button>
        </div>
        {(guarantees.invariants || []).map((invariant, idx) => (
          <div key={idx} className="flex gap-2 mb-2">
            <input
              type="text"
              value={invariant}
              onChange={(e) => updateInvariant(idx, e.target.value)}
              className="flex-1 px-3 py-2 rounded border"
              style={{
                backgroundColor: '#1a1a24',
                borderColor: 'rgba(168, 216, 255, 0.2)',
                color: '#f0f0f5'
              }}
              placeholder="e.g., Values must be non-negative"
            />
            <button
              onClick={() => removeInvariant(idx)}
              className="p-2 rounded hover:bg-red-900/20"
              style={{ color: '#ef4444' }}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Temporal Behavior */}
      <div className="p-4 rounded border" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
        <h3 className="font-medium mb-3" style={{ color: '#f0f0f5' }}>Temporal Behavior</h3>
        
        <div className="space-y-3">
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b0b8c0' }}>Freshness</label>
            <input
              type="text"
              value={guarantees.temporal_behavior?.freshness || ''}
              onChange={(e) => onChange({
                ...guarantees,
                temporal_behavior: { ...guarantees.temporal_behavior, freshness: e.target.value }
              })}
              className="w-full px-3 py-2 rounded border"
              style={{
                backgroundColor: '#1a1a24',
                borderColor: 'rgba(168, 216, 255, 0.2)',
                color: '#f0f0f5'
              }}
              placeholder="e.g., Updated daily at 3am UTC"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={guarantees.temporal_behavior?.backfill_expected || false}
              onChange={(e) => onChange({
                ...guarantees,
                temporal_behavior: { ...guarantees.temporal_behavior, backfill_expected: e.target.checked }
              })}
              className="rounded"
            />
            <label className="text-sm" style={{ color: '#b0b8c0' }}>Backfill Expected</label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={guarantees.temporal_behavior?.late_arriving_data || false}
              onChange={(e) => onChange({
                ...guarantees,
                temporal_behavior: { ...guarantees.temporal_behavior, late_arriving_data: e.target.checked }
              })}
              className="rounded"
            />
            <label className="text-sm" style={{ color: '#b0b8c0' }}>Late Arriving Data</label>
          </div>
        </div>
      </div>

      {/* PII */}
      <div className="p-4 rounded border" style={{ borderColor: 'rgba(168, 216, 255, 0.1)' }}>
        <h3 className="font-medium mb-3" style={{ color: '#f0f0f5' }}>PII Information</h3>
        
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={guarantees.pii?.contains_pii || false}
              onChange={(e) => onChange({
                ...guarantees,
                pii: { ...guarantees.pii, contains_pii: e.target.checked }
              })}
              className="rounded"
            />
            <label className="text-sm" style={{ color: '#b0b8c0' }}>Contains PII</label>
          </div>

          {guarantees.pii?.contains_pii && (
            <div>
              <label className="block text-sm mb-1" style={{ color: '#b0b8c0' }}>PII Types (comma-separated)</label>
              <input
                type="text"
                value={(guarantees.pii?.pii_types || []).join(', ')}
                onChange={(e) => onChange({
                  ...guarantees,
                  pii: { ...guarantees.pii, pii_types: e.target.value.split(',').map(s => s.trim()).filter(Boolean) }
                })}
                className="w-full px-3 py-2 rounded border"
                style={{
                  backgroundColor: '#1a1a24',
                  borderColor: 'rgba(168, 216, 255, 0.2)',
                  color: '#f0f0f5'
                }}
                placeholder="e.g., email, ssn, phone"
              />
            </div>
          )}
        </div>
      </div>

      {/* Known Failure Modes */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium" style={{ color: '#f0f0f5' }}>
            Known Failure Modes
          </label>
          <button
            onClick={addFailureMode}
            className="text-sm flex items-center gap-1 hover:underline"
            style={{ color: '#a8d8ff' }}
          >
            <Plus className="h-4 w-4" /> Add
          </button>
        </div>
        {(guarantees.known_failure_modes || []).map((mode, idx) => (
          <div key={idx} className="flex gap-2 mb-2">
            <input
              type="text"
              value={mode}
              onChange={(e) => updateFailureMode(idx, e.target.value)}
              className="flex-1 px-3 py-2 rounded border"
              style={{
                backgroundColor: '#1a1a24',
                borderColor: 'rgba(168, 216, 255, 0.2)',
                color: '#f0f0f5'
              }}
              placeholder="e.g., Nulls during system maintenance"
            />
            <button
              onClick={() => removeFailureMode(idx)}
              className="p-2 rounded hover:bg-red-900/20"
              style={{ color: '#ef4444' }}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Notes
        </label>
        <textarea
          value={guarantees.notes || ''}
          onChange={(e) => onChange({ ...guarantees, notes: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="Additional notes..."
        />
      </div>
    </div>
  )
}

// ==================== Validation Tab ====================

function ValidationTab({ validation, onChange }: { validation: ValidationState; onChange: (v: ValidationState) => void }) {
  return (
    <div className="space-y-6">
      {/* Confidence Score */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Confidence Score (0-1)
        </label>
        <input
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={validation.confidence_score || ''}
          onChange={(e) => onChange({ ...validation, confidence_score: parseFloat(e.target.value) || undefined })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
        />
      </div>

      {/* Confidence Sources */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Confidence Sources (comma-separated)
        </label>
        <input
          type="text"
          value={(validation.confidence_sources || []).join(', ')}
          onChange={(e) => onChange({
            ...validation,
            confidence_sources: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="e.g., ai_inferred, sme_reviewed, system_generated"
        />
      </div>

      {/* Validated By */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Validated By (comma-separated emails)
        </label>
        <input
          type="text"
          value={(validation.validated_by || []).join(', ')}
          onChange={(e) => onChange({
            ...validation,
            validated_by: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="e.g., analyst@company.com"
        />
      </div>

      {/* Upstream Sources */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Upstream Sources (comma-separated)
        </label>
        <input
          type="text"
          value={(validation.upstream_sources || []).join(', ')}
          onChange={(e) => onChange({
            ...validation,
            upstream_sources: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="e.g., source_system.table, api_endpoint"
        />
      </div>

      {/* Downstream Usage */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Downstream Usage (comma-separated)
        </label>
        <input
          type="text"
          value={(validation.downstream_usage || []).join(', ')}
          onChange={(e) => onChange({
            ...validation,
            downstream_usage: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="e.g., dashboard_name, ml_model_name"
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Notes
        </label>
        <textarea
          value={validation.notes || ''}
          onChange={(e) => onChange({ ...validation, notes: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="Additional validation notes..."
        />
      </div>
    </div>
  )
}

// ==================== Grain Tab ====================

function GrainTab({ grain, onChange }: { grain: Partial<DictionaryGrain> | null; onChange: (g: Partial<DictionaryGrain>) => void }) {
  const currentGrain = grain || {}

  return (
    <div className="space-y-6">
      {/* Entity */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Entity <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          value={currentGrain.entity || ''}
          onChange={(e) => onChange({ ...currentGrain, entity: e.target.value })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="e.g., one row per customer per day"
        />
      </div>

      {/* Primary Key */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Primary Key (comma-separated columns)
        </label>
        <input
          type="text"
          value={(currentGrain.primary_key || []).join(', ')}
          onChange={(e) => onChange({
            ...currentGrain,
            primary_key: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="e.g., customer_id, date"
        />
      </div>

      {/* Time Grain */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Time Grain
        </label>
        <select
          value={currentGrain.time_grain || ''}
          onChange={(e) => onChange({ ...currentGrain, time_grain: e.target.value })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
        >
          <option value="">Select time grain</option>
          <option value="event_time">Event Time</option>
          <option value="second">Second</option>
          <option value="minute">Minute</option>
          <option value="hour">Hour</option>
          <option value="day">Day</option>
          <option value="week">Week</option>
          <option value="month">Month</option>
          <option value="quarter">Quarter</option>
          <option value="year">Year</option>
        </select>
      </div>

      {/* Natural Key */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Natural Key (comma-separated columns)
        </label>
        <input
          type="text"
          value={(currentGrain.natural_key || []).join(', ')}
          onChange={(e) => onChange({
            ...currentGrain,
            natural_key: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
          })}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="e.g., email, username"
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: '#f0f0f5' }}>
          Notes
        </label>
        <textarea
          value={currentGrain.notes || ''}
          onChange={(e) => onChange({ ...currentGrain, notes: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 rounded border"
          style={{
            backgroundColor: '#1a1a24',
            borderColor: 'rgba(168, 216, 255, 0.2)',
            color: '#f0f0f5'
          }}
          placeholder="Additional grain notes..."
        />
      </div>
    </div>
  )
}

