'use client'

import { useState } from 'react'
import { Upload, Search, Brain, FileText, MessageCircle, Image, Music, Mic, Video, Network, Zap, Users, BarChart3 } from 'lucide-react'
import axios from 'axios'
import Link from 'next/link'

export default function Home() {
  const [query, setQuery] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const [queryResponse, setQueryResponse] = useState<string>('')
  const [queryLoading, setQueryLoading] = useState(false)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api'

  const getFileIcon = (file: File) => {
    const type = file.type
    if (type.startsWith('image/')) return <Image className="w-4 h-4 text-green-500" />
    if (type.startsWith('audio/')) return <Music className="w-4 h-4 text-purple-500" />
    if (type.startsWith('video/')) return <Video className="w-4 h-4 text-red-500" />
    return <FileText className="w-4 h-4 text-gray-500" />
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
      setUploadStatus('')
    }
  }

  const uploadFiles = async () => {
    if (files.length === 0) return

    setUploading(true)
    setUploadStatus('')

    try {
      // Process files sequentially for better performance
      const results = []
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        setUploadStatus(`Uploading ${i + 1} of ${files.length}: ${file.name}`)
        
        try {
          // For serverless, send file content as JSON
          const fileContent = await file.text()
          const response = await axios.post(`${API_BASE}/upload`, {
            content: fileContent,
            filename: file.name
          }, {
            headers: {
              'Content-Type': 'application/json',
            },
            timeout: 30000, // 30 second timeout
          })
          results.push({ file: file.name, status: 'success', data: response.data })
        } catch (error) {
          console.error(`Upload error for ${file.name}:`, error)
          results.push({ file: file.name, status: 'error', error: error.message })
        }
      }
      
      const successful = results.filter(r => r.status === 'success').length
      setUploadStatus(`Successfully uploaded ${successful} of ${files.length} files`)
      
      // Clear files after upload attempt
      setFiles([])

    } catch (error) {
      console.error('Upload error:', error)
      setUploadStatus('Error uploading files. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setQueryLoading(true)
    setQueryResponse('')

    try {
      const response = await axios.post(`${API_BASE}/query`, {
        query: query.trim()
      }, {
        timeout: 10000 // 10 second timeout for faster feedback
      })

      const data = response.data
      let displayResponse = data.answer || 'No response received.'
      
      // Add performance info if available
      if (data.processing_time_ms) {
        displayResponse += `\n\n⚡ Response time: ${data.processing_time_ms}ms`
      }
      if (data.from_cache) {
        displayResponse += ' (cached)'
      }
      
      setQueryResponse(displayResponse)
    } catch (error) {
      console.error('Query error:', error)
      if (error.code === 'ECONNABORTED') {
        setQueryResponse('Query timeout - please try a shorter question or check if documents are uploaded.')
      } else {
        setQueryResponse('Error processing your question. Please try again.')
      }
    } finally {
      setQueryLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <Brain className="w-16 h-16 text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            AI Memory Bank
          </h1>
          
          {/* Navigation Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Link
              href="/knowledge-graph"
              className="flex items-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Network className="w-5 h-5" />
              <span className="font-medium">Knowledge Graph</span>
            </Link>
            
            <Link
              href="/ai-assistant"
              className="flex items-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Brain className="w-5 h-5" />
              <span className="font-medium">AI Assistant</span>
            </Link>
            
            <Link
              href="/integrations"
              className="flex items-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Zap className="w-5 h-5" />
              <span className="font-medium">Integrations</span>
            </Link>
            
            <Link
              href="/analytics"
              className="flex items-center gap-2 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <BarChart3 className="w-5 h-5" />
              <span className="font-medium">Analytics</span>
            </Link>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your personal lifelong knowledge assistant. Upload documents, images, and audio files. 
            Ask questions and discover insights from your multimodal knowledge.
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
              <Upload className="w-6 h-6 mr-2 text-blue-600" />
              Upload Files
            </h2>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                multiple
                accept=".txt,.pdf,.doc,.docx,.md,.mp3,.wav,.m4a,.flac,.ogg,.aac,.jpg,.jpeg,.png,.gif,.bmp,.webp,.tiff"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <div className="flex space-x-2 mb-4">
                  <FileText className="w-8 h-8 text-blue-400" />
                  <Image className="w-8 h-8 text-green-400" />
                  <Music className="w-8 h-8 text-purple-400" />
                </div>
                <p className="text-lg text-gray-600 mb-2">
                  Drop files here or click to upload
                </p>
                <p className="text-sm text-gray-500">
                  Documents: PDF, DOC, TXT, MD • Images: JPG, PNG, GIF • Audio: MP3, WAV, M4A
                </p>
              </label>
            </div>
            
            {files.length > 0 && (
              <div className="mt-4">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Uploaded Files ({files.length})
                </h3>
                <div className="space-y-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center p-2 bg-gray-50 rounded"
                    >
                      {getFileIcon(file)}
                      <span className="text-sm text-gray-700 ml-2">{file.name}</span>
                      <span className="text-xs text-gray-500 ml-auto">
                        {(file.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex flex-col items-center space-y-2">
                  <button
                    onClick={uploadFiles}
                    disabled={uploading || files.length === 0}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    {uploading ? 'Processing...' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
                  </button>
                  {uploadStatus && (
                    <p className={`text-sm ${uploadStatus.includes('Error') ? 'text-red-600' : 'text-green-600'}`}>
                      {uploadStatus}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Search Section */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4 flex items-center">
              <MessageCircle className="w-6 h-6 mr-2 text-blue-600" />
              Ask Questions
            </h2>
            <form onSubmit={handleQuery} className="space-y-4">
              <div className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask anything about your documents..."
                  className="w-full p-4 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  className="absolute right-2 top-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Search className="w-5 h-5" />
                </button>
              </div>
            </form>

            {/* Response Area */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg min-h-[200px]">
              {queryLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600">Processing your question...</span>
                </div>
              ) : queryResponse ? (
                <div className="space-y-2">
                  <h4 className="font-semibold text-gray-900">Answer:</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{queryResponse}</p>
                </div>
              ) : (
                <p className="text-gray-600 text-center">
                  Upload documents, images, or audio files and ask questions to see AI-powered responses here.
                </p>
              )}
            </div>
          </div>

          {/* Features Preview */}
          <div className="mt-12 grid md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <Image className="w-10 h-10 text-green-600 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Image Understanding
              </h3>
              <p className="text-gray-600">
                AI analyzes and describes visual content
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <Music className="w-10 h-10 text-purple-600 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Audio Transcription
              </h3>
              <p className="text-gray-600">
                Convert speech to searchable text
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <Brain className="w-10 h-10 text-blue-600 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Multimodal Search
              </h3>
              <p className="text-gray-600">
                Search across text, images, and audio
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}