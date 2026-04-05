import React, { useState, useEffect } from 'react';
import { Activity, Trash2, RefreshCw, Radio } from 'lucide-react';

interface OccupiedPort {
  port: number;
  pid: number | null;
  process: string;
  description: string;
  agent_id: string | null;
}

export default function PortViewer() {
  const [ports, setPorts] = useState<OccupiedPort[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPorts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/system/ports');
      if (!response.ok) throw new Error('Failed to fetch ports');
      const data = await response.data || await response.json();
      setPorts(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const killProcess = async (pid: number) => {
    try {
      const response = await fetch(`/api/system/kill/${pid}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to kill process');
      alert(`Process ${pid} terminated.`);
      fetchPorts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  useEffect(() => {
    fetchPorts();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <h1 style={{ fontSize: '24px', fontWeight: 600 }}>Port Viewer</h1>
        <button 
          onClick={fetchPorts}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} color="var(--accent)" />
          <span style={{ fontWeight: 500 }}>Occupied Ports (8000-8100)</span>
        </div>
        
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ textAlign: 'left', background: 'rgba(0,0,0,0.02)', borderBottom: '1px solid var(--border)' }}>
              <th style={{ padding: '12px 20px', fontWeight: 500, color: 'var(--text-muted)' }}>Port</th>
              <th style={{ padding: '12px 20px', fontWeight: 500, color: 'var(--text-muted)' }}>Description</th>
              <th style={{ padding: '12px 20px', fontWeight: 500, color: 'var(--text-muted)' }}>Process</th>
              <th style={{ padding: '12px 20px', fontWeight: 500, color: 'var(--text-muted)' }}>PID</th>
              <th style={{ padding: '12px 20px', fontWeight: 500, color: 'var(--text-muted)', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {ports.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No active ports found in specified range.
                </td>
              </tr>
            ) : (
              ports.map((p) => (
                <tr key={p.port} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 20px', fontWeight: 600 }}>:{p.port}</td>
                  <td style={{ padding: '12px 20px' }}>
                    <div style={{ 
                      color: p.agent_id ? 'var(--accent)' : 'var(--text-secondary)',
                      fontWeight: p.agent_id ? 500 : 400 
                    }}>
                      {p.description}
                    </div>
                  </td>
                  <td style={{ padding: '12px 20px' }}>
                    <code style={{ background: 'var(--bg-tertiary)', padding: '2px 4px', borderRadius: '4px', fontSize: '13px' }}>
                      {p.process}
                    </code>
                  </td>
                  <td style={{ padding: '12px 20px', color: 'var(--text-muted)', fontSize: '13px' }}>
                    {p.pid || 'N/A'}
                  </td>
                  <td style={{ padding: '12px 20px', textAlign: 'right' }}>
                    {p.pid && p.port !== 8000 && (
                      <button 
                        onClick={() => killProcess(p.pid!)}
                        style={{
                          background: 'rgba(ef, 68, 68, 0.1)',
                          color: '#ef4444',
                          border: 'none',
                          padding: '6px 10px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '12px'
                        }}
                      >
                        <Trash2 size={14} />
                        Kill
                      </button>
                    )}
                    {p.port === 8000 && (
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>(Gateway)</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {error && (
        <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '6px', fontSize: '13px' }}>
          Error: {error}
        </div>
      )}
    </div>
  );
}