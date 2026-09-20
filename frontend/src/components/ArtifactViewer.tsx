import { useRef, useEffect } from 'react'
import DOMPurify from 'dompurify'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Props {
  artifact: { type: string; content: string } | null
  onClose: () => void
}

export function ArtifactViewer({ artifact, onClose }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    if (artifact?.type === 'html' && iframeRef.current) {
      // Sanitize HTML before rendering in sandboxed iframe
      const clean = DOMPurify.sanitize(artifact.content, {
        FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input'],
        FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'href'],
        ALLOW_DATA_ATTR: false,
      })
      const doc = iframeRef.current.contentDocument
      if (doc) {
        doc.open()
        doc.write(clean)
        doc.close()
      }
    }
  }, [artifact])

  if (!artifact) return null

  return (
    <div className="artifact-viewer">
      <div className="artifact-viewer__header">
        <span className="artifact-viewer__title">
          {artifact.type === 'html' ? '🌐 HTML Artifact' : '📝 Markdown Artifact'}
        </span>
        <button className="artifact-viewer__close" onClick={onClose} aria-label="Close artifact">✕</button>
      </div>
      <div className="artifact-viewer__body">
        {artifact.type === 'html' ? (
          <iframe
            ref={iframeRef}
            className="artifact-viewer__iframe"
            sandbox="allow-same-origin"
            title="HTML Artifact"
          />
        ) : (
          <div className="artifact-viewer__markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{artifact.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
