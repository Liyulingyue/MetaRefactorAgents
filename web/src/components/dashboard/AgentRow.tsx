import { Link } from 'react-router-dom';
import { Play, Square, MessageSquare, FileText, Settings2, Brain, FolderOpen } from 'lucide-react';
import type { Agent } from '../../types';

interface AgentRowProps {
  agent: Agent;
  onShowThoughts: (id: string) => void;
  onShowFiles: (id: string) => void;
  onShowLogs: (id: string) => void;
  onShowSettings: (id: string) => void;
  onStart: (agent: Agent) => void;
  onStop: (agent: Agent) => void;
}

export function AgentRow({
  agent,
  onShowThoughts,
  onShowFiles,
  onShowLogs,
  onShowSettings,
  onStart,
  onStop
}: AgentRowProps) {
  const isRunning = agent.status === 'running';

  return (
    <tr style={{ borderBottom: '1px solid var(--border)' }}>
      <td style={{ padding: '14px 24px' }}>
        <Link to={`/chat/${agent.id}`} style={{ fontWeight: 500, color: 'var(--accent)' }}>
          {agent.id}
        </Link>
      </td>
      <td style={{ padding: '14px 24px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>:{agent.port}</td>
      <td style={{ padding: '14px 24px' }}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          padding: '3px 10px', borderRadius: '99px', fontSize: '12px',
          background: isRunning ? 'rgba(22, 163, 74, 0.1)' : 'rgba(154, 160, 176, 0.1)',
          color: isRunning ? 'var(--success)' : 'var(--text-muted)',
        }}>
          <span style={{
            width: '6px', height: '6px', borderRadius: '50%',
            background: isRunning ? 'var(--success)' : 'var(--text-muted)',
          }} />
          {isRunning ? 'Running' : 'Stopped'}
        </span>
      </td>
      <td style={{ padding: '14px 24px' }}>
        <span style={{ fontSize: '12px', color: isRunning ? 'var(--success)' : 'var(--error)' }}>
          {isRunning ? 'Healthy' : 'Unreachable'}
        </span>
      </td>
      <td style={{ padding: '14px 24px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Link to={`/chat/${agent.id}`} style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            padding: '5px 10px', background: 'var(--accent-dim)', color: 'var(--accent)',
            borderRadius: '6px', fontSize: '12px',
          }}>
            <MessageSquare size={12} />Chat
          </Link>

          <button onClick={() => onShowThoughts(agent.id)} style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
            border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
          }}>
            <Brain size={12} />Thoughts
          </button>

          <button onClick={() => onShowFiles(agent.id)} style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
            border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
          }}>
            <FolderOpen size={12} />Files
          </button>

          <button onClick={() => onShowLogs(agent.id)} style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
            border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
          }}>
            <FileText size={12} />Logs
          </button>

          <button onClick={() => onShowSettings(agent.id)} style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
            border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
          }}>
            <Settings2 size={12} />Settings
          </button>

          {!isRunning ? (
            <button onClick={() => onStart(agent)} style={{
              display: 'flex', alignItems: 'center', gap: '4px',
              padding: '5px 10px', background: 'rgba(22, 163, 74, 0.1)', color: 'var(--success)',
              border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
            }}>
              <Play size={12} />Start
            </button>
          ) : (
            <button onClick={() => onStop(agent)} style={{
              display: 'flex', alignItems: 'center', gap: '4px',
              padding: '5px 10px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--error)',
              border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
            }}>
              <Square size={12} />Stop
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
