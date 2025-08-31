'use client'

import React, { useState, useEffect } from 'react'
import { Search, Lightbulb, ArrowRight, BookOpen, Users, TrendingUp, Zap } from 'lucide-react'
import axios from 'axios'

interface RelatedConcept {
  concept: string
  shared_documents: number
  relationship_type: string
}

interface KnowledgePath {
  path: string[]
  strength: number
}

interface DocumentSuggestion {
  suggestion_type: string
  source_tag: string
  related_concept: string
  strength: number
  reason: string
}

interface KnowledgeSummary {
  document_count: number
  knowledge_overview: {
    total_concepts: number
    total_entities: number
    total_relationships: number
    dominant_topics: Array<{
      concept: string
      importance_score: number
      type: string
    }>
    knowledge_clusters: Array<{
      central_concept: string
      connection_count: number
      cluster_type: string
    }>
  }
}

interface KnowledgeDiscoveryProps {
  className?: string
}

export default function KnowledgeDiscovery({ className }: KnowledgeDiscoveryProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [relatedConcepts, setRelatedConcepts] = useState<RelatedConcept[]>([])
  const [knowledgePaths, setKnowledgePaths] = useState<KnowledgePath[]>([])
  const [suggestions, setSuggestions] = useState<DocumentSuggestion[]>([])
  const [knowledgeSummary, setKnowledgeSummary] = useState<KnowledgeSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [pathSearch, setPathSearch] = useState({ start: '', end: '' })

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadKnowledgeSummary()
  }, [])

  const loadKnowledgeSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/knowledge/summary`)
      setKnowledgeSummary(response.data)
    } catch (error) {
      console.error('Error loading knowledge summary:', error)
      // Fallback summary
      setKnowledgeSummary({
        document_count: 0,
        knowledge_overview: {
          total_concepts: 0,
          total_entities: 0,
          total_relationships: 0,
          dominant_topics: [],
          knowledge_clusters: []
        }
      })
    }
  }

  const searchRelatedConcepts = async () => {
    if (!searchTerm.trim()) return

    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE}/knowledge-graph/concept/${encodeURIComponent(searchTerm)}/related`)
      setRelatedConcepts(response.data.related_concepts || [])
    } catch (error) {
      console.error('Error searching related concepts:', error)
      setRelatedConcepts([])
    } finally {
      setLoading(false)
    }
  }

  const searchKnowledgePaths = async () => {
    if (!pathSearch.start.trim() || !pathSearch.end.trim()) return

    try {
      setLoading(true)
      const response = await axios.get(
        `${API_BASE}/knowledge-graph/path/${encodeURIComponent(pathSearch.start)}/${encodeURIComponent(pathSearch.end)}`
      )
      
      const paths = response.data.paths || []
      setKnowledgePaths(paths.map((path: string[], index: number) => ({
        path,
        strength: paths.length - index // Simple strength based on order
      })))
    } catch (error) {
      console.error('Error searching knowledge paths:', error)
      setKnowledgePaths([])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent, action: () => void) => {
    if (e.key === 'Enter') {
      action()
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Knowledge Summary */}
      {knowledgeSummary && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-blue-600" />
            Knowledge Overview
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {knowledgeSummary.knowledge_overview.total_concepts}
              </div>
              <div className="text-sm text-gray-600">Concepts</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {knowledgeSummary.knowledge_overview.total_relationships}
              </div>
              <div className="text-sm text-gray-600">Connections</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {knowledgeSummary.knowledge_overview.knowledge_clusters.length}
              </div>
              <div className="text-sm text-gray-600">Clusters</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {knowledgeSummary.document_count}
              </div>
              <div className="text-sm text-gray-600">Documents</div>
            </div>
          </div>

          {/* Dominant Topics */}
          {knowledgeSummary.knowledge_overview.dominant_topics.length > 0 && (
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Dominant Topics</h4>
              <div className="flex flex-wrap gap-2">
                {knowledgeSummary.knowledge_overview.dominant_topics.slice(0, 8).map((topic, index) => (
                  <div
                    key={index}
                    className="px-3 py-1 bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 rounded-full text-sm font-medium flex items-center gap-1"
                  >
                    {topic.concept}
                    <span className="text-xs text-blue-600">({topic.importance_score})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Concept Discovery */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Search className="w-6 h-6 text-green-600" />
          Concept Discovery
        </h3>
        
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => handleKeyPress(e, searchRelatedConcepts)}
            placeholder="Enter a concept to find related ideas..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <button
            onClick={searchRelatedConcepts}
            disabled={loading || !searchTerm.trim()}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors"
          >
            {loading ? 'Searching...' : 'Discover'}
          </button>
        </div>

        {relatedConcepts.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Related to "{searchTerm}":</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {relatedConcepts.map((related, index) => (
                <div
                  key={index}
                  className="p-3 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow cursor-pointer"
                  onClick={() => setSearchTerm(related.concept)}
                >
                  <div className="font-medium text-gray-900">{related.concept}</div>
                  <div className="text-sm text-gray-600">
                    {related.shared_documents} shared documents • {related.relationship_type}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Knowledge Path Finder */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Lightbulb className="w-6 h-6 text-purple-600" />
          Knowledge Path Finder
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <input
            type="text"
            value={pathSearch.start}
            onChange={(e) => setPathSearch(prev => ({ ...prev, start: e.target.value }))}
            placeholder="Start concept..."
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <input
            type="text"
            value={pathSearch.end}
            onChange={(e) => setPathSearch(prev => ({ ...prev, end: e.target.value }))}
            onKeyPress={(e) => handleKeyPress(e, searchKnowledgePaths)}
            placeholder="End concept..."
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <button
            onClick={searchKnowledgePaths}
            disabled={loading || !pathSearch.start.trim() || !pathSearch.end.trim()}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 transition-colors"
          >
            Find Path
          </button>
        </div>

        {knowledgePaths.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">
              Knowledge paths from "{pathSearch.start}" to "{pathSearch.end}":
            </h4>
            <div className="space-y-2">
              {knowledgePaths.map((pathInfo, index) => (
                <div
                  key={index}
                  className="p-3 bg-purple-50 border border-purple-200 rounded-lg"
                >
                  <div className="flex items-center gap-2 text-sm">
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                      Path {index + 1}
                    </span>
                    <div className="flex items-center gap-2 flex-wrap">
                      {pathInfo.path.map((concept, conceptIndex) => (
                        <React.Fragment key={conceptIndex}>
                          <span className="font-medium text-gray-900">{concept}</span>
                          {conceptIndex < pathInfo.path.length - 1 && (
                            <ArrowRight className="w-4 h-4 text-gray-400" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {knowledgePaths.length === 0 && pathSearch.start && pathSearch.end && !loading && (
          <div className="text-center py-8 text-gray-500">
            <Zap className="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <p>No knowledge paths found between these concepts.</p>
            <p className="text-sm">Try different or more specific terms.</p>
          </div>
        )}
      </div>

      {/* Quick Tips */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-600" />
          Discovery Tips
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-700">
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <strong>Concept Discovery:</strong> Search for any topic to find related concepts and ideas
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <strong>Knowledge Paths:</strong> Find connections between seemingly unrelated concepts
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <strong>Explore Clusters:</strong> Identify highly connected knowledge areas
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <strong>Visual Exploration:</strong> Use the Knowledge Graph for interactive discovery
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}