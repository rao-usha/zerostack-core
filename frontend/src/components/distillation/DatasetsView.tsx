/**
 * Datasets view for Distillation Workbench.
 * Create, manage, and export training datasets.
 */
import {
  Plus, ChevronRight, Download, FileText, FileJson, Trash2
} from 'lucide-react'
import { Dataset, DatasetStats } from '../../types/distillation'

interface DatasetItem {
  id: string
  split: string
  structured?: { schema_name: string }
}

interface DatasetsViewProps {
  // Data
  datasets: Dataset[]
  selectedDataset: Dataset | null
  datasetStats: DatasetStats | null
  datasetItems: DatasetItem[]
  // Actions
  setCreateDatasetOpen: (open: boolean) => void
  setSelectedDataset: (dataset: Dataset | null) => void
  setDatasetStats: (stats: DatasetStats | null) => void
  setDatasetItems: (items: DatasetItem[]) => void
  loadDatasetDetails: (datasetId: string) => void
  loadDatasets: () => void
  handleExportDataset: (datasetId: string, format: 'jsonl' | 'csv' | 'alpaca') => void
}

export default function DatasetsView({
  datasets,
  selectedDataset,
  datasetStats,
  datasetItems,
  setCreateDatasetOpen,
  setSelectedDataset,
  setDatasetStats,
  setDatasetItems,
  loadDatasetDetails,
  loadDatasets,
  handleExportDataset
}: DatasetsViewProps) {
  return (
    <div className="rounded-lg p-6" style={{
      backgroundColor: 'rgba(30, 30, 40, 0.8)',
      border: '1px solid rgba(168, 216, 255, 0.2)'
    }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold" style={{ color: '#a8d8ff' }}>Datasets</h2>
        <button
          onClick={() => setCreateDatasetOpen(true)}
          className="px-3 py-2 rounded-lg flex items-center space-x-2"
          style={{
            backgroundColor: 'rgba(168, 216, 255, 0.15)',
            border: '1px solid rgba(168, 216, 255, 0.4)',
            color: '#a8d8ff'
          }}
        >
          <Plus className="h-4 w-4" /><span>New Dataset</span>
        </button>
      </div>

      {!selectedDataset ? (
        <div className="space-y-3">
          {datasets.length === 0 ? (
            <p style={{ color: '#b3d9ff' }}>No datasets yet. Create one to start building training data.</p>
          ) : (
            datasets.map(dataset => (
              <div
                key={dataset.id}
                onClick={() => {
                  setSelectedDataset(dataset)
                  loadDatasetDetails(dataset.id)
                }}
                className="p-4 rounded-lg cursor-pointer hover:bg-white/5 transition-all"
                style={{
                  backgroundColor: 'rgba(20, 20, 30, 0.6)',
                  border: '1px solid rgba(168, 216, 255, 0.1)'
                }}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{dataset.name}</h3>
                    <p className="text-xs mt-1" style={{ color: '#b3d9ff' }}>
                      v{dataset.version} • {dataset.item_count} items • {dataset.dataset_type}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    dataset.status === 'exported' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
                  }`}>{dataset.status}</span>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => { setSelectedDataset(null); setDatasetStats(null); setDatasetItems([]) }}
              className="text-sm flex items-center space-x-1"
              style={{ color: '#a8d8ff' }}
            >
              <ChevronRight className="h-4 w-4 rotate-180" /><span>Back to list</span>
            </button>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleExportDataset(selectedDataset.id, 'jsonl')}
                className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  color: '#a8d8ff'
                }}
              >
                <Download className="h-3 w-3" /><span>JSONL</span>
              </button>
              <button
                onClick={() => handleExportDataset(selectedDataset.id, 'csv')}
                className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  color: '#a8d8ff'
                }}
              >
                <FileText className="h-3 w-3" /><span>CSV</span>
              </button>
              <button
                onClick={() => handleExportDataset(selectedDataset.id, 'alpaca')}
                className="px-3 py-1 rounded text-xs flex items-center space-x-1"
                style={{
                  backgroundColor: 'rgba(168, 216, 255, 0.2)',
                  border: '1px solid rgba(168, 216, 255, 0.4)',
                  color: '#a8d8ff'
                }}
              >
                <FileJson className="h-3 w-3" /><span>Alpaca</span>
              </button>
            </div>
          </div>

          <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
            <h3 className="font-medium" style={{ color: '#f0f0f5' }}>{selectedDataset.name}</h3>
            <p className="text-sm mt-1" style={{ color: '#b3d9ff' }}>{selectedDataset.description || 'No description'}</p>
          </div>

          {/* Stats */}
          {datasetStats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                <div className="text-lg font-bold" style={{ color: '#a8d8ff' }}>{datasetStats.total_items}</div>
                <div className="text-xs" style={{ color: '#b3d9ff' }}>Total Items</div>
              </div>
              {Object.entries(datasetStats.by_split).map(([split, count]) => (
                <div key={split} className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
                  <div className="text-lg font-bold" style={{ color: '#c4b5fd' }}>{count}</div>
                  <div className="text-xs capitalize" style={{ color: '#b3d9ff' }}>{split}</div>
                </div>
              ))}
            </div>
          )}

          {/* Items */}
          <h4 className="font-medium" style={{ color: '#a8d8ff' }}>Items ({datasetItems.length})</h4>
          <div className="space-y-2 max-h-96 overflow-auto">
            {datasetItems.map((item, idx) => (
              <div key={item.id} className="p-3 rounded-lg flex items-center justify-between" style={{
                backgroundColor: 'rgba(20, 20, 30, 0.6)',
                border: '1px solid rgba(168, 216, 255, 0.1)'
              }}>
                <div className="flex items-center space-x-3">
                  <span className="text-xs" style={{ color: '#b3d9ff' }}>#{idx + 1}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    item.split === 'train' ? 'bg-blue-500/20 text-blue-400' :
                    item.split === 'validation' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>{item.split}</span>
                  {item.structured && (
                    <span className="px-2 py-0.5 rounded text-xs" style={{
                      backgroundColor: 'rgba(168, 216, 255, 0.1)',
                      color: '#a8d8ff'
                    }}>{item.structured.schema_name}</span>
                  )}
                </div>
                <button
                  onClick={async () => {
                    await fetch(`/api/v1/distillation/datasets/${selectedDataset.id}/items/${item.id}`, { method: 'DELETE' })
                    loadDatasetDetails(selectedDataset.id)
                    loadDatasets()
                  }}
                  className="p-1 rounded hover:bg-white/10"
                  style={{ color: '#ef4444' }}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
