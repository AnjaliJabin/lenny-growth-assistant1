import type { Message } from '../lib/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  message: Message
  onViewArtifact: (artifact: { type: string; content: string }) => void
}

export function ChatMessage({ message, onViewArtifact }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`message ${isUser ? 'message--user' : 'message--assistant'}`}>
      <div className="message__bubble">
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        )}
      </div>

      {message.sources.length > 0 && (
        <div className="message__sources">
          <span className="sources__label">Sources:</span>
          {message.sources.map((s, i) => (
            <span key={i} className="source__tag" title={`Score: ${s.score}`}>
              📄 {s.episode}
            </span>
          ))}
        </div>
      )}

      {message.artifact && (
        <button
          className="artifact__btn"
          onClick={() => onViewArtifact(message.artifact!)}
        >
          {message.artifact.type === 'html' ? '🌐' : '📝'} View{' '}
          {message.artifact.type === 'html' ? 'HTML' : 'Markdown'} Artifact
        </button>
      )}
    </div>
  )
}
