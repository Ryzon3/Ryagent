class RyAgentAPI {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Auth methods
  async validateToken(token: string): Promise<{ valid: boolean }> {
    return this.request('/api/auth/validate', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
  }

  async getAuthToken(): Promise<{ token: string }> {
    return this.request('/api/auth/token')
  }

  setAuthToken(token: string) {
    this.token = token
  }

  // Tab methods
  async getTabs(): Promise<{ tabs: Tab[] }> {
    return this.request('/api/tabs')
  }

  async getTab(tabId: string): Promise<Tab> {
    return this.request(`/api/tabs/${tabId}`)
  }

  async createTab(tabData: {
    name: string
    model: string
    system_prompt: string
  }): Promise<Tab> {
    return this.request('/api/tabs', {
      method: 'POST',
      body: JSON.stringify(tabData),
    })
  }

  async deleteTab(tabId: string): Promise<{ status: string }> {
    return this.request(`/api/tabs/${tabId}`, {
      method: 'DELETE',
    })
  }

  async sendMessage(
    tabId: string,
    message: { prompt: string }
  ): Promise<{ status: string; messages: Message[] }> {
    return this.request(`/api/tabs/${tabId}/messages`, {
      method: 'POST',
      body: JSON.stringify(message),
    })
  }

  // Health check
  async healthCheck(): Promise<{
    status: string
    version: string
    tabs_count: number
  }> {
    return this.request('/health')
  }
}

// Types
export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface Tab {
  id: string
  name: string
  model: string
  system_prompt: string
  messages: Message[]
  created_at: string
  last_accessed: string
}

// Export singleton instance
export const api = new RyAgentAPI()