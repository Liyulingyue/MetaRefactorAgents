import { Cpu, Play, Square } from 'lucide-react';
import type { Agent } from '../../types';

interface StatCardsProps {
  agents: Agent[];
}

export function StatCards({ agents }: StatCardsProps) {
  const running = agents.filter(a => a.status === 'running').length;
  
  const stats = [
    { label: 'Total Agents', value: agents.length, icon: Cpu, color: 'var(--accent)' },
    { label: 'Running', value: running, icon: Play, color: 'var(--success)' },
    { label: 'Stopped', value: agents.length - running, icon: Square, color: 'var(--text-muted)' },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
      {stats.map(({ label, value, icon: Icon, color }) => (
        <div key={label} style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: '12px', padding: '20px 24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{label}</span>
            <Icon size={16} style={{ color }} />
          </div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{value}</div>
        </div>
      ))}
    </div>
  );
}
