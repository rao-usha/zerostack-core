/**
 * Structuring view for Distillation Workbench.
 * Extract structured data from banked responses using schemas.
 */
import { Loader2, Wand2, Edit3 } from 'lucide-react'
import { SchemaDefinition, BankedItem, StructuredItem, Dataset } from '../../types/distillation'

interface StructureViewProps {
  // Data
  schemas: SchemaDefinition[]
  bankedItems: BankedItem[]
  structuredItems: StructuredItem[]
  datasets: Dataset[]
  // State
  selectedSchema: string
  setSelectedSchema: (schema: string) => void
  extracting: boolean
  // Actions
  handleLLMExtract: (bankedId: string, schemaName: string) => void
  setSelectedBanked: (banked: BankedItem) => void
  setStructureModalOpen: (open: boolean) => void
  handleAddToDataset: (datasetId: string, bankedId?: string, structuredId?: string) => void
}

export default function StructureView({
  schemas,
  bankedItems,
  structuredItems,
  datasets,
  selectedSchema,
  setSelectedSchema,
  extracting,
  handleLLMExtract,
  setSelectedBanked,
  setStructureModalOpen,
  handleAddToDataset
}: StructureViewProps) {
  return (
    <div className="rounded-lg p-6" style={{
      backgroundColor: 'rgba(30, 30, 40, 0.8)',
      border: '1px solid rgba(168, 216, 255, 0.2)'
    }}>
      <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Structuring</h2>
      <p className="text-sm mb-4" style={{ color: '#b3d9ff' }}>
        Extract structured data from banked responses using schemas
      </p>

      {/* Schema Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {schemas.map(schema => (
          <div key={schema.key} className="p-4 rounded-lg" style={{
            backgroundColor: 'rgba(20, 20, 30, 0.6)',
            border: '1px solid rgba(168, 216, 255, 0.1)'
          }}>
            <h3 className="font-medium" style={{ color: '#a8d8ff' }}>{schema.name}</h3>
            <p className="text-xs mt-1" style={{ color: '#b3d9ff' }}>{schema.description}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.keys(schema.fields).map(field => (
                <span key={field} className="px-1 py-0.5 rounded text-xs" style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.1)',
                  color: '#a8d8ff'
                }}>{field}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Banked Items for Structuring */}
      <h3 className="text-lg font-medium mb-3" style={{ color: '#a8d8ff' }}>Banked Responses</h3>
      {bankedItems.length === 0 ? (
        <p style={{ color: '#b3d9ff' }}>No banked responses. Bank some responses first.</p>
      ) : (
        <div className="space-y-3">
          {bankedItems.map(banked => (
            <div key={banked.id} className="p-4 rounded-lg" style={{
              backgroundColor: 'rgba(20, 20, 30, 0.6)',
              border: '1px solid rgba(168, 216, 255, 0.1)'
            }}>
              <div className="flex items-center justify-between">
                <div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    banked.status === 'approved' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                  }`}>{banked.status}</span>
                  <span className="ml-2 text-xs" style={{ color: '#b3d9ff' }}>
                    {new Date(banked.banked_at).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <select
                    value={selectedSchema}
                    onChange={e => setSelectedSchema(e.target.value)}
                    className="px-2 py-1 rounded text-xs"
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
                  <button
                    onClick={() => selectedSchema && handleLLMExtract(banked.id, selectedSchema)}
                    disabled={!selectedSchema || extracting}
                    className="px-2 py-1 rounded text-xs flex items-center space-x-1 disabled:opacity-50"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.2)',
                      border: '1px solid rgba(168, 216, 255, 0.4)',
                      color: '#a8d8ff'
                    }}
                  >
                    {extracting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Wand2 className="h-3 w-3" />}
                    <span>Auto Extract</span>
                  </button>
                  <button
                    onClick={() => {
                      setSelectedBanked(banked)
                      setStructureModalOpen(true)
                    }}
                    className="px-2 py-1 rounded text-xs flex items-center space-x-1"
                    style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.2)',
                      border: '1px solid rgba(168, 216, 255, 0.4)',
                      color: '#a8d8ff'
                    }}
                  >
                    <Edit3 className="h-3 w-3" /><span>Manual</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Structured Items */}
      <h3 className="text-lg font-medium mt-6 mb-3" style={{ color: '#a8d8ff' }}>
        Structured Extractions ({structuredItems.length})
      </h3>
      {structuredItems.length === 0 ? (
        <p style={{ color: '#b3d9ff' }}>No structured extractions yet.</p>
      ) : (
        <div className="space-y-3">
          {structuredItems.map(item => (
            <div key={item.id} className="p-4 rounded-lg" style={{
              backgroundColor: 'rgba(20, 20, 30, 0.6)',
              border: '1px solid rgba(168, 216, 255, 0.1)'
            }}>
              <div className="flex items-center justify-between mb-2">
                <span className="px-2 py-1 rounded text-xs" style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  color: '#a8d8ff'
                }}>{item.schema_name}</span>
                <span className="text-xs" style={{ color: '#b3d9ff' }}>{item.extraction_method}</span>
              </div>
              <pre className="text-xs overflow-auto max-h-32 p-2 rounded" style={{
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                color: '#f0f0f5'
              }}>
                {JSON.stringify(item.structured_data, null, 2)}
              </pre>
              <div className="flex justify-end mt-2">
                {datasets.length > 0 && (
                  <select
                    onChange={e => e.target.value && handleAddToDataset(e.target.value, undefined, item.id)}
                    className="px-2 py-1 rounded text-xs"
                    style={{
                      backgroundColor: 'rgba(20, 20, 30, 0.8)',
                      border: '1px solid rgba(168, 216, 255, 0.3)',
                      color: '#f0f0f5'
                    }}
                  >
                    <option value="">Add to dataset...</option>
                    {datasets.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
