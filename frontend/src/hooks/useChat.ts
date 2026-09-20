import { useState, useEffect, useCallback } from 'react'
import { api, type Session, type Message } from '../lib/api'

export function useChat() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [provider, setProvider] = useState<string>('')

  const loadSessions = useCallback(async () => {
    try {
      const data = await api.listSessions()
      setSessions(data)
    } catch {
      // non-fatal
    }
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  const selectSession = useCallback(async (id: string) => {
    setActiveSessionId(id)
    setError(null)
    try {
      const msgs = await api.getMessages(id)
      setMessages(msgs)
    } catch {
      setMessages([])
    }
  }, [])

  const newSession = useCallback(() => {
    setActiveSessionId(null)
    setMessages([])
    setError(null)
  }, [])

  const deleteSession = useCallback(async (id: string) => {
    await api.deleteSession(id)
    setSessions(prev => prev.filter(s => s.id !== id))
    if (activeSessionId === id) newSession()
  }, [activeSessionId, newSession])

  const sendMessage = useCallback(async (text: string) => {
    setLoading(true)
    setError(null)
    const optimisticUser: Message = {
      id: `tmp-${Date.now()}`,
      session_id: activeSessionId || '',
      role: 'user',
      content: text,
      sources: [],
      artifact: null,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, optimisticUser])

    try {
      const res = await api.chat(text, activeSessionId || undefined)
      setProvider(res.provider)
      if (!activeSessionId) {
        setActiveSessionId(res.session_id)
        await loadSessions()
      } else {
        setSessions(prev => prev.map(s =>
          s.id === res.session_id ? { ...s, updated_at: new Date().toISOString() } : s
        ))
      }
      setMessages(prev => [
        ...prev.filter(m => m.id !== optimisticUser.id),
        { ...optimisticUser, session_id: res.session_id },
        res.message,
      ])
    } catch (e: unknown) {
      setMessages(prev => prev.filter(m => m.id !== optimisticUser.id))
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [activeSessionId, loadSessions])

  return {
    sessions, activeSessionId, messages, loading, error, provider,
    selectSession, newSession, deleteSession, sendMessage,
  }
}
