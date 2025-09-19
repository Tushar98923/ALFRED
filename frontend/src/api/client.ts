export type Conversation = {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export type Message = {
  id: number
  conversation: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

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


