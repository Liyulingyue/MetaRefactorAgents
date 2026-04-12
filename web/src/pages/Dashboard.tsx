import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, PlusCircle, Cpu, Share2 } from 'lucide-react';
import { agentApi } from '../api/client';
import type { Agent } from '../types';
import { StatCards } from '../components/dashboard/StatCards';
import { AgentTable } from '../components/dashboard/AgentTable';
import { LogsModal } from '../components/dashboard/LogsModal';
import { ConfigModal } from '../components/dashboard/ConfigModal';
import { FilesModal } from '../components/dashboard/FilesModal';

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedLogs, setSelectedLogs] = useState<{ id: string, content: string, title: string } | null>(null);
  const [selectedAgentConfig, setSelectedAgentConfig] = useState<{ id: string, allow_cors: boolean } | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<{ id: string, files: any[], isShared: boolean } | null>(null);

  const fetchAgents = async () => {
    try {
      const list = await agentApi.listAgents();
      const withStatus = await Promise.all(
        list.map(async (a) => {
          // 使用 agentId 进行通过网关的健康检查
          const healthy = await agentApi.checkAgentHealth(a.id);
          return { ...a, status: healthy ? 'running' : 'stopped' } as Agent;
        })
      );
      setAgents(withStatus);
    } catch (e) {
      console.error('Failed to fetch agents', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchAgents(); }, []);

  const handleRefresh = () => { setRefreshing(true); fetchAgents(); };
  const handleStart = async (agent: Agent) => {
    try { await agentApi.startAgent(agent.id, agent.port); await fetchAgents(); }
    catch (e) { console.error(e); }
  };

  const handleStop = async (agent: Agent) => {
    try { await agentApi.stopAgent(agent.id); await fetchAgents(); }
    catch (e) { console.error(e); }
  };

  const handleDelete = async (agent: Agent) => {
    try { await agentApi.deleteAgent(agent.id); await fetchAgents(); }
    catch (e) { console.error(e); }
  };

  const handleShowLogs = async (agentId: string) => {
    try {
      const logs = await agentApi.getAgentLogs(agentId);
      setSelectedLogs({ id: agentId, content: logs, title: 'Logs' });
    } catch (e) {
      console.error(e);
      alert("Failed to load logs");
    }
  };

  const handleShowThoughts = async (agentId: string) => {
    try {
      const thoughts = await agentApi.getAgentThoughts(agentId);
      setSelectedLogs({ id: agentId, content: thoughts, title: 'Thoughts' });
    } catch (e) {
      console.error(e);
      alert("Failed to load thoughts");
    }
  };

  const handleShowSettings = async (agentId: string) => {
    try {
      const config = await agentApi.getAgentConfig(agentId);
      setSelectedAgentConfig({ id: agentId, allow_cors: config.allow_cors });
    } catch (e) {
      console.error(e);
    }
  };

  const handleShowFiles = async (agentId: string) => {
    try {
      const files = await agentApi.getAgentFiles(agentId);
      setSelectedFiles({ id: agentId, files, isShared: false });
    } catch (e) {
      console.error(e);
      alert("Failed to load files");
    }
  };

  const handleUpdateConfig = async (allow_cors: boolean) => {
    if (!selectedAgentConfig) return;
    try {
      await agentApi.updateAgentConfig(selectedAgentConfig.id, { allow_cors });
      setSelectedAgentConfig({ ...selectedAgentConfig, allow_cors });
    } catch (e) {
      console.error(e);
    }
  };

  const running = agents.filter(a => a.status === 'running').length;

  return (
    <div style={{ padding: '24px', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Monitor and manage your agent fleet</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <Link to="/shared" style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', background: 'var(--bg-secondary)', color: 'var(--accent)',
            border: '1px solid var(--accent-dim)', borderRadius: '8px', fontSize: '13px', cursor: 'pointer', textDecoration: 'none',
          }}>
            <Share2 size={14} /> Shared Files
          </Link>
          <Link to="/create" style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', background: 'var(--accent)', color: 'white',
            borderRadius: '8px', fontSize: '13px', fontWeight: 500,
            boxShadow: '0 1px 3px rgba(99,102,241,0.3)',
          }}>
            <PlusCircle size={14} />New Agent
          </Link>
          <button onClick={handleRefresh} style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
            border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
          }}>
            <RefreshCw size={14} style={refreshing ? { animation: 'spin 1s linear infinite' } : {}} />
            Refresh
          </button>
        </div>
      </div>

      <StatCards agents={agents} />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Loading agents...</div>
      ) : agents.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px',
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
          <Cpu size={40} style={{ color: 'var(--text-muted)', marginBottom: '12px' }} />
          <div style={{ color: 'var(--text-muted)' }}>No agents found. Create one to get started.</div>
          <Link to="/create" style={{
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            marginTop: '16px', padding: '8px 20px',
            background: 'var(--accent)', color: 'white', borderRadius: '8px', fontSize: '13px',
            boxShadow: '0 1px 3px rgba(99,102,241,0.3)',
          }}>
            <PlusCircle size={14} /> Create Agent
          </Link>
        </div>
      ) : (
        <AgentTable
          agents={agents}
          onShowThoughts={handleShowThoughts}
          onShowFiles={handleShowFiles}
          onShowLogs={handleShowLogs}
          onShowSettings={handleShowSettings}
          onStart={handleStart}
          onStop={handleStop}
          onDelete={handleDelete}
        />
      )}

      {selectedLogs && (
        <LogsModal
          id={selectedLogs.id}
          title={selectedLogs.title}
          content={selectedLogs.content}
          onClose={() => setSelectedLogs(null)}
        />
      )}

      {selectedAgentConfig && (
        <ConfigModal
          id={selectedAgentConfig.id}
          allow_cors={selectedAgentConfig.allow_cors}
          onClose={() => setSelectedAgentConfig(null)}
          onUpdate={handleUpdateConfig}
        />
      )}

      {selectedFiles && (
        <FilesModal
          id={selectedFiles.id}
          files={selectedFiles.files}
          isShared={selectedFiles.isShared}
          onClose={() => setSelectedFiles(null)}
        />
      )}
    </div>
  );
}
