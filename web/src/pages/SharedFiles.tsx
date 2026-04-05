import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen, Download, RefreshCw, FileText, ArrowLeft } from 'lucide-react';
import { agentApi } from '../api/client';

export default function SharedFiles() {
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchFiles = async () => {
    try {
      const data = await agentApi.getSharedFiles();
      setFiles(data);
    } catch (e) {
      console.error('Failed to fetch shared files', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchFiles(); }, []);

  const handleRefresh = () => { setRefreshing(true); fetchFiles(); };

  return (
    <div style={{ padding: '24px', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Link to="/" style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
            <ArrowLeft size={18} />
          </Link>
          <div>
            <h1>Shared Files</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Files published by agents for user download</p>
          </div>
        </div>
        <button onClick={handleRefresh} style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          padding: '8px 16px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
          border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
        }}>
          <RefreshCw size={14} style={refreshing ? { animation: 'spin 1s linear infinite' } : {}} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Loading...</div>
      ) : files.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px',
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
          <FolderOpen size={40} style={{ color: 'var(--text-muted)', marginBottom: '12px' }} />
          <div style={{ color: 'var(--text-muted)' }}>No shared files yet.</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
            Agents can publish files here via <code style={{ background: 'var(--bg-tertiary)', padding: '2px 6px', borderRadius: '4px' }}>publish_to_shared</code>
          </div>
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
            <FolderOpen size={14} style={{ color: 'var(--accent)' }} />
            {files.length} file{files.length !== 1 ? 's' : ''}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0' }}>
            {files.map((file, idx) => (
              <div key={idx} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '14px 24px',
                borderBottom: idx < files.length - 1 ? '1px solid var(--border)' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', minWidth: 0, flex: 1 }}>
                  <FileText size={20} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {file.name}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {(file.size / 1024).toFixed(1)} KB &bull; {new Date(file.mtime * 1000).toLocaleString()}
                    </div>
                  </div>
                </div>
                <a
                  href={agentApi.getSharedDownloadUrl(file.path)}
                  download
                  style={{
                    display: 'flex', alignItems: 'center', gap: '6px',
                    padding: '8px 16px', background: 'var(--accent-dim)', color: 'var(--accent)',
                    borderRadius: '8px', fontSize: '13px', textDecoration: 'none', fontWeight: 500,
                    flexShrink: 0, marginLeft: '16px',
                  }}
                >
                  <Download size={14} /> Download
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
