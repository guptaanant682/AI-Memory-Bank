'use client'

import { useState, useEffect } from 'react'
import { Brain, TrendingUp, Target, Lightbulb, BookOpen, ArrowRight, RefreshCw } from 'lucide-react'
import axios from 'axios'

interface KnowledgeGap {
  gap_category: string
  description: string
  severity: 'low' | 'medium' | 'high'
  concepts?: Array<{
    concept: string
    importance: number
    connections: number
    gap_type: string
  }>
  topics?: Array<{
    topic: string
    document_count: number
    avg_content_length: number
    gap_type: string
  }>
  domains?: Array<{
    domain: string
    missing_concepts: string[]
    coverage_percentage: number
  }>
  recommendation: string
}

interface LearningOpportunity {
  opportunity_type: string
  title: string
  description: string
  action_items: string[]
  priority: 'low' | 'medium' | 'high'
  estimated_time: string
}

interface SuggestedTopic {
  suggestion_type: string
  suggested_topic: string
  reason: string
  relevance_score: number
  learning_path: string[]
}

interface KnowledgeAnalysis {
  user_id: string
  analyzed_at: string
  knowledge_coverage: {
    total_documents: number
    topic_distribution: Record<string, { count: number; percentage: number }>
    concept_coverage: {
      total_concepts: number
      highly_connected: number
      moderately_connected: number
      weakly_connected: number
      average_connections: number
    }
    domain_analysis?: {
      domains: Record<string, {
        document_count: number
        percentage: number
        avg_confidence: number
        sample_titles: string[]
      }>
    }
  }
  identified_gaps: KnowledgeGap[]
  learning_opportunities: LearningOpportunity[]
  suggested_topics: SuggestedTopic[]
  knowledge_depth_analysis: {
    topic_depth_scores: Record<string, {
      score: number
      document_count: number
      avg_document_length: number
      total_content: number
    }>
    overall_depth_rating: string
    deep_knowledge_areas: Array<{
      topic: string
      score: number
      documents: number
    }>
    shallow_knowledge_areas: Array<{
      topic: string
      score: number
      documents: number
    }>
  }
}

interface DailyInsights {
  date: string
  user_id: string
  insights: Array<{
    type: string
    title: string
    description: string
    icon: string
  }>
  recommended_actions: Array<{
    action: string
    description: string
    priority: string
    estimated_time: string
  }>
  knowledge_highlight?: {
    title: string
    summary: string
    tags: string[]
    uploaded_at: string
  }
  learning_streak: number
  motivation: string
}

interface AILearningDashboardProps {
  userId: string
}

