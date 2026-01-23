/**
 * ML Query Analyzer Component
 * 
 * Displays analysis of ML-related queries, showing detected features,
 * patterns, and confidence scores.
 */
import React from 'react';

interface MLFeature {
  name: string;
  type: string;
  source_table: string;
  source_column: string;
  transformation: string;
}

interface MLAnalysisResult {
  is_ml_related: boolean;
  confidence: number;
  query_type?: string;
  features?: MLFeature[];
  source_tables?: string[];
  target_dataset?: string;
  detected_patterns?: string[];
  message?: string;
}

interface MLQueryAnalyzerProps {
  analysis: MLAnalysisResult;
}

const MLQueryAnalyzer: React.FC<MLQueryAnalyzerProps> = ({ analysis }) => {
  if (!analysis.is_ml_related) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-gray-600">
          <span className="text-lg">ℹ️</span>
          <span className="text-sm">This query does not appear to be ML-related</span>
        </div>
      </div>
    );
  }

  const confidenceColor = analysis.confidence >= 0.7 ? 'green' : analysis.confidence >= 0.4 ? 'yellow' : 'orange';
  const confidenceText = analysis.confidence >= 0.7 ? 'High' : analysis.confidence >= 0.4 ? 'Medium' : 'Low';

  const queryTypeColors: Record<string, string> = {
    'FEATURE_EXTRACTION': 'bg-blue-100 text-blue-800 border-blue-300',
    'TRAINING_DATA': 'bg-purple-100 text-purple-800 border-purple-300',
    'VALIDATION_DATA': 'bg-orange-100 text-orange-800 border-orange-300',
    'INFERENCE_DATA': 'bg-green-100 text-green-800 border-green-300',
  };

  const featureTypeIcons: Record<string, string> = {
    'NUMERIC': '🔢',
    'CATEGORICAL': '🏷️',
    'TEMPORAL': '📅',
    'TEXT': '📝',
    'UNKNOWN': '❓',
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <span>🤖</span>
          <span>ML Query Detected</span>
        </h4>
        
        <div className="flex items-center gap-2">
          {/* Confidence Badge */}
          <div className={`px-3 py-1 rounded-full text-xs font-medium bg-${confidenceColor}-100 text-${confidenceColor}-800 border border-${confidenceColor}-300`}>
            {confidenceText} Confidence ({(analysis.confidence * 100).toFixed(0)}%)
          </div>
          
          {/* Query Type Badge */}
          {analysis.query_type && (
            <div className={`px-3 py-1 rounded-full text-xs font-medium border ${queryTypeColors[analysis.query_type] || 'bg-gray-100'}`}>
              {analysis.query_type.replace('_', ' ')}
            </div>
          )}
        </div>
      </div>

      {/* Detected Patterns */}
      {analysis.detected_patterns && analysis.detected_patterns.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-medium text-gray-600 mb-2">Detected Patterns:</div>
          <div className="flex flex-wrap gap-2">
            {analysis.detected_patterns.map((pattern, idx) => (
              <div key={idx} className="px-2 py-1 bg-white border border-purple-200 rounded text-xs text-gray-700">
                ✓ {pattern}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Source Tables */}
      {analysis.source_tables && analysis.source_tables.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-medium text-gray-600 mb-2">Data Sources:</div>
          <div className="flex flex-wrap gap-2">
            {analysis.source_tables.map((table, idx) => (
              <div key={idx} className="px-3 py-1 bg-blue-50 border border-blue-200 rounded font-mono text-sm">
                {table}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Features Extracted */}
      {analysis.features && analysis.features.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-medium text-gray-600 mb-2">
            Features Extracted ({analysis.features.length}):
          </div>
          
          <div className="bg-white rounded-lg border border-purple-200 overflow-hidden">
            <div className="max-h-60 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">Feature Name</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">Type</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">Source</th>
                    <th className="text-left px-3 py-2 text-xs font-medium text-gray-600">Transformation</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.features.map((feature, idx) => (
                    <tr key={idx} className="border-t border-gray-100 hover:bg-purple-50">
                      <td className="px-3 py-2 font-mono text-xs">{feature.name}</td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-1 text-xs">
                          <span>{featureTypeIcons[feature.type]}</span>
                          <span>{feature.type}</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 font-mono text-xs text-gray-600">
                        {feature.source_table}.{feature.source_column}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs text-gray-500 truncate max-w-xs" title={feature.transformation}>
                        {feature.transformation.substring(0, 50)}{feature.transformation.length > 50 ? '...' : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Target Dataset */}
      {analysis.target_dataset && (
        <div className="mb-4">
          <div className="text-xs font-medium text-gray-600 mb-2">Target Dataset:</div>
          <div className="px-3 py-2 bg-green-50 border border-green-200 rounded font-mono text-sm inline-block">
            {analysis.target_dataset}
          </div>
        </div>
      )}

      {/* Feature Type Distribution */}
      {analysis.features && analysis.features.length > 0 && (
        <div className="pt-4 border-t border-purple-200">
          <div className="text-xs font-medium text-gray-600 mb-2">Feature Type Distribution:</div>
          <div className="flex flex-wrap gap-3">
            {Object.entries(
              analysis.features.reduce((acc, f) => {
                acc[f.type] = (acc[f.type] || 0) + 1;
                return acc;
              }, {} as Record<string, number>)
            ).map(([type, count]) => (
              <div key={type} className="flex items-center gap-1 text-xs">
                <span>{featureTypeIcons[type]}</span>
                <span className="font-medium">{type}:</span>
                <span className="text-gray-600">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-4 p-3 bg-purple-100 border border-purple-200 rounded text-xs text-gray-700">
        <span className="font-medium">💡 Tip:</span> This query appears to be used for machine learning. 
        Consider tracking it as part of your ML pipeline for better reproducibility and lineage tracking.
      </div>
    </div>
  );
};

export default MLQueryAnalyzer;
