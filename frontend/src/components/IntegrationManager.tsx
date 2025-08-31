'use client'

import { useState, useEffect } from 'react'
import { Cloud, Database, MessageSquare, Webhook, Settings, CheckCircle, AlertCircle, Clock, Plus } from 'lucide-react'
import axios from 'axios'

interface Integration {
  platform: string
  status: 'active' | 'inactive' | 'not_configured' | 'error'
  last_sync?: string
  created_at?: string
}

interface IntegrationStatus {
  user_id: string
  integrations: Record<string, Integration>
  recent_activity: Array<{
    id: string
    platform: string
    action: string
    timestamp: string
    details: any
  }>
  websocket_connections: number
  sync_queue_size: number
}

interface IntegrationManagerProps {
  userId: string
}

export default function IntegrationManager({ userId }: IntegrationManagerProps) {
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [setupModal, setSetupModal] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadIntegrationStatus()
    setupWebSocketConnection()
  }, [userId])

  const loadIntegrationStatus = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE}/integrations/${userId}/status`)
      setIntegrationStatus(response.data)
    } catch (err) {
      console.error('Error loading integration status:', err)
      setError('Failed to load integration status')
    } finally {
      setLoading(false)
    }
  }

  const setupWebSocketConnection = () => {
    try {
      const wsUrl = `ws://localhost:8000/ws/${userId}`
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setIsConnected(true)
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('Received WebSocket message:', data)
        
        // Update integration status based on real-time updates
        if (data.type === 'document_synced' || data.type === 'message_archived' || data.type === 'webhook_document_created') {
          loadIntegrationStatus() // Refresh status
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected')
        // Attempt reconnection after 5 seconds
        setTimeout(setupWebSocketConnection, 5000)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }

      return () => {
        ws.close()
      }
    } catch (error) {
      console.error('Error setting up WebSocket:', error)
      setIsConnected(false)
    }
  }

  const handleSetupIntegration = async (platform: string, config: any) => {
    try {
      let endpoint = ''
      let payload = { user_id: userId, ...config }

      switch (platform) {
        case 'google_drive':
          endpoint = '/integrations/google-drive'
          break
        case 'notion':
          endpoint = '/integrations/notion'
          break
        case 'slack':
          endpoint = '/integrations/slack'
          break
        default:
          throw new Error('Unknown platform')
      }

      await axios.post(`${API_BASE}${endpoint}`, payload)
      await loadIntegrationStatus()
      setSetupModal(null)
    } catch (error) {
      console.error(`Error setting up ${platform}:`, error)
      setError(`Failed to setup ${platform} integration`)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'inactive':
        return <Clock className="w-5 h-5 text-yellow-600" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      default:
        return <Settings className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'google_drive':
        return <Cloud className="w-8 h-8 text-blue-600" />
      case 'notion':
        return <Database className="w-8 h-8 text-black" />
      case 'slack':
        return <MessageSquare className="w-8 h-8 text-purple-600" />
      default:
        return <Webhook className="w-8 h-8 text-gray-600" />
    }
  }

  const getPlatformName = (platform: string) => {
    switch (platform) {
      case 'google_drive':
        return 'Google Drive'
      case 'notion':
        return 'Notion'
      case 'slack':
        return 'Slack'
      default:
        return platform.replace('_', ' ').toUpperCase()
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Real-time Integrations</h2>
          </div>
          
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Status Overview */}
        {integrationStatus && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">Active Connections</span>
              </div>
              <div className="text-2xl font-bold text-blue-900 mt-1">
                {integrationStatus.websocket_connections}
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-900">Active Integrations</span>
              </div>
              <div className="text-2xl font-bold text-green-900 mt-1">
                {Object.values(integrationStatus.integrations).filter(i => i.status === 'active').length}
              </div>
            </div>
            
            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-900">Pending Syncs</span>
              </div>
              <div className="text-2xl font-bold text-yellow-900 mt-1">
                {integrationStatus.sync_queue_size}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrationStatus && Object.entries(integrationStatus.integrations).map(([platform, integration]) => (
          <div key={platform} className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {getPlatformIcon(platform)}
                <div>
                  <h3 className="font-semibold text-gray-900">{getPlatformName(platform)}</h3>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(integration.status)}`}>
                    {integration.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
              {getStatusIcon(integration.status)}
            </div>

            <div className="space-y-2 mb-4">
              {integration.last_sync && (
                <div className="text-sm text-gray-600">
                  <strong>Last Sync:</strong> {new Date(integration.last_sync).toLocaleString()}
                </div>
              )}
              {integration.created_at && (
                <div className="text-sm text-gray-600">
                  <strong>Connected:</strong> {new Date(integration.created_at).toLocaleString()}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              {integration.status === 'not_configured' ? (
                <button
                  onClick={() => setSetupModal(platform)}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Setup
                </button>
              ) : (
                <button
                  onClick={() => setSetupModal(platform)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Configure
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      {integrationStatus && integrationStatus.recent_activity.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          
          <div className="space-y-3">
            {integrationStatus.recent_activity.slice(0, 10).map((activity) => (
              <div key={activity.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                {getPlatformIcon(activity.platform)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900 capitalize">
                      {activity.action.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-500">
                      from {getPlatformName(activity.platform)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mb-1">
                    {activity.details.file_name && `File: ${activity.details.file_name}`}
                    {activity.details.document_id && `Document: ${activity.details.document_id}`}
                    {activity.details.workspace_name && `Workspace: ${activity.details.workspace_name}`}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(activity.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Setup Modals */}
      {setupModal && (
        <IntegrationSetupModal
          platform={setupModal}
          onClose={() => setSetupModal(null)}
          onSetup={(config) => handleSetupIntegration(setupModal, config)}
        />
      )}
    </div>
  )
}

interface IntegrationSetupModalProps {
  platform: string
  onClose: () => void
  onSetup: (config: any) => void
}

function IntegrationSetupModal({ platform, onClose, onSetup }: IntegrationSetupModalProps) {
  const [config, setConfig] = useState<any>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await onSetup(config)
    } finally {
      setLoading(false)
    }
  }

  const renderConfigForm = () => {
    switch (platform) {
      case 'google_drive':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Google Drive Credentials (JSON)
              </label>
              <textarea
                rows={4}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Paste your Google Drive service account JSON here"
                onChange={(e) => {
                  try {
                    const credentials = JSON.parse(e.target.value)
                    setConfig({ credentials })
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
              />
            </div>
          </div>
        )
      
      case 'notion':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notion API Token
              </label>
              <input
                type="password"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="secret_xxx"
                onChange={(e) => setConfig((prev: any) => ({ ...prev, api_token: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database ID
              </label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Notion database ID"
                onChange={(e) => setConfig((prev: any) => ({ ...prev, database_id: e.target.value }))}
              />
            </div>
          </div>
        )
      
      case 'slack':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bot Token
              </label>
              <input
                type="password"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="xoxb-xxx"
                onChange={(e) => setConfig((prev: any) => ({ ...prev, bot_token: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Channel ID
              </label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="C1234567890"
                onChange={(e) => setConfig((prev: any) => ({ ...prev, channel_id: e.target.value }))}
              />
            </div>
          </div>
        )
      
      default:
        return <div>Configuration form for {platform} not implemented</div>
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Setup {platform.replace('_', ' ').toUpperCase()}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {renderConfigForm()}
          
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'Connecting...' : 'Connect'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}