export default function AILearningDashboard({ userId }: AILearningDashboardProps) {
  const [analysis, setAnalysis] = useState<KnowledgeAnalysis | null>(null)
  const [insights, setInsights] = useState<DailyInsights | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'overview' | 'gaps' | 'opportunities' | 'insights'>('overview')

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadAnalysisData()
    loadDailyInsights()
  }, [userId])

  const loadAnalysisData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/ai-agent/${userId}/knowledge-gaps`)
      setAnalysis(response.data)
    } catch (err) {
      console.error('Error loading knowledge analysis:', err)
      setError('Failed to load knowledge analysis')
    }
  }

  const loadDailyInsights = async () => {
    try {
      const response = await axios.get(`${API_BASE}/ai-agent/${userId}/daily-insights`)
      setInsights(response.data)
    } catch (err) {
      console.error('Error loading daily insights:', err)
      setError('Failed to load daily insights')
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    setLoading(true)
    await Promise.all([loadAnalysisData(), loadDailyInsights()])
    setLoading(false)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-blue-100 text-blue-800'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-green-100 text-green-800'
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-lg p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-6 h-6 text-purple-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">AI Learning Assistant</h2>
              <p className="text-gray-600">Personalized learning insights and recommendations</p>
            </div>
          </div>
          
          <button
            onClick={refresh}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Analysis
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}
      </div>

      {/* Overview Cards */}
      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3">
              <BookOpen className="w-8 h-8 text-blue-600" />
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {analysis.knowledge_coverage.total_documents}
                </div>
                <div className="text-sm text-gray-600">Total Documents</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-green-600" />
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {analysis.knowledge_coverage.concept_coverage?.total_concepts || 0}
                </div>
                <div className="text-sm text-gray-600">Concepts</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-red-600" />
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {analysis.identified_gaps.length}
                </div>
                <div className="text-sm text-gray-600">Knowledge Gaps</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3">
              <Lightbulb className="w-8 h-8 text-yellow-600" />
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {analysis.learning_opportunities.length}
                </div>
                <div className="text-sm text-gray-600">Opportunities</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-lg">
        <div className="border-b border-gray-200">
          <nav className="flex">
            {[
              { key: 'overview', label: 'Overview', icon: Brain },
              { key: 'gaps', label: 'Knowledge Gaps', icon: Target },
              { key: 'opportunities', label: 'Opportunities', icon: TrendingUp },
              { key: 'insights', label: 'Daily Insights', icon: Lightbulb }
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as any)}
                className={`flex items-center gap-2 px-6 py-4 font-medium text-sm border-b-2 transition-colors ${
                  activeTab === key
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && analysis && (
            <div className="space-y-6">
              {/* Knowledge Depth Rating */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Knowledge Depth Assessment</h3>
                <p className="text-lg text-gray-700 mb-4">
                  {analysis.knowledge_depth_analysis.overall_depth_rating}
                </p>
                
                {/* Top Knowledge Areas */}
                {analysis.knowledge_depth_analysis.deep_knowledge_areas.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Strong Areas</h4>
                      <div className="space-y-2">
                        {analysis.knowledge_depth_analysis.deep_knowledge_areas.slice(0, 3).map((area, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-white rounded">
                            <span className="font-medium">{area.topic}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600">{area.documents} docs</span>
                              <div className="w-12 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-green-600 h-2 rounded-full" 
                                  style={{ width: `${Math.min(area.score, 100)}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {analysis.knowledge_depth_analysis.shallow_knowledge_areas.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Areas for Growth</h4>
                        <div className="space-y-2">
                          {analysis.knowledge_depth_analysis.shallow_knowledge_areas.slice(0, 3).map((area, index) => (
                            <div key={index} className="flex items-center justify-between p-2 bg-white rounded">
                              <span className="font-medium">{area.topic}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-600">{area.documents} docs</span>
                                <div className="w-12 bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-yellow-500 h-2 rounded-full" 
                                    style={{ width: `${Math.min(area.score, 100)}%` }}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Topic Distribution */}
              {Object.keys(analysis.knowledge_coverage.topic_distribution).length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Topic Distribution</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(analysis.knowledge_coverage.topic_distribution)
                      .slice(0, 9)
                      .map(([topic, data]) => (
                      <div key={topic} className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{topic}</h4>
                          <span className="text-sm text-gray-600">{data.percentage}%</span>
                        </div>
                        <div className="text-sm text-gray-600">{data.count} documents</div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${data.percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Knowledge Gaps Tab */}
          {activeTab === 'gaps' && analysis && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Identified Knowledge Gaps</h3>
              
              {analysis.identified_gaps.length === 0 ? (
                <div className="text-center py-8">
                  <Target className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No significant knowledge gaps identified!</p>
                  <p className="text-sm text-gray-500 mt-1">Your knowledge base appears well-connected.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {analysis.identified_gaps.map((gap, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-6">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-gray-900">{gap.gap_category}</h4>
                          <p className="text-gray-600 mt-1">{gap.description}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getSeverityColor(gap.severity)}`}>
                          {gap.severity} priority
                        </span>
                      </div>

                      {/* Gap Details */}
                      {gap.concepts && (
                        <div className="mb-4">
                          <h5 className="font-medium text-gray-900 mb-2">Isolated Concepts:</h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {gap.concepts.map((concept, idx) => (
                              <div key={idx} className="bg-gray-50 p-2 rounded text-sm">
                                <span className="font-medium">{concept.concept}</span>
                                <span className="text-gray-600 ml-2">
                                  (importance: {concept.importance}, connections: {concept.connections})
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {gap.topics && (
                        <div className="mb-4">
                          <h5 className="font-medium text-gray-900 mb-2">Shallow Topics:</h5>
                          <div className="space-y-2">
                            {gap.topics.map((topic, idx) => (
                              <div key={idx} className="bg-gray-50 p-2 rounded text-sm">
                                <span className="font-medium">{topic.topic}</span>
                                <span className="text-gray-600 ml-2">
                                  ({topic.document_count} docs, avg {topic.avg_content_length} words)
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {gap.domains && (
                        <div className="mb-4">
                          <h5 className="font-medium text-gray-900 mb-2">Missing Foundations:</h5>
                          <div className="space-y-2">
                            {gap.domains.map((domain, idx) => (
                              <div key={idx} className="bg-gray-50 p-3 rounded">
                                <div className="font-medium">{domain.domain}</div>
                                <div className="text-sm text-gray-600 mt-1">
                                  Missing: {domain.missing_concepts.join(', ')}
                                </div>
                                <div className="text-sm text-green-600">
                                  {domain.coverage_percentage}% covered
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="bg-blue-50 p-3 rounded">
                        <div className="font-medium text-blue-900">Recommendation:</div>
                        <div className="text-blue-800 text-sm mt-1">{gap.recommendation}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Learning Opportunities Tab */}
          {activeTab === 'opportunities' && analysis && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Learning Opportunities</h3>
              
              {analysis.learning_opportunities.length === 0 ? (
                <div className="text-center py-8">
                  <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No specific opportunities identified at the moment.</p>
                  <p className="text-sm text-gray-500 mt-1">Keep adding content to discover new learning paths!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {analysis.learning_opportunities.map((opportunity, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-6">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-gray-900">{opportunity.title}</h4>
                          <p className="text-gray-600 mt-1">{opportunity.description}</p>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(opportunity.priority)}`}>
                            {opportunity.priority} priority
                          </span>
                          <span className="text-xs text-gray-500">{opportunity.estimated_time}</span>
                        </div>
                      </div>

                      <div className="bg-gray-50 p-4 rounded">
                        <h5 className="font-medium text-gray-900 mb-2">Action Items:</h5>
                        <ul className="space-y-2">
                          {opportunity.action_items.map((item, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm">
                              <ArrowRight className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Suggested Topics */}
              {analysis.suggested_topics.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Suggested Topics to Explore</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysis.suggested_topics.slice(0, 6).map((topic, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-gray-900">{topic.suggested_topic}</h4>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                            {Math.round(topic.relevance_score * 100)}% match
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">{topic.reason}</p>
                        
                        <div>
                          <h5 className="text-sm font-medium text-gray-900 mb-2">Learning Path:</h5>
                          <div className="space-y-1">
                            {topic.learning_path.slice(0, 3).map((step, idx) => (
                              <div key={idx} className="text-xs text-gray-600 flex items-center gap-1">
                                <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
                                {step}
                              </div>
                            ))}
                            {topic.learning_path.length > 3 && (
                              <div className="text-xs text-gray-500">+ {topic.learning_path.length - 3} more steps</div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Daily Insights Tab */}
          {activeTab === 'insights' && insights && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Daily Insights</h3>
                <span className="text-sm text-gray-600">{new Date(insights.date).toLocaleDateString()}</span>
              </div>

              {/* Motivation */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg">
                <div className="flex items-center gap-3 mb-3">
                  <Lightbulb className="w-6 h-6 text-yellow-500" />
                  <h4 className="font-semibold text-gray-900">Daily Motivation</h4>
                </div>
                <p className="text-gray-700">{insights.motivation}</p>
              </div>

              {/* Insights */}
              {insights.insights.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Today's Insights</h4>
                  <div className="space-y-3">
                    {insights.insights.map((insight, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <div className="text-2xl">{insight.icon}</div>
                          <div>
                            <h5 className="font-medium text-gray-900">{insight.title}</h5>
                            <p className="text-gray-600 mt-1">{insight.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Actions */}
              {insights.recommended_actions.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Recommended Actions</h4>
                  <div className="space-y-3">
                    {insights.recommended_actions.map((action, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h5 className="font-medium text-gray-900">{action.action}</h5>
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(action.priority)}`}>
                              {action.priority}
                            </span>
                            <span className="text-xs text-gray-500">{action.estimated_time}</span>
                          </div>
                        </div>
                        <p className="text-gray-600 text-sm">{action.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Knowledge Highlight */}
              {insights.knowledge_highlight && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Recent Knowledge Highlight</h4>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h5 className="font-medium text-blue-900 mb-2">{insights.knowledge_highlight.title}</h5>
                    <p className="text-blue-800 text-sm mb-3">{insights.knowledge_highlight.summary}</p>
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        {insights.knowledge_highlight.tags.map((tag, index) => (
                          <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <span className="text-xs text-blue-600 ml-auto">
                        {new Date(insights.knowledge_highlight.uploaded_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}