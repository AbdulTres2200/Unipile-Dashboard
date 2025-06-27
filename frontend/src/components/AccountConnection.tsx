'use client'

import { useState, useEffect } from 'react'
import { Mail, Linkedin, CheckCircle, AlertCircle, Loader2, ExternalLink, MessageSquare, RefreshCw } from 'lucide-react'
import { api, ConnectionStatus, Account } from '@/lib/api'
import { useRouter } from 'next/navigation'

export default function AccountConnection() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [syncLoading, setSyncLoading] = useState(false)
  const router = useRouter()

  useEffect(() => {
    setMounted(true)
    loadConnectionStatus()

    // Poll for status updates every 5 seconds
    const interval = setInterval(loadConnectionStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadConnectionStatus = async () => {
    try {
      const [status, accountsData] = await Promise.all([
        api.getConnectionStatus(),
        api.getAccounts()
      ])
      setConnectionStatus(status)
      setAccounts(accountsData.accounts)
      setError(null)
    } catch (err) {
      console.error('Failed to load connection status:', err)
      setError(err instanceof Error ? err.message : 'Failed to load status')
    }
  }

  const handleConnect = async (provider: string) => {
    setLoading(provider)
    setError(null)

    try {
      // Try the new connect endpoint first
      const response = await api.connectLatestAccount(provider)

      if (response.success) {
        // Success! Refresh the data
        await loadConnectionStatus()
        setLoading(null)
      } else {
        throw new Error(response.message || 'Failed to connect account')
      }
    } catch (err) {
      console.error(`Failed to connect ${provider}:`, err)

      // Fallback to hosted auth
      try {
        const response = await api.createHostedAuth(provider)

        if (response.success && response.is_real) {
          window.location.href = response.auth_url
        } else {
          throw new Error(response.message || 'Failed to create auth link')
        }
      } catch (fallbackErr) {
        setError(fallbackErr instanceof Error ? fallbackErr.message : 'Connection failed')
        setLoading(null)
      }
    }
  }

  const handleSyncAccounts = async () => {
    setSyncLoading(true)
    setError(null)

    try {
      const response = await api.syncAccounts()

      if (response.success) {
        await loadConnectionStatus()
        setError(null)
      } else {
        throw new Error(response.message || 'Failed to sync accounts')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync accounts')
    } finally {
      setSyncLoading(false)
    }
  }

  const getProviderStatus = (provider: 'gmail' | 'linkedin') => {
    if (!connectionStatus) return { connected: false, accounts: [] }
    return connectionStatus[provider]
  }

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Message Aggregator
            </h1>
            <p className="text-lg text-gray-600">
              Connect Gmail and LinkedIn to start aggregating your conversations
            </p>
          </div>

          {/* Quick Actions */}
          {connectionStatus?.both_connected && (
            <div className="mb-8 bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    🎉 Ready to explore your messages!
                  </h3>
                  <p className="text-gray-600">
                    Your accounts are connected. View and search through all your conversations.
                  </p>
                </div>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="flex items-center space-x-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <MessageSquare className="w-5 h-5" />
                  <span>View Messages</span>
                </button>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          {/* Sync Button */}
          <div className="mb-6 text-center">
            <button
              onClick={handleSyncAccounts}
              disabled={syncLoading}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${syncLoading ? 'animate-spin' : ''}`} />
              <span>{syncLoading ? 'Syncing...' : 'Sync with Unipile'}</span>
            </button>
            <p className="text-sm text-gray-500 mt-2">
              Sync to get the latest connected accounts from Unipile
            </p>
          </div>

          {/* Connection Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">

            {/* Gmail Connection */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                      <Mail className="w-6 h-6 text-red-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Gmail</h3>
                      <p className="text-sm text-gray-600">Connect your email</p>
                    </div>
                  </div>

                  {getProviderStatus('gmail').connected ? (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  ) : (
                    <div className="w-6 h-6" />
                  )}
                </div>

                <div className="mb-4">
                  {getProviderStatus('gmail').connected ? (
                    <div className="text-sm text-green-700 bg-green-50 p-3 rounded-lg">
                      ✅ Connected ({getProviderStatus('gmail').accounts.length} account{getProviderStatus('gmail').accounts.length !== 1 ? 's' : ''})
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600">
                      Import all your Gmail conversations and emails automatically
                    </div>
                  )}
                </div>

                <button
                  onClick={() => handleConnect('gmail')}
                  disabled={loading === 'gmail' || getProviderStatus('gmail').connected}
                  className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                    getProviderStatus('gmail').connected
                      ? 'bg-green-100 text-green-700 cursor-not-allowed'
                      : loading === 'gmail'
                      ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                      : 'bg-red-600 text-white hover:bg-red-700'
                  }`}
                >
                  {loading === 'gmail' ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Connecting...</span>
                    </>
                  ) : getProviderStatus('gmail').connected ? (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      <span>Connected</span>
                    </>
                  ) : (
                    <>
                      <ExternalLink className="w-4 h-4" />
                      <span>Connect Gmail</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* LinkedIn Connection */}
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Linkedin className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">LinkedIn</h3>
                      <p className="text-sm text-gray-600">Connect your network</p>
                    </div>
                  </div>

                  {getProviderStatus('linkedin').connected ? (
                    <CheckCircle className="w-6 h-6 text-green-500" />
                  ) : (
                    <div className="w-6 h-6" />
                  )}
                </div>

                <div className="mb-4">
                  {getProviderStatus('linkedin').connected ? (
                    <div className="text-sm text-green-700 bg-green-50 p-3 rounded-lg">
                      ✅ Connected ({getProviderStatus('linkedin').accounts.length} account{getProviderStatus('linkedin').accounts.length !== 1 ? 's' : ''})
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600">
                      Import all your LinkedIn messages and professional conversations
                    </div>
                  )}
                </div>

                <button
                  onClick={() => handleConnect('linkedin')}
                  disabled={loading === 'linkedin' || getProviderStatus('linkedin').connected}
                  className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                    getProviderStatus('linkedin').connected
                      ? 'bg-green-100 text-green-700 cursor-not-allowed'
                      : loading === 'linkedin'
                      ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {loading === 'linkedin' ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Connecting...</span>
                    </>
                  ) : getProviderStatus('linkedin').connected ? (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      <span>Connected</span>
                    </>
                  ) : (
                    <>
                      <ExternalLink className="w-4 h-4" />
                      <span>Connect LinkedIn</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Status Summary */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Connection Status</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {connectionStatus?.total_accounts || 0}
                </div>
                <div className="text-sm text-gray-600">Total Accounts</div>
              </div>

              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {getProviderStatus('gmail').accounts.length}
                </div>
                <div className="text-sm text-gray-600">Gmail Accounts</div>
              </div>

              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {getProviderStatus('linkedin').accounts.length}
                </div>
                <div className="text-sm text-gray-600">LinkedIn Accounts</div>
              </div>
            </div>

            {connectionStatus?.both_connected && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span className="text-green-700 font-medium">
                    🎉 Both accounts connected! Ready for message import and person matching.
                  </span>
                </div>
              </div>
            )}

            {/* Connected Accounts List */}
            {accounts.length > 0 && (
              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-900 mb-3">Connected Accounts</h4>
                <div className="space-y-2">
                  {accounts.map((account) => (
                    <div key={account.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        {account.provider === 'GOOGLE' ? (
                          <Mail className="w-4 h-4 text-red-500" />
                        ) : (
                          <Linkedin className="w-4 h-4 text-blue-500" />
                        )}
                        <div>
                          <div className="font-medium text-gray-900">
                            {account.name || account.email || account.provider}
                          </div>
                          <div className="text-xs text-gray-500">
                            Connected {new Date(account.connected_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <div className="text-xs text-green-600 font-medium">
                        {account.status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Next Steps */}
          <div className="mt-8 text-center">
            {connectionStatus?.both_connected ? (
              <div className="text-green-700">
                <p className="text-lg font-medium mb-2">🚀 Ready for Step 3!</p>
                <p className="text-sm">Both accounts are connected. Next we'll implement message import and person matching.</p>
              </div>
            ) : (
              <div className="text-gray-600">
                <p className="text-sm">Connect both Gmail and LinkedIn to enable unified conversation timelines</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}