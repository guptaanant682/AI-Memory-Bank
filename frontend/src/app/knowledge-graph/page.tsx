'use client'

import { useState, useEffect } from 'react'
import { ArrowLeft, Download, RefreshCw, Network, TrendingUp, Users, Brain } from 'lucide-react'
import Link from 'next/link'
import axios from 'axios'
import KnowledgeGraphVisualizer from '@/components/KnowledgeGraphVisualizer'
import KnowledgeDiscovery from '@/components/KnowledgeDiscovery'

interface Node {
  id: string
  label: string
  type: string
  size: number
  color: string
}

interface Edge {
  source: string
  target: string
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

interface ConceptDetails {
  concept: string
  related_concepts: Array<{
    concept: string
    shared_documents: number
    relationship_type: string
  }>
}

export default function KnowledgeGraphPage() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [conceptDetails, setConceptDetails] = useState<ConceptDetails | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadGraphData()
  }, [])

  const loadGraphData = async () => {
    try {
      setLoading(true)
      setError('')
      
      const response = await axios.get(`${API_BASE}/knowledge-graph`)
      setGraphData(response.data)
    } catch (err) {
      console.error('Error loading knowledge graph:', err)
      setError('Failed to load knowledge graph. Please ensure documents are uploaded and processed.')
      
      // Load sample data for demonstration
      setGraphData(generateSampleData())
    } finally {
      setLoading(false)
    }
  }

  const loadConceptDetails = async (concept: string) => {
    try {
      setLoadingDetails(true)
      const response = await axios.get(`${API_BASE}/knowledge-graph/concept/${encodeURIComponent(concept)}/related`)
      setConceptDetails(response.data)
    } catch (err) {
      console.error('Error loading concept details:', err)
      // Generate sample related concepts
      setConceptDetails({
        concept,
        related_concepts: [
          { concept: 'Related Topic 1', shared_documents: 5, relationship_type: 'co_occurrence' },
          { concept: 'Related Topic 2', shared_documents: 3, relationship_type: 'co_occurrence' },
        ]
      })
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleNodeClick = (node: Node) => {
    setSelectedNode(node)
    loadConceptDetails(node.label)
  }

  const handleNodeHover = (node: Node | null) => {
    // Optional: Update UI on hover
  }

  const downloadGraphData = () => {
    const dataStr = JSON.stringify(graphData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'knowledge-graph-data.json'
    link.click()
    URL.revokeObjectURL(url)
  }

  const generateSampleData = (): GraphData => {
    const nodes: Node[] = [
      { id: 'ai', label: 'Artificial Intelligence', type: 'concept', size: 50, color: '#3b82f6' },
      { id: 'ml', label: 'Machine Learning', type: 'concept', size: 45, color: '#3b82f6' },
      { id: 'nlp', label: 'Natural Language Processing', type: 'concept', size: 35, color: '#10b981' },
      { id: 'cv', label: 'Computer Vision', type: 'concept', size: 30, color: '#10b981' },
      { id: 'dl', label: 'Deep Learning', type: 'concept', size: 40, color: '#8b5cf6' },
      { id: 'neural', label: 'Neural Networks', type: 'concept', size: 35, color: '#8b5cf6' },
      { id: 'transformer', label: 'Transformers', type: 'concept', size: 25, color: '#f59e0b' },
      { id: 'bert', label: 'BERT', type: 'concept', size: 20, color: '#f59e0b' },
      { id: 'gpt', label: 'GPT', type: 'concept', size: 20, color: '#f59e0b' },
      { id: 'rag', label: 'RAG', type: 'concept', size: 15, color: '#ef4444' },
    ]

    const edges: Edge[] = [
      { source: 'ai', target: 'ml', strength: 8, type: 'contains' },
      { source: 'ml', target: 'dl', strength: 6, type: 'contains' },
      { source: 'ml', target: 'nlp', strength: 5, type: 'related_to' },
      { source: 'ml', target: 'cv', strength: 4, type: 'related_to' },
      { source: 'dl', target: 'neural', strength: 7, type: 'uses' },
      { source: 'nlp', target: 'transformer', strength: 6, type: 'uses' },
      { source: 'transformer', target: 'bert', strength: 4, type: 'example' },
      { source: 'transformer', target: 'gpt', strength: 4, type: 'example' },
      { source: 'nlp', target: 'rag', strength: 3, type: 'technique' },
      { source: 'cv', target: 'neural', strength: 4, type: 'uses' },
    ]

    return {
      nodes,
      edges,
      metadata: {
        total_nodes: nodes.length,
        total_edges: edges.length,
        generated_at: new Date().toISOString()
      }
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading knowledge graph...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Home
              </Link>
              <div className="h-6 w-px bg-gray-300" />
              <div className="flex items-center gap-2">
                <Network className="w-6 h-6 text-blue-600" />
                <h1 className="text-2xl font-bold text-gray-900">Knowledge Graph</h1>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={loadGraphData}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
              <button
                onClick={downloadGraphData}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800">{error}</p>
              <p className="text-sm text-yellow-600 mt-1">Showing sample data for demonstration.</p>
            </div>
          )}
        </div>
      </div>

      {/* Stats Bar */}
      <div className="bg-white border-t">
        <div className="container mx-auto px-4 py-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Network className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {graphData.metadata?.total_nodes || graphData.nodes.length}
                </div>
                <div className="text-sm text-gray-600">Concepts</div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {graphData.metadata?.total_edges || graphData.edges.length}
                </div>
                <div className="text-sm text-gray-600">Connections</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {new Set(graphData.nodes.map(n => n.type)).size}
                </div>
                <div className="text-sm text-gray-600">Categories</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Brain className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {Math.round((graphData.edges.length / Math.max(graphData.nodes.length, 1)) * 100) / 100}
                </div>
                <div className="text-sm text-gray-600">Avg Connections</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="space-y-6">
          {/* Knowledge Discovery Tools */}
          <KnowledgeDiscovery />
          
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Knowledge Graph Visualization */}
            <div className="lg:col-span-3">
              <KnowledgeGraphVisualizer
                data={graphData}
                width={800}
                height={600}
                onNodeClick={handleNodeClick}
                onNodeHover={handleNodeHover}
              />
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Selected Concept Details */}
              {selectedNode && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Concept Details</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900">{selectedNode.label}</h4>
                      <p className="text-sm text-gray-600 capitalize">Type: {selectedNode.type}</p>
                      <p className="text-sm text-gray-600">Importance: {selectedNode.size}</p>
                    </div>

                    {loadingDetails ? (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        Loading related concepts...
                      </div>
                    ) : conceptDetails && conceptDetails.related_concepts.length > 0 ? (
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">Related Concepts</h5>
                        <div className="space-y-2">
                          {conceptDetails.related_concepts.map((related, index) => (
                            <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                              <div className="font-medium text-gray-900">{related.concept}</div>
                              <div className="text-gray-600">
                                {related.shared_documents} shared documents
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-600">
                        No related concepts found.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Instructions */}
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">How to Use</h3>
                <div className="space-y-3 text-sm text-gray-600">
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                    <div>Click and drag nodes to explore the graph structure</div>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></div>
                    <div>Hover over nodes to highlight connections</div>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></div>
                    <div>Use search and filters to focus on specific concepts</div>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-orange-600 rounded-full mt-2 flex-shrink-0"></div>
                    <div>Click nodes to view detailed information</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}