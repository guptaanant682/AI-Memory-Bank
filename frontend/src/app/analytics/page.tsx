'use client'

import { useState, useEffect } from 'react'
import { ArrowLeft, BarChart3, TrendingUp, Brain, Target, Users, Activity, Calendar, Clock } from 'lucide-react'
import Link from 'next/link'
import axios from 'axios'

interface AnalyticsData {
  user_id: string
  generated_at: string
  overview_metrics: any
  recent_trends: {
    upload_velocity: number
    trending_topics: Array<{
      topic: string
      growth_rate: number
      early_count: number
      recent_count: number
    }>
    new_topics: Array<{
      topic: string
      recent_mentions: number
      growth_type: string
    }>
  }
  knowledge_health: {
    network_density: number
    knowledge_hubs: Array<{
      concept: string
      influence_score: number
    }>
    clustering: number
  }
  recommendations: Array<{
    type: string
    title: string
    description: string
    priority: string
  }>
}

interface KnowledgeEvolution {
  user_id: string
  analysis_period: string
  analyzed_at: string
  timeline_analysis: {
    total_documents_in_period: number
    daily_upload_velocity: number
    upload_consistency: number
    peak_activity_periods: Array<{
      date: string
      document_count: number
      above_average: number
    }>
  }
  knowledge_growth: {
    total_documents: number
    document_velocity: number
    content_depth: number
    topic_diversity: number
    growth_trajectory: string
    learning_intensity: {
      average_weekly_intensity: number
      peak_intensity: number
      intensity_consistency: number
      high_intensity_weeks: number
    }
    knowledge_breadth_vs_depth: {
      breadth_score: number
      depth_score: number
      learning_style: string
      topic_specializations: Array<{
        topic: string
        document_count: number
        total_content: number
      }>
    }
  }
  trend_predictions: {
    next_month_projections: {
      estimated_documents: number
      confidence: string
      based_on_last_30_days: number
    }
    emerging_topics: Array<{
      topic_id: string
      keywords: string[]
      confidence: number
      description: string
    }>
    recommended_focus_areas: Array<{
      type: string
      topic: string
      reason: string
      priority: string
      action: string
    }>
  }
}

