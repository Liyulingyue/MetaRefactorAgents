import { useState } from 'react';
import { ChevronRight, Folder, FileText, CheckSquare, Square } from 'lucide-react';

export interface FileNode {
  name: string;
  path: string;
  isDir: boolean;
  children: FileNode[];
}

function buildFileTree(files: unknown[]): FileNode[] {
  const root: FileNode[] = [];
  for (const f of files as { path: string }[]) {
    const parts = f.path.split('/').filter(Boolean);
    let cur = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      const existing = cur.find(n => n.name === part);
      if (existing) {
        cur = existing.children;
      } else {
        const node: FileNode = { name: part, path: parts.slice(0, i + 1).join('/'), isDir: !isLast, children: [] };
        cur.push(node);
        cur = node.children;
      }
    }
  }
  const sort = (nodes: FileNode[]) => {
    nodes.sort((a, b) => {
      if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    nodes.forEach(n => sort(n.children));
  };
  sort(root);
  return root;
}

interface FileTreeNodeProps {
  node: FileNode;
  depth: number;
  onSelect: (path: string, name: string) => void;
  selectedPath: string;
  multiSelect?: boolean;
  selectedPaths?: Set<string>;
  onToggle?: (path: string) => void;
}

function FileTreeNode({ node, depth, onSelect, selectedPath, multiSelect, selectedPaths, onToggle }: FileTreeNodeProps) {
  const [expanded, setExpanded] = useState(true);
  const isSelected = node.path === selectedPath;
  const isChecked = multiSelect && selectedPaths?.has(node.path);
  const isDir = node.isDir;

  return (
    <>
      <div
        onClick={() => {
          if (isDir) {
            setExpanded(!expanded);
          } else if (multiSelect && onToggle) {
            onToggle(node.path);
          } else {
            onSelect(node.path, node.name);
          }
        }}
        style={{
          padding: '5px 8px',
          paddingLeft: `${8 + depth * 14}px`,
          borderRadius: '6px',
          fontSize: '13px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          background: multiSelect
            ? isChecked ? 'var(--accent-transparent)' : 'transparent'
            : isSelected ? 'var(--accent-transparent)' : 'transparent',
          color: multiSelect
            ? isChecked ? 'var(--accent)' : 'var(--text-primary)'
            : isSelected ? 'var(--accent)' : 'var(--text-primary)',
          userSelect: 'none',
        }}
      >
        {multiSelect && !isDir ? (
          isChecked ? <CheckSquare size={12} style={{ flexShrink: 0 }} /> : <Square size={12} style={{ flexShrink: 0 }} />
        ) : isDir ? (
          <ChevronRight size={12} style={{ transform: expanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s', flexShrink: 0 }} />
        ) : null}
        {isDir ? (
          <Folder size={14} style={{ flexShrink: 0 }} />
        ) : (
          <FileText size={14} style={{ flexShrink: 0, opacity: 0.6 }} />
        )}
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.name}</span>
      </div>
      {isDir && expanded && node.children.map(child => (
        <FileTreeNode
          key={child.path}
          node={child}
          depth={depth + 1}
          onSelect={onSelect}
          selectedPath={selectedPath}
          multiSelect={multiSelect}
          selectedPaths={selectedPaths}
          onToggle={onToggle}
        />
      ))}
    </>
  );
}

interface FileTreeProps {
  files: unknown[];
  onSelect: (path: string, name: string) => void;
  selectedPath: string;
  multiSelect?: boolean;
  selectedPaths?: Set<string>;
  onToggle?: (path: string) => void;
}

export function FileTree({ files, onSelect, selectedPath, multiSelect, selectedPaths, onToggle }: FileTreeProps) {
  const fileTree = buildFileTree(files);

  if (fileTree.length === 0) {
    return <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>No files yet</div>;
  }

  return fileTree.map(node => (
    <FileTreeNode
      key={node.path}
      node={node}
      depth={0}
      onSelect={onSelect}
      selectedPath={selectedPath}
      multiSelect={multiSelect}
      selectedPaths={selectedPaths}
      onToggle={onToggle}
    />
  ));
}
