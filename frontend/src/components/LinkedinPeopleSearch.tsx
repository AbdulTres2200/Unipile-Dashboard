'use client'

import React, { useState } from 'react'
import { Search, MapPin, Building, Users, GraduationCap, Globe, Target, Briefcase, UserPlus, RefreshCw, Filter, X, ExternalLink, Linkedin, ChevronDown, ChevronUp } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

interface SearchResult {
  type: string; industry: string | null; id: string; name: string; member_urn: string; public_identifier: string
  profile_url: string; public_profile_url: string; profile_picture_url: string | null; profile_picture_url_large: string | null
  network_distance: string; location: string; headline: string; keywords_match?: string; verified?: boolean
  shared_connections_count?: number; followers_count?: number; first_name?: string; last_name?: string
  primary_locale?: { country: string; language: string }; is_open_profile?: boolean; is_premium?: boolean
  is_influencer?: boolean; is_creator?: boolean; connections_count?: number; follower_count?: number
  current_positions?: { company: string; role: string; location?: string; industry?: string[] }[]
  education?: { school: string; degree?: string; field_of_study?: string }[]
}

export default function LinkedInPeopleSearch() {
  const [searchForm, setSearchForm] = useState({ keywords: '', industry: [], location: [], profile_language: [], network_distance: [], company: [], past_company: [], school: [], service: [], connections_of: [], followers_of: [], open_to: [] })
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [maxResults, setMaxResults] = useState(40)
  const [count, setCount] = useState(50)
  const [includeDetails, setIncludeDetails] = useState(false)
  const [searchPerformed, setSearchPerformed] = useState(false)

  const languageOptions = [{ code: 'en', name: 'English' }, { code: 'es', name: 'Spanish' }, { code: 'fr', name: 'French' }, { code: 'de', name: 'German' }, { code: 'it', name: 'Italian' }, { code: 'pt', name: 'Portuguese' }, { code: 'ru', name: 'Russian' }, { code: 'zh', name: 'Chinese' }, { code: 'ja', name: 'Japanese' }, { code: 'ko', name: 'Korean' }, { code: 'ar', name: 'Arabic' }, { code: 'hi', name: 'Hindi' }]
  const networkDistanceOptions = [{ value: 1, label: '1st connections' }, { value: 2, label: '2nd connections' }, { value: 3, label: '3rd+ connections' }]
  const openToOptions = [
    'proBono',
    'boardMember'
  ]

  const handleInputChange = (field: string, value: any) => setSearchForm(prev => ({ ...prev, [field]: value }))
  
  const handleArrayInputChange = (field: string, value: string) => {
    const items = value.trim() ? value.split(',').map(item => item.trim()).filter(item => item) : []
    setSearchForm(prev => ({ ...prev, [field]: items }))
  }

  const handleSearch = async () => {
    setLoading(true); setError(null); setSearchPerformed(true)
    try {
      const searchFilters = {}
      if (searchForm.keywords?.trim()) searchFilters.keywords = searchForm.keywords.trim()
      
      const arrayFields = ['industry', 'location', 'company', 'past_company', 'school', 'service', 'connections_of', 'followers_of', 'open_to']
      arrayFields.forEach(field => {
        if (searchForm[field]?.length > 0) searchFilters[field] = searchForm[field].join(',')
      })
      
      if (searchForm.profile_language?.length > 0) searchFilters.profile_language = searchForm.profile_language.join(',')
      if (searchForm.network_distance?.length > 0) searchFilters.network_distance = searchForm.network_distance.map(String).join(',')

      const response = await fetch(`${API_BASE}/api/linkedin/people-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filters: searchFilters, max_results: maxResults, count, include_details: includeDetails })
      })

      if (!response.ok) throw new Error((await response.json()).detail || 'Search failed')
      const data = await response.json()
      setResults(data.results || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during search')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const clearForm = () => {
    setSearchForm({ keywords: '', industry: [], location: [], profile_language: [], network_distance: [], company: [], past_company: [], school: [], service: [], connections_of: [], followers_of: [], open_to: [] })
    setResults([]); setError(null); setSearchPerformed(false)
  }

  const getNetworkDistanceLabel = (distance: string) => ({ 'DISTANCE_1': '1st', 'DISTANCE_2': '2nd', 'DISTANCE_3': '3rd+' }[distance] || distance)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
              <Linkedin className="w-8 h-8 text-blue-600" />
              <span>LinkedIn People Search</span>
            </h1>
            <p className="text-gray-600 mt-2">Search for professionals on LinkedIn using advanced filters</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-lg p-6 sticky top-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                    <Filter className="w-5 h-5" />
                    <span>Search Filters</span>
                  </h2>
                  <button onClick={clearForm} className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1">
                    <X className="w-4 h-4" />
                    <span>Clear</span>
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                      <Search className="w-4 h-4" />
                      <span>Keywords</span>
                    </label>
                    <input type="text" placeholder="e.g., Python Developer, Machine Learning" value={searchForm.keywords || ''} onChange={(e) => handleInputChange('keywords', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                  </div>

                  <div>
                    <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                      <MapPin className="w-4 h-4" />
                      <span>Location</span>
                    </label>
                    <input type="text" placeholder="e.g., Karachi, Pakistan" value={searchForm.location?.join(', ') || ''} onChange={(e) => handleArrayInputChange('location', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                    <p className="text-xs text-gray-500 mt-1">Separate multiple locations with commas</p>
                  </div>

                  <div>
                    <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                      <Building className="w-4 h-4" />
                      <span>Industry</span>
                    </label>
                    <input type="text" placeholder="e.g., Information Technology, Healthcare" value={searchForm.industry?.join(', ') || ''} onChange={(e) => handleArrayInputChange('industry', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                    <p className="text-xs text-gray-500 mt-1">Separate multiple industries with commas</p>
                  </div>

                  <div>
                    <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                      <Briefcase className="w-4 h-4" />
                      <span>Current Company</span>
                    </label>
                    <input type="text" placeholder="e.g., Google, Microsoft" value={searchForm.company?.join(', ') || ''} onChange={(e) => handleArrayInputChange('company', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                    <p className="text-xs text-gray-500 mt-1">Separate multiple companies with commas</p>
                  </div>

                  <div>
                    <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                      <Users className="w-4 h-4" />
                      <span>Network Distance</span>
                    </label>
                    <div className="space-y-2">
                      {networkDistanceOptions.map((option) => (
                        <label key={option.value} className="flex items-center space-x-2">
                          <input type="checkbox" checked={searchForm.network_distance?.includes(option.value) || false} onChange={(e) => {
                            const current = searchForm.network_distance || []
                            handleInputChange('network_distance', e.target.checked ? [...current, option.value] : current.filter(d => d !== option.value))
                          }} className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                          <span className="text-sm text-gray-700">{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* <div>
                    <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                      <input type="checkbox" checked={includeDetails} onChange={(e) => setIncludeDetails(e.target.checked)} className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                      <span>Include detailed profiles (slower)</span>
                    </label>
                    <p className="text-xs text-gray-500">Fetches additional profile information like follower count, premium status, etc.</p>
                  </div> */}

                  <button onClick={() => setShowAdvanced(!showAdvanced)} className="w-full flex items-center justify-between px-3 py-2 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
                    <span>Advanced Filters</span>
                    {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  {showAdvanced && (
                    <div className="space-y-4 pt-4 border-t border-gray-200">
                      <div>
                        <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                          <Globe className="w-4 h-4" />
                          <span>Profile Language</span>
                        </label>
                        <div className="max-h-32 overflow-y-auto space-y-1 border border-gray-300 rounded-lg p-2">
                          {languageOptions.map((lang) => (
                            <label key={lang.code} className="flex items-center space-x-2">
                              <input type="checkbox" checked={searchForm.profile_language?.includes(lang.code) || false} onChange={(e) => {
                                const current = searchForm.profile_language || []
                                handleInputChange('profile_language', e.target.checked ? [...current, lang.code] : current.filter(l => l !== lang.code))
                              }} className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                              <span className="text-sm text-gray-700">{lang.name}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                          <Building className="w-4 h-4" />
                          <span>Past Company</span>
                        </label>
                        <input type="text" placeholder="e.g., Apple, Tesla" value={searchForm.past_company?.join(', ') || ''} onChange={(e) => handleArrayInputChange('past_company', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                      </div>

                      <div>
                        <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                          <GraduationCap className="w-4 h-4" />
                          <span>School</span>
                        </label>
                        <input type="text" placeholder="e.g., Stanford University, MIT" value={searchForm.school?.join(', ') || ''} onChange={(e) => handleArrayInputChange('school', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                      </div>

                      <div>
                        <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 mb-2">
                          <Target className="w-4 h-4" />
                          <span>Open To</span>
                        </label>
                        <div className="space-y-2">
                          {openToOptions.map((option) => (
                            <label key={option} className="flex items-center space-x-2">
                              <input type="checkbox" checked={searchForm.open_to?.includes(option) || false} onChange={(e) => {
                                const current = searchForm.open_to || []
                                handleInputChange('open_to', e.target.checked ? [...current, option] : current.filter(o => o !== option))
                              }} className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                              <span className="text-sm text-gray-700">{option}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-gray-700 mb-2 block">Max Results</label>
                          <input type="number" min="1" max="1000" value={maxResults} onChange={(e) => setMaxResults(parseInt(e.target.value) || 40)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-700 mb-2 block">Batch Count</label>
                          <input type="number" min="1" max="100" value={count} onChange={(e) => setCount(parseInt(e.target.value) || 50)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                        </div>
                      </div>
                    </div>
                  )}

                  <button onClick={handleSearch} disabled={loading} className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors">
                    {loading ? <><RefreshCw className="w-4 h-4 animate-spin" /><span>Searching...</span></> : <><Search className="w-4 h-4" /><span>Search LinkedIn</span></>}
                  </button>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="p-6 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Search Results</h2>
                    {searchPerformed && <span className="text-sm text-gray-600">{results.length} profiles found</span>}
                  </div>
                </div>

                {error && <div className="p-6 bg-red-50 border-b border-red-200"><p className="text-red-700">{error}</p></div>}

                <div className="max-h-[800px] overflow-y-auto">
                  {!searchPerformed ? (
                    <div className="p-12 text-center text-gray-500">
                      <Search className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Search</h3>
                      <p>Fill in the search filters and click "Search LinkedIn" to find professionals</p>
                    </div>
                  ) : loading ? (
                    <div className="p-12 text-center">
                      <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
                      <p className="text-gray-600">Searching LinkedIn profiles...</p>
                    </div>
                  ) : results.length === 0 ? (
                    <div className="p-12 text-center text-gray-500">
                      <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h3>
                      <p>Try adjusting your search filters or keywords</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-200">
                      {results.map((person) => (
                        <div key={person.id} className="p-6 hover:bg-gray-50 transition-colors">
                          <div className="flex items-start space-x-4">
                            <div className="flex-shrink-0">
                              {person.profile_picture_url ? (
                                <img src={person.profile_picture_url_large || person.profile_picture_url} alt={person.name} className="w-16 h-16 rounded-full object-cover" onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextElementSibling.style.display = 'flex' }} />
                              ) : null}
                              <div className={`w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center ${person.profile_picture_url ? 'hidden' : 'flex'}`}>
                                <span className="text-white font-bold text-lg">{person.name.charAt(0).toUpperCase()}</span>
                              </div>
                            </div>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center space-x-2">
                                  <h3 className="text-lg font-semibold text-gray-900">{person.name}</h3>
                                  {person.verified && <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center"><div className="w-3 h-3 bg-blue-600 rounded-full"></div></div>}
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{getNetworkDistanceLabel(person.network_distance)}</span>
                                  <a href={person.public_profile_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 transition-colors"><ExternalLink className="w-4 h-4" /></a>
                                </div>
                              </div>

                              <p className="text-gray-700 mb-2 leading-relaxed">{person.headline}</p>

                              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-2">
                                {person.location && <div className="flex items-center space-x-1"><MapPin className="w-4 h-4" /><span>{person.location}</span></div>}
                                {person.connections_count !== undefined && <div className="flex items-center space-x-1"><Users className="w-4 h-4" /><span>{person.connections_count} connections</span></div>}
                                {person.follower_count !== undefined && <div className="flex items-center space-x-1"><UserPlus className="w-4 h-4" /><span>{person.follower_count} followers</span></div>}
                              </div>

                              {person.shared_connections_count !== undefined && <div className="flex items-center space-x-1 text-sm text-gray-600 mb-2"><Users className="w-4 h-4" /><span>{person.shared_connections_count} shared connections</span></div>}

                              <div className="flex flex-wrap gap-2 mb-2">
                                {person.is_premium && <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Premium</span>}
                                {person.is_influencer && <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">Influencer</span>}
                                {person.is_creator && <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Creator</span>}
                                {person.is_open_profile && <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Open Profile</span>}
                              </div>

                              {person.current_positions && person.current_positions.length > 0 && (
                                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                  <div className="flex items-center space-x-2 mb-2">
                                    <Briefcase className="w-4 h-4 text-blue-600" />
                                    <span className="text-sm font-medium text-blue-800">Current Position</span>
                                  </div>
                                  <div className="text-sm text-blue-700">
                                    <p className="font-medium">{person.current_positions[0].role}</p>
                                    <p>{person.current_positions[0].company}</p>
                                    {person.current_positions[0].location && <p className="text-blue-600">{person.current_positions[0].location}</p>}
                                  </div>
                                </div>
                              )}

                              {person.education && person.education.length > 0 && (
                                <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                                  <div className="flex items-center space-x-2 mb-2">
                                    <GraduationCap className="w-4 h-4 text-green-600" />
                                    <span className="text-sm font-medium text-green-800">Education</span>
                                  </div>
                                  <div className="text-sm text-green-700">
                                    <p className="font-medium">{person.education[0].school}</p>
                                    {person.education[0].degree && <p>{person.education[0].degree}</p>}
                                    {person.education[0].field_of_study && <p className="text-green-600">{person.education[0].field_of_study}</p>}
                                  </div>
                                </div>
                              )}

                              {person.keywords_match && (
                                <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <Target className="w-4 h-4 text-yellow-600" />
                                    <span className="text-sm font-medium text-yellow-800">Keywords Match</span>
                                  </div>
                                  <p className="text-sm text-yellow-700">{person.keywords_match}</p>
                                </div>
                              )}

                              <div className="mt-4 flex items-center space-x-4 text-sm">
                                <span className="text-gray-500">Profile ID: {person.public_identifier}</span>
                                {person.industry && <span className="text-gray-500">Industry: {person.industry}</span>}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {searchPerformed && results.length > 0 && (
                <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center"><Users className="w-4 h-4 text-blue-600" /></div>
                      <div><p className="text-sm text-gray-600">Total Results</p><p className="text-xl font-semibold text-gray-900">{results.length}</p></div>
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center"><UserPlus className="w-4 h-4 text-green-600" /></div>
                      <div><p className="text-sm text-gray-600">Verified Profiles</p><p className="text-xl font-semibold text-gray-900">{results.filter(p => p.verified).length}</p></div>
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center"><Users className="w-4 h-4 text-purple-600" /></div>
                      <div><p className="text-sm text-gray-600">Shared Connections</p><p className="text-xl font-semibold text-gray-900">{results.reduce((sum, p) => sum + (p.shared_connections_count || 0), 0)}</p></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}