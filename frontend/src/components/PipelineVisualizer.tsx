/**
 * Pipeline Visualizer Component
 * 
 * Displays data pipelines as a sequence of stages showing how data
 * flows through multiple transformations.
 */
import React from 'react';

interface PipelineStage {
  stage_number: number;
  table: string;
  entity_type: string;
  transformation?: string;
  transform_sql?: string;
  created_at?: string;
}

interface Pipeline {
  pipeline_id: string;
  name: string;
  stages: PipelineStage[];
  source_tables: string[];
  target_tables: string[];
  last_run?: string;
}

interface PipelineVisualizerProps {
  pipelines: Pipeline[];
  maxVisible?: number;
}

const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ pipelines, maxVisible = 5 }) => {
  if (pipelines.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <div className="text-gray-500 mb-2">🔍</div>
        <div className="text-sm text-gray-600">No pipelines detected</div>
        <div className="text-xs text-gray-500 mt-1">
          Pipelines are automatically discovered from query lineage
        </div>
      </div>
    );
  }

  const displayPipelines = pipelines.slice(0, maxVisible);

  const transformationColors: Record<string, string> = {
    'DERIVED_FROM': 'bg-blue-100 text-blue-700',
    'AGGREGATED': 'bg-purple-100 text-purple-700',
    'JOINED': 'bg-green-100 text-green-700',
    'FILTERED': 'bg-yellow-100 text-yellow-700',
    'TRANSFORMED': 'bg-orange-100 text-orange-700',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <span>🔄</span>
          <span>Data Pipelines ({pipelines.length})</span>
        </h3>
      </div>

      {displayPipelines.map((pipeline, pipelineIdx) => (
        <div
          key={pipeline.pipeline_id}
          className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
        >
          {/* Pipeline Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="font-medium text-gray-800">{pipeline.name}</div>
              <div className="text-xs text-gray-500 mt-1">
                {pipeline.stages.length} stage{pipeline.stages.length !== 1 ? 's' : ''}
                {pipeline.last_run && (
                  <span className="ml-2">
                    • Last run: {new Date(pipeline.last_run).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
            
            <div className="text-xs text-gray-500 font-mono">
              ID: {pipeline.pipeline_id.substring(0, 8)}...
            </div>
          </div>

          {/* Pipeline Stages */}
          <div className="relative">
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {pipeline.stages.map((stage, idx) => (
                <React.Fragment key={idx}>
                  {/* Stage Box */}
                  <div className="flex-shrink-0 group relative">
                    <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-3 min-w-[140px]">
                      <div className="text-xs font-medium text-blue-600 mb-1">
                        Stage {stage.stage_number}
                      </div>
                      <div className="font-mono text-sm text-gray-800 break-words">
                        {stage.table}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {stage.entity_type.replace('_', ' ')}
                      </div>
                    </div>

                    {/* Hover Tooltip with Transformation SQL */}
                    {stage.transform_sql && (
                      <div className="absolute hidden group-hover:block bottom-full left-0 mb-2 z-10 w-64">
                        <div className="bg-gray-900 text-white text-xs rounded p-2 shadow-lg">
                          <div className="font-medium mb-1">Transformation SQL:</div>
                          <div className="font-mono text-gray-300 break-words">
                            {stage.transform_sql.substring(0, 150)}
                            {stage.transform_sql.length > 150 ? '...' : ''}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Arrow with Transformation Type */}
                  {idx < pipeline.stages.length - 1 && (
                    <div className="flex-shrink-0 flex flex-col items-center">
                      <div className="text-gray-400 text-2xl">→</div>
                      {stage.transformation && (
                        <div className={`text-[10px] px-2 py-0.5 rounded mt-1 ${transformationColors[stage.transformation] || 'bg-gray-100 text-gray-600'}`}>
                          {stage.transformation}
                        </div>
                      )}
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Pipeline Summary */}
          <div className="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between text-xs">
            <div className="flex items-center gap-4 text-gray-600">
              <div className="flex items-center gap-1">
                <span className="font-medium">From:</span>
                <span className="font-mono">{pipeline.source_tables.join(', ')}</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="font-medium">To:</span>
                <span className="font-mono">{pipeline.target_tables.join(', ')}</span>
              </div>
            </div>
          </div>
        </div>
      ))}

      {pipelines.length > maxVisible && (
        <div className="text-center py-2">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            View {pipelines.length - maxVisible} more pipeline{pipelines.length - maxVisible !== 1 ? 's' : ''}
          </button>
        </div>
      )}
    </div>
  );
};

export default PipelineVisualizer;
