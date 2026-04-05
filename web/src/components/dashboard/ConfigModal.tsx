import { X, Globe, Shield } from 'lucide-react';

interface ConfigModalProps {
  id: string;
  allow_cors: boolean;
  onClose: () => void;
  onUpdate: (allow: boolean) => void;
}

export function ConfigModal({ id, allow_cors, onClose, onUpdate }: ConfigModalProps) {
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(4px)', zIndex: 1000,
    }}>
      <div style={{
        background: 'var(--bg-card)', width: '400px',
        borderRadius: '12px', display: 'flex', flexDirection: 'column',
        boxShadow: '0 8px 32px rgba(0,0,0,0.2)', border: '1px solid var(--border)',
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-tertiary)' }}>
          <h3 style={{ margin: 0, fontSize: '15px' }}>Agent Configuration: {id}</h3>
          <button onClick={onClose} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={18} />
          </button>
        </div>
        <div style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)' }}>
                <Globe size={20} />
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: 500 }}>Allow CORS</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Enable browser access across origins</div>
              </div>
            </div>
            <button
              onClick={() => onUpdate(!allow_cors)}
              style={{
                width: '42px', height: '24px', borderRadius: '12px',
                background: allow_cors ? 'var(--success)' : 'var(--bg-tertiary)',
                border: 'none', cursor: 'pointer', position: 'relative',
                transition: 'background-color 0.2s',
              }}
            >
              <div style={{
                position: 'absolute', top: '2px', left: allow_cors ? '20px' : '2px',
                width: '20px', height: '200px', // OOPS typo in original? existing code in Chat showed height: '20px', checking...
                maxWidth: '20px', maxHeight: '20px', borderRadius: '50%',
                background: 'white', transition: 'left 0.2s',
              }} />
            </button>
          </div>
          <div style={{ marginTop: '24px', padding: '12px', background: 'var(--bg-secondary)', borderRadius: '8px', display: 'flex', gap: '8px' }}>
            <Shield size={14} style={{ color: 'var(--accent)', marginTop: '2px' }} />
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              These settings take effect immediately through the gateway.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
