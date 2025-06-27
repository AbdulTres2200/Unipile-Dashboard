const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface HostedAuthResponse {
  success: boolean
  auth_url: string
  provider: string
  is_real: boolean
  message: string
}

export interface ConnectionStatus {
  gmail: {
    connected: boolean
    accounts: any[]
  }
  linkedin: {
    connected: boolean
    accounts: any[]
  }
  both_connected: boolean
  total_accounts: number
}

export interface Account {
  id: string
  provider: string
  email?: string
  name?: string
  status: string
  connected_at: string
}

export interface Person {
  id: string
  name: string
  email?: string
  message_count: number
  last_message_date: string
  channels: string[]
}

export interface Message {
  id: string
  channel: 'email' | 'linkedin'
  sender: string
  recipient: string
  subject?: string
  content: string
  timestamp: string
  thread_id?: string
}

export const api = {
  // Create hosted auth link
  async createHostedAuth(provider: string, userId: string = 'default_user'): Promise<HostedAuthResponse> {
    const response = await fetch(`${API_BASE}/api/auth/hosted-auth/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider,
        user_id: userId
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create auth link')
    }

    return response.json()
  },

  // Manual OAuth success
  async completeOAuthManually(provider: string, userId: string = 'default_user'): Promise<any> {
    const response = await fetch(`${API_BASE}/api/auth/manual/oauth-success`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider,
        user_id: userId
      })
    })

    if (!response.ok) {
      throw new Error('Failed to complete OAuth manually')
    }

    return response.json()
  },

  // Get connection status
  async getConnectionStatus(): Promise<ConnectionStatus> {
    const response = await fetch(`${API_BASE}/api/auth/accounts/status`)

    if (!response.ok) {
      throw new Error('Failed to get connection status')
    }

    return response.json()
  },

  // Get all connected accounts
  async getAccounts(): Promise<{ accounts: Account[], total: number }> {
    const response = await fetch(`${API_BASE}/api/auth/accounts`)

    if (!response.ok) {
      throw new Error('Failed to get accounts')
    }

    return response.json()
  },

  // Connect latest account for provider
  async connectLatestAccount(provider: string): Promise<any> {
    const response = await fetch(`${API_BASE}/api/auth/connect/${provider}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Failed to connect ${provider}`)
    }
    return response.json()
  },

  // Sync accounts with Unipile
  async syncAccounts(): Promise<any> {
    const response = await fetch(`${API_BASE}/api/auth/sync-accounts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to sync accounts')
    }
    return response.json()
  },

  // Get all people with message counts
  async getPeople(): Promise<{ people: Person[], total: number }> {
    const response = await fetch(`${API_BASE}/api/people`)
    if (!response.ok) throw new Error('Failed to get people')
    return response.json()
  },

  // Get messages for a specific person
  async getPersonMessages(personId: string): Promise<{ messages: Message[], total: number }> {
    const response = await fetch(`${API_BASE}/api/people/${personId}/messages`)
    if (!response.ok) throw new Error('Failed to get person messages')
    return response.json()
  },

  // Get recent messages across all accounts
  async getRecentMessages(limit: number = 50): Promise<{ messages: Message[], total: number }> {
    const response = await fetch(`${API_BASE}/api/messages?limit=${limit}`)
    if (!response.ok) throw new Error('Failed to get recent messages')
    return response.json()
  }
}