import { useEffect, useRef, useState } from 'react'
import { Maximize2, Minimize2 } from 'lucide-react'

interface Term {
  term: string
  definition?: string
  metadata?: any
}

interface Relation {
  src_term: string
  rel_type: string
  dst_term: string
  metadata?: any
}

interface OntologyData {
  terms: Term[]
  relations: Relation[]
}

interface OntologyForceGraphProps {
  data: OntologyData
  height?: number
}

export default function OntologyForceGraph({ data, height = 400 }: OntologyForceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [selectedNode, setSelectedNode] = useState<Term | null>(null)

  useEffect(() => {
    if (!svgRef.current || !data.terms.length) return

    const svg = svgRef.current
    const width = svg.clientWidth
    const actualHeight = isFullscreen ? window.innerHeight - 100 : height

    // Clear previous content
    svg.innerHTML = ''

    // Create nodes and links
    const nodes = data.terms.map(t => ({
      id: t.term,
      ...t
    }))

    const links = data.relations.map(r => ({
      source: r.src_term,
      target: r.dst_term,
      type: r.rel_type
    }))

    // Simple force-directed layout (without D3 for now)
    // We'll position nodes in a circle and draw connecting lines
    const centerX = width / 2
    const centerY = actualHeight / 2
    const radius = Math.min(width, actualHeight) * 0.35

    const angleStep = (2 * Math.PI) / nodes.length

    // Calculate positions
    const nodePositions = new Map()
    nodes.forEach((node, i) => {
      const angle = i * angleStep
      const x = centerX + radius * Math.cos(angle)
      const y = centerY + radius * Math.sin(angle)
      nodePositions.set(node.id, { x, y })
    })

    // Create SVG content
    const svgContent = `
      <!-- Links -->
      <g class="links">
        ${links.map(link => {
          const source = nodePositions.get(link.source)
          const target = nodePositions.get(link.target)
          if (!source || !target) return ''
          
          const color = link.type === 'is_a' ? '#60a5fa' : 
                       link.type === 'part_of' ? '#a78bfa' :
                       link.type === 'synonym_of' ? '#34d399' :
                       '#64748b'
          
          return `
            <line 
              x1="${source.x}" 
              y1="${source.y}" 
              x2="${target.x}" 
              y2="${target.y}" 
              stroke="${color}" 
              stroke-width="2" 
              stroke-opacity="0.6"
              marker-end="url(#arrowhead)"
            />
            <text 
              x="${(source.x + target.x) / 2}" 
              y="${(source.y + target.y) / 2 - 5}" 
              font-size="10" 
              fill="#94a3b8"
              text-anchor="middle"
            >
              ${link.type}
            </text>
          `
        }).join('')}
      </g>

      <!-- Nodes -->
      <g class="nodes">
        ${nodes.map(node => {
          const pos = nodePositions.get(node.id)
          if (!pos) return ''
          
          return `
            <g class="node" data-term="${node.id}" style="cursor: pointer;">
              <circle 
                cx="${pos.x}" 
                cy="${pos.y}" 
                r="20" 
                fill="#1e293b" 
                stroke="#3b82f6" 
                stroke-width="3"
                class="node-circle"
              />
              <text 
                x="${pos.x}" 
                y="${pos.y + 35}" 
                text-anchor="middle" 
                font-size="12" 
                font-weight="bold"
                fill="#e2e8f0"
              >
                ${node.id}
              </text>
            </g>
          `
        }).join('')}
      </g>

      <!-- Arrow marker -->
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="10"
          refX="8"
          refY="3"
          orient="auto"
        >
          <polygon points="0 0, 10 3, 0 6" fill="#64748b" opacity="0.6" />
        </marker>
      </defs>
    `

    svg.innerHTML = svgContent

    // Add click handlers
    svg.querySelectorAll('.node').forEach(nodeEl => {
      nodeEl.addEventListener('click', (e) => {
        const termId = (e.currentTarget as HTMLElement).getAttribute('data-term')
        const term = data.terms.find(t => t.term === termId)
        if (term) setSelectedNode(term)
      })
      
      // Hover effects
      nodeEl.addEventListener('mouseenter', () => {
        const circle = nodeEl.querySelector('.node-circle')
        if (circle) {
          circle.setAttribute('r', '25')
          circle.setAttribute('stroke-width', '4')
        }
      })
      
      nodeEl.addEventListener('mouseleave', () => {
        const circle = nodeEl.querySelector('.node-circle')
        if (circle) {
          circle.setAttribute('r', '20')
          circle.setAttribute('stroke-width', '3')
        }
      })
    })

  }, [data, height, isFullscreen])

  return (
    <div className={`${isFullscreen ? 'fixed inset-0 z-50 bg-dark-bg p-6' : 'relative'}`}>
      <div className="relative bg-dark-card rounded-lg border border-pastel-blue/20 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-pastel-blue/20 bg-dark-surface">
          <div>
            <h3 className="font-semibold text-dark-text">Ontology Graph</h3>
            <p className="text-sm text-dark-muted">
              {data.terms.length} terms, {data.relations.length} relations
            </p>
          </div>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 hover:bg-dark-muted/20 rounded-lg transition-colors"
          >
            {isFullscreen ? (
              <Minimize2 className="w-5 h-5 text-dark-text" />
            ) : (
              <Maximize2 className="w-5 h-5 text-dark-text" />
            )}
          </button>
        </div>

        {/* Graph */}
        <div className="relative">
          <svg
            ref={svgRef}
            width="100%"
            height={isFullscreen ? window.innerHeight - 150 : height}
            className="bg-dark-surface"
          />

          {/* Legend */}
          <div className="absolute bottom-4 left-4 bg-dark-card/90 backdrop-blur-sm rounded-lg p-3 border border-pastel-blue/20">
            <div className="text-xs font-semibold text-dark-text mb-2">Relation Types</div>
            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-blue-400"></div>
                <span className="text-dark-muted">is_a</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-purple-400"></div>
                <span className="text-dark-muted">part_of</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-green-400"></div>
                <span className="text-dark-muted">synonym_of</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-0.5 bg-slate-500"></div>
                <span className="text-dark-muted">related_to</span>
              </div>
            </div>
          </div>

          {/* Selected Node Info */}
          {selectedNode && (
            <div className="absolute top-4 right-4 bg-dark-card/95 backdrop-blur-sm rounded-lg p-4 border border-pastel-blue/20 max-w-xs">
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-bold text-accent-blue">{selectedNode.term}</h4>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-dark-muted hover:text-dark-text"
                >
                  ×
                </button>
              </div>
              {selectedNode.definition && (
                <p className="text-sm text-dark-muted mb-2">{selectedNode.definition}</p>
              )}
              {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                <div className="text-xs text-dark-muted">
                  <div className="font-semibold mb-1">Metadata:</div>
                  <pre className="bg-dark-surface p-2 rounded">
                    {JSON.stringify(selectedNode.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {!data.terms.length && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-dark-muted">
            <p>No terms to visualize</p>
            <p className="text-sm">Add terms to see the graph</p>
          </div>
        </div>
      )}
    </div>
  )
}


