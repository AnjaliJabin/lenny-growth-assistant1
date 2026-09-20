import { useState, useRef, useEffect, type KeyboardEvent } from 'react'

interface Props {
  onSend: (text: string) => void
  disabled: boolean
}

const SUGGESTIONS = [
  'What is product-market fit and how do I measure it?',
  'Write a Ship 30 essay about growth loops',
  'Generate a markdown doc about onboarding best practices',
  'How should I structure a growth team?',
  'What pricing strategy works best for SaaS?',
]

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px'
    }
  }, [value])

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="chat-input">
      <div className="chat-input__suggestions">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            className="suggestion__chip"
            onClick={() => { setValue(s); textareaRef.current?.focus() }}
            disabled={disabled}
          >
            {s}
          </button>
        ))}
      </div>
      <div className="chat-input__row">
        <textarea
          ref={textareaRef}
          className="chat-input__textarea"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask about product growth, request a Ship 30 essay, or generate an artifact…"
          disabled={disabled}
          rows={1}
          aria-label="Chat message input"
        />
        <button
          className="chat-input__send"
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send message"
        >
          {disabled ? '⏳' : '➤'}
        </button>
      </div>
      <p className="chat-input__hint">Enter to send · Shift+Enter for new line</p>
    </div>
  )
}
