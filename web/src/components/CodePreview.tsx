import { FileText, Loader2 } from 'lucide-react';

interface CodePreviewProps {
  fileName?: string;
  content?: string;
  loading?: boolean;
}

export function CodePreview({ fileName, content, loading }: CodePreviewProps) {
  if (loading) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '8px' }}>
        <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', opacity: 0.3 }} />
        <span style={{ fontSize: '13px' }}>Loading file content...</span>
      </div>
    );
  }

  if (!content) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '8px' }}>
        <FileText size={32} style={{ opacity: 0.3 }} />
        <span style={{ fontSize: '13px' }}>{fileName ? 'Select a file to preview' : 'No file selected'}</span>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', lineHeight: 1.6, overflow: 'auto', height: '100%' }}>
      <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '14px', color: 'var(--text-primary)', margin: 0 }}>
        {content}
      </pre>
    </div>
  );
}
