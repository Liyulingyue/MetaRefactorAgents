import { Link } from 'react-router-dom';
import { ChevronLeft, Folder, Layout, Trash2, Bomb } from 'lucide-react';
import type { Agent } from '../../types';

interface ChatHeaderProps {
  agentId?: string;
  selectedAgent: string;
  agentHealthy: boolean;
  showFiles: boolean;
  setShowFiles: (show: boolean) => void;
  showPreview: boolean;
  setShowPreview: (show: boolean) => void;
  agents: Agent[];
  switchAgent: (id: string) => void;
  handleClearChat: () => void;
  handleDeepClear: () => void;
}

export function ChatHeader({
  agentId,
  selectedAgent,
  agentHealthy,
  showFiles,
  setShowFiles,
  showPreview,
  setShowPreview,
  agents,
  switchAgent,
  handleClearChat,
  handleDeepClear
}: ChatHeaderProps) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
      {agentId && (
        <Link to="/" style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
          <ChevronLeft size={18} />
        </Link>
      )}
      <h1 style={{ margin: 0, fontSize: '20px' }}>{agentId ? `Chat with ${agentId}` : 'Agent Chat'}</h1>

      {selectedAgent && (
        <span style={{
          padding: '3px 10px', borderRadius: '99px', fontSize: '11px',
          background: agentHealthy ? 'rgba(22, 163, 74, 0.1)' : 'rgba(220, 38, 38, 0.1)',
          color: agentHealthy ? 'var(--success)' : 'var(--error)',
        }}>
          {agentHealthy ? 'Running' : 'Offline'}
        </span>
      )}

      <div style={{ flex: 1 }} />

      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => setShowFiles(!showFiles)}
          style={{
            padding: '6px 12px', background: showFiles ? 'var(--accent)' : 'var(--bg-secondary)',
            color: showFiles ? 'white' : 'var(--text-primary)',
            border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px',
            display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer',
          }}
        >
          <Folder size={14} />
          Files
        </button>

        <button
          onClick={() => setShowPreview(!showPreview)}
          style={{
            padding: '6px 12px', background: showPreview ? 'var(--accent)' : 'var(--bg-secondary)',
            color: showPreview ? 'white' : 'var(--text-primary)',
            border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px',
            display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer',
          }}
        >
          <Layout size={14} />
          Preview
        </button>

        {!agentId && (
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
        )}

        {selectedAgent && (
          <>
            <button onClick={handleDeepClear} style={{
              padding: '6px 12px', background: 'rgba(220, 38, 38, 0.1)', color: 'var(--error)',
              border: '1px solid var(--error)', borderRadius: '8px', fontSize: '13px',
              display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer',
            }} title="Deep clear: clear all chat history and logs">
              <Bomb size={14} />
              Deep Clear
            </button>
            <button onClick={handleClearChat} style={{
              padding: '6px 12px', background: 'var(--bg-secondary)', color: 'var(--text-muted)',
              border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px',
              display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer',
            }} title="Clear chat history">
              <Trash2 size={14} />
              Clear
            </button>
          </>
        )}
      </div>
    </div>
  );
}
