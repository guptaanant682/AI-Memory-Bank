'use client'

import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Network, Eye, Zap, Search, Filter } from 'lucide-react'

interface Node extends d3.SimulationNodeDatum {
  id: string
  label: string
  type: string
  size: number
  color: string
  fx?: number | null
  fy?: number | null
}

interface Edge {
  source: string | Node
  target: string | Node
  strength: number
  type: string
}

interface GraphData {
  nodes: Node[]
  edges: Edge[]
  metadata?: {
    total_nodes: number
    total_edges: number
    generated_at: string
  }
}

interface KnowledgeGraphVisualizerProps {
  data: GraphData
  width?: number
  height?: number
  onNodeClick?: (node: Node) => void
  onNodeHover?: (node: Node | null) => void
}

export default function KnowledgeGraphVisualizer({
  data,
  width = 800,
  height = 600,
  onNodeClick,
  onNodeHover
}: KnowledgeGraphVisualizerProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    if (!data.nodes.length || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove() // Clear previous render

    // Filter data based on search and filter
    const filteredNodes = data.nodes.filter(node => {
      const matchesSearch = searchTerm === '' || 
        node.label.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesType = filterType === 'all' || node.type === filterType
      return matchesSearch && matchesType
    })

    const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
    const filteredEdges = data.edges.filter(edge => {
      const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id
      const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id
      return filteredNodeIds.has(sourceId) && filteredNodeIds.has(targetId)
    })

    // Create force simulation
    const simulation = d3.forceSimulation<Node>(filteredNodes)
      .force('link', d3.forceLink<Node, Edge>(filteredEdges)
        .id(d => d.id)
        .distance(d => Math.max(50, 100 - (d.strength || 1) * 10))
        .strength(0.3)
      )
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => Math.max(8, d.size / 2 + 2)))

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Create main group for zooming/panning
    const g = svg.append('g')

    // Create arrow markers for directed edges
    const defs = svg.append('defs')
    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 4)
      .attr('markerHeight', 4)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999')

    // Create edges
    const links = g.selectAll('.link')
      .data(filteredEdges)
      .enter().append('line')
      .attr('class', 'link')
      .style('stroke', '#999')
      .style('stroke-opacity', 0.6)
      .style('stroke-width', d => Math.max(1, Math.sqrt(d.strength || 1)))
      .attr('marker-end', 'url(#arrowhead)')

    // Create nodes
    const nodes = g.selectAll('.node')
      .data(filteredNodes)
      .enter().append('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(d3.drag<SVGGElement, Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
      )

    // Add circles for nodes
    nodes.append('circle')
      .attr('r', d => Math.max(5, d.size / 4))
      .style('fill', d => d.color)
      .style('stroke', '#fff')
      .style('stroke-width', 2)
      .on('mouseover', (event, d) => handleNodeHover(event, d))
      .on('mouseout', (event) => handleNodeHover(event, null))
      .on('click', (event, d) => handleNodeClick(event, d))

    // Add labels
    nodes.append('text')
      .text(d => d.label.length > 15 ? d.label.substring(0, 15) + '...' : d.label)
      .style('font-size', '10px')
      .style('font-family', 'Arial, sans-serif')
      .style('text-anchor', 'middle')
      .style('dominant-baseline', 'central')
      .style('fill', '#333')
      .style('pointer-events', 'none')
      .attr('dy', d => Math.max(5, d.size / 4) + 12)

    // Update positions on simulation tick
    simulation.on('tick', () => {
      links
        .attr('x1', d => (d.source as Node).x!)
        .attr('y1', d => (d.source as Node).y!)
        .attr('x2', d => (d.target as Node).x!)
        .attr('y2', d => (d.target as Node).y!)

      nodes.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGGElement, Node, Node>, d: Node) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, Node, Node>, d: Node) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, Node, Node>, d: Node) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    function handleNodeHover(event: any, node: Node | null) {
      if (onNodeHover) {
        onNodeHover(node)
      }
      
      // Highlight connected nodes
      if (node) {
        const connectedNodeIds = new Set<string>()
        filteredEdges.forEach(edge => {
          const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id
          const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id
          
          if (sourceId === node.id) connectedNodeIds.add(targetId)
          if (targetId === node.id) connectedNodeIds.add(sourceId)
        })

        nodes.selectAll('circle')
          .style('opacity', (d: any) => d.id === node.id || connectedNodeIds.has(d.id) ? 1.0 : 0.3)
        
        links
          .style('opacity', (d: any) => {
            const sourceId = typeof d.source === 'string' ? d.source : d.source.id
            const targetId = typeof d.target === 'string' ? d.target : d.target.id
            return sourceId === node.id || targetId === node.id ? 1.0 : 0.1
          })
      } else {
        nodes.selectAll('circle').style('opacity', 1.0)
        links.style('opacity', 0.6)
      }
    }

    function handleNodeClick(event: any, node: Node) {
      setSelectedNode(node)
      setShowDetails(true)
      if (onNodeClick) {
        onNodeClick(node)
      }
    }

    // Cleanup function
    return () => {
      simulation.stop()
    }

  }, [data, width, height, searchTerm, filterType, onNodeClick, onNodeHover])

  const uniqueTypes = [...new Set(data.nodes.map(n => n.type))]

  return (
    <div className="w-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Controls */}
      <div className="p-4 bg-gray-50 border-b flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Knowledge Graph</h3>
        </div>
        
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search concepts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Types</option>
            {uniqueTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
          >
            <Eye className="w-4 h-4" />
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
        </div>
      </div>

      <div className="flex">
        {/* Main Graph */}
        <div className="flex-1">
          <svg
            ref={svgRef}
            width={width}
            height={height}
            className="border-r"
          >
          </svg>
        </div>

        {/* Details Panel */}
        {showDetails && (
          <div className="w-80 p-4 bg-gray-50 overflow-y-auto">
            <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-purple-600" />
              Graph Insights
            </h4>
            
            {/* Graph Statistics */}
            <div className="mb-6">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Statistics</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Concepts:</span>
                  <span className="font-medium">{data.metadata?.total_nodes || data.nodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Connections:</span>
                  <span className="font-medium">{data.metadata?.total_edges || data.edges.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Visible Nodes:</span>
                  <span className="font-medium">{data.nodes.filter(n => 
                    (searchTerm === '' || n.label.toLowerCase().includes(searchTerm.toLowerCase())) &&
                    (filterType === 'all' || n.type === filterType)
                  ).length}</span>
                </div>
              </div>
            </div>

            {/* Selected Node Details */}
            {selectedNode && (
              <div className="mb-6">
                <h5 className="text-sm font-medium text-gray-700 mb-2">Selected Concept</h5>
                <div className="p-3 bg-white rounded border">
                  <div className="font-medium text-gray-900 mb-2">{selectedNode.label}</div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="capitalize">{selectedNode.type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Importance:</span>
                      <span>{selectedNode.size}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Connections:</span>
                      <span>{data.edges.filter(e => {
                        const sourceId = typeof e.source === 'string' ? e.source : e.source.id
                        const targetId = typeof e.target === 'string' ? e.target : e.target.id
                        return sourceId === selectedNode.id || targetId === selectedNode.id
                      }).length}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Top Concepts */}
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">Top Concepts</h5>
              <div className="space-y-2">
                {data.nodes
                  .sort((a, b) => b.size - a.size)
                  .slice(0, 5)
                  .map(node => (
                    <div
                      key={node.id}
                      className="flex items-center justify-between p-2 bg-white rounded border hover:shadow-sm transition-shadow cursor-pointer"
                      onClick={() => {
                        setSelectedNode(node)
                        setSearchTerm(node.label)
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: node.color }}
                        />
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {node.label}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">{node.size}</span>
                    </div>
                  ))}
              </div>
            </div>

            {/* Legend */}
            <div className="mt-6 pt-4 border-t">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Legend</h5>
              <div className="space-y-1 text-xs text-gray-600">
                <div>• Node size = concept importance</div>
                <div>• Edge thickness = relationship strength</div>
                <div>• Click and drag to explore</div>
                <div>• Hover to highlight connections</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}