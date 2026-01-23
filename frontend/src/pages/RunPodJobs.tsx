import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface JobMetrics {
  mae?: number;
  rmse?: number;
  training_time_seconds?: number;
  horizon_days?: number;
  num_items?: number;
  timestamp?: string;
}

interface Job {
  job_id: string;
  status: string;
  metrics: JobMetrics;
  timestamp?: string;
  mae?: number;
  rmse?: number;
  training_time?: number;
  output_files: string[];
}

interface JobsResponse {
  jobs: Job[];
  pod_id?: string;
  pod_name?: string;
  gpu_type?: string;
  count: number;
  error?: string;
}

interface OutputFile {
  name: string;
  size: string;
  modified?: string;
}

interface JobDetails {
  job_id: string;
  pod_id: string;
  pod_name: string;
  gpu_type: string;
  metrics: JobMetrics;
  feature_importance: string;
  forecasts_preview: string;
  output_files: OutputFile[];
  input_files: OutputFile[];
  error?: string;
}

export default function RunPodJobs() {
  const [jobs, setJobs] = useState<JobsResponse | null>(null);
  const [selectedJob, setSelectedJob] = useState<JobDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/ml-development/runpod/jobs');
      const data = await response.json();
      if (data.error) {
        setError(data.error);
      }
      setJobs(data);
    } catch (err) {
      setError('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobDetails = async (jobId: string) => {
    setDetailsLoading(true);
    try {
      const response = await fetch(`/api/v1/ml-development/runpod/jobs/${jobId}`);
      const data = await response.json();
      setSelectedJob(data);
    } catch (err) {
      setSelectedJob({ error: 'Failed to fetch job details' } as JobDetails);
    } finally {
      setDetailsLoading(false);
    }
  };

  const formatTimestamp = (ts?: string) => {
    if (!ts) return '-';
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">RunPod Jobs</h1>
            <p className="text-gray-600 mt-1">
              View and monitor ML forecast jobs running on RunPod GPUs
            </p>
          </div>
          <button
            onClick={fetchJobs}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Pod Info */}
      {jobs && jobs.pod_name && (
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="font-medium">{jobs.pod_name}</span>
              <span className="text-purple-200">|</span>
              <span className="text-purple-100">{jobs.gpu_type}</span>
            </div>
            <span className="text-purple-200 text-sm">{jobs.count} jobs</span>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading jobs...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {!loading && jobs && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Jobs List */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-4 py-3 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Forecast Jobs</h2>
            </div>
            <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
              {jobs.jobs.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <p>No jobs found on pod</p>
                  <Link 
                    to="/ml-development" 
                    className="text-blue-600 hover:underline mt-2 inline-block"
                  >
                    Run a forecast →
                  </Link>
                </div>
              ) : (
                jobs.jobs.map((job) => (
                  <div
                    key={job.job_id}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition ${
                      selectedJob?.job_id === job.job_id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                    }`}
                    onClick={() => fetchJobDetails(job.job_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <code className="text-sm font-mono text-gray-900">{job.job_id}</code>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(job.timestamp || job.metrics?.timestamp)}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        job.status === 'completed' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {job.status}
                      </span>
                    </div>
                    {job.mae !== undefined && (
                      <div className="mt-2 flex gap-4 text-sm">
                        <span className="text-gray-600">
                          MAE: <span className="font-medium text-gray-900">{job.mae?.toFixed(4)}</span>
                        </span>
                        <span className="text-gray-600">
                          RMSE: <span className="font-medium text-gray-900">{job.rmse?.toFixed(4)}</span>
                        </span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Job Details */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-4 py-3 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Job Details</h2>
            </div>
            
            {detailsLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">Loading...</span>
              </div>
            )}

            {!detailsLoading && !selectedJob && (
              <div className="p-8 text-center text-gray-500">
                <p>Select a job to view details</p>
              </div>
            )}

            {!detailsLoading && selectedJob && !selectedJob.error && (
              <div className="p-4 space-y-6 max-h-[600px] overflow-y-auto">
                {/* Metrics */}
                {selectedJob.metrics && Object.keys(selectedJob.metrics).length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Metrics</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {selectedJob.metrics.mae !== undefined && (
                        <div className="bg-blue-50 rounded-lg p-3">
                          <p className="text-xs text-blue-600 uppercase">MAE</p>
                          <p className="text-xl font-bold text-blue-900">
                            {selectedJob.metrics.mae.toFixed(4)}
                          </p>
                        </div>
                      )}
                      {selectedJob.metrics.rmse !== undefined && (
                        <div className="bg-purple-50 rounded-lg p-3">
                          <p className="text-xs text-purple-600 uppercase">RMSE</p>
                          <p className="text-xl font-bold text-purple-900">
                            {selectedJob.metrics.rmse.toFixed(4)}
                          </p>
                        </div>
                      )}
                      {selectedJob.metrics.training_time_seconds !== undefined && (
                        <div className="bg-green-50 rounded-lg p-3">
                          <p className="text-xs text-green-600 uppercase">Training Time</p>
                          <p className="text-xl font-bold text-green-900">
                            {selectedJob.metrics.training_time_seconds.toFixed(1)}s
                          </p>
                        </div>
                      )}
                      {selectedJob.metrics.num_items !== undefined && (
                        <div className="bg-orange-50 rounded-lg p-3">
                          <p className="text-xs text-orange-600 uppercase">Items Forecast</p>
                          <p className="text-xl font-bold text-orange-900">
                            {selectedJob.metrics.num_items}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Feature Importance Chart */}
                {selectedJob.feature_importance && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Feature Importance</h3>
                    <div className="bg-gray-50 rounded-lg p-3">
                      {(() => {
                        // Parse CSV to create chart data
                        const lines = selectedJob.feature_importance.trim().split('\n');
                        const data = lines.slice(1).map(line => {
                          const [feature, importance] = line.split(',');
                          return { feature, importance: parseFloat(importance) };
                        }).filter(d => !isNaN(d.importance)).slice(0, 10);
                        
                        const maxImportance = Math.max(...data.map(d => d.importance));
                        
                        return (
                          <div className="space-y-2">
                            {data.map((item, i) => (
                              <div key={i} className="flex items-center gap-2">
                                <span className="text-xs text-gray-600 w-32 truncate" title={item.feature}>
                                  {item.feature}
                                </span>
                                <div className="flex-1 h-5 bg-gray-200 rounded overflow-hidden">
                                  <div 
                                    className="h-full rounded transition-all duration-500"
                                    style={{
                                      width: `${(item.importance / maxImportance) * 100}%`,
                                      background: `linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%)`
                                    }}
                                  />
                                </div>
                                <span className="text-xs text-gray-500 w-12 text-right">
                                  {item.importance.toFixed(0)}
                                </span>
                              </div>
                            ))}
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                )}

                {/* Forecasts Visualization */}
                {selectedJob.forecasts_preview && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Forecast Results</h3>
                    <div className="bg-gray-50 rounded-lg p-3">
                      {(() => {
                        // Parse CSV to create chart data
                        const lines = selectedJob.forecasts_preview.trim().split('\n');
                        const headers = lines[0].split(',');
                        const salesIdx = headers.findIndex(h => h.includes('forecast_sales'));
                        const itemIdx = headers.findIndex(h => h.includes('item_id'));
                        const storeIdx = headers.findIndex(h => h.includes('store_id'));
                        
                        const data = lines.slice(1, 11).map(line => {
                          const cols = line.split(',');
                          return {
                            item: cols[itemIdx] || 'Unknown',
                            store: cols[storeIdx] || '',
                            sales: parseFloat(cols[salesIdx]) || 0
                          };
                        }).filter(d => !isNaN(d.sales));
                        
                        const maxSales = Math.max(...data.map(d => d.sales), 1);
                        
                        return (
                          <div>
                            {/* Bar Chart */}
                            <div className="h-40 flex items-end gap-1 mb-2 px-2">
                              {data.map((item, i) => (
                                <div 
                                  key={i} 
                                  className="flex-1 group relative"
                                >
                                  <div
                                    className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t transition-all duration-300 hover:from-blue-600 hover:to-blue-500"
                                    style={{ height: `${(item.sales / maxSales) * 100}%`, minHeight: '4px' }}
                                  />
                                  {/* Tooltip */}
                                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                                    {item.item}<br/>
                                    Sales: {item.sales.toFixed(2)}
                                  </div>
                                </div>
                              ))}
                            </div>
                            {/* X-axis labels */}
                            <div className="flex gap-1 px-2">
                              {data.map((item, i) => (
                                <div key={i} className="flex-1 text-center">
                                  <span className="text-[8px] text-gray-500 block truncate" title={item.item}>
                                    {item.item.split('_').pop()}
                                  </span>
                                </div>
                              ))}
                            </div>
                            {/* Summary Stats */}
                            <div className="mt-3 pt-3 border-t border-gray-200 flex justify-around text-center">
                              <div>
                                <p className="text-xs text-gray-500">Total Forecast</p>
                                <p className="text-lg font-bold text-blue-600">
                                  {data.reduce((sum, d) => sum + d.sales, 0).toFixed(1)}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-500">Avg per Item</p>
                                <p className="text-lg font-bold text-purple-600">
                                  {(data.reduce((sum, d) => sum + d.sales, 0) / data.length).toFixed(2)}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-gray-500">Items</p>
                                <p className="text-lg font-bold text-green-600">{data.length}</p>
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                )}

                {/* Output Files */}
                {selectedJob.output_files && selectedJob.output_files.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Output Files</h3>
                    <div className="bg-gray-50 rounded-lg divide-y divide-gray-200">
                      {selectedJob.output_files.map((file, i) => (
                        <div key={i} className="px-3 py-2 flex items-center justify-between">
                          <span className="font-mono text-sm text-gray-900">{file.name}</span>
                          <span className="text-xs text-gray-500">{file.size}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Input Files */}
                {selectedJob.input_files && selectedJob.input_files.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Input Files</h3>
                    <div className="bg-gray-50 rounded-lg divide-y divide-gray-200">
                      {selectedJob.input_files.map((file, i) => (
                        <div key={i} className="px-3 py-2 flex items-center justify-between">
                          <span className="font-mono text-sm text-gray-900">{file.name}</span>
                          <span className="text-xs text-gray-500">{file.size}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!detailsLoading && selectedJob?.error && (
              <div className="p-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-red-700 text-sm">{selectedJob.error}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
