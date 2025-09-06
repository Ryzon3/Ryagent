'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api } from '@/lib/api'

interface AuthContextType {
  isAuthenticated: boolean
  token: string | null
  login: (token: string) => Promise<boolean>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  token: null,
  login: async () => false,
  logout: () => {},
  loading: true,
})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    initializeAuth()
  }, [])

  const initializeAuth = async () => {
    try {
      // Try to get stored token
      const storedToken = localStorage.getItem('ryagent-token')
      
      if (storedToken) {
        // Validate stored token
        const validation = await api.validateToken(storedToken)
        if (validation.valid) {
          setToken(storedToken)
          api.setAuthToken(storedToken)
          setIsAuthenticated(true)
        } else {
          localStorage.removeItem('ryagent-token')
        }
      } else {
        // Get token from server (development mode)
        try {
          const tokenResponse = await api.getAuthToken()
          const newToken = tokenResponse.token
          
          localStorage.setItem('ryagent-token', newToken)
          setToken(newToken)
          api.setAuthToken(newToken)
          setIsAuthenticated(true)
        } catch (error) {
          console.error('Failed to get auth token:', error)
        }
      }
    } catch (error) {
      console.error('Auth initialization failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const login = async (newToken: string): Promise<boolean> => {
    try {
      const validation = await api.validateToken(newToken)
      
      if (validation.valid) {
        setToken(newToken)
        api.setAuthToken(newToken)
        localStorage.setItem('ryagent-token', newToken)
        setIsAuthenticated(true)
        return true
      }
      
      return false
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  const logout = () => {
    setToken(null)
    api.setAuthToken('')
    localStorage.removeItem('ryagent-token')
    setIsAuthenticated(false)
  }

  const value: AuthContextType = {
    isAuthenticated,
    token,
    login,
    logout,
    loading,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}