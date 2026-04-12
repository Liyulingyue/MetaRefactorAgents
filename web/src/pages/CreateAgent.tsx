import { useState, useEffect } from 'react';
import { PlusCircle, CheckCircle, AlertCircle, Terminal } from 'lucide-react';
import { agentApi } from '../api/client';

const BASE_PORT = 8001;

export default function CreateAgent() {
  const [agentId, setAgentId] = useState('');
  const [template, setTemplate] = useState('default');
  const [templates, setTemplates] = useState<string[]>([]);
  const [status, setStatus] = useState<'idle' | 'creating' | 'starting' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  useEffect(() => {
    agentApi.listTemplates().then(data => {
      setTemplates(data.map(t => t.name));
      if (data.length > 0) {
        setTemplate(data[0].name);
      }
    });
  }, []);

  const handleCreate = async () => {
    if (!agentId.trim()) return;
    setStatus('creating');
    setMessage('');

    try {
      await agentApi.createAgent({ agent_id: agentId, template });
      setStatus('starting');

      const port = BASE_PORT + Math.floor(Math.random() * 100);
      await agentApi.startAgent(agentId, port);

      setStatus('success');
      setMessage(`Agent ${agentId} created and started on port ${port}`);
    } catch (e: unknown) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Unknown error occurred');
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1>Create Agent</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Initialize a new agent workspace from a template</p>
      </div>

      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: 500 }}>
            Agent ID
          </label>
          <input
            type="text"
            value={agentId}
            onChange={e => setAgentId(e.target.value)}
            placeholder="e.g. Agent-03"
            style={{
              width: '100%', padding: '10px 14px', background: 'var(--bg-tertiary)',
              color: 'var(--text-primary)', border: '1px solid var(--border)',
              borderRadius: '8px', fontSize: '13px', outline: 'none',
            }}
            onFocus={e => (e.target.style.borderColor = 'var(--accent)')}
            onBlur={e => (e.target.style.borderColor = 'var(--border)')}
          />
          <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
            Unique identifier for this agent. Will be used as the workspace directory name.
          </div>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: 500 }}>
            Template
          </label>
          <select
            value={template}
            onChange={e => setTemplate(e.target.value)}
            style={{
              width: '100%', padding: '10px 14px', background: 'var(--bg-tertiary)',
              color: 'var(--text-primary)', border: '1px solid var(--border)',
              borderRadius: '8px', fontSize: '13px', outline: 'none',
            }}
          >
            {templates.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
            The template defines the agent's initial capabilities and toolset.
          </div>
        </div>

        {status === 'success' && (
          <div style={{
            padding: '12px 16px', borderRadius: '8px', marginBottom: '20px',
            background: 'rgba(22, 163, 74, 0.1)', border: '1px solid rgba(22, 163, 74, 0.3)',
            display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--success)',
          }}>
            <CheckCircle size={16} />
            {message}
          </div>
        )}

        {status === 'error' && (
          <div style={{
            padding: '12px 16px', borderRadius: '8px', marginBottom: '20px',
            background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.3)',
            display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--error)',
          }}>
            <AlertCircle size={16} />
            {message}
          </div>
        )}

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleCreate}
            disabled={!agentId.trim() || status === 'creating' || status === 'starting'}
            style={{
              padding: '10px 24px', background: agentId.trim() ? 'var(--accent)' : 'var(--bg-tertiary)',
              color: agentId.trim() ? 'white' : 'var(--text-muted)',
              border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 500,
              cursor: agentId.trim() ? 'pointer' : 'default',
              display: 'flex', alignItems: 'center', gap: '8px',
              boxShadow: agentId.trim() ? '0 1px 3px rgba(99,102,241,0.3)' : 'none',
            }}
          >
            {status === 'creating' || status === 'starting' ? (
              <>Creating...</>
            ) : (
              <>
                <PlusCircle size={14} />
                Create & Start Agent
              </>
            )}
          </button>
          {(status === 'success' || status === 'error') && (
            <button
              onClick={() => { setStatus('idle'); setMessage(''); setAgentId(''); }}
              style={{
                padding: '10px 20px', background: 'var(--bg-tertiary)',
                color: 'var(--text-secondary)', border: '1px solid var(--border)',
                borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
              }}
            >
              Reset
            </button>
          )}
        </div>
      </div>

      <div style={{
        marginTop: '24px', padding: '16px',
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '13px', fontWeight: 500 }}>
          <Terminal size={14} style={{ color: 'var(--accent)' }} />
          What happens next?
        </div>
        <ol style={{ color: 'var(--text-muted)', fontSize: '12px', paddingLeft: '20px', lineHeight: 2 }}>
          <li>A new workspace directory is created under <code style={{ color: 'var(--text-secondary)', background: 'var(--bg-tertiary)', padding: '1px 6px', borderRadius: '4px' }}>workspace/{'{agent_id}'}</code></li>
          <li>The selected template is cloned into the workspace</li>
          <li>A new Python process is spawned on an available port</li>
          <li>The agent becomes ready to receive chat requests via the gateway</li>
        </ol>
      </div>
    </div>
  );
}
