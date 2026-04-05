import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Send, User, Bot, Loader2, ChevronLeft, Trash2 } from 'lucide-react';
import { agentApi } from '../api/client';
import type { Agent, Message } from '../types';

const STORAGE_KEY = 'chat_histories';

function loadHistories(): Record<string, Message[]> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

function saveHistories(histories: Record<string, Message[]>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(histories));
}

export default function Chat() {
  const { agentId } = useParams<{ agentId?: string }>();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [agentHealthy, setAgentHealthy] = useState(false);
  const [histories, setHistories] = useState<Record<string, Message[]>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const switchAgent = useCallback((agentId: string) => {
    setSelectedAgent(agentId);
    const loadedHistories = loadHistories();
    setHistories(loadedHistories);
    setMessages(loadedHistories[agentId] || []);
  }, []);

  useEffect(() => {
    agentApi.listAgents().then(async (list) => {
      const withStatus = await Promise.all(
        list.map(async (a) => {
          const healthy = await agentApi.checkAgentHealth(a.id);
          return { ...a, status: healthy ? 'running' : 'stopped' } as Agent;
        })
      );
      setAgents(withStatus);
      
      const loadedHistories = loadHistories();
      setHistories(loadedHistories);
      
      if (agentId) {
        switchAgent(agentId);
      } else if (withStatus.length > 0) {
        switchAgent(withStatus[0].id);
      }
    });
  }, [agentId, switchAgent]);

  useEffect(() => {
    const agent = agents.find(a => a.id === selectedAgent);
    setAgentHealthy(agent?.status === 'running');
  }, [selectedAgent, agents]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const clearChat = () => {
    const newHistories = { ...histories, [selectedAgent]: [] };
    setHistories(newHistories);
    setMessages([]);
    saveHistories(newHistories);
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedAgent || loading) return;
    const userMsg: Message = { role: 'user', content: input };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    const currentInput = input;
    setInput('');
    setLoading(true);
    try {
      const res = await agentApi.chat(selectedAgent, { prompt: currentInput, history: messages });
      const assistantMsg = { role: 'assistant' as const, content: res.response };
      const newMessages = [...updatedMessages, assistantMsg];
      setMessages(newMessages);
      
      const newHistories = { ...histories, [selectedAgent]: newMessages };
      setHistories(newHistories);
      saveHistories(newHistories);
    } catch (e: unknown) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e instanceof Error ? e.message : 'Request failed'}` }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: '24px', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
        {agentId && (
          <Link to="/" style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
            <ChevronLeft size={18} />
          </Link>
        )}
        <h1 style={{ margin: 0 }}>{agentId ? `Chat with ${agentId}` : 'Agent Chat'}</h1>
        {selectedAgent && (
          <span style={{
            padding: '3px 10px', borderRadius: '99px', fontSize: '11px',
            background: agentHealthy ? 'rgba(22, 163, 74, 0.1)' : 'rgba(220, 38, 38, 0.1)',
            color: agentHealthy ? 'var(--success)' : 'var(--error)',
          }}>
            {agentHealthy ? 'Running' : 'Offline'}
          </span>
        )}
        {!agentId && (
          <>
            <select
              value={selectedAgent}
              onChange={e => switchAgent(e.target.value)}
              style={{
                padding: '6px 12px', background: 'var(--bg-secondary)', color: 'var(--text-primary)',
                border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px',
              }}
            >
              {agents.length === 0 && <option value="">No agents</option>}
              {agents.map(a => <option key={a.id} value={a.id}>{a.id} (:{a.port})</option>)}
            </select>
            {selectedAgent && (
              <button
                onClick={clearChat}
                style={{
                  padding: '6px 12px', background: 'var(--bg-secondary)', color: 'var(--text-muted)',
                  border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px',
                  display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer',
                }}
                title="Clear chat history"
              >
                <Trash2 size={14} />
                Clear
              </button>
            )}
          </>
        )}
      </div>

      <div style={{
        flex: 1, minHeight: 0,
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}>
        <div style={{
          flex: 1, overflow: 'auto', padding: '20px 24px',
          display: 'flex', flexDirection: 'column', gap: '16px',
        }}>
          {messages.length === 0 && (
            <div style={{
              flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              color: 'var(--text-muted)', gap: '12px',
            }}>
              <Bot size={40} style={{ opacity: 0.4 }} />
              <div style={{ fontSize: '14px' }}>
                {selectedAgent ? `Send a message to ${selectedAgent}` : 'Select an agent above to start'}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} style={{
              display: 'flex', gap: '12px', alignItems: 'flex-start',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
            }}>
              <div style={{
                width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-tertiary)',
                color: msg.role === 'user' ? 'white' : 'var(--text-secondary)',
              }}>
                {msg.role === 'user' ? <User size={15} /> : <Bot size={15} />}
              </div>
              <div style={{
                maxWidth: '70%', padding: '10px 14px', borderRadius: '12px',
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-tertiary)',
                border: '1px solid var(--border)',
                color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                fontSize: '13px', lineHeight: 1.6,
                whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              }}>
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
              <div style={{
                width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'var(--bg-tertiary)',
              }}>
                <Bot size={15} />
              </div>
              <div style={{
                padding: '10px 14px', borderRadius: '12px',
                background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Agent is thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={{
          padding: '16px 24px', borderTop: '1px solid var(--border)',
          display: 'flex', gap: '12px', alignItems: 'flex-end',
        }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={selectedAgent ? `Message ${selectedAgent}...` : 'Select an agent first'}
            disabled={!selectedAgent || loading}
            rows={1}
            style={{
              flex: 1, padding: '10px 14px', background: 'var(--bg-tertiary)',
              color: 'var(--text-primary)', border: '1px solid var(--border)',
              borderRadius: '10px', fontSize: '13px', resize: 'none', outline: 'none',
              minHeight: '42px', maxHeight: '150px', fontFamily: 'inherit',
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !selectedAgent || loading}
            style={{
              width: '42px', height: '42px', borderRadius: '10px', flexShrink: 0,
              background: input.trim() && selectedAgent ? 'var(--accent)' : 'var(--bg-tertiary)',
              color: input.trim() && selectedAgent ? 'white' : 'var(--text-muted)',
              border: 'none', cursor: input.trim() && selectedAgent ? 'pointer' : 'default',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: input.trim() && selectedAgent ? '0 1px 3px rgba(99,102,241,0.3)' : 'none',
            }}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
