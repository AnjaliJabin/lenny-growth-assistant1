const BASE = ''

export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  sources: { episode: string; file: string; score: number }[]
  artifact: { type: 'markdown' | 'html'; content: string } | null
  created_at: string
}

export interface ChatResponse {
  session_id: string
  message: Message
  provider: string
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  createSession: (title = 'New Chat') =>
    request<Session>('/api/sessions', { method: 'POST', body: JSON.stringify({ title }) }),

  listSessions: () => request<Session[]>('/api/sessions'),

  getMessages: (sessionId: string) =>
    request<Message[]>(`/api/sessions/${sessionId}/messages`),

  deleteSession: (sessionId: string) =>
    fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' }),

  chat: (message: string, sessionId?: string) =>
    request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    }),

  health: () => request<{ status: string; provider: string; db: string; retrieval: string }>('/health'),
}
