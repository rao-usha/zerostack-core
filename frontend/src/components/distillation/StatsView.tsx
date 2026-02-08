/**
 * Statistics view for Distillation Workbench.
 * Displays response statistics and model preferences.
 */
import { Statistics, ModelPreferences, StructuredItem, Dataset } from '../../types/distillation'

interface StatsViewProps {
  statistics: Statistics | null
  modelPreferences: ModelPreferences | null
  structuredItems: StructuredItem[]
  datasets: Dataset[]
}

export default function StatsView({
  statistics,
  modelPreferences,
  structuredItems,
  datasets
}: StatsViewProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg p-6" style={{
        backgroundColor: 'rgba(30, 30, 40, 0.8)',
        border: '1px solid rgba(168, 216, 255, 0.2)'
      }}>
        <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Statistics</h2>
        {statistics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
              <div className="text-2xl font-bold" style={{ color: '#a8d8ff' }}>{statistics.total_responses}</div>
              <div className="text-sm" style={{ color: '#b3d9ff' }}>Total Responses</div>
            </div>
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
              <div className="text-2xl font-bold" style={{ color: '#10b981' }}>{statistics.total_banked}</div>
              <div className="text-sm" style={{ color: '#b3d9ff' }}>Banked</div>
            </div>
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
              <div className="text-2xl font-bold" style={{ color: '#c4b5fd' }}>{structuredItems.length}</div>
              <div className="text-sm" style={{ color: '#b3d9ff' }}>Structured</div>
            </div>
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'rgba(20, 20, 30, 0.6)' }}>
              <div className="text-2xl font-bold" style={{ color: '#fbbf24' }}>{datasets.length}</div>
              <div className="text-sm" style={{ color: '#b3d9ff' }}>Datasets</div>
            </div>
          </div>
        )}
      </div>

      {/* Model Preferences */}
      <div className="rounded-lg p-6" style={{
        backgroundColor: 'rgba(30, 30, 40, 0.8)',
        border: '1px solid rgba(168, 216, 255, 0.2)'
      }}>
        <h2 className="text-xl font-semibold mb-4" style={{ color: '#a8d8ff' }}>Model Preferences</h2>
        {modelPreferences && modelPreferences.total_votes > 0 ? (
          <div className="space-y-3">
            <p className="text-sm" style={{ color: '#b3d9ff' }}>Based on {modelPreferences.total_votes} votes</p>
            {Object.entries(modelPreferences.win_rates).map(([model, rate]) => (
              <div key={model}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm" style={{ color: '#f0f0f5' }}>{model}</span>
                  <span className="text-sm" style={{ color: '#a8d8ff' }}>{rate}%</span>
                </div>
                <div className="h-2 rounded-full" style={{ backgroundColor: 'rgba(168, 216, 255, 0.1)' }}>
                  <div className="h-full rounded-full" style={{ width: `${rate}%`, backgroundColor: '#a8d8ff' }} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#b3d9ff' }}>No votes recorded yet.</p>
        )}
      </div>
    </div>
  )
}
