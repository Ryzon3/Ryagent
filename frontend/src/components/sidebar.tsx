'use client'

import { useState } from 'react'
import { 
  Plus, 
  MessageSquare, 
  Trash2, 
  Settings, 
  Bot,
  MoreVertical,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { type Tab } from '@/lib/api'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './theme-toggle'

interface SidebarProps {
  tabs: Tab[]
  activeTab: string | null
  onTabSelect: (tabId: string) => void
  onNewTab: () => void
  onDeleteTab: (tabId: string) => void
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export function Sidebar({
  tabs,
  activeTab,
  onTabSelect,
  onNewTab,
  onDeleteTab,
  collapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  const [hoveredTab, setHoveredTab] = useState<string | null>(null)

  const getTabIcon = (tab: Tab) => {
    const messageCount = tab.messages.length
    if (messageCount === 0) return <Bot className="h-4 w-4" />
    return <MessageSquare className="h-4 w-4" />
  }

  const getTabBadge = (tab: Tab) => {
    const messageCount = tab.messages.length
    if (messageCount === 0) return null
    return (
      <Badge variant="secondary" className="ml-auto">
        {messageCount}
      </Badge>
    )
  }

  const formatTabName = (name: string, maxLength: number = 20) => {
    if (name.length <= maxLength) return name
    return name.slice(0, maxLength) + '...'
  }

  return (
    <div 
      className={cn(
        "flex flex-col bg-card border-r transition-all duration-300",
        collapsed ? "w-16" : "w-72"
      )}
    >
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  RA
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col">
                <span className="text-sm font-semibold">RyAgent</span>
                <span className="text-xs text-muted-foreground">
                  {tabs.length} agent{tabs.length !== 1 ? 's' : ''}
                </span>
              </div>
            </div>
          )}
          
          <div className="flex items-center space-x-1">
            {!collapsed && (
              <Button 
                onClick={onNewTab} 
                size="sm" 
                className="h-8 w-8 p-0"
              >
                <Plus className="h-4 w-4" />
              </Button>
            )}
            
            {onToggleCollapse && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleCollapse}
                className="h-8 w-8 p-0"
              >
                {collapsed ? (
                  <PanelLeftOpen className="h-4 w-4" />
                ) : (
                  <PanelLeftClose className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* New Tab Button (collapsed mode) */}
      {collapsed && (
        <div className="p-2">
          <Button 
            onClick={onNewTab} 
            variant="outline" 
            size="sm" 
            className="h-10 w-full"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Tabs List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {tabs.length === 0 ? (
            <div className={cn(
              "text-center py-8 text-muted-foreground",
              collapsed && "px-1"
            )}>
              {collapsed ? (
                <Bot className="h-6 w-6 mx-auto mb-2 opacity-50" />
              ) : (
                <>
                  <Bot className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No agents yet</p>
                  <p className="text-xs opacity-75">Create your first one!</p>
                </>
              )}
            </div>
          ) : (
            tabs.map((tab) => (
              <div
                key={tab.id}
                className={cn(
                  "relative group rounded-lg border-2 transition-all duration-200 hover:shadow-md",
                  activeTab === tab.id
                    ? "border-primary bg-primary/10 shadow-sm"
                    : "border-transparent hover:border-border hover:bg-accent/50",
                  collapsed ? "aspect-square" : ""
                )}
                onMouseEnter={() => setHoveredTab(tab.id)}
                onMouseLeave={() => setHoveredTab(null)}
              >
                <Button
                  variant="ghost"
                  onClick={() => onTabSelect(tab.id)}
                  className={cn(
                    "w-full h-auto p-3 justify-start font-normal text-left hover:bg-transparent",
                    collapsed && "p-2 justify-center"
                  )}
                >
                  <div className={cn(
                    "flex items-center w-full",
                    collapsed ? "flex-col space-y-1" : "space-x-3"
                  )}>
                    <div className={cn(
                      "flex-shrink-0",
                      activeTab === tab.id ? "text-primary" : "text-muted-foreground"
                    )}>
                      {getTabIcon(tab)}
                    </div>
                    
                    {!collapsed && (
                      <>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">
                            {formatTabName(tab.name)}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {tab.model} • {new Date(tab.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        
                        {getTabBadge(tab)}
                      </>
                    )}
                    
                    {collapsed && (
                      <div className="text-xs text-center">
                        <div className="font-medium truncate max-w-full">
                          {tab.name.slice(0, 2).toUpperCase()}
                        </div>
                      </div>
                    )}
                  </div>
                </Button>

                {/* Tab Actions */}
                {((hoveredTab === tab.id && !collapsed) || activeTab === tab.id) && (
                  <div className="absolute top-2 right-2">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 opacity-70 hover:opacity-100"
                        >
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Settings className="mr-2 h-4 w-4" />
                          Settings
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          className="text-destructive focus:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation()
                            onDeleteTab(tab.id)
                          }}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      {!collapsed && (
        <>
          <Separator />
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                <span className="text-xs text-muted-foreground">
                  Server Online
                </span>
              </div>
              <ThemeToggle />
            </div>
            <div className="flex items-center justify-center">
              <Badge variant="outline" className="text-xs">
                v0.1.0
              </Badge>
            </div>
          </div>
        </>
      )}
    </div>
  )
}