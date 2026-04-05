import { useState, useEffect } from 'react';
import { RefreshCw, Download, RotateCcw, Trash2, ShieldPlus, FileArchive, Clock, HardDrive, Archive } from 'lucide-react';
import { backupApi } from '../api/client';

interface Backup {
  name: string;
  size: number;
  created_at: string;
  path: string;
}

export default function BackupManager() {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [loading, setLoading] = useState(false);
  const [backupName, setBackupName] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const data = await backupApi.listBackups();
      setBackups(data);
    } catch (err) {
      console.error('Failed to fetch backups', err);
      setMessage({ type: 'error', text: '获取备份列表失败' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBackups(); }, []);

  const handleCreateBackup = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await backupApi.createBackup(backupName || undefined);
      setBackupName('');
      setMessage({ type: 'success', text: '备份创建成功' });
      fetchBackups();
    } catch (err) {
      setMessage({ type: 'error', text: '创建备份失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (name: string) => {
    if (!window.confirm(`确定要从备份 ${name} 恢复吗？这会覆盖当前的所有 Agent 数据！`)) return;
    setLoading(true);
    setMessage(null);
    try {
      await backupApi.restoreBackup(name);
      setMessage({ type: 'success', text: '恢复成功，系统状态已回滚' });
    } catch (err) {
      setMessage({ type: 'error', text: '恢复失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (name: string) => {
    if (!window.confirm(`确定要删除备份 ${name} 吗？`)) return;
    setLoading(true);
    try {
      await backupApi.deleteBackup(name);
      setMessage({ type: 'success', text: '备份已删除' });
      fetchBackups();
    } catch (err) {
      setMessage({ type: 'error', text: '删除失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (name: string) => {
    window.open(backupApi.getDownloadUrl(name), '_blank');
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

  return (
    <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Archive size={22} style={{ color: 'var(--accent)' }} />
            系统备份与恢复
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>管理 workspace 目录快照，升级前建议创建备份</p>
        </div>
        <button onClick={fetchBackups} style={{
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

      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
        padding: '24px', marginBottom: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', fontSize: '15px', fontWeight: 500 }}>
          <ShieldPlus size={16} style={{ color: 'var(--accent)' }} />
          新建备份
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            placeholder="输入备份名称 (可选，默认为时间戳)"
            value={backupName}
            onChange={e => setBackupName(e.target.value)}
            style={{
              flex: 1, padding: '10px 14px', background: 'var(--bg-tertiary)',
              color: 'var(--text-primary)', border: '1px solid var(--border)',
              borderRadius: '10px', fontSize: '13px', outline: 'none',
            }}
          />
          <button
            disabled={loading}
            onClick={handleCreateBackup}
            style={{
              padding: '10px 20px', background: 'var(--accent)', color: 'white',
              border: 'none', borderRadius: '10px', fontSize: '13px', fontWeight: 500,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1, display: 'flex', alignItems: 'center', gap: '8px',
            }}
          >
            {loading ? <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <HardDrive size={14} />}
            创建快照
          </button>
        </div>
        <p style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
          注意：备份仅包含 workspace 目录下的文件，不包含数据库或其他外部配置。
        </p>
      </div>

      <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px', fontWeight: 500 }}>
        <FileArchive size={16} style={{ color: 'var(--accent)' }} />
        已有备份 ({backups.length})
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
          {backups.map((backup, idx) => (
            <div key={backup.name} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '16px 20px',
              borderBottom: idx < backups.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', minWidth: 0, flex: 1 }}>
                <div style={{
                  width: '44px', height: '44px', background: 'var(--accent-dim)', borderRadius: '10px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                }}>
                  <FileArchive size={20} style={{ color: 'var(--accent)' }} />
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {backup.name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '4px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> {formatDate(backup.created_at)}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <HardDrive size={12} /> {formatSize(backup.size)}
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0, marginLeft: '16px' }}>
                <button
                  onClick={() => handleDownload(backup.name)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '6px',
                    padding: '7px 14px', background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
                    border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px',
                    cursor: 'pointer',
                  }}
                >
                  <Download size={13} /> 下载
                </button>
                <button
                  onClick={() => handleRestore(backup.name)}
                  disabled={loading}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '6px',
                    padding: '7px 14px',
                    background: 'rgba(234,88,12,0.1)', color: '#ea580c',
                    border: '1px solid rgba(234,88,12,0.2)', borderRadius: '8px', fontSize: '12px',
                    cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
                  }}
                >
                  <RotateCcw size={13} /> 还原
                </button>
                <button
                  onClick={() => handleDelete(backup.name)}
                  disabled={loading}
                  style={{
                    padding: '7px', background: 'rgba(220,38,38,0.05)', color: '#dc2626',
                    border: '1px solid rgba(220,38,38,0.1)', borderRadius: '8px',
                    cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
