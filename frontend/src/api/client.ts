// ── Types ──────────────────────────────────────────────────────

export type Conversation = {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count?: number
}

export type Message = {
  id: number
  conversation: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

export type KnowledgeDocument = {
  id: number
  title: string
  filename: string
  file_type: string
  file_size: number
  status: 'pending' | 'processing' | 'ready' | 'error'
  chunk_count: number
  error_message: string
  created_at: string
  updated_at: string
}

export type RAGSource = { name: string; score: number }

export type CommandResponse = {
  mode: 'command'; command: string; conversation_id: number; error?: string
}

export type KnowledgeResponse = {
  mode: 'knowledge'; answer: string; sources: RAGSource[]
  chunks_retrieved: number; conversation_id: number; error?: string
}

export type AssistantResponse = CommandResponse | KnowledgeResponse | { error: string }
export type KnowledgeStats = { total_chunks: number; document_count: number }

export type LLMProvider = {
  id: number
  provider: string
  provider_display: string
  base_url: string
  model_name: string
  is_active: boolean
  is_configured: boolean
  masked_key: string
  created_at: string
  updated_at: string
}

export type ProviderChoice = { value: string; label: string }


// ── Conversations ──────────────────────────────────────────────

export async function listConversations(): Promise<Conversation[]> {
  const res = await fetch('/api/conversations/')
  if (!res.ok) throw new Error('Failed to load conversations')
  return res.json()
}

export async function getConversation(id: number): Promise<Conversation & { messages: Message[] }> {
  const res = await fetch(`/api/conversations/${id}/`)
  if (!res.ok) throw new Error('Failed to load conversation')
  return res.json()
}

export async function createConversation(title: string): Promise<Conversation> {
  const res = await fetch('/api/conversations/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  })
  if (!res.ok) throw new Error('Failed to create conversation')
  return res.json()
}

export async function deleteConversation(id: number): Promise<void> {
  const res = await fetch(`/api/conversations/${id}/`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete conversation')
}


// ── Assistant ──────────────────────────────────────────────────

export async function postCommand(text: string, conversation_id?: number): Promise<AssistantResponse> {
  const res = await fetch('/api/command/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, conversation_id })
  })
  return res.json()
}


// ── Knowledge Base ─────────────────────────────────────────────

export async function listDocuments(): Promise<KnowledgeDocument[]> {
  const res = await fetch('/api/knowledge/documents/')
  if (!res.ok) throw new Error('Failed to load documents')
  return res.json()
}

export async function uploadDocument(file: File, title?: string): Promise<KnowledgeDocument> {
  const formData = new FormData()
  formData.append('file', file)
  if (title) formData.append('title', title)
  const res = await fetch('/api/knowledge/upload/', { method: 'POST', body: formData })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || 'Upload failed')
  }
  return res.json()
}

export async function deleteDocument(id: number): Promise<void> {
  const res = await fetch(`/api/knowledge/documents/${id}/`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete document')
}

export async function getKnowledgeStats(): Promise<KnowledgeStats> {
  const res = await fetch('/api/knowledge/stats/')
  if (!res.ok) throw new Error('Failed to load stats')
  return res.json()
}


// ── LLM Providers ──────────────────────────────────────────────

export async function listProviders(): Promise<LLMProvider[]> {
  const res = await fetch('/api/providers/')
  if (!res.ok) throw new Error('Failed to load providers')
  return res.json()
}

export async function getProviderChoices(): Promise<ProviderChoice[]> {
  const res = await fetch('/api/providers/available/')
  if (!res.ok) throw new Error('Failed to load provider choices')
  return res.json()
}

export async function saveProvider(data: {
  provider: string; api_key?: string; base_url?: string; model_name?: string
}): Promise<LLMProvider> {
  // Check if this provider already exists
  const existing = await listProviders()
  const found = existing.find(p => p.provider === data.provider)

  if (found) {
    const res = await fetch(`/api/providers/${found.id}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to update provider')
    return res.json()
  } else {
    const res = await fetch('/api/providers/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to save provider')
    return res.json()
  }
}

export async function activateProvider(id: number): Promise<LLMProvider> {
  const res = await fetch(`/api/providers/${id}/activate/`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to activate provider')
  return res.json()
}

export async function deleteProvider(id: number): Promise<void> {
  const res = await fetch(`/api/providers/${id}/`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete provider')
}
