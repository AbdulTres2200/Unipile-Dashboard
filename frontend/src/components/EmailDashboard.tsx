'use client'

import { useState, useEffect } from 'react'
import {
  Mail,
  Linkedin,
  User,
  Clock,
  MessageSquare,
  Search,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Eye,
  EyeOff
} from 'lucide-react'
import { api, Person, Message, Account } from '@/lib/api'

export default function EmailDashboard() {
  const [people, setPeople] = useState<Person[]>([])
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [personMessages, setPersonMessages] = useState<Message[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedChannel, setSelectedChannel] = useState<'all' | 'email' | 'linkedin'>('all')
  const [error, setError] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(true)

  useEffect(() => {
    loadDashboardData(true) // Pass true for initial load
  }, [])

  // Removed auto-refresh - only manual refresh button works now

  const loadDashboardData = async (isInitialLoad = false) => {
    try {
      // Only show loading screen on initial load
      if (isInitialLoad) {
        setLoading(true)
      }

      const [peopleData, accountsData] = await Promise.all([
        api.getPeople(),
        api.getAccounts()
      ])

      setPeople(peopleData.people)
      setAccounts(accountsData.accounts)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      if (isInitialLoad) {
        setLoading(false)
      }
    }
  }

  const loadPersonMessages = async (person: Person) => {
    try {
      setMessagesLoading(true)
      setSelectedPerson(person)

      const data = await api.getPersonMessages(person.id)
      setPersonMessages(data.messages)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load messages')
    } finally {
      setMessagesLoading(false)
    }
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const truncateContent = (content: string, maxLength: number = 150) => {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength) + '...'
  }

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email':
        return <Mail className="w-4 h-4 text-red-500" />
      case 'linkedin':
        return <Linkedin className="w-4 h-4 text-blue-500" />
      default:
        return <MessageSquare className="w-4 h-4 text-gray-500" />
    }
  }

  const filteredPeople = people.filter(person => {
    const matchesSearch = person.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (person.email && person.email.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesChannel = selectedChannel === 'all' || person.channels.includes(selectedChannel)

    return matchesSearch && matchesChannel
  })

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading your conversations...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">

          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Message Dashboard</h1>
              <p className="text-gray-600 mt-1">
                {people.length} contacts • {accounts.length} connected accounts
              </p>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={loadDashboardData}
                className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* People List */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-lg overflow-hidden">

                {/* Search and Filters */}
                <div className="p-4 border-b border-gray-200">
                  <div className="space-y-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search contacts..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>

                    <div className="flex space-x-2">
                      {['all', 'email', 'linkedin'].map((channel) => (
                        <button
                          key={channel}
                          onClick={() => setSelectedChannel(channel as any)}
                          className={`px-3 py-1 text-sm rounded-full transition-colors ${
                            selectedChannel === channel
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {channel === 'all' ? 'All' : channel === 'email' ? 'Gmail' : 'LinkedIn'}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* People List */}
                <div className="max-h-96 overflow-y-auto">
                  {filteredPeople.length === 0 ? (
                    <div className="p-6 text-center text-gray-500">
                      <User className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>No contacts found</p>
                      <p className="text-sm mt-1">Try adjusting your search or filters</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-200">
                      {filteredPeople.map((person) => (
                        <div
                          key={person.id}
                          onClick={() => loadPersonMessages(person)}
                          className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                            selectedPerson?.id === person.id ? 'bg-blue-50 border-r-4 border-blue-500' : ''
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2 mb-1">
                                <h3 className="font-medium text-gray-900 truncate">
                                  {person.name}
                                </h3>
                                <div className="flex space-x-1">
                                  {person.channels.map((channel) => (
                                    <div key={channel} className="flex-shrink-0">
                                      {getChannelIcon(channel)}
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {person.email && (
                                <p className="text-sm text-gray-600 truncate mb-1">
                                  {person.email}
                                </p>
                              )}

                              <div className="flex items-center justify-between text-xs text-gray-500">
                                <span>{person.message_count} messages</span>
                                {person.last_message_date && (
                                  <span>{formatDate(person.last_message_date)}</span>
                                )}
                              </div>
                            </div>

                            <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0 ml-2" />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Messages Panel */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-lg overflow-hidden">

                {selectedPerson ? (
                  <>
                    {/* Messages Header */}
                    <div className="p-4 border-b border-gray-200 bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <button
                            onClick={() => setSelectedPerson(null)}
                            className="lg:hidden p-1 hover:bg-gray-200 rounded-lg transition-colors"
                          >
                            <ArrowLeft className="w-4 h-4" />
                          </button>

                          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                            <span className="text-white font-semibold">
                              {selectedPerson.name.charAt(0).toUpperCase()}
                            </span>
                          </div>

                          <div>
                            <h2 className="text-lg font-semibold text-gray-900">
                              {selectedPerson.name}
                            </h2>
                            {selectedPerson.email && (
                              <p className="text-sm text-gray-600">
                                {selectedPerson.email}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setShowPreview(!showPreview)}
                            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                            title={showPreview ? 'Hide preview' : 'Show preview'}
                          >
                            {showPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>

                          <span className="text-sm text-gray-500">
                            {personMessages.length} messages
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Messages List */}
                    <div className="max-h-96 overflow-y-auto">
                      {messagesLoading ? (
                        <div className="p-6 text-center">
                          <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-4" />
                          <p className="text-gray-600">Loading messages...</p>
                        </div>
                      ) : personMessages.length === 0 ? (
                        <div className="p-6 text-center text-gray-500">
                          <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                          <p>No messages found</p>
                        </div>
                      ) : (
                        <div className="divide-y divide-gray-200">
                          {personMessages
                            .filter(message => selectedChannel === 'all' || message.channel === selectedChannel)
                            .map((message) => (
                            <div key={message.id} className="p-4 hover:bg-gray-50 transition-colors">
                              <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0 mt-1">
                                  {getChannelIcon(message.channel)}
                                </div>

                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between mb-1">
                                    <div className="flex items-center space-x-2">
                                      <span className="text-sm font-medium text-gray-900">
                                        {message.sender}
                                      </span>
                                      <span className="text-xs text-gray-500">→</span>
                                      <span className="text-sm text-gray-600">
                                        {message.recipient}
                                      </span>
                                    </div>

                                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                                      <Clock className="w-3 h-3" />
                                      <span>{formatDate(message.timestamp)}</span>
                                    </div>
                                  </div>

                                  {message.subject && (
                                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                                      {message.subject}
                                    </h4>
                                  )}

                                  {showPreview && (
                                    <p className="text-sm text-gray-600 leading-relaxed">
                                      {truncateContent(message.content)}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  /* No Selection State */
                  <div className="p-12 text-center text-gray-500">
                    <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Select a Contact
                    </h3>
                    <p>Choose a contact from the list to view their messages</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Stats Overview */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <User className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Contacts</p>
                  <p className="text-xl font-semibold text-gray-900">{people.length}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                  <Mail className="w-4 h-4 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Email Contacts</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {people.filter(p => p.channels.includes('email')).length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Linkedin className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">LinkedIn Contacts</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {people.filter(p => p.channels.includes('linkedin')).length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <MessageSquare className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Messages</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {people.reduce((sum, person) => sum + person.message_count, 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}