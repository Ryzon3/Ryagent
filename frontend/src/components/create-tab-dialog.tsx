'use client'

import { useState } from 'react'
import { Bot, Sparkles, Zap, Brain } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'

interface CreateTabDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreateTab: (data: {
    name: string
    model: string
    system_prompt: string
  }) => void
  loading?: boolean
}

const models = [
  {
    id: 'gpt-4o-mini',
    name: 'GPT-4o Mini',
    description: 'Fast and efficient for most tasks',
    icon: Zap,
    badge: 'Recommended'
  },
  {
    id: 'gpt-4o',
    name: 'GPT-4o',
    description: 'Most capable model for complex tasks',
    icon: Brain,
    badge: 'Premium'
  },
  {
    id: 'claude-3-haiku',
    name: 'Claude 3 Haiku',
    description: 'Quick and creative responses',
    icon: Sparkles,
    badge: 'Fast'
  },
]

const systemPrompts = [
  {
    name: 'General Assistant',
    prompt: 'You are a helpful, harmless, and honest AI assistant. Provide accurate information and be concise in your responses.'
  },
  {
    name: 'Code Helper',
    prompt: 'You are an expert software developer. Help with coding questions, debugging, code reviews, and best practices. Always provide clean, well-commented code examples.'
  },
  {
    name: 'Creative Writer',
    prompt: 'You are a creative writing assistant. Help with storytelling, content creation, brainstorming ideas, and improving writing quality. Be imaginative and engaging.'
  },
  {
    name: 'Research Assistant',
    prompt: 'You are a research assistant specializing in gathering, analyzing, and presenting information. Provide well-sourced, accurate, and comprehensive responses.'
  },
]

export function CreateTabDialog({ open, onOpenChange, onCreateTab, loading }: CreateTabDialogProps) {
  const [name, setName] = useState('')
  const [selectedModel, setSelectedModel] = useState('gpt-4o-mini')
  const [systemPrompt, setSystemPrompt] = useState(systemPrompts[0].prompt)
  const [selectedTemplate, setSelectedTemplate] = useState(systemPrompts[0].name)
  const [errors, setErrors] = useState<{ name?: string; systemPrompt?: string }>({})
  
  const validateForm = () => {
    const newErrors: { name?: string; systemPrompt?: string } = {}
    
    if (!name.trim()) {
      newErrors.name = 'Tab name is required'
    } else if (name.trim().length < 2) {
      newErrors.name = 'Tab name must be at least 2 characters'
    } else if (name.trim().length > 50) {
      newErrors.name = 'Tab name must be less than 50 characters'
    }
    
    if (!systemPrompt.trim()) {
      newErrors.systemPrompt = 'System prompt is required'
    } else if (systemPrompt.trim().length > 2000) {
      newErrors.systemPrompt = 'System prompt must be less than 2000 characters'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = () => {
    if (!validateForm()) return

    onCreateTab({
      name: name.trim(),
      model: selectedModel,
      system_prompt: systemPrompt
    })

    // Reset form
    setName('')
    setSelectedModel('gpt-4o-mini')
    setSystemPrompt(systemPrompts[0].prompt)
    setSelectedTemplate(systemPrompts[0].name)
    setErrors({})
  }

  const handleTemplateSelect = (templateName: string) => {
    const template = systemPrompts.find(t => t.name === templateName)
    if (template) {
      setSystemPrompt(template.prompt)
      setSelectedTemplate(templateName)
      if (errors.systemPrompt) {
        setErrors(prev => ({ ...prev, systemPrompt: undefined }))
      }
    }
  }

  const selectedModelData = models.find(m => m.id === selectedModel)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Bot className="w-5 h-5 text-primary" />
            <span>Create New Agent Tab</span>
          </DialogTitle>
          <DialogDescription>
            Set up a new AI conversation with custom settings and personality
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          {/* Tab Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Tab Name</Label>
            <Input
              id="name"
              placeholder="My AI Assistant"
              value={name}
              onChange={(e) => {
                setName(e.target.value)
                if (errors.name) {
                  setErrors(prev => ({ ...prev, name: undefined }))
                }
              }}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
              className={errors.name ? 'border-destructive' : ''}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name}</p>
            )}
          </div>

          {/* Model Selection */}
          <div className="space-y-3">
            <Label>AI Model</Label>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {models.map((model) => {
                  const Icon = model.icon
                  return (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center space-x-3">
                        <Icon className="w-4 h-4" />
                        <div className="flex flex-col">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">{model.name}</span>
                            <Badge variant="secondary" className="text-xs">
                              {model.badge}
                            </Badge>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {model.description}
                          </span>
                        </div>
                      </div>
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
            
            {selectedModelData && (
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <selectedModelData.icon className="w-4 h-4" />
                <span>{selectedModelData.description}</span>
              </div>
            )}
          </div>

          {/* System Prompt Templates */}
          <div className="space-y-3">
            <Label>Personality Template</Label>
            <div className="grid grid-cols-2 gap-2">
              {systemPrompts.map((template) => (
                <Button
                  key={template.name}
                  variant={selectedTemplate === template.name ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleTemplateSelect(template.name)}
                  className="justify-start h-auto p-3"
                >
                  <div className="text-left">
                    <div className="font-medium text-xs">{template.name}</div>
                  </div>
                </Button>
              ))}
            </div>
          </div>

          {/* Custom System Prompt */}
          <div className="space-y-2">
            <Label htmlFor="prompt">System Prompt</Label>
            <Textarea
              id="prompt"
              placeholder="Describe how the AI should behave..."
              value={systemPrompt}
              onChange={(e) => {
                setSystemPrompt(e.target.value)
                if (errors.systemPrompt) {
                  setErrors(prev => ({ ...prev, systemPrompt: undefined }))
                }
              }}
              rows={4}
              className={`resize-none ${errors.systemPrompt ? 'border-destructive' : ''}`}
            />
            <div className="flex justify-between items-center">
              {errors.systemPrompt ? (
                <p className="text-sm text-destructive">{errors.systemPrompt}</p>
              ) : (
                <div />
              )}
              <p className="text-xs text-muted-foreground">
                {systemPrompt.length}/2000
              </p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={!name.trim() || loading}
          >
            {loading ? 'Creating...' : 'Create Agent'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}