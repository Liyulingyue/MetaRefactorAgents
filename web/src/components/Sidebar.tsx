import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, PlusCircle, GitBranch, ShieldCheck } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/create', icon: PlusCircle, label: 'Create Agent' },
  { to: '/lineage', icon: GitBranch, label: 'Lineage' },
  { to: '/system', icon: ShieldCheck, label: 'Port Viewer' },
];

export default function Sidebar() {
  return (
    <nav style={{
      width: '200px',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      padding: '0',
      flexShrink: 0,
      height: '100vh',
      boxShadow: '2px 0 8px rgba(0,0,0,0.04)',
    }}>
      <div style={{
        padding: '20px',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '34px',
            height: '34px',
            background: 'linear-gradient(135deg, var(--accent), #a855f7)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: '15px',
            color: 'white',
          }}>M</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px' }}>MRA</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Meta Refactor Agents</div>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, padding: '12px 0' }}>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '10px 20px',
              color: isActive ? 'var(--accent)' : 'var(--text-secondary)',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              transition: 'all 0.15s',
              fontSize: '13px',
              fontWeight: isActive ? 500 : 400,
            })}
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </div>

      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          Gateway: localhost:8000
        </div>
      </div>
    </nav>
  );
}
