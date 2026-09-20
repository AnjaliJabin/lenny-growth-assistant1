import type { Session } from '../lib/api'

interface Props {
  sessions: Session[]
  activeSessionId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => void
  provider: string
}

export function Sidebar({ sessions, activeSessionId, onSelect, onNew, onDelete, provider }: Props) {
  return (
    <aside className="sidebar" role="navigation" aria-label="Chat sessions">
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <span className="sidebar__logo-icon">🚀</span>
          <span className="sidebar__logo-text">Lenny Assistant</span>
        </div>
        <button className="sidebar__new-btn" onClick={onNew} aria-label="New chat">
          + New Chat
        </button>
      </div>

      <div className="sidebar__provider">
        <span className="provider__badge" data-provider={provider}>
          {provider === 'ollama' ? '🦙 Ollama (local)' : provider === 'anthropic' ? '☁️ Claude' : '⚙️ ' + provider}
        </span>
      </div>

      <nav className="sidebar__sessions">
        {sessions.length === 0 && (
          <p className="sidebar__empty">No chats yet. Start one!</p>
        )}
        {sessions.map(s => (
          <div
            key={s.id}
            className={`session-item ${s.id === activeSessionId ? 'session-item--active' : ''}`}
          >
            <button
              className="session-item__title"
              onClick={() => onSelect(s.id)}
              aria-current={s.id === activeSessionId ? 'page' : undefined}
            >
              💬 {s.title.length > 35 ? s.title.slice(0, 35) + '…' : s.title}
            </button>
            <button
              className="session-item__delete"
              onClick={e => { e.stopPropagation(); onDelete(s.id) }}
              aria-label={`Delete session ${s.title}`}
            >
              ×
            </button>
          </div>
        ))}
      </nav>

      <div className="sidebar__footer">
        <p>Grounded in Lenny's Podcast</p>
      </div>
    </aside>
  )
}
