/**
 * Modal for manual data structuring.
 */
import { X } from 'lucide-react'
import { SchemaDefinition, BankedItem } from '../../../types/distillation'

interface StructureModalProps {
  open: boolean
  onClose: () => void
  selectedBanked: BankedItem | null
  schemas: SchemaDefinition[]
  selectedSchema: string
  setSelectedSchema: (schema: string) => void
  structuredData: Record<string, any>
  setStructuredData: (data: Record<string, any>) => void
  handleSaveStructured: () => void
}

export default function StructureModal({
  open,
  onClose,
  selectedBanked,
  schemas,
  selectedSchema,
  setSelectedSchema,
  structuredData,
  setStructuredData,
  handleSaveStructured
}: StructureModalProps) {
  if (!open || !selectedBanked) return null

  const currentSchema = schemas.find(s => s.key === selectedSchema)

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-auto" style={{
        backgroundColor: 'rgba(30, 30, 40, 0.95)',
        border: '1px solid rgba(168, 216, 255, 0.3)'
      }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold" style={{ color: '#a8d8ff' }}>Manual Structuring</h3>
          <button onClick={() => { onClose(); setStructuredData({}) }} className="p-1 rounded hover:bg-white/10" style={{ color: '#b3d9ff' }}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>Schema</label>
            <select
              value={selectedSchema}
              onChange={e => setSelectedSchema(e.target.value)}
              className="w-full px-3 py-2 rounded-lg"
              style={{
                backgroundColor: 'rgba(20, 20, 30, 0.8)',
                border: '1px solid rgba(168, 216, 255, 0.3)',
                color: '#f0f0f5'
              }}
            >
              <option value="">Select schema</option>
              {schemas.map(s => (
                <option key={s.key} value={s.key}>{s.name}</option>
              ))}
            </select>
          </div>
          {selectedSchema && currentSchema && (
            <div className="space-y-3">
              {Object.entries(currentSchema.fields).map(([field, info]) => (
                <div key={field}>
                  <label className="block text-sm mb-1" style={{ color: '#b3d9ff' }}>
                    {field} {info.required && <span className="text-red-400">*</span>}
                  </label>
                  <textarea
                    value={structuredData[field] || ''}
                    onChange={e => setStructuredData({ ...structuredData, [field]: e.target.value })}
                    placeholder={info.description}
                    className="w-full px-3 py-2 rounded-lg"
                    style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.8)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                    rows={2}
                  />
                </div>
              ))}
            </div>
          )}
          <button
            onClick={handleSaveStructured}
            disabled={!selectedSchema}
            className="w-full py-2 rounded-lg disabled:opacity-50"
            style={{
              backgroundColor: 'rgba(168, 216, 255, 0.2)',
              border: '1px solid rgba(168, 216, 255, 0.4)',
              color: '#a8d8ff'
            }}
          >
            Save Structured Data
          </button>
        </div>
      </div>
    </div>
  )
}
