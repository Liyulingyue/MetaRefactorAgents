import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { GitBranch, Play, MessageSquare } from 'lucide-react';
import { agentApi } from '../api/client';
import type { Agent, LineageNode } from '../types';

export default function Lineage() {
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    agentApi.listAgents().then(async (list) => {
      const withStatus = await Promise.all(
        list.map(async (a) => {
          const healthy = await agentApi.checkAgentHealth(a.id);
          return { ...a, status: healthy ? 'running' : 'stopped' } as Agent;
        })
      );
      setAgents(withStatus);
    });
  }, []);

  const nodes: LineageNode[] = agents.map(a => ({
    id: a.id,
    name: a.id,
    status: a.status || 'unknown',
    port: a.port,
  }));

  return (
    <div style={{ padding: '24px', height: '100%' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1>Agent Lineage</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Visualize the agent family tree and relationships</p>
      </div>

      {agents.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px',
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
          <GitBranch size={40} style={{ color: 'var(--text-muted)', marginBottom: '12px' }} />
          <div style={{ color: 'var(--text-muted)' }}>No agents yet. Create one to see the lineage.</div>
        </div>
      ) : (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '32px',
          overflowX: 'auto', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '32px', minWidth: 'fit-content' }}>
            {nodes.map((node) => (
              <div key={node.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0' }}>
                <div style={{
                  position: 'relative',
                  width: '160px',
                  padding: '16px',
                  background: 'var(--bg-secondary)',
                  border: `2px solid ${node.status === 'running' ? 'var(--success)' : 'var(--border)'}`,
                  borderRadius: '12px',
                  textAlign: 'center',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                }}>
                  <div style={{
                    position: 'absolute', top: '-1px', right: '-1px',
                    width: '10px', height: '10px', borderRadius: '50%',
                    background: node.status === 'running' ? 'var(--success)' : 'var(--text-muted)',
                    border: '2px solid var(--bg-card)',
                  }} />
                  <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px' }}>{node.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    :{node.port}
                  </div>
                  <div style={{
                    marginTop: '10px', display: 'flex', gap: '6px', justifyContent: 'center',
                  }}>
                    <Link to={`/chat/${node.id}`} style={{
                      display: 'flex', alignItems: 'center', gap: '4px',
                      padding: '4px 8px', background: 'var(--accent-dim)', color: 'var(--accent)',
                      borderRadius: '6px', fontSize: '11px',
                    }}>
                      <MessageSquare size={10} />
                      Chat
                    </Link>
                    {node.status !== 'running' && (
                      <button style={{
                        display: 'flex', alignItems: 'center', gap: '4px',
                        padding: '4px 8px', background: 'rgba(22, 163, 74, 0.1)', color: 'var(--success)',
                        border: 'none', borderRadius: '6px', fontSize: '11px', cursor: 'pointer',
                      }}>
                        <Play size={10} />
                        Start
                      </button>
                    )}
                  </div>
                </div>
                <div style={{
                  width: '2px', height: '32px',
                  background: 'linear-gradient(to bottom, var(--border), transparent)',
                }} />
                <div style={{
                  fontSize: '11px', color: 'var(--text-muted)', padding: '2px 10px',
                  border: '1px solid var(--border)', borderRadius: '99px',
                  background: 'var(--bg-tertiary)',
                }}>
                  v1.0
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{
        marginTop: '24px', padding: '16px',
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}>
        <div style={{ fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>Lineage Info</div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.8 }}>
          <p>This dashboard shows the agent family tree. Each node represents an agent process.</p>
          <p style={{ marginTop: '6px' }}>
            Agents can spawn children through self-evolution. The current system starts with two root agents
            (Agent-01, Agent-02) as defined in the gateway registry.
          </p>
        </div>
      </div>
    </div>
  );
}
