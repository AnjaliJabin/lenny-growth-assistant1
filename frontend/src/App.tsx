import { useEffect, useRef, useState } from 'react'
import { useChat } from './hooks/useChat'
import { Sidebar } from './components/Sidebar'
import { ChatMessage } from './components/ChatMessage'
import { ChatInput } from './components/ChatInput'
import { ArtifactViewer } from './components/ArtifactViewer'
import './App.css'

export default function App() {
  const {
    sessions, activeSessionId, messages, loading, error, provider,
    selectSession, newSession, deleteSession, sendMessage,
  } = useChat()

  const [artifact, setArtifact] = useState<{ type: string; content: string } | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  return (
    <div className={`app ${artifact ? 'app--split' : ''}`}>
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={selectSession}
        onNew={newSession}
        onDelete={deleteSession}
        provider={provider}
      />

      <main className="chat-area" role="main">
        <div className="chat-area__messages" aria-live="polite" aria-label="Chat messages">
          {messages.length === 0 && !loading && (
            <div className="chat-area__welcome">
              <div className="welcome__icon">🚀</div>
              <h1 className="welcome__title">Lenny Growth Assistant</h1>
              <p className="welcome__subtitle">
                Ask product and growth questions grounded in Lenny's Podcast transcripts.
                Request Ship 30 essays or generate Markdown/HTML artifacts.
              </p>
            </div>
          )}

          {messages.map(msg => (
            <ChatMessage
              key={msg.id}
              message={msg}
              onViewArtifact={setArtifact}
            />
          ))}

          {loading && (
            <div className="message message--assistant">
              <div className="message__bubble message__bubble--loading">
                <span className="loading-dot" />
                <span className="loading-dot" />
                <span className="loading-dot" />
              </div>
            </div>
          )}

          {error && (
            <div className="chat-area__error" role="alert">
              ⚠️ {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <ChatInput onSend={sendMessage} disabled={loading} />
      </main>

      {artifact && (
        <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />
      )}
    </div>
  )
}
