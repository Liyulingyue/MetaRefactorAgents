import { Activity } from 'lucide-react';
import type { Agent } from '../../types';
import { AgentRow } from './AgentRow';

interface AgentTableProps {
  agents: Agent[];
  onShowThoughts: (id: string) => void;
  onShowFiles: (id: string) => void;
  onShowLogs: (id: string) => void;
  onShowSettings: (id: string) => void;
  onStart: (agent: Agent) => void;
  onStop: (agent: Agent) => void;
  onDelete: (agent: Agent) => void;
}

export function AgentTable({
  agents,
  onShowThoughts,
  onShowFiles,
  onShowLogs,
  onShowSettings,
  onStart,
  onStop,
  onDelete
}: AgentTableProps) {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    }}>
      <div style={{
        padding: '14px 24px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: '8px',
        fontSize: '13px', fontWeight: 500,
      }}>
        <Activity size={14} style={{ color: 'var(--accent)' }} />
        Agent Registry
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-tertiary)' }}>
            {['Agent ID', 'Template', 'Port', 'Status', 'Health', 'Actions'].map(h => (
              <th key={h} style={{
                padding: '12px 24px', textAlign: 'left',
                fontSize: '11px', fontWeight: 500, color: 'var(--text-muted)',
                textTransform: 'uppercase', letterSpacing: '0.05em',
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {agents.map(agent => (
            <AgentRow
              key={agent.id}
              agent={agent}
              onShowThoughts={onShowThoughts}
              onShowFiles={onShowFiles}
              onShowLogs={onShowLogs}
              onShowSettings={onShowSettings}
              onStart={onStart}
              onStop={onStop}
              onDelete={onDelete}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
