import { useState, useEffect } from 'react';
import { RefreshCw, Download, RotateCcw, Trash2, ShieldPlus, FileArchive, Clock, HardDrive, Archive, FolderOpen, CheckSquare, Square, LayoutTemplate, Zap, Info, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileTree } from '../components/FileTree';
import { agentApi, backupApi } from '../api/client';

interface Backup {
  name: string;
  size: number;
  created_at: string;
  path: string;
  agent_id: string;
}

interface AgentFile {
  name: string;
  path: string;
  size: number;
  mtime: number;
}

interface Template {
  name: string;
  description: string;
  path: string;
  replace: string[];
  exclude: string[];
}

export default function BackupManager() {
  const [agents, setAgents] = useState<string[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [agentFiles, setAgentFiles] = useState<AgentFile[]>([]);
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [backupName, setBackupName] = useState('');
  const [backups, setBackups] = useState<Backup[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [autoBackup, setAutoBackup] = useState(true);
  const [applyLoading, setApplyLoading] = useState(false);
  const [readmeModal, setReadmeModal] = useState<{ name: string; content: string } | null>(null);

  const fetchAgents = async () => {
    try {
      const data = await agentApi.listAgents();
      setAgents(data.map(a => a.id));
      if (data.length > 0 && !selectedAgent) {
        setSelectedAgent(data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch agents', err);
    }
  };

  const fetchFiles = async (agentId: string) => {
    setLoadingFiles(true);
    try {
      const data = await agentApi.getAgentFiles(agentId);
      setAgentFiles(data);
      setSelectedPaths(new Set());
    } catch (err) {
      console.error('Failed to fetch files', err);
    } finally {
      setLoadingFiles(false);
    }
  };

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const data = await backupApi.listBackups();
      setBackups(data);
    } catch (err) {
      console.error('Failed to fetch backups', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAgents(); fetchBackups(); fetchTemplates(); }, []);

  const fetchTemplates = async () => {
    try {
      const data = await backupApi.listTemplates();
      setTemplates(data);
      if (data.length > 0) setSelectedTemplate(data[0].name);
    } catch (err) {
      console.error('Failed to fetch templates', err);
    }
  };

  const fetchReadme = async (tplName: string) => {
    try {
      const data = await backupApi.listTemplates();
      const tpl = data.find((t: Template) => t.name === tplName);
      if (tpl) setReadmeModal({ name: tpl.name, content: tpl.description || '无说明文档' });
    } catch (err) {
      console.error('Failed to fetch readme', err);
    }
  };

  useEffect(() => {
    if (selectedAgent) fetchFiles(selectedAgent);
  }, [selectedAgent]);

  const toggleFile = (path: string) => {
    setSelectedPaths(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedPaths.size === agentFiles.length) {
      setSelectedPaths(new Set());
    } else {
      setSelectedPaths(new Set(agentFiles.map(f => f.path)));
    }
  };

  const handleCreateBackup = async () => {
    if (!selectedAgent) {
      setMessage({ type: 'error', text: '请先选择一个 Agent' });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const filePaths = selectedPaths.size > 0 && selectedPaths.size < agentFiles.length
        ? Array.from(selectedPaths) : undefined;
      await backupApi.createBackup(selectedAgent, backupName || undefined, filePaths);
      setBackupName('');
      setSelectedPaths(new Set());
      setMessage({ type: 'success', text: '备份创建成功' });
      fetchBackups();
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.response?.data?.detail || '创建备份失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (backup: Backup) => {
    if (!window.confirm(`确定要从备份 ${backup.name} 恢复到 Agent ${backup.agent_id} 吗？`)) return;
    setLoading(true);
    setMessage(null);
    try {
      await backupApi.restoreBackup(backup.name, backup.agent_id);
      setMessage({ type: 'success', text: `已恢复到 ${backup.agent_id}` });
      if (selectedAgent === backup.agent_id) fetchFiles(backup.agent_id);
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.response?.data?.detail || '恢复失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedAgent || !selectedTemplate) return;
    const msg = autoBackup
      ? `将自动创建备份后应用模板 ${selectedTemplate} 到 ${selectedAgent}，继续？`
      : `将直接应用模板 ${selectedTemplate} 到 ${selectedAgent}（不创建备份），继续？`;
    if (!window.confirm(msg)) return;
    setApplyLoading(true);
    setMessage(null);
    try {
      await backupApi.applyTemplate(selectedAgent, selectedTemplate, autoBackup);
      setMessage({ type: 'success', text: `模板 ${selectedTemplate} 已应用到 ${selectedAgent}` });
      fetchBackups();
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.response?.data?.detail || '应用模板失败' });
    } finally {
      setApplyLoading(false);
    }
  };

  const handleDelete = async (backup: Backup) => {
    if (!window.confirm(`确定要删除备份 ${backup.name} 吗？`)) return;
    setLoading(true);
    try {
      await backupApi.deleteBackup(backup.name, backup.agent_id);
      setMessage({ type: 'success', text: '备份已删除' });
      fetchBackups();
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.response?.data?.detail || '删除失败' });
    } finally {
      setLoading(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
  };

  const agentBackups = backups.filter(b => b.agent_id === selectedAgent);
  const otherBackups = backups.filter(b => b.agent_id !== selectedAgent);

  return (
    <>
      {readmeModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000,
        }} onClick={() => setReadmeModal(null)}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: '16px', width: '600px', maxWidth: '90vw',
            maxHeight: '80vh', display: 'flex', flexDirection: 'column',
            boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
          }} onClick={e => e.stopPropagation()}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px 20px', borderBottom: '1px solid var(--border)',
            }}>
              <div style={{ fontSize: '15px', fontWeight: 600 }}>{readmeModal.name}</div>
              <button onClick={() => setReadmeModal(null)} style={{
                border: 'none', background: 'transparent', cursor: 'pointer',
                color: 'var(--text-muted)', display: 'flex', padding: '4px',
              }}>
                <X size={18} />
              </button>
            </div>
            <div style={{
              padding: '20px', overflow: 'auto', flex: 1,
              fontSize: '13px', lineHeight: 1.7, color: 'var(--text-primary)',
            }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {readmeModal.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}

    <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Archive size={22} style={{ color: 'var(--accent)' }} />
            Agent 备份与恢复
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>选择 Agent 并备份其生成的文件</p>
        </div>
        <button onClick={() => { fetchBackups(); fetchAgents(); }} style={{
          padding: '8px', background: 'var(--bg-secondary)', border: '1px solid var(--border)',
          borderRadius: '8px', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex',
        }} title="刷新列表">
          <RefreshCw size={16} style={loading ? { animation: 'spin 1s linear infinite' } : {}} />
        </button>
      </div>

      {message && (
        <div style={{
          marginBottom: '16px', padding: '12px 16px', borderRadius: '8px',
          background: message.type === 'success' ? 'rgba(22,163,74,0.1)' : 'rgba(220,38,38,0.1)',
          color: message.type === 'success' ? 'var(--success)' : 'var(--error)',
          border: `1px solid ${message.type === 'success' ? 'rgba(22,163,74,0.2)' : 'rgba(220,38,38,0.2)'}`,
          fontSize: '13px',
        }}>
          {message.text}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px', alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
            padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '14px', fontWeight: 500 }}>
              <FolderOpen size={14} style={{ color: 'var(--accent)' }} />
              选择 Agent
            </div>
            <select
              value={selectedAgent}
              onChange={e => setSelectedAgent(e.target.value)}
              style={{
                width: '100%', padding: '8px 12px', background: 'var(--bg-tertiary)',
                color: 'var(--text-primary)', border: '1px solid var(--border)',
                borderRadius: '8px', fontSize: '13px', outline: 'none', cursor: 'pointer',
              }}
            >
              {agents.length === 0 && <option value="">-- 无可用 Agent --</option>}
              {agents.map(id => <option key={id} value={id}>{id}</option>)}
            </select>
          </div>

          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
            padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: 500 }}>
                <ShieldPlus size={14} style={{ color: 'var(--accent)' }} />
                新建备份
              </div>
              {agentFiles.length > 0 && (
                <button onClick={toggleAll} style={{
                  display: 'flex', alignItems: 'center', gap: '4px',
                  fontSize: '11px', color: 'var(--text-muted)', background: 'none',
                  border: 'none', cursor: 'pointer', padding: '2px 4px',
                }}>
                  {selectedPaths.size === agentFiles.length ? <CheckSquare size={12} /> : <Square size={12} />}
                  全选
                </button>
              )}
            </div>

            {loadingFiles ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '12px' }}>
                <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} />
                加载文件...
              </div>
            ) : agentFiles.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                {selectedAgent ? '该 Agent 无可备份文件' : '请先选择 Agent'}
              </div>
            ) : (
              <div style={{ maxHeight: '200px', overflow: 'auto', marginBottom: '12px' }}>
                <FileTree
                  files={agentFiles}
                  onSelect={() => {}}
                  selectedPath=""
                  multiSelect={true}
                  selectedPaths={selectedPaths}
                  onToggle={toggleFile}
                />
              </div>
            )}

            {selectedPaths.size > 0 && selectedPaths.size < agentFiles.length && (
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                已选 {selectedPaths.size} / {agentFiles.length} 个文件
              </div>
            )}

            <input
              type="text"
              placeholder="备份名称 (可选)"
              value={backupName}
              onChange={e => setBackupName(e.target.value)}
              style={{
                width: '100%', padding: '8px 12px', marginBottom: '8px',
                background: 'var(--bg-tertiary)', color: 'var(--text-primary)',
                border: '1px solid var(--border)', borderRadius: '8px',
                fontSize: '12px', outline: 'none', boxSizing: 'border-box',
              }}
            />
            <button
              disabled={loading || !selectedAgent || agentFiles.length === 0}
              onClick={handleCreateBackup}
              style={{
                width: '100%', padding: '8px', background: 'var(--accent)', color: 'white',
                border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: 500,
                cursor: (loading || !selectedAgent || agentFiles.length === 0) ? 'not-allowed' : 'pointer',
                opacity: (loading || !selectedAgent || agentFiles.length === 0) ? 0.6 : 1,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
              }}
            >
              {loading ? <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <HardDrive size={12} />}
              创建备份 ({selectedPaths.size > 0 && selectedPaths.size < agentFiles.length ? `${selectedPaths.size} 个文件` : '全部文件'})
            </button>
          </div>

          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
            padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', fontSize: '14px', fontWeight: 500 }}>
              <LayoutTemplate size={14} style={{ color: 'var(--accent)' }} />
              应用模板
            </div>

            <select
              value={selectedTemplate}
              onChange={e => setSelectedTemplate(e.target.value)}
              disabled={!selectedAgent}
              style={{
                width: '100%', padding: '8px 12px', marginBottom: '10px',
                background: 'var(--bg-tertiary)', color: 'var(--text-primary)',
                border: '1px solid var(--border)', borderRadius: '8px',
                fontSize: '13px', outline: 'none', cursor: 'pointer',
              }}
            >
              {templates.length === 0 && <option value="">-- 无可用模板 --</option>}
              {templates.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
            </select>

            {selectedTemplate && (
              <button
                onClick={() => fetchReadme(selectedTemplate)}
                style={{
                  width: '100%', padding: '6px 8px', marginBottom: '10px',
                  background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
                  border: '1px solid var(--border)', borderRadius: '8px',
                  fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px',
                }}
              >
                <Info size={11} /> 查看说明
              </button>
            )}

            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '10px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoBackup}
                onChange={e => setAutoBackup(e.target.checked)}
              />
              应用前自动创建备份
            </label>

            <button
              disabled={applyLoading || !selectedAgent || !selectedTemplate}
              onClick={handleApplyTemplate}
              style={{
                width: '100%', padding: '8px',
                background: 'rgba(234,88,12,0.1)', color: '#ea580c',
                border: '1px solid rgba(234,88,12,0.25)', borderRadius: '8px',
                fontSize: '12px', fontWeight: 500, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                opacity: (applyLoading || !selectedAgent || !selectedTemplate) ? 0.6 : 1,
              }}
            >
              {applyLoading ? <RefreshCw size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Zap size={12} />}
              升级
            </button>
          </div>
        </div>

        <div>
          <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px', fontWeight: 500 }}>
            <FileArchive size={16} style={{ color: 'var(--accent)' }} />
            {selectedAgent ? `${selectedAgent} 的备份` : '所有备份'} ({selectedAgent ? agentBackups.length : backups.length})
          </div>

          {backups.length === 0 && !loading ? (
            <div style={{
              textAlign: 'center', padding: '60px',
              background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}>
              <Archive size={40} style={{ color: 'var(--text-muted)', marginBottom: '12px', opacity: 0.4 }} />
              <div style={{ color: 'var(--text-muted)' }}>暂无备份文件</div>
            </div>
          ) : (
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
              overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}>
              {(selectedAgent ? agentBackups : backups).map((backup, idx) => (
                <div key={backup.path} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '14px 20px',
                  borderBottom: idx < (selectedAgent ? agentBackups : backups).length - 1 ? '1px solid var(--border)' : 'none',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0, flex: 1 }}>
                    <div style={{
                      width: '40px', height: '40px', background: 'var(--accent-dim)', borderRadius: '10px',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                      <FileArchive size={18} style={{ color: 'var(--accent)' }} />
                    </div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {backup.name}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '2px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'var(--bg-tertiary)', padding: '1px 6px', borderRadius: '4px' }}>
                          {backup.agent_id}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                          <Clock size={10} /> {formatDate(backup.created_at)}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                          <HardDrive size={10} /> {formatSize(backup.size)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0, marginLeft: '12px' }}>
                    <button
                      onClick={() => window.open(backupApi.getDownloadUrl(backup.name, backup.agent_id), '_blank')}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '5px',
                        padding: '6px 12px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                        border: '1px solid var(--border)', borderRadius: '8px', fontSize: '11px',
                        cursor: 'pointer',
                      }}
                    >
                      <Download size={11} /> 下载
                    </button>
                    <button
                      onClick={() => handleRestore(backup)}
                      disabled={loading}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '5px',
                        padding: '6px 12px',
                        background: 'rgba(234,88,12,0.1)', color: '#ea580c',
                        border: '1px solid rgba(234,88,12,0.2)', borderRadius: '8px', fontSize: '11px',
                        cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
                      }}
                    >
                      <RotateCcw size={11} /> 还原
                    </button>
                    <button
                      onClick={() => handleDelete(backup)}
                      disabled={loading}
                      style={{
                        padding: '6px', background: 'rgba(220,38,38,0.05)', color: '#dc2626',
                        border: '1px solid rgba(220,38,38,0.1)', borderRadius: '8px',
                        cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
                      }}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {otherBackups.length > 0 && selectedAgent && (
            <>
              <div style={{ marginTop: '24px', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px', fontWeight: 500 }}>
                <FileArchive size={16} style={{ color: 'var(--text-muted)' }} />
                其他 Agent 的备份 ({otherBackups.length})
              </div>
              <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
                overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
              }}>
                {otherBackups.map((backup, idx) => (
                  <div key={backup.path} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '14px 20px',
                    borderBottom: idx < otherBackups.length - 1 ? '1px solid var(--border)' : 'none',
                    opacity: 0.7,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0, flex: 1 }}>
                      <div style={{
                        width: '40px', height: '40px', background: 'var(--bg-tertiary)', borderRadius: '10px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                      }}>
                        <FileArchive size={18} style={{ color: 'var(--text-muted)' }} />
                      </div>
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {backup.name}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '2px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'var(--bg-tertiary)', padding: '1px 6px', borderRadius: '4px' }}>
                            {backup.agent_id}
                          </span>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                            <Clock size={10} /> {formatDate(backup.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0, marginLeft: '12px' }}>
                      <button onClick={() => window.open(backupApi.getDownloadUrl(backup.name, backup.agent_id), '_blank')} style={{
                        display: 'flex', alignItems: 'center', gap: '5px', padding: '6px 12px',
                        background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                        border: '1px solid var(--border)', borderRadius: '8px', fontSize: '11px', cursor: 'pointer',
                      }}>
                        <Download size={11} /> 下载
                      </button>
                      <button onClick={() => handleDelete(backup)} disabled={loading} style={{
                        padding: '6px', background: 'rgba(220,38,38,0.05)', color: '#dc2626',
                        border: '1px solid rgba(220,38,38,0.1)', borderRadius: '8px',
                        cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
                      }}>
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
    </>
  );
}
