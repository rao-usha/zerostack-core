import { useState, useEffect } from 'react';
import {
  ChevronUp,
  ChevronDown,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2
} from 'lucide-react';

interface MLModel {
  id: string;
  name: string;
  status: string;
}

interface ValidationRequirement {
  name: string;
  description: string;
  passed: boolean;
  details: string | null;
}

interface ValidationResult {
  can_promote: boolean;
  requirements: ValidationRequirement[];
  message: string;
}

interface ModelPromotionDialogProps {
  model: MLModel;
  direction: 'promote' | 'demote';
  onClose: () => void;
  onSuccess: () => void;
}

const API_BASE = import.meta.env.VITE_API_URL || '';

const STATUS_ORDER = ['draft', 'staging', 'production', 'retired'];

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  staging: 'Staging',
  production: 'Production',
  retired: 'Retired'
};

export default function ModelPromotionDialog({
  model,
  direction,
  onClose,
  onSuccess
}: ModelPromotionDialogProps) {
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(true);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Calculate target status
  const currentIdx = STATUS_ORDER.indexOf(model.status);
  const targetStatus = direction === 'promote'
    ? STATUS_ORDER[currentIdx + 1]
    : STATUS_ORDER[currentIdx - 1];

  useEffect(() => {
    if (direction === 'promote' && targetStatus) {
      validatePromotion();
    } else {
      setValidating(false);
      setValidation({
        can_promote: true,
        requirements: [],
        message: 'Demotion allowed with notes'
      });
    }
  }, [model.id, targetStatus, direction]);

  const validatePromotion = async () => {
    try {
      setValidating(true);
      const response = await fetch(
        `${API_BASE}/api/v1/ml-development/models/${model.id}/validate-promotion?target_status=${targetStatus}`
      );
      if (!response.ok) throw new Error('Validation failed');
      const data = await response.json();
      setValidation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
    } finally {
      setValidating(false);
    }
  };

  const handleSubmit = async () => {
    if (!notes.trim()) {
      setError('Notes are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const endpoint = direction === 'promote'
        ? `${API_BASE}/api/v1/ml-development/models/${model.id}/promote`
        : `${API_BASE}/api/v1/ml-development/models/${model.id}/demote`;

      const body = direction === 'promote'
        ? { target_status: targetStatus, notes }
        : { target_status: targetStatus, notes };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail?.message || data.detail || 'Operation failed');
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const isPromote = direction === 'promote';
  const canSubmit = !validating && (validation?.can_promote ?? false) && notes.trim().length > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-surface rounded-lg border border-dark-border w-full max-w-md mx-4">
        {/* Header */}
        <div className="p-4 border-b border-dark-border flex items-center gap-3">
          {isPromote ? (
            <div className="p-2 bg-green-900/30 rounded-lg">
              <ChevronUp className="h-5 w-5 text-green-400" />
            </div>
          ) : (
            <div className="p-2 bg-red-900/30 rounded-lg">
              <ChevronDown className="h-5 w-5 text-red-400" />
            </div>
          )}
          <div>
            <h3 className="text-lg font-semibold text-gray-100">
              {isPromote ? 'Promote' : 'Demote'} Model
            </h3>
            <p className="text-sm text-gray-400">{model.name}</p>
          </div>
        </div>

        {/* Status Transition */}
        <div className="p-4 border-b border-dark-border">
          <div className="flex items-center justify-center gap-4">
            <div className="text-center">
              <span className="px-3 py-1 rounded-full text-sm bg-dark-border text-gray-300">
                {STATUS_LABELS[model.status]}
              </span>
            </div>
            <div className={isPromote ? 'text-green-400' : 'text-red-400'}>
              {isPromote ? '→' : '←'}
            </div>
            <div className="text-center">
              <span className={`px-3 py-1 rounded-full text-sm ${
                isPromote ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
              }`}>
                {STATUS_LABELS[targetStatus]}
              </span>
            </div>
          </div>
        </div>

        {/* Validation Requirements */}
        {isPromote && (
          <div className="p-4 border-b border-dark-border">
            <h4 className="text-sm font-medium text-gray-300 mb-3">
              Validation Requirements
            </h4>
            {validating ? (
              <div className="flex items-center gap-2 text-gray-400">
                <Loader2 className="h-4 w-4 animate-spin" />
                Validating...
              </div>
            ) : validation ? (
              <div className="space-y-2">
                {validation.requirements.map((req, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-2 p-2 rounded ${
                      req.passed ? 'bg-green-900/10' : 'bg-red-900/10'
                    }`}
                  >
                    {req.passed ? (
                      <CheckCircle className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm ${req.passed ? 'text-green-400' : 'text-red-400'}`}>
                        {req.description}
                      </p>
                      {req.details && (
                        <p className="text-xs text-gray-500 mt-0.5">{req.details}</p>
                      )}
                    </div>
                  </div>
                ))}
                {validation.requirements.length === 0 && (
                  <p className="text-sm text-gray-400">No specific requirements</p>
                )}
              </div>
            ) : null}
          </div>
        )}

        {/* Notes */}
        <div className="p-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            {isPromote ? 'Promotion' : 'Demotion'} Notes
            <span className="text-red-400">*</span>
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={isPromote
              ? 'Explain why this model is ready for promotion...'
              : 'Explain the reason for demotion...'
            }
            className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 min-h-[80px]"
          />

          {error && (
            <div className="mt-3 p-2 bg-red-900/20 border border-red-500/50 rounded flex items-center gap-2 text-sm text-red-400">
              <AlertTriangle size={14} />
              {error}
            </div>
          )}

          {isPromote && validation && !validation.can_promote && (
            <div className="mt-3 p-2 bg-yellow-900/20 border border-yellow-500/50 rounded flex items-center gap-2 text-sm text-yellow-400">
              <AlertTriangle size={14} />
              {validation.message}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-dark-border flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-dark-border rounded hover:bg-gray-600 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || loading}
            className={`px-4 py-2 text-sm font-medium text-white rounded disabled:opacity-50 flex items-center gap-2 ${
              isPromote
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {isPromote ? 'Promote' : 'Demote'}
          </button>
        </div>
      </div>
    </div>
  );
}
