// Type declarations for modules without types

declare module 'react-plotly.js' {
  import { Component } from 'react'
  import Plotly from 'plotly.js'

  interface PlotParams {
    data: Plotly.Data[]
    layout?: Partial<Plotly.Layout>
    config?: Partial<Plotly.Config>
    style?: React.CSSProperties
    className?: string
    useResizeHandler?: boolean
    onInitialized?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void
    onUpdate?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void
    onPurge?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void
    onError?: (err: Error) => void
    divId?: string
    onClick?: (event: Plotly.PlotMouseEvent) => void
    onHover?: (event: Plotly.PlotHoverEvent) => void
    onUnhover?: (event: Plotly.PlotMouseEvent) => void
    onSelected?: (event: Plotly.PlotSelectionEvent) => void
  }

  export default class Plot extends Component<PlotParams> {}
}

declare module '@xyflow/react' {
  import { ComponentType, CSSProperties, ReactNode, MouseEvent } from 'react'

  export interface Node<T = any> {
    id: string
    type?: string
    position: { x: number; y: number }
    data: T
    style?: CSSProperties
    className?: string
    sourcePosition?: string
    targetPosition?: string
    hidden?: boolean
    selected?: boolean
    dragging?: boolean
    draggable?: boolean
    selectable?: boolean
    connectable?: boolean
    deletable?: boolean
    width?: number
    height?: number
    parentNode?: string
    zIndex?: number
    extent?: string | [[number, number], [number, number]]
    expandParent?: boolean
    positionAbsolute?: { x: number; y: number }
    ariaLabel?: string
    focusable?: boolean
  }

  export interface Edge<T = any> {
    id: string
    source: string
    target: string
    sourceHandle?: string
    targetHandle?: string
    type?: string
    animated?: boolean
    hidden?: boolean
    data?: T
    style?: CSSProperties
    className?: string
    label?: ReactNode
    labelStyle?: CSSProperties
    labelShowBg?: boolean
    labelBgStyle?: CSSProperties
    labelBgPadding?: [number, number]
    labelBgBorderRadius?: number
    markerStart?: string | { type: MarkerType; color?: string; strokeWidth?: number }
    markerEnd?: string | { type: MarkerType; color?: string; strokeWidth?: number }
    selected?: boolean
    selectable?: boolean
    deletable?: boolean
    focusable?: boolean
    interactionWidth?: number
  }

  export enum MarkerType {
    Arrow = 'arrow',
    ArrowClosed = 'arrowclosed'
  }

  export enum ConnectionLineType {
    Bezier = 'default',
    Straight = 'straight',
    Step = 'step',
    SmoothStep = 'smoothstep',
    SimpleBezier = 'simplebezier'
  }

  export interface ReactFlowProps {
    nodes?: Node[]
    edges?: Edge[]
    onNodesChange?: (changes: any[]) => void
    onEdgesChange?: (changes: any[]) => void
    onNodeClick?: (event: MouseEvent, node: Node) => void
    onEdgeClick?: (event: MouseEvent, edge: Edge) => void
    onInit?: (instance: any) => void
    fitView?: boolean
    fitViewOptions?: any
    minZoom?: number
    maxZoom?: number
    defaultViewport?: { x: number; y: number; zoom: number }
    nodeTypes?: Record<string, ComponentType<any>>
    edgeTypes?: Record<string, ComponentType<any>>
    connectionLineType?: ConnectionLineType
    connectionLineStyle?: CSSProperties
    snapToGrid?: boolean
    snapGrid?: [number, number]
    onlyRenderVisibleElements?: boolean
    nodesDraggable?: boolean
    nodesConnectable?: boolean
    nodesFocusable?: boolean
    edgesFocusable?: boolean
    elementsSelectable?: boolean
    selectNodesOnDrag?: boolean
    panOnDrag?: boolean | number[]
    selectionOnDrag?: boolean
    selectionMode?: string
    panOnScroll?: boolean
    panOnScrollSpeed?: number
    panOnScrollMode?: string
    zoomOnScroll?: boolean
    zoomOnPinch?: boolean
    zoomOnDoubleClick?: boolean
    preventScrolling?: boolean
    attributionPosition?: string
    proOptions?: any
    defaultEdgeOptions?: any
    elevateEdgesOnSelect?: boolean
    elevateNodesOnSelect?: boolean
    disableKeyboardA11y?: boolean
    autoPanOnNodeDrag?: boolean
    autoPanOnConnect?: boolean
    connectionRadius?: number
    children?: ReactNode
    className?: string
    style?: CSSProperties
  }

  export const ReactFlow: ComponentType<ReactFlowProps>
  export const Background: ComponentType<any>
  export const Controls: ComponentType<any>
  export const MiniMap: ComponentType<any>
  export const Panel: ComponentType<any>

  export function useNodesState(initialNodes?: Node[]): [Node[], (changes: any) => void, (nodes: Node[] | ((nodes: Node[]) => Node[])) => void]
  export function useEdgesState(initialEdges?: Edge[]): [Edge[], (changes: any) => void, (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void]
}

declare module 'elkjs' {
  export interface ElkNode {
    id: string
    width?: number
    height?: number
    x?: number
    y?: number
    children?: ElkNode[]
    ports?: ElkPort[]
    edges?: ElkEdge[]
    layoutOptions?: Record<string, string>
  }

  export interface ElkPort {
    id: string
    x?: number
    y?: number
  }

  export interface ElkEdge {
    id: string
    sources: string[]
    targets: string[]
    sections?: ElkEdgeSection[]
  }

  export interface ElkEdgeSection {
    startPoint: { x: number; y: number }
    endPoint: { x: number; y: number }
    bendPoints?: Array<{ x: number; y: number }>
  }

  export interface LayoutOptions {
    [key: string]: string
  }

  export default class ELK {
    constructor(options?: { defaultLayoutOptions?: LayoutOptions })
    layout(graph: ElkNode, options?: { layoutOptions?: LayoutOptions }): Promise<ElkNode>
  }
}