export default function AnalyticsPage() {
  const [dashboardData, setDashboardData] = useState<AnalyticsData | null>(null)
  const [evolutionData, setEvolutionData] = useState<KnowledgeEvolution | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [timeRange, setTimeRange] = useState<30 | 90 | 180>(90)

  const userId = "default"
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadAnalyticsData()
  }, [timeRange])

  const loadAnalyticsData = async () => {
    try {
      setLoading(true)
      setError('')

      // Load dashboard data and evolution analysis in parallel
      const [dashboardResponse, evolutionResponse] = await Promise.all([
        axios.get(`${API_BASE}/analytics/${userId}/dashboard`),
        axios.get(`${API_BASE}/analytics/${userId}/evolution?days_back=${timeRange}`)
      ])

      setDashboardData(dashboardResponse.data)
      setEvolutionData(evolutionResponse.data)
    } catch (err) {
      console.error('Error loading analytics:', err)
      setError('Failed to load analytics data')
      
      // Set sample data for demonstration
      setDashboardData({
        user_id: userId,
        generated_at: new Date().toISOString(),
        overview_metrics: {},
        recent_trends: {
          upload_velocity: 2.3,
          trending_topics: [
            { topic: 'AI', growth_rate: 45.2, early_count: 5, recent_count: 8 },
            { topic: 'Machine Learning', growth_rate: 32.1, early_count: 3, recent_count: 5 }
          ],
          new_topics: [
            { topic: 'Neural Networks', recent_mentions: 4, growth_type: 'new' }
          ]
        },
        knowledge_health: {
          network_density: 0.15,
          knowledge_hubs: [
            { concept: 'Artificial Intelligence', influence_score: 0.85 },
            { concept: 'Data Science', influence_score: 0.72 }
          ],
          clustering: 0.31
        },
        recommendations: [
          {
            type: 'consistency',
            title: 'Improve Learning Consistency',
            description: 'Your learning pattern shows some inconsistency. Try to maintain regular knowledge intake.',
            priority: 'medium'
          }
        ]
      })

      setEvolutionData({
        user_id: userId,
        analysis_period: `${timeRange} days`,
        analyzed_at: new Date().toISOString(),
        timeline_analysis: {
          total_documents_in_period: 24,
          daily_upload_velocity: 0.8,
          upload_consistency: 75.2,
          peak_activity_periods: [
            { date: '2024-01-15', document_count: 5, above_average: 2.5 }
          ]
        },
        knowledge_growth: {
          total_documents: 24,
          document_velocity: 0.8,
          content_depth: 1250.5,
          topic_diversity: 3.2,
          growth_trajectory: 'accelerating',
          learning_intensity: {
            average_weekly_intensity: 3.2,
            peak_intensity: 7.1,
            intensity_consistency: 68.5,
            high_intensity_weeks: 2
          },
          knowledge_breadth_vs_depth: {
            breadth_score: 65.2,
            depth_score: 45.8,
            learning_style: 'breadth-focused',
            topic_specializations: [
              { topic: 'AI', document_count: 8, total_content: 15000 },
              { topic: 'Programming', document_count: 6, total_content: 12000 }
            ]
          }
        },
        trend_predictions: {
          next_month_projections: {
            estimated_documents: 12,
            confidence: 'high',
            based_on_last_30_days: 10
          },
          emerging_topics: [
            {
              topic_id: 'emerging_1',
              keywords: ['neural', 'networks', 'deep'],
              confidence: 0.78,
              description: 'Topic characterized by: neural, networks, deep'
            }
          ],
          recommended_focus_areas: [
            {
              type: 'deepen_knowledge',
              topic: 'Machine Learning',
              reason: 'You have moderate coverage but could benefit from deeper exploration',
              priority: 'medium',
              action: 'Find more comprehensive resources'
            }
          ]
        }
      })
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-green-100 text-green-800'
    }
  }

  const getTrajectoryColor = (trajectory: string) => {
    switch (trajectory) {
      case 'accelerating': return 'text-green-600'
      case 'decelerating': return 'text-red-600'
      default: return 'text-blue-600'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
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
                <BarChart3 className="w-6 h-6 text-orange-600" />
                <h1 className="text-2xl font-bold text-gray-900">Knowledge Analytics</h1>
              </div>
            </div>

            {/* Time Range Selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Time Range:</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value) as 30 | 90 | 180)}
                className="border border-gray-300 rounded-lg px-3 py-1 text-sm focus:ring-2 focus:ring-orange-500"
              >
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 180 days</option>
              </select>
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

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Overview Cards */}
        {evolutionData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center gap-3">
                <Activity className="w-8 h-8 text-blue-600" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {evolutionData.timeline_analysis.total_documents_in_period}
                  </div>
                  <div className="text-sm text-gray-600">Documents Added</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-8 h-8 text-green-600" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {evolutionData.timeline_analysis.daily_upload_velocity.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Daily Velocity</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center gap-3">
                <Target className="w-8 h-8 text-purple-600" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {evolutionData.knowledge_growth.topic_diversity.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Topic Diversity</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center gap-3">
                <Clock className="w-8 h-8 text-orange-600" />
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {evolutionData.timeline_analysis.upload_consistency.toFixed(0)}%
                  </div>
                  <div className="text-sm text-gray-600">Consistency Score</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Knowledge Growth Analysis */}
        {evolutionData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Growth Trajectory */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Knowledge Growth</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="font-medium">Growth Trajectory</span>
                  <span className={`font-semibold capitalize ${getTrajectoryColor(evolutionData.knowledge_growth.growth_trajectory)}`}>
                    {evolutionData.knowledge_growth.growth_trajectory}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="font-medium">Content Depth</span>
                  <span className="font-semibold text-gray-900">
                    {evolutionData.knowledge_growth.content_depth.toFixed(0)} avg words
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="font-medium">Learning Style</span>
                  <span className="font-semibold text-blue-600 capitalize">
                    {evolutionData.knowledge_growth.knowledge_breadth_vs_depth.learning_style.replace('-', ' ')}
                  </span>
                </div>
              </div>
            </div>

            {/* Learning Intensity */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Intensity</h3>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Weekly Intensity</span>
                    <span>{evolutionData.knowledge_growth.learning_intensity.average_weekly_intensity.toFixed(1)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${Math.min(evolutionData.knowledge_growth.learning_intensity.average_weekly_intensity * 10, 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Consistency</span>
                    <span>{evolutionData.knowledge_growth.learning_intensity.intensity_consistency.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${evolutionData.knowledge_growth.learning_intensity.intensity_consistency}%` }}
                    ></div>
                  </div>
                </div>

                <div className="pt-2 border-t">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">{evolutionData.knowledge_growth.learning_intensity.high_intensity_weeks}</span> high-intensity weeks
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Breadth vs Depth Analysis */}
        {evolutionData && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Knowledge Breadth vs Depth</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">Breadth Score</span>
                  <span className="font-bold text-blue-600">{evolutionData.knowledge_growth.knowledge_breadth_vs_depth.breadth_score.toFixed(1)}/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-600 h-3 rounded-full" 
                    style={{ width: `${evolutionData.knowledge_growth.knowledge_breadth_vs_depth.breadth_score}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">Depth Score</span>
                  <span className="font-bold text-purple-600">{evolutionData.knowledge_growth.knowledge_breadth_vs_depth.depth_score.toFixed(1)}/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-purple-600 h-3 rounded-full" 
                    style={{ width: `${evolutionData.knowledge_growth.knowledge_breadth_vs_depth.depth_score}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Topic Specializations */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Topic Specializations</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {evolutionData.knowledge_growth.knowledge_breadth_vs_depth.topic_specializations.map((spec, index) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg">
                    <h5 className="font-medium text-gray-900">{spec.topic}</h5>
                    <div className="text-sm text-gray-600 mt-1">
                      {spec.document_count} documents
                    </div>
                    <div className="text-sm text-gray-600">
                      {(spec.total_content / 1000).toFixed(1)}k words
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Trending Topics and Predictions */}
        {dashboardData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trending Topics */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trending Topics</h3>
              
              {dashboardData.recent_trends.trending_topics.length > 0 ? (
                <div className="space-y-3">
                  {dashboardData.recent_trends.trending_topics.map((topic, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded">
                      <div>
                        <div className="font-medium text-gray-900">{topic.topic}</div>
                        <div className="text-sm text-gray-600">
                          {topic.early_count} → {topic.recent_count} documents
                        </div>
                      </div>
                      <div className="text-green-600 font-semibold">
                        +{topic.growth_rate.toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-center py-4">No trending topics identified yet.</p>
              )}

              {/* New Topics */}
              {dashboardData.recent_trends.new_topics.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-medium text-gray-900 mb-3">New Topics</h4>
                  <div className="space-y-2">
                    {dashboardData.recent_trends.new_topics.map((topic, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 bg-blue-50 rounded">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <span className="font-medium text-blue-900">{topic.topic}</span>
                        <span className="text-sm text-blue-600 ml-auto">
                          {topic.recent_mentions} mentions
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Knowledge Health */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Knowledge Network Health</h3>
              
              <div className="space-y-4 mb-6">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Network Density</span>
                  <span className="font-semibold text-blue-600">
                    {(dashboardData.knowledge_health.network_density * 100).toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Clustering Coefficient</span>
                  <span className="font-semibold text-purple-600">
                    {(dashboardData.knowledge_health.clustering * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Knowledge Hubs */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Top Knowledge Hubs</h4>
                <div className="space-y-2">
                  {dashboardData.knowledge_health.knowledge_hubs.map((hub, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="font-medium text-gray-900">{hub.concept}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-orange-500 h-2 rounded-full" 
                            style={{ width: `${hub.influence_score * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600">
                          {(hub.influence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Predictions and Recommendations */}
        {evolutionData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Future Predictions */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Future Predictions</h3>
              
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <h4 className="font-medium text-blue-900 mb-2">Next Month Projection</h4>
                <div className="text-2xl font-bold text-blue-900">
                  {evolutionData.trend_predictions.next_month_projections.estimated_documents} documents
                </div>
                <div className="text-sm text-blue-700">
                  Based on last {evolutionData.trend_predictions.next_month_projections.based_on_last_30_days} documents
                </div>
                <div className="text-sm text-blue-600 mt-1">
                  Confidence: {evolutionData.trend_predictions.next_month_projections.confidence}
                </div>
              </div>

              {/* Emerging Topics */}
              {evolutionData.trend_predictions.emerging_topics.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Emerging Topics</h4>
                  <div className="space-y-2">
                    {evolutionData.trend_predictions.emerging_topics.map((topic, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium text-gray-900">Topic {index + 1}</span>
                          <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded">
                            {(topic.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 mb-1">
                          Keywords: {topic.keywords.join(', ')}
                        </div>
                        <div className="text-sm text-gray-500">{topic.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Recommendations */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
              
              <div className="space-y-4">
                {dashboardData?.recommendations.map((rec, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{rec.title}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(rec.priority)}`}>
                        {rec.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{rec.description}</p>
                  </div>
                ))}

                {evolutionData.trend_predictions.recommended_focus_areas.map((focus, index) => (
                  <div key={`focus-${index}`} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{focus.topic}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(focus.priority)}`}>
                        {focus.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{focus.reason}</p>
                    <p className="text-sm text-blue-600">{focus.action}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}