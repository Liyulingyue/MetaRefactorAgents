import { useState, useEffect } from 'react';
import { GitBranch, GitCommit, Clock, FileCode } from 'lucide-react';
import { agentApi } from '../api/client';
import type { Template } from '../types';

interface TreeNode extends Template {
  children: TreeNode[];
}

function buildTree(templates: Template[]): TreeNode[] {
  const map = new Map<string, TreeNode>();
  templates.forEach(t => map.set(t.id, { ...t, children: [] }));
  
  const roots: TreeNode[] = [];
  map.forEach(node => {
    const parentId = node.lineage.parent;
    if (parentId && map.has(parentId)) {
      map.get(parentId)!.children.push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

function formatId(id: string): string {
  if (/^\d{14}$/.test(id)) {
    return `${id.slice(0,4)}-${id.slice(4,6)}-${id.slice(6,8)} ${id.slice(8,10)}:${id.slice(10,12)}:${id.slice(12,14)}`;
  }
  return id;
}

function TreeNodeComponent({ node, level = 0 }: { node: TreeNode; level?: number }) {
  const [expanded, setExpanded] = useState(level < 2);

  return (
    <div style={{ marginLeft: level > 0 ? '24px' : 0 }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        marginTop: '8px',
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        transition: 'all 0.2s',
      }}>
        <div style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: node.lineage.parent ? 'var(--accent)' : 'var(--success)',
        }} />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontWeight: 600, fontSize: '14px' }}>{node.name}</span>
            <span style={{
              fontSize: '11px', padding: '2px 6px',
              background: 'var(--accent-dim)', color: 'var(--accent)',
              borderRadius: '4px',
            }}>
              v{node.lineage.version}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={10} />
              {formatId(node.id)}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <GitCommit size={10} />
              {node.lineage.parent ? `parent: ${node.lineage.parent}` : 'root'}
            </span>
          </div>
          {node.lineage.note && (
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px', fontStyle: 'italic' }}>
              {node.lineage.note}
            </div>
          )}
        </div>
        {node.children.length > 0 && (
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              display: 'flex', alignItems: 'center', gap: '4px',
              padding: '4px 8px', background: 'var(--bg-tertiary)',
              border: '1px solid var(--border)', borderRadius: '6px',
              fontSize: '11px', color: 'var(--text-muted)', cursor: 'pointer',
            }}
          >
            <GitBranch size={10} />
            {node.children.length} child{node.children.length > 1 ? 'ren' : ''}
            {expanded ? ' ▲' : ' ▼'}
          </button>
        )}
      </div>
      {expanded && node.children.map(child => (
        <TreeNodeComponent key={child.id} node={child} level={level + 1} />
      ))}
    </div>
  );
}

export default function Lineage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    agentApi.listTemplates().then(templates => {
      setTemplates(templates);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const tree = buildTree(templates);

  return (
    <div style={{ padding: '24px', height: '100%' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <GitBranch size={24} />
          Template Lineage
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
          Visualize the template evolution tree
        </p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          Loading...
        </div>
      ) : templates.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px',
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
        }}>
          <GitBranch size={40} style={{ color: 'var(--text-muted)', marginBottom: '12px' }} />
          <div style={{ color: 'var(--text-muted)' }}>No templates found.</div>
        </div>
      ) : (
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <FileCode size={14} />
            {templates.length} template{templates.length > 1 ? 's' : ''}
          </div>
          {tree.map(node => (
            <TreeNodeComponent key={node.id} node={node} />
          ))}
        </div>
      )}

      <div style={{
        marginTop: '24px', padding: '16px',
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
      }}>
        <div style={{ fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>Lineage Info</div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.8 }}>
          <p>Templates evolve through iteration. Each node shows the template ID (timestamp-based), version, parent reference, and evolution notes.</p>
          <p style={{ marginTop: '6px' }}>
            New templates are created by forking from an existing one. The <code style={{ background: 'var(--bg-tertiary)', padding: '2px 4px', borderRadius: '4px' }}>parent</code> field references the parent's ID.
          </p>
        </div>
      </div>
    </div>
  );
}
