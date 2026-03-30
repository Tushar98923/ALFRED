import React, { useEffect, useMemo, useRef, useState } from 'react'
import { getSpeechRecognition } from './voice'
import {
  listConversations, getConversation, createConversation, deleteConversation,
  listDocuments, uploadDocument, deleteDocument, getKnowledgeStats,
  listProviders, getProviderChoices, saveProvider, activateProvider, deleteProvider,
  postCommand,
  type Conversation, type Message, type KnowledgeDocument,
  type RAGSource, type AssistantResponse, type LLMProvider, type ProviderChoice,
} from '../api/client'


export default function App() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [listening, setListening] = useState(false)

  const [conversationId, setConversationId] = useState<number | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [lastResponse, setLastResponse] = useState<AssistantResponse | null>(null)

  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [sidebarTab, setSidebarTab] = useState<'chats' | 'knowledge' | 'settings'>('chats')
  const [uploading, setUploading] = useState(false)
  const [kbChunks, setKbChunks] = useState(0)

  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [providerChoices, setProviderChoices] = useState<ProviderChoice[]>([])
  const [showSettings, setShowSettings] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const canSend = useMemo(() => text.trim().length > 0 && !loading, [text, loading])

  // ── Init ────────────────────────────────────────────────────

  useEffect(() => {
    listConversations().then(setConversations).catch(() => {})
    loadDocuments()
    getKnowledgeStats().then(s => setKbChunks(s.total_chunks)).catch(() => {})
    loadProviders()
  }, [])

  useEffect(() => {
    if (!conversationId) { setMessages([]); return }
    getConversation(conversationId).then(c => setMessages(c.messages || [])).catch(() => {})
  }, [conversationId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, lastResponse])

  useEffect(() => {
    const rec = getSpeechRecognition()
    recognitionRef.current = rec
    if (!rec) return
    rec.continuous = false
    rec.interimResults = false
    rec.onresult = (evt: any) => {
      const t = Array.from(evt.results).map((r: any) => r[0]?.transcript).join(' ')
      setText((p: string) => (p ? p + ' ' : '') + t)
      setListening(false)
    }
    rec.onend = () => setListening(false)
    rec.onerror = () => setListening(false)
  }, [])

  // ── Helpers ─────────────────────────────────────────────────

  const loadDocuments = () => {
    listDocuments().then(setDocuments).catch(() => {})
  }

  const loadProviders = () => {
    listProviders().then(setProviders).catch(() => {})
    getProviderChoices().then(setProviderChoices).catch(() => {})
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await uploadDocument(file)
      loadDocuments()
      getKnowledgeStats().then(s => setKbChunks(s.total_chunks)).catch(() => {})
    } catch (err: any) {
      setError(err?.message || 'Upload failed')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleDeleteDoc = async (id: number) => {
    await deleteDocument(id).catch(() => {})
    loadDocuments()
    getKnowledgeStats().then(s => setKbChunks(s.total_chunks)).catch(() => {})
  }

  const handleDeleteConv = async (id: number) => {
    await deleteConversation(id).catch(() => {})
    if (conversationId === id) { setConversationId(null); setMessages([]); setLastResponse(null) }
    listConversations().then(setConversations).catch(() => {})
  }

  const toggleVoice = () => {
    const rec = recognitionRef.current
    if (!rec) return
    if (listening) { rec.stop(); setListening(false) }
    else { setListening(true); rec.start() }
  }

  // ── Send ────────────────────────────────────────────────────

  const handleSend = async () => {
    if (!canSend) return
    const userText = text.trim()
    setText('')
    setError('')
    setLastResponse(null)

    // Optimistic: immediately show the user message
    const tempUserMsg: Message = {
      id: Date.now(),
      conversation: conversationId ?? 0,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    }
    setMessages((prev: Message[]) => [...prev, tempUserMsg])
    setLoading(true)

    try {
      const result = await postCommand(userText, conversationId ?? undefined)
      setLastResponse(result)

      if ('error' in result && result.error && !('mode' in result)) {
        setError(result.error as string)
      } else if ('conversation_id' in result) {
        const cid = (result as any).conversation_id as number
        setConversationId(cid)

        // Optimistic sidebar: add new conversation or move existing to top
        setConversations((prev: Conversation[]) => {
          const exists = prev.some((c: Conversation) => c.id === cid)
          if (!exists) {
            // New conversation — add to top immediately
            return [{
              id: cid,
              title: userText.slice(0, 40),
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }, ...prev]
          }
          // Existing conversation — move to top
          const conv = prev.find((c: Conversation) => c.id === cid)!
          return [{ ...conv, updated_at: new Date().toISOString() }, ...prev.filter((c: Conversation) => c.id !== cid)]
        })

        // Optimistic: immediately show the assistant message
        const assistantContent =
          result.mode === 'knowledge' && 'answer' in result ? (result as any).answer :
          result.mode === 'command' && 'command' in result ? (result as any).command : ''

        if (assistantContent) {
          const tempAssistantMsg: Message = {
            id: Date.now() + 1,
            conversation: cid,
            role: 'assistant',
            content: assistantContent,
            created_at: new Date().toISOString(),
          }
          setMessages((prev: Message[]) => [...prev, tempAssistantMsg])
        }
      }
    } catch (e: any) {
      setError(e?.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const formatTime = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // ── Render ──────────────────────────────────────────────────

  return (
    <div className="app">
      <div className="geo-dot-grid" />

      {/* ━━ Sidebar ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <aside className="sidebar">
        <div className="sidebar-tabs">
          {(['chats', 'knowledge', 'settings'] as const).map(tab => (
            <button
              key={tab}
              className={`sidebar-tab ${sidebarTab === tab ? 'active' : ''}`}
              onClick={() => setSidebarTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="sidebar-content">
          {sidebarTab === 'chats' && (
            <>
              <div className="sidebar-header">
                <span className="sidebar-title">Conversations</span>
                <button className="btn btn-sm" onClick={async () => {
                  try {
                    const c = await createConversation('New conversation')
                    setConversations((cs: Conversation[]) => [c, ...cs])
                    setConversationId(c.id)
                    setMessages([])
                    setLastResponse(null)
                  } catch {}
                }}>+ New</button>
              </div>
              <ul className="conv-list">
                {conversations.map(c => (
                  <li key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <button
                      className={`conv-item ${conversationId === c.id ? 'active' : ''}`}
                      onClick={() => { setConversationId(c.id); setLastResponse(null) }}
                    >
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {c.title || `#${c.id}`}
                      </span>
                      <span className="conv-meta">{formatTime(c.updated_at)}</span>
                    </button>
                    <button
                      className="btn-danger btn-sm"
                      onClick={() => handleDeleteConv(c.id)}
                      title="Delete"
                      style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 11, color: '#ccc', padding: 4 }}
                    >×</button>
                  </li>
                ))}
                {conversations.length === 0 && (
                  <li className="empty-state">No conversations yet</li>
                )}
              </ul>
            </>
          )}

          {sidebarTab === 'knowledge' && (
            <>
              <div className="sidebar-header">
                <span className="sidebar-title">Documents</span>
                <button className="btn btn-sm" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                  {uploading ? '...' : '+ Upload'}
                </button>
                <input ref={fileInputRef} type="file" accept=".txt,.md,.pdf,.docx,.csv"
                  onChange={handleUpload} style={{ display: 'none' }} />
              </div>
              <div className="kb-stats">
                {documents.filter(d => d.status === 'ready').length} docs · {kbChunks} chunks
              </div>
              {documents.map(doc => (
                <div key={doc.id} className="doc-item">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div className="doc-name">{doc.title}</div>
                      <div className="doc-meta">
                        .{doc.file_type} · {(doc.file_size / 1024).toFixed(0)}kb
                        {doc.status === 'ready' && ` · ${doc.chunk_count} chunks`}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span className="doc-status" style={{
                        background: doc.status === 'ready' ? 'var(--success)' :
                          doc.status === 'error' ? 'var(--error)' :
                          doc.status === 'processing' ? 'var(--warning)' : 'var(--text-tertiary)'
                      }} />
                      <button className="btn-danger btn-sm" onClick={() => handleDeleteDoc(doc.id)}
                        style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: 12, padding: 2 }}>×</button>
                    </div>
                  </div>
                  {doc.status === 'error' && doc.error_message && (
                    <div style={{ fontSize: 10, color: 'var(--error)', marginTop: 4 }}>{doc.error_message}</div>
                  )}
                </div>
              ))}
              {documents.length === 0 && (
                <div className="empty-state">
                  Upload .txt, .md, .pdf, .docx,<br/>or .csv to build your knowledge base.
                </div>
              )}
            </>
          )}

          {sidebarTab === 'settings' && (
            <>
              <div className="sidebar-header">
                <span className="sidebar-title">LLM Providers</span>
              </div>
              <ProviderManager
                providers={providers}
                choices={providerChoices}
                onRefresh={loadProviders}
              />
            </>
          )}
        </div>
      </aside>

      {/* ━━ Main ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <main className="main">
        <header className="header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="logo">Alfred</span>
            {loading && (
              <span className="loading-dots">
                <span>·</span><span>·</span><span>·</span>
              </span>
            )}
          </div>
          <div className="header-right">
            {kbChunks > 0 && <span className="badge badge-knowledge">{kbChunks} chunks</span>}
            <span className="badge">auto-route</span>
            <button className="btn btn-ghost" onClick={toggleVoice} disabled={!getSpeechRecognition()}>
              {listening ? '■ stop' : '● voice'}
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && !lastResponse && (
            <div className="welcome">
              <div className="welcome-grid" />
              <h2>Alfred</h2>
              <p>
                Ask a question about your documents or give a system command.
                Intent is detected automatically.
              </p>
              {kbChunks === 0 && (
                <div className="welcome-hint">
                  Upload documents in the knowledge tab to enable RAG.
                </div>
              )}
            </div>
          )}

          {messages.map(m => (
            <div key={m.id} className={`message message-${m.role}`}>
              <div className="message-role">{m.role}</div>
              <div className="message-content">{m.content}</div>
              <div className="message-time">{formatTime(m.created_at)}</div>
            </div>
          ))}

          {loading && (
            <div className="message message-assistant">
              <div className="message-role">assistant</div>
              <div className="message-content">
                <span className="loading-dots"><span>·</span><span>·</span><span>·</span></span>
              </div>
            </div>
          )}

          {lastResponse && 'mode' in lastResponse && (
            <div style={{ maxWidth: 640 }}>
              {lastResponse.mode === 'knowledge' && 'sources' in lastResponse && lastResponse.sources.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <span className="badge badge-knowledge" style={{ marginBottom: 6, display: 'inline-block' }}>knowledge</span>
                  <div className="sources">
                    {lastResponse.sources.map((s: RAGSource, i: number) => (
                      <span key={i} className="source-tag">
                        {s.name} · {(s.score * 100).toFixed(0)}%
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {lastResponse.mode === 'command' && 'command' in lastResponse && (
                <div style={{ marginTop: 8 }}>
                  <span className="badge badge-command" style={{ marginBottom: 6, display: 'inline-block' }}>command</span>
                  <div className="command-block">{lastResponse.command}</div>
                  <Execute command={lastResponse.command} />
                </div>
              )}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {error && <div className="error-bar">{error}</div>}

        {/* Input */}
        <div className="input-bar">
          <div className="input-row">
            <input
              className="input-field"
              value={text}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question or give a command..."
            />
            <button className="btn btn-primary" onClick={handleSend} disabled={!canSend}>
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}


// ─── Provider Manager ───────────────────────────────────────────

function ProviderManager({ providers, choices, onRefresh }: {
  providers: LLMProvider[]
  choices: ProviderChoice[]
  onRefresh: () => void
}) {
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({ provider: '', api_key: '', base_url: '', model_name: '' })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.provider) return
    setSaving(true)
    try {
      await saveProvider(form)
      onRefresh()
      setAdding(false)
      setForm({ provider: '', api_key: '', base_url: '', model_name: '' })
    } catch {}
    setSaving(false)
  }

  const handleActivate = async (id: number) => {
    await activateProvider(id).catch(() => {})
    onRefresh()
  }

  const handleDelete = async (id: number) => {
    await deleteProvider(id).catch(() => {})
    onRefresh()
  }

  return (
    <div>
      {providers.map(p => (
        <div key={p.id} className={`provider-card ${p.is_active ? 'active' : ''}`}>
          <div className="provider-name">
            <span>{p.provider_display}</span>
            <div style={{ display: 'flex', gap: 4 }}>
              {!p.is_active && p.is_configured && (
                <button className="btn btn-sm" onClick={() => handleActivate(p.id)}>Activate</button>
              )}
              {p.is_active && <span className="badge" style={{ borderColor: 'var(--success)', color: 'var(--success)' }}>active</span>}
              <button className="btn btn-sm" onClick={() => handleDelete(p.id)}
                style={{ color: 'var(--error)', borderColor: 'transparent' }}>×</button>
            </div>
          </div>
          <div className="provider-status">
            {p.masked_key ? `Key: ${p.masked_key}` : 'No key set'}
            {p.base_url && ` · ${p.base_url}`}
            {p.model_name && ` · ${p.model_name}`}
          </div>
        </div>
      ))}

      {adding ? (
        <div className="provider-card">
          <select className="provider-input" value={form.provider}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setForm({ ...form, provider: e.target.value })}>
            <option value="">Select provider...</option>
            {choices.map(c => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          <input className="provider-input" placeholder="API Key"
            type="password" value={form.api_key}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, api_key: e.target.value })} />
          <input className="provider-input" placeholder="Base URL (optional)"
            value={form.base_url}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, base_url: e.target.value })} />
          <input className="provider-input" placeholder="Model name (optional)"
            value={form.model_name}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, model_name: e.target.value })} />
          <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
            <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving || !form.provider}>
              {saving ? '...' : 'Save'}
            </button>
            <button className="btn btn-sm" onClick={() => setAdding(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <button className="btn" style={{ width: '100%', marginTop: 8 }} onClick={() => setAdding(true)}>
          + Add Provider
        </button>
      )}

      {providers.length === 0 && !adding && (
        <div className="empty-state">
          Add an LLM provider to get started.<br/>
          Supports Gemini, OpenAI, Anthropic, and more.
        </div>
      )}
    </div>
  )
}


// ─── Execute ────────────────────────────────────────────────────

function Execute({ command }: { command: string }) {
  const [running, setRunning] = useState(false)
  const [output, setOutput] = useState<{ stdout?: string; stderr?: string; error?: string } | null>(null)

  const run = async () => {
    setRunning(true); setOutput(null)
    try {
      const res = await fetch('/api/execute/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      })
      setOutput(await res.json())
    } catch (e: any) {
      setOutput({ error: e?.message || 'Failed' })
    }
    setRunning(false)
  }

  return (
    <div>
      <button className="btn btn-sm" onClick={run} disabled={running} style={{ marginTop: 6 }}>
        {running ? 'Running...' : '▶ Execute'}
      </button>
      {output && (
        <div className="command-output">{JSON.stringify(output, null, 2)}</div>
      )}
    </div>
  )
}
