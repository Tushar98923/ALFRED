import React, { useEffect, useMemo, useRef, useState } from 'react'
import { getSpeechRecognition } from './voice'
import { listConversations, getConversation, createConversation, type Conversation, type Message } from '../api/client'

async function postCommand(text: string, conversation_id?: number): Promise<{ command?: string; error?: string; conversation_id?: number }> {
  const res = await fetch('/api/command/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, conversation_id })
  })
  return res.json()
}

export default function App() {
  const [text, setText] = useState('')
  const [command, setCommand] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<{ text: string; command?: string }[]>([])
  const [listening, setListening] = useState(false)
  const [dark, setDark] = useState(true)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  const canSend = useMemo(() => text.trim().length > 0 && !loading, [text, loading])

  const handleSend = async () => {
    if (!canSend) return
    setLoading(true)
    setError('')
    setCommand('')
    try {
      const result = await postCommand(text.trim(), conversationId ?? undefined)
      if (result.error) setError(result.error)
      if (result.command) {
        setCommand(result.command)
        setHistory((h) => [{ text, command: result.command }, ...h].slice(0, 20))
        if (typeof result.conversation_id === 'number') setConversationId(result.conversation_id)
      }
    } catch (e: any) {
      setError(e?.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const rec = getSpeechRecognition()
    recognitionRef.current = rec
    if (!rec) return
    rec.continuous = false
    rec.interimResults = false
    rec.onresult = (evt: any) => {
      const transcript = Array.from(evt.results)
        .map((r: any) => r[0]?.transcript)
        .join(' ')
      setText((prev) => (prev ? prev + ' ' : '') + transcript)
      setListening(false)
    }
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
  }, [])

  useEffect(() => {
    // load conversations on mount
    listConversations().then(setConversations).catch(() => {})
  }, [])

  useEffect(() => {
    if (!conversationId) return
    getConversation(conversationId).then((c) => setMessages(c.messages || [])).catch(() => {})
  }, [conversationId])

  const toggleVoice = () => {
    const rec = recognitionRef.current
    if (!rec) return
    if (listening) {
      rec.stop()
      setListening(false)
    } else {
      setListening(true)
      rec.start()
    }
  }

  const bg = dark ? '#0b0f17' : '#f3f4f6'
  const panel = dark ? '#0f172a' : '#ffffff'
  const textColor = dark ? '#e5e7eb' : '#111827'
  const subText = dark ? '#9aa2b1' : '#6b7280'

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: bg, color: textColor, padding: 24
    }}>
      <div style={{ width: 720, maxWidth: '100%', background: panel, borderRadius: 12, padding: 20, border: '1px solid #1f2937' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0, fontSize: 24 }}>ALFRED</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 12, color: subText }}>{loading ? 'Contacting model…' : 'Idle'}</span>
            <button onClick={() => setDark((d) => !d)} style={{
              background: dark ? '#f3f4f6' : '#111827',
              color: dark ? '#111827' : '#f3f4f6',
              border: 'none', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', fontWeight: 600
            }}>{dark ? 'Light' : 'Dark'}</button>
          </div>
        </div>
        <p style={{ marginTop: 8, color: subText }}>Type a task or use voice. Review and run safely.</p>

        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 12, marginTop: 16 }}>
          <aside style={{ background: '#0b1220', border: '1px solid #1f2937', borderRadius: 8, padding: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ fontWeight: 700 }}>Conversations</div>
              <button onClick={async () => {
                const title = text.trim() ? text.trim().slice(0, 40) : 'New chat'
                try {
                  const c = await createConversation(title)
                  setConversations((cs) => [c, ...cs])
                  setConversationId(c.id)
                  setMessages([])
                } catch {}
              }} style={{ background: '#22c55e', color: 'black', border: 'none', borderRadius: 6, padding: '6px 8px', cursor: 'pointer', fontWeight: 600 }}>New</button>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 6, maxHeight: 420, overflow: 'auto' }}>
              {conversations.map((c) => (
                <li key={c.id}>
                  <button onClick={() => setConversationId(c.id)} style={{
                    width: '100%', textAlign: 'left', background: conversationId === c.id ? '#1f2937' : 'transparent',
                    color: textColor, border: '1px solid #1f2937', borderRadius: 6, padding: '8px 10px', cursor: 'pointer'
                  }}>{c.title || `Conversation ${c.id}`}</button>
                </li>
              ))}
            </ul>
          </aside>

          <section>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="e.g., create a folder named Reports on Desktop"
                style={{
                  flex: 1,
                  background: '#0b1220',
                  border: '1px solid #1f2937',
                  color: 'white',
                  borderRadius: 8,
                  padding: '10px 12px'
                }}
              />
              <button onClick={toggleVoice} disabled={!getSpeechRecognition()} style={{
                background: '#60a5fa',
                color: 'black',
                border: 'none',
                borderRadius: 8,
                padding: '10px 12px',
                cursor: getSpeechRecognition() ? 'pointer' : 'not-allowed',
                fontWeight: 600
              }}>{listening ? 'Listening…' : 'Voice'}</button>

              <button onClick={handleSend} disabled={!canSend} style={{
                background: canSend ? '#22c55e' : '#374151',
                color: 'black',
                border: 'none',
                borderRadius: 8,
                padding: '10px 14px',
                cursor: canSend ? 'pointer' : 'not-allowed',
                fontWeight: 600
              }}>Send</button>
            </div>

            <div style={{ marginTop: 12 }}>
              {messages.map((m) => (
                <div key={m.id} style={{
                  background: m.role === 'user' ? '#0b1220' : 'transparent',
                  border: '1px solid #1f2937', borderRadius: 8, padding: 10, marginBottom: 8
                }}>
                  <div style={{ fontSize: 12, color: subText, marginBottom: 4 }}>{m.role.toUpperCase()}</div>
                  <div>{m.content}</div>
                </div>
              ))}
              {command && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 12, color: subText }}>Suggested PowerShell command</div>
                  <pre style={{
                    marginTop: 6,
                    background: '#0b1220',
                    border: '1px solid #1f2937',
                    color: '#e5e7eb',
                    padding: 12,
                    borderRadius: 8,
                    whiteSpace: 'pre-wrap'
                  }}>{command}</pre>
                  <Execute command={command} />
                </div>
              )}
            </div>
          </section>
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g., create a folder named Reports on Desktop"
            style={{
              flex: 1,
              background: '#0b1220',
              border: '1px solid #1f2937',
              color: 'white',
              borderRadius: 8,
              padding: '10px 12px'
            }}
          />
          <button onClick={toggleVoice} disabled={!getSpeechRecognition()} style={{
            background: '#60a5fa',
            color: 'black',
            border: 'none',
            borderRadius: 8,
            padding: '10px 12px',
            cursor: getSpeechRecognition() ? 'pointer' : 'not-allowed',
            fontWeight: 600
          }}>{listening ? 'Listening…' : 'Voice'}</button>

          <button onClick={handleSend} disabled={!canSend} style={{
            background: canSend ? '#22c55e' : '#374151',
            color: 'black',
            border: 'none',
            borderRadius: 8,
            padding: '10px 14px',
            cursor: canSend ? 'pointer' : 'not-allowed',
            fontWeight: 600
          }}>Send</button>
        </div>

        {loading && <p style={{ marginTop: 12 }}>Thinking…</p>}
        {error && <p style={{ marginTop: 12, color: '#fca5a5' }}>{error}</p>}
        {command && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, color: '#9aa2b1' }}>Suggested PowerShell command</div>
            <pre style={{
              marginTop: 6,
              background: '#0b1220',
              border: '1px solid #1f2937',
              color: '#e5e7eb',
              padding: 12,
              borderRadius: 8,
              whiteSpace: 'pre-wrap'
            }}>{command}</pre>
            <Execute command={command} />
          </div>
        )}

        {history.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <div style={{ fontSize: 12, color: '#9aa2b1', marginBottom: 6 }}>Recent</div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 8 }}>
              {history.map((h, idx) => (
                <li key={idx} style={{ background: '#0b1220', border: '1px solid #1f2937', borderRadius: 8, padding: 10 }}>
                  <div style={{ fontWeight: 600 }}>{h.text}</div>
                  {h.command && <div style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', color: '#9aa2b1', marginTop: 4 }}>{h.command}</div>}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

function Execute({ command }: { command: string }) {
  const [running, setRunning] = useState(false)
  const [output, setOutput] = useState<{ stdout?: string; stderr?: string; error?: string } | null>(null)

  const run = async () => {
    setRunning(true)
    setOutput(null)
    try {
      const res = await fetch('/api/execute/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      })
      const data = await res.json()
      setOutput(data)
    } catch (e: any) {
      setOutput({ error: e?.message || 'Failed' })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div style={{ marginTop: 10 }}>
      <button onClick={run} disabled={running} style={{
        background: '#fbbf24', color: 'black', border: 'none', borderRadius: 8, padding: '8px 12px', cursor: running ? 'not-allowed' : 'pointer', fontWeight: 600
      }}>Run Safely</button>
      {output && (
        <pre style={{ marginTop: 8, background: '#0b1220', border: '1px solid #1f2937', color: '#e5e7eb', padding: 10, borderRadius: 8, whiteSpace: 'pre-wrap' }}>
{JSON.stringify(output, null, 2)}
        </pre>
      )}
    </div>
  )
}


