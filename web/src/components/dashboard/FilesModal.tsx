import { X, FolderOpen, Download } from 'lucide-react';
import { agentApi } from '../../api/client';

interface FilesModalProps {
  id: string;
  files: any[];
  isShared: boolean;
  onClose: () => void;
}

export function FilesModal({ id, files, isShared, onClose }: FilesModalProps) {
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(4px)', zIndex: 1000,
    }}>
      <div style={{
        background: 'var(--bg-card)', width: '600px', height: '500px',
        borderRadius: '12px', display: 'flex', flexDirection: 'column',
        boxShadow: '0 8px 32px rgba(0,0,0,0.2)', border: '1px solid var(--border)',
      }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px', fontWeight: 500 }}>
            <FolderOpen size={16} style={{ color: 'var(--accent)' }} />
            {isShared ? 'Shared' : 'Output'} Files - {id}
          </div>
          <button onClick={onClose} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={20} />
          </button>
        </div>
        <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
          {files.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>No files found.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {files.map((file, i) => (
                <div key={i} style={{
                  padding: '12px 16px', background: 'var(--bg-tertiary)',
                  borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  border: '1px solid var(--border)',
                }}>
                  <div style={{ fontSize: '13px', fontWeight: 500 }}>{file.name}</div>
                  <a
                    href={isShared ? agentApi.getSharedFileUrl(file.path) : agentApi.getDownloadUrl(id, file.path)}
                    download={file.name}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '6px',
                      textDecoration: 'none', color: 'var(--accent)', fontSize: '12px', fontWeight: 500,
                      padding: '4px 8px', background: 'var(--accent-dim)', borderRadius: '6px',
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
  );
}
