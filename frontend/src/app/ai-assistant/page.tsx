'use client'

import { ArrowLeft, Brain } from 'lucide-react'
import Link from 'next/link'
import AILearningDashboard from '@/components/AILearningDashboard'

export default function AIAssistantPage() {
  const userId = "default" // In a real app, get from authentication

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
                <Brain className="w-6 h-6 text-purple-600" />
                <h1 className="text-2xl font-bold text-gray-900">AI Learning Assistant</h1>
              </div>
            </div>
          </div>

          <p className="text-gray-600 mt-2">
            Get personalized insights, discover knowledge gaps, and receive intelligent learning recommendations.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <AILearningDashboard userId={userId} />
      </div>
    </div>
  )
}