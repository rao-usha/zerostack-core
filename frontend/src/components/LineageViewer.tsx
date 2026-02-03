import React, { useCallback, useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
  ConnectionLineType,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import ELK from 'elkjs';

// Custom node component for lineage nodes
const LineageNode = ({ data }: { data: any }) => {
  const { icon, name, description, node_type, metadata, color } = data;

  const borderColor = color || '#4A90E2';
  
  return (
    <div
      style={{
        background: 'white',
        border: `2px solid ${borderColor}`,
        borderRadius: '8px',
        padding: '12px 16px',
        minWidth: '180px',
        maxWidth: '250px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
        <span style={{ fontSize: '20px' }}>{icon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontWeight: 600,
              fontSize: '14px',
              color: '#1f2937',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={name}
          >
            {name}
          </div>
        </div>
      </div>
      {description && (
        <div
          style={{
            fontSize: '12px',
            color: '#6b7280',
            marginTop: '4px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={description}
        >
          {description}
        </div>
      )}
      <div
        style={{
          fontSize: '10px',
          color: '#9ca3af',
          marginTop: '6px',
          textTransform: 'uppercase',
          fontWeight: 500,
        }}
      >
        {node_type.replace(/_/g, ' ')}
      </div>
      {metadata && Object.keys(metadata).length > 0 && (
        <div style={{ marginTop: '6px', fontSize: '11px', color: '#6b7280' }}>
          {metadata.row_count !== undefined && `${metadata.row_count} rows`}
          {metadata.column_count !== undefined && `, ${metadata.column_count} cols`}
          {metadata.extension && ` (${metadata.extension})`}
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  lineageNode: LineageNode,
};

interface LineageViewerProps {
  schema?: string;
  table?: string;
  nodeId?: string;
  nodeType?: string;
}

interface LineageData {
  nodes: any[];
  edges: any[];
  root_id?: string;
}

const elk = new ELK();

// ELK layout options for hierarchical graph
const elkOptions = {
  'elk.algorithm': 'layered',
  'elk.layered.spacing.nodeNodeBetweenLayers': '100',
  'elk.spacing.nodeNode': '80',
  'elk.direction': 'RIGHT',
  'elk.layered.nodePlacement.strategy': 'SIMPLE',
};

const getLayoutedElements = async (nodes: Node[], edges: Edge[]) => {
  const graph = {
    id: 'root',
    layoutOptions: elkOptions,
    children: nodes.map((node) => ({
      id: node.id,
      width: 220,
      height: 100,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  try {
    const layoutedGraph = await elk.layout(graph);

    const layoutedNodes = nodes.map((node) => {
      const layoutedNode = layoutedGraph.children?.find((lgNode: { id: string }) => lgNode.id === node.id);
      return {
        ...node,
        position: {
          x: layoutedNode?.x || 0,
          y: layoutedNode?.y || 0,
        },
      };
    });

    return { nodes: layoutedNodes, edges };
  } catch (error) {
    console.error('Layout error:', error);
    // Fallback to simple layout
    return {
      nodes: nodes.map((node, index) => ({
        ...node,
        position: {
          x: (index % 3) * 300,
          y: Math.floor(index / 3) * 150,
        },
      })),
      edges,
    };
  }
};

export const LineageViewer: React.FC<LineageViewerProps> = ({ schema, table, nodeId, nodeType }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLineage = async () => {
      setLoading(true);
      setError(null);

      try {
        let url = '';
        if (schema && table) {
          url = `/api/v1/lineage/table/${schema}/${table}`;
        } else if (nodeId && nodeType) {
          url = `/api/v1/lineage/node/${nodeId}?node_type=${nodeType}`;
        } else {
          setError('Please provide either schema/table or nodeId/nodeType');
          setLoading(false);
          return;
        }

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch lineage: ${response.statusText}`);
        }

        const data: LineageData = await response.json();

        // Convert API nodes to ReactFlow nodes
        const rfNodes: Node[] = data.nodes.map((node) => ({
          id: node.id,
          type: 'lineageNode',
          position: { x: 0, y: 0 }, // Will be set by layout
          data: node,
        }));

        // Convert API edges to ReactFlow edges
        const rfEdges: Edge[] = data.edges.map((edge, index) => ({
          id: `edge-${index}`,
          source: edge.source_id,
          target: edge.target_id,
          label: edge.label || edge.edge_type.replace(/_/g, ' '),
          type: ConnectionLineType.SmoothStep,
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#6b7280',
          },
          style: { stroke: '#6b7280', strokeWidth: 2 },
          labelStyle: { fill: '#6b7280', fontSize: 11, fontWeight: 500 },
          labelBgStyle: { fill: 'white', fillOpacity: 0.9 },
        }));

        // Apply automatic layout
        const layouted = await getLayoutedElements(rfNodes, rfEdges);
        setNodes(layouted.nodes);
        setEdges(layouted.edges);
      } catch (err) {
        console.error('Error fetching lineage:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchLineage();
  }, [schema, table, nodeId, nodeType, setNodes, setEdges]);

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    console.log('Node clicked:', node);
    // Future: navigate to node detail or expand lineage
  }, []);

  if (loading) {
    return (
      <div style={{ 
        width: '100%', 
        height: '600px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#f9fafb',
        borderRadius: '8px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔍</div>
          <div style={{ color: '#6b7280', fontSize: '14px' }}>Loading lineage...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        width: '100%', 
        height: '600px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#fef2f2',
        borderRadius: '8px',
        border: '1px solid #fca5a5'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>⚠️</div>
          <div style={{ color: '#b91c1c', fontSize: '14px', fontWeight: 500 }}>
            Error loading lineage
          </div>
          <div style={{ color: '#6b7280', fontSize: '12px', marginTop: '4px' }}>
            {error}
          </div>
        </div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div style={{ 
        width: '100%', 
        height: '600px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        background: '#f9fafb',
        borderRadius: '8px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>📊</div>
          <div style={{ color: '#6b7280', fontSize: '14px' }}>
            No lineage data available
          </div>
          <div style={{ color: '#9ca3af', fontSize: '12px', marginTop: '4px' }}>
            This table doesn't have tracked lineage yet
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '600px', border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: ConnectionLineType.SmoothStep,
          animated: true,
        }}
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node: Node) => {
            return node.data.color || '#4A90E2';
          }}
          maskColor="rgba(0, 0, 0, 0.05)"
          style={{
            background: 'white',
            border: '1px solid #e5e7eb',
          }}
        />
        <Panel position="top-right" style={{ background: 'white', padding: '8px 12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            <div style={{ fontWeight: 600, marginBottom: '4px' }}>Data Lineage</div>
            <div>{nodes.length} nodes • {edges.length} connections</div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
};

export default LineageViewer;
