import { X, FileText, Download } from 'lucide-react';

interface LogsModalProps {
  id: string;
  title: string;
  content: string;
  onClose: () => void;
}

export function LogsModal({ id, title, content, onClose }: LogsModalProps) {
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(4px)', zIndex: 1000,
    }}>
      <div style={{
        background: 'var(--bg-card)', width: '800px', height: '600px',
        borderRadius: '12px', display: 'flex', flexDirection: 'column',
        boxShadow: '0 8px 32px rgba(0,0,0,0.2)', border: '1px solid var(--border)',
      }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px', fontWeight: 500 }}>
            <FileText size={16} style={{ color: 'var(--accent)' }} />
            {title} - {id}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => {
                const blob = new Blob([content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${id}_${title.toLowerCase()}.log`;
                a.click();
              }}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '6px 12px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
                border: '1px solid var(--border)', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
              }}
            >
              <Download size={12} /> Download
            </button>
            <button onClick={onClose} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}>
              <X size={20} />
            </button>
          </div>
        </div>
        <div style={{
          flex: 1, padding: '20px', overflow: 'auto',
          background: 'var(--bg-tertiary)', color: '#94a3b8',
          fontFamily: 'monospace', fontSize: '12px', whiteSpace: 'pre-wrap',
          lineHeight: '1.6',
        }}>
          {content || `No ${title.toLowerCase()} available.`}
        </div>
      </div>
    </div>
  );
}
