import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Play, Square, RefreshCw, MessageSquare, Activity, PlusCircle, Cpu, FileText, X, Settings2, Globe, Shield, Brain, FolderOpen, Download, Share2 } from 'lucide-react';
import { agentApi } from '../api/client';
import type { Agent } from '../types';

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

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {[
          { label: 'Total Agents', value: agents.length, icon: Cpu, color: 'var(--accent)' },
          { label: 'Running', value: running, icon: Play, color: 'var(--success)' },
          { label: 'Stopped', value: agents.length - running, icon: Square, color: 'var(--text-muted)' },
        ].map(({ label, value, icon: Icon, color }) => (
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
                {['Agent ID', 'Port', 'Status', 'Health', 'Actions'].map(h => (
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
                <tr key={agent.id} style={{ borderBottom: '1px solid var(--border)' }}>
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
                      background: agent.status === 'running' ? 'rgba(22, 163, 74, 0.1)' : 'rgba(154, 160, 176, 0.1)',
                      color: agent.status === 'running' ? 'var(--success)' : 'var(--text-muted)',
                    }}>
                      <span style={{
                        width: '6px', height: '6px', borderRadius: '50%',
                        background: agent.status === 'running' ? 'var(--success)' : 'var(--text-muted)',
                      }} />
                      {agent.status === 'running' ? 'Running' : 'Stopped'}
                    </span>
                  </td>
                  <td style={{ padding: '14px 24px' }}>
                    <span style={{ fontSize: '12px', color: agent.status === 'running' ? 'var(--success)' : 'var(--error)' }}>
                      {agent.status === 'running' ? 'Healthy' : 'Unreachable'}
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

                      <button onClick={() => handleShowThoughts(agent.id)} style={{
                        display: 'flex', alignItems: 'center', gap: '4px',
                        padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                        border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
                      }}>
                        <Brain size={12} />Thoughts
                      </button>

                      <button onClick={() => handleShowFiles(agent.id)} style={{
                        display: 'flex', alignItems: 'center', gap: '4px',
                        padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                        border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
                      }}>
                        <FolderOpen size={12} />Files
                      </button>

                      <button onClick={() => handleShowLogs(agent.id)} style={{
                        display: 'flex', alignItems: 'center', gap: '4px',
                        padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                        border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
                      }}>
                        <FileText size={12} />Logs
                      </button>

                      <button onClick={() => handleShowSettings(agent.id)} style={{
                        display: 'flex', alignItems: 'center', gap: '4px',
                        padding: '5px 10px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                        border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
                      }}>
                        <Settings2 size={12} />Settings
                      </button>

                      {agent.status !== 'running' ? (
                        <button onClick={() => handleStart(agent)} style={{
                          display: 'flex', alignItems: 'center', gap: '4px',
                          padding: '5px 10px', background: 'rgba(22, 163, 74, 0.1)', color: 'var(--success)',
                          border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
                        }}>
                          <Play size={12} />Start
                        </button>
                      ) : (
                        <button onClick={() => handleStop(agent)} style={{
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
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedAgentConfig && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)', zIndex: 1000,
        }}>
          <div style={{
            background: 'var(--bg-card)', width: '400px',
            borderRadius: '12px', display: 'flex', flexDirection: 'column',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', overflow: 'hidden',
          }}>
            <div style={{
              padding: '16px 24px', borderBottom: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>Settings: {selectedAgentConfig.id}</h3>
              <button 
                onClick={() => setSelectedAgentConfig(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>
            <div style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ 
                    width: '36px', height: '36px', borderRadius: '8px', 
                    background: selectedAgentConfig.allow_cors ? 'rgba(99,102,241,0.1)' : 'var(--bg-tertiary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    {selectedAgentConfig.allow_cors ? <Globe size={18} style={{ color: 'var(--accent)' }} /> : <Shield size={18} style={{ color: 'var(--text-muted)' }} />}
                  </div>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 500 }}>Allow CORS (Direct Connect)</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Enable browser access without gateway proxy</div>
                  </div>
                </div>
                <button 
                  onClick={() => handleUpdateConfig(!selectedAgentConfig.allow_cors)}
                  style={{
                    width: '40px', height: '20px', borderRadius: '10px',
                    background: selectedAgentConfig.allow_cors ? 'var(--accent)' : 'var(--text-muted)',
                    position: 'relative', border: 'none', cursor: 'pointer', transition: '0.3s'
                  }}
                >
                  <div style={{
                    width: '16px', height: '16px', borderRadius: '50%', background: 'white',
                    position: 'absolute', top: '2px', left: selectedAgentConfig.allow_cors ? '22px' : '2px',
                    transition: '0.3s'
                  }} />
                </button>
              </div>
              <div style={{ 
                fontSize: '11px', color: 'var(--text-muted)', background: 'var(--bg-tertiary)', 
                padding: '12px', borderRadius: '8px', border: '1px solid var(--border)'
              }}>
                <RefreshCw size={10} style={{ marginRight: '6px' }} />
                Requires restart to apply changes.
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedFiles && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)', zIndex: 1000,
        }}>
          <div style={{
            background: 'var(--bg-card)', width: '600px', maxHeight: '80vh',
            borderRadius: '12px', display: 'flex', flexDirection: 'column',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', overflow: 'hidden',
          }}>
            <div style={{
              padding: '16px 24px', borderBottom: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <h3 style={{ margin: 0, fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FolderOpen size={18} /> {selectedFiles.isShared ? 'Shared Files' : `Files: ${selectedFiles.id}`}
              </h3>
              <button 
                onClick={() => setSelectedFiles(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>
            <div style={{ padding: '16px', overflowY: 'auto', flex: 1 }}>
              {selectedFiles.files.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No files found in this directory.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px' }}>
                  {selectedFiles.files.map((file: any, idx) => (
                    <div key={idx} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '10px 16px', background: 'var(--bg-tertiary)', borderRadius: '8px',
                      border: '1px solid var(--border)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                        <FileText size={18} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontSize: '14px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {file.name}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            {(file.size / 1024).toFixed(1)} KB • {new Date(file.mtime * 1000).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <a 
                        href={selectedFiles.isShared ? agentApi.getSharedDownloadUrl(file.path) : agentApi.getDownloadUrl(selectedFiles.id, file.path)}
                        download
                        style={{
                          display: 'flex', alignItems: 'center', gap: '4px',
                          padding: '6px 12px', background: 'var(--accent-dim)', color: 'var(--accent)',
                          borderRadius: '6px', fontSize: '12px', textDecoration: 'none', fontWeight: 500
                        }}
                      >
                        <Download size={14} /> Download
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {selectedLogs && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)', zIndex: 1000,
        }}>
          <div style={{
            background: 'var(--bg-card)', width: '80%', maxHeight: '80%',
            borderRadius: '12px', display: 'flex', flexDirection: 'column',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', overflow: 'hidden',
          }}>
            <div style={{
              padding: '16px 24px', borderBottom: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {selectedLogs.title === 'Thoughts' ? <Brain size={16} style={{ color: 'var(--accent)' }} /> : <FileText size={16} style={{ color: 'var(--accent)' }} />}
                <h3 style={{ margin: 0, fontSize: '16px' }}>{selectedLogs.title}: {selectedLogs.id}</h3>
              </div>
              <button 
                onClick={() => setSelectedLogs(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>
            <div style={{
              padding: '24px', overflowY: 'auto', flex: 1,
              background: '#0f172a', color: '#e2e8f0',
              fontFamily: 'monospace', fontSize: '12px', whiteSpace: 'pre-wrap',
            }}>
              {selectedLogs.content || `No ${selectedLogs.title.toLowerCase()} available.`}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
