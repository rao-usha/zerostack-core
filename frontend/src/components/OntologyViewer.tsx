import { useState, useEffect } from 'react'
import { Network, FileJson, Loader2 } from 'lucide-react'
import OntologyForceGraph from './OntologyForceGraph'
import { getOntology } from '../api/client'

interface OntologyViewerProps {
  ontologyId: string
  defaultView?: 'graph' | 'json'
}

export default function OntologyViewer({ ontologyId, defaultView = 'graph' }: OntologyViewerProps) {
  const [view, setView] = useState<'graph' | 'json'>(defaultView)
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadOntology()
  }, [ontologyId])

  const loadOntology = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await getOntology(ontologyId)
      setData(result)
    } catch (err: any) {
      setError(err.message || 'Failed to load ontology')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 bg-dark-card rounded-lg border border-pastel-blue/20">
        <Loader2 className="w-6 h-6 animate-spin text-accent-blue" />
        <span className="ml-2 text-dark-muted">Loading ontology...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
        Error: {error}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-4 bg-dark-card rounded-lg border border-pastel-blue/20 text-dark-muted text-center">
        No data available
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* View Toggle */}
      <div className="inline-flex items-center gap-1 bg-dark-surface rounded-lg p-1">
        <button
          onClick={() => setView('graph')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all font-medium ${
            view === 'graph'
              ? 'bg-accent-blue text-white shadow-md'
              : 'text-dark-muted hover:text-dark-text'
          }`}
        >
          <Network className="w-4 h-4" />
          Force Graph
        </button>
        <button
          onClick={() => setView('json')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all font-medium ${
            view === 'json'
              ? 'bg-accent-blue text-white shadow-md'
              : 'text-dark-muted hover:text-dark-text'
          }`}
        >
          <FileJson className="w-4 h-4" />
          JSON View
        </button>
      </div>

      {/* Content */}
      {view === 'graph' ? (
        <OntologyForceGraph data={data} height={400} />
      ) : (
        <div className="bg-dark-card rounded-lg border border-pastel-blue/20 overflow-hidden">
          <div className="p-3 border-b border-pastel-blue/20 bg-dark-surface">
            <h3 className="font-semibold text-dark-text">JSON View</h3>
            <p className="text-sm text-dark-muted">
              {data.terms?.length || 0} terms, {data.relations?.length || 0} relations
            </p>
          </div>
          <div className="p-4 max-h-[500px] overflow-auto">
            <pre className="text-sm text-dark-text font-mono">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Stats Summary */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-dark-card rounded-lg p-3 border border-pastel-blue/20">
          <div className="text-2xl font-bold text-accent-blue">{data.terms?.length || 0}</div>
          <div className="text-sm text-dark-muted">Terms</div>
        </div>
        <div className="bg-dark-card rounded-lg p-3 border border-pastel-blue/20">
          <div className="text-2xl font-bold text-pastel-purple">{data.relations?.length || 0}</div>
          <div className="text-sm text-dark-muted">Relations</div>
        </div>
      </div>
    </div>
  )
}


