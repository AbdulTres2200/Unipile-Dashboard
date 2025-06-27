'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { CheckCircle, ArrowLeft, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { api } from '../../../lib/api'

export default function AuthSuccess() {
  const [mounted, setMounted] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [completed, setCompleted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    setMounted(true)

    // Check if this is a test connection or real OAuth
    const isTest = searchParams.get('test') === 'true'

    if (!isTest) {
      // Real OAuth - automatically complete the connection
      completeConnection()
    } else {
      // Test connection - already completed
      setCompleted(true)
    }
  }, [])

  const completeConnection = async () => {
    setProcessing(true)
    setError(null)

    try {
      // Try to determine provider from URL or default to gmail
      const provider = searchParams.get('provider') || 'gmail'

      console.log('Completing OAuth for provider:', provider)

      const result = await api.completeOAuthManually(provider)

      if (result.success) {
        console.log('OAuth completed successfully:', result)
        setCompleted(true)

        // Auto-redirect to dashboard after 3 seconds
        setTimeout(() => {
          router.push('/')
        }, 3000)
      } else {
        throw new Error(result.message || 'Failed to complete connection')
      }
    } catch (err) {
      console.error('Failed to complete OAuth:', err)
      setError(err instanceof Error ? err.message : 'Failed to complete connection')
    } finally {
      setProcessing(false)
    }
  }

  const retryConnection = () => {
    setError(null)
    completeConnection()
  }

  if (!mounted) return null

  const provider = searchParams.get('provider') || 'account'
  const isTest = searchParams.get('test') === 'true'

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full text-center">

        {/* Processing State */}
        {processing && (
          <>
            <Loader2 className="w-16 h-16 animate-spin text-blue-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Completing Connection...
            </h1>
            <p className="text-gray-600 mb-6">
              Setting up your {provider} account and preparing message import.
            </p>
          </>
        )}

        {/* Error State */}
        {error && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Connection Error
            </h1>
            <p className="text-gray-600 mb-6">
              {error}
            </p>
            <div className="space-y-3">
              <button
                onClick={retryConnection}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <Link
                href="/"
                className="block w-full bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Back to Dashboard
              </Link>
            </div>
          </>
        )}

        {/* Success State */}
        {completed && !processing && !error && (
          <>
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {isTest ? 'Test Connection Successful!' : 'Account Connected!'}
            </h1>
            <p className="text-gray-600 mb-6">
              {isTest
                ? `Test ${provider} connection completed for development.`
                : `Your ${provider} account has been successfully connected! Message import will begin automatically.`
              }
            </p>

            {!isTest && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-green-700">
                  🎉 Redirecting to dashboard in 3 seconds...
                </p>
              </div>
            )}

            <Link
              href="/"
              className="inline-flex items-center space-x-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Go to Dashboard</span>
            </Link>
          </>
        )}
      </div>
    </div>
  )
}