import { useState, useRef, useEffect } from 'react'
import './App.css'

const SUGGESTIONS = [
  { label: '2¹⁰ + √144 = ?', query: 'What is 2 raised to the power 10, plus the square root of 144?' },
  { label: '500 USD → INR', query: 'Convert 500 USD to INR' },
  { label: '10 km → miles', query: 'Convert 10 kilometers to miles' },
  { label: '100°F → °C', query: 'What is 100 degrees Fahrenheit in Celsius?' },
  { label: '75 kg → lbs', query: 'Convert 75 kg to pounds' },
  { label: '1000 EUR → JPY', query: 'Convert 1000 EUR to Japanese Yen' },
]

function ToolStep({ step }) {
  const [open, setOpen] = useState(false)
  const prettyResult = (() => {
    try { return JSON.stringify(JSON.parse(step.result), null, 2) }
    catch { return step.result }
  })()

  return (
    <div className="tool-step">
      <button className="tool-badge" onClick={() => setOpen(o => !o)}>
        <span className="tool-icon">⚙</span>
        {step.tool}
        <span className="chevron">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="tool-details">
          <div className="tool-row">
            <span className="tool-label">Args</span>
            <pre>{JSON.stringify(step.args, null, 2)}</pre>
          </div>
          <div className="tool-row">
            <span className="tool-label">Result</span>
            <pre>{prettyResult}</pre>
          </div>
        </div>
      )}
    </div>
  )
}

function Message({ msg }) {
  return (
    <div className={`msg-row ${msg.role}`}>
      {msg.role === 'agent' && <div className="avatar">AI</div>}
      <div className={`bubble ${msg.role}`}>
        <p className="msg-text">{msg.text}</p>
        {msg.steps && msg.steps.length > 0 && (
          <div className="steps-list">
            {msg.steps.map((s, i) => <ToolStep key={i} step={s} />)}
          </div>
        )}
      </div>
      {msg.role === 'user' && <div className="avatar user-av">You</div>}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="msg-row agent">
      <div className="avatar">AI</div>
      <div className="bubble agent typing">
        <span className="dot" /><span className="dot" /><span className="dot" />
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const autoResize = (el) => {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }

  const handleChange = (e) => {
    setInput(e.target.value)
    autoResize(e.target)
  }

  const send = async (query) => {
    const q = (query ?? input).trim()
    if (!q || loading) return
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'agent', text: data.answer, steps: data.steps }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', text: `Error: ${err.message}`, steps: [] }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-logo">⚡</div>
          <div>
            <h1>AI Agent</h1>
            <p>Calculations · Currency Conversion · Unit Conversion</p>
          </div>
        </div>
      </header>

      <main className="chat-area">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <div className="empty-emoji">🤖</div>
            <h2>What would you like to calculate or convert?</h2>
            <p>The agent uses tools — not its own memory — to answer your question.</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => send(s.query)}>
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <div className="input-wrap">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask me to calculate something, convert a currency, or convert units…"
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={() => send()}
            disabled={!input.trim() || loading}
          >
            {loading ? '…' : 'Send'}
          </button>
        </div>
        <p className="hint">Press Enter to send · Shift+Enter for new line</p>
      </footer>
    </div>
  )
}
