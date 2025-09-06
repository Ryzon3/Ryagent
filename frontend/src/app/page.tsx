'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Plus, MessageSquare, Trash2, Settings, Loader2, Send, Bot, User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { api, type Tab, type Message } from '@/lib/api'
import { Sidebar } from '@/components/sidebar'
import { CreateTabDialog } from '@/components/create-tab-dialog'
import { DeleteConfirmationDialog } from '@/components/delete-confirmation-dialog'

export default function Dashboard() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [tabs, setTabs] = useState<Tab[]>([])
  const [activeTab, setActiveTab] = useState<string | null>(null)
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [createTabOpen, setCreateTabOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [tabToDelete, setTabToDelete] = useState<string | null>(null)
  const [createTabLoading, setCreateTabLoading] = useState(false)

  const loadTabs = useCallback(async () => {
    try {
      const data = await api.getTabs()
      setTabs(data.tabs)
      if (data.tabs.length > 0 && !activeTab) {
        setActiveTab(data.tabs[0].id)
      }
    } catch (error) {
      console.error('Failed to load tabs:', error)
    }
  }, [activeTab])

  // Load tabs when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadTabs()
    }
  }, [isAuthenticated, loadTabs])

  // Show loading spinner while auth is initializing
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>Loading RyAgent...</p>
        </div>
      </div>
    )
  }

  // Show auth error if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle>Authentication Required</CardTitle>
            <CardDescription>
              Unable to authenticate with RyAgent server
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Make sure the RyAgent server is running on localhost:8000
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const createTab = async (data: { name: string; model: string; system_prompt: string }) => {
    setCreateTabLoading(true)
    try {
      const newTab = await api.createTab(data)
      setTabs([...tabs, newTab])
      setActiveTab(newTab.id)
      setCreateTabOpen(false)
    } catch (error) {
      console.error('Failed to create tab:', error)
    } finally {
      setCreateTabLoading(false)
    }
  }

  const openCreateTab = () => {
    setCreateTabOpen(true)
  }

  const openDeleteDialog = (tabId: string) => {
    setTabToDelete(tabId)
    setDeleteDialogOpen(true)
  }

  const confirmDeleteTab = async () => {
    if (!tabToDelete) return

    try {
      await api.deleteTab(tabToDelete)
      setTabs(tabs.filter(tab => tab.id !== tabToDelete))
      if (activeTab === tabToDelete) {
        const remainingTabs = tabs.filter(tab => tab.id !== tabToDelete)
        setActiveTab(remainingTabs.length > 0 ? remainingTabs[0].id : null)
      }
    } catch (error) {
      console.error('Failed to delete tab:', error)
    } finally {
      setTabToDelete(null)
      setDeleteDialogOpen(false)
    }
  }

  const sendMessage = async () => {
    if (!newMessage.trim() || !activeTab) return

    setLoading(true)
    try {
      await api.sendMessage(activeTab, { prompt: newMessage })
      setNewMessage('')
      
      // Refresh the active tab to get updated messages
      const updatedTab = await api.getTab(activeTab)
      setTabs(tabs.map(tab => tab.id === activeTab ? updatedTab : tab))
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setLoading(false)
    }
  }

  const activeTabData = tabs.find(tab => tab.id === activeTab)

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <Sidebar
        tabs={tabs}
        activeTab={activeTab}
        onTabSelect={(tabId) => setActiveTab(tabId)}
        onNewTab={openCreateTab}
        onDeleteTab={openDeleteDialog}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {activeTabData ? (
          <>
            {/* Header */}
            <div className="border-b bg-card px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-semibold">{activeTabData.name}</h1>
                  <p className="text-sm text-muted-foreground">
                    Model: {activeTabData.model} • {activeTabData.messages.length} messages • Created {new Date(activeTabData.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </Button>
              </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {activeTabData.messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center max-w-md">
                      <Bot className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
                      <h3 className="text-xl font-semibold mb-2">Start Your Conversation</h3>
                      <p className="text-muted-foreground mb-6">
                        Begin chatting with your AI assistant. Ask questions, get help with tasks, or have a creative discussion.
                      </p>
                      <div className="grid grid-cols-1 gap-2 text-sm">
                        <div className="p-3 rounded-lg bg-muted text-left">
                          <strong>💡 Try asking:</strong> &quot;Help me write a Python function&quot;
                        </div>
                        <div className="p-3 rounded-lg bg-muted text-left">
                          <strong>🎨 Or:</strong> &quot;Generate ideas for a creative project&quot;
                        </div>
                        <div className="p-3 rounded-lg bg-muted text-left">
                          <strong>📚 Or:</strong> &quot;Explain a complex topic to me&quot;
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  activeTabData.messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex items-start space-x-4 animate-in slide-in-from-bottom-2 duration-300 ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      {message.role === 'assistant' && (
                        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 shadow-sm">
                          <Bot className="w-4 h-4 text-primary-foreground" />
                        </div>
                      )}
                      
                      <div
                        className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm transition-all duration-200 hover:shadow-md ${
                          message.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted hover:bg-muted/80'
                        }`}
                      >
                        <div className="text-sm font-medium mb-1 opacity-80">
                          {message.role === 'user' ? 'You' : 'Assistant'}
                        </div>
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      </div>
                      
                      {message.role === 'user' && (
                        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0 shadow-sm">
                          <User className="w-4 h-4 text-secondary-foreground" />
                        </div>
                      )}
                    </div>
                  ))
                )}
                
                {/* Loading indicator */}
                {loading && (
                  <div className="flex items-start space-x-4 justify-start">
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-primary-foreground" />
                    </div>
                    <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-muted">
                      <div className="flex items-center space-x-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Assistant is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="border-t bg-card p-6">
                <div className="flex items-end space-x-4">
                  <div className="flex-1">
                    <Textarea
                      placeholder="Type your message here..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          sendMessage()
                        }
                      }}
                      disabled={loading}
                      className="min-h-[60px] max-h-[200px] resize-none transition-all duration-200 focus:min-h-[80px]"
                      rows={2}
                    />
                    <div className="flex items-center justify-between mt-2">
                      <div className="text-xs text-muted-foreground">
                        Press Enter to send, Shift + Enter for new line
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {newMessage.length}/2000
                      </div>
                    </div>
                  </div>
                  <Button 
                    onClick={sendMessage} 
                    disabled={loading || !newMessage.trim()}
                    size="lg"
                    className="px-6 transition-all duration-200 hover:scale-105"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-md">
              <MessageSquare className="w-20 h-20 mx-auto text-muted-foreground mb-6" />
              <h2 className="text-2xl font-semibold mb-3">Welcome to RyAgent</h2>
              <p className="text-muted-foreground mb-6">
                Your personal AI assistant dashboard. Create your first conversation to get started.
              </p>
              <Button onClick={openCreateTab} size="lg" className="px-8">
                <Plus className="w-5 h-5 mr-2" />
                Create Your First Tab
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Dialogs */}
      <CreateTabDialog
        open={createTabOpen}
        onOpenChange={setCreateTabOpen}
        onCreateTab={createTab}
        loading={createTabLoading}
      />

      <DeleteConfirmationDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={confirmDeleteTab}
        title="Delete Agent Tab"
        description={`Are you sure you want to delete this tab? This action cannot be undone and will permanently remove all conversation history.`}
      />
    </div>
  )
}