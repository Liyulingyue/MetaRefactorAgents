import { FileText, Loader2 } from 'lucide-react';
import { marked } from 'marked';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';

hljs.registerLanguage('python', python);

type RenderMode = 'auto' | 'md' | 'py' | 'text';

interface CodePreviewProps {
  fileName?: string;
  content?: string;
  loading?: boolean;
  mode?: RenderMode;
  onModeChange?: (mode: RenderMode) => void;
}

function MarkdownPreview({ content }: { content: string }) {
  const html = marked(content);
  return (
    <div
      className="markdown-body"
      style={{
        padding: '20px',
        overflow: 'auto',
        height: '100%',
        color: 'var(--text-primary)',
        lineHeight: 1.7,
      }}
      dangerouslySetInnerHTML={{ __html: html as string }}
    />
  );
}

function CodeHighlight({ content, lang }: { content: string; lang: string }) {
  const highlighted = hljs.highlight(content, { language: lang }).value;
  return (
    <div style={{ padding: '20px', overflow: 'auto', height: '100%' }}>
      <pre style={{
        margin: 0,
        fontFamily: "'Fira Code', 'Cascadia Code', Consolas, monospace",
        fontSize: '13px',
        lineHeight: 1.6,
      }}>
        <code
          className={`hljs language-${lang}`}
          dangerouslySetInnerHTML={{ __html: highlighted }}
        />
      </pre>
    </div>
  );
}

function PlainTextPreview({ content }: { content: string }) {
  return (
    <div style={{ padding: '20px', lineHeight: 1.6, overflow: 'auto', height: '100%' }}>
      <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '14px', color: 'var(--text-primary)', margin: 0 }}>
        {content}
      </pre>
    </div>
  );
}

export function CodePreview({ fileName, content, loading, mode = 'auto' }: CodePreviewProps) {
  const activeMode = mode;

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

  if (activeMode === 'md' || (activeMode === 'auto' && (fileName?.endsWith('.md') || fileName?.endsWith('.markdown')))) {
    return <MarkdownPreview content={content} />;
  }

  if (activeMode === 'py' || (activeMode === 'auto' && fileName?.endsWith('.py'))) {
    return <CodeHighlight content={content} lang="python" />;
  }

  return <PlainTextPreview content={content} />;
}

export function RenderModeToggle({
  fileName,
  mode,
  onModeChange,
}: {
  fileName?: string;
  mode: RenderMode;
  onModeChange: (mode: RenderMode) => void;
}) {
  const ext = fileName?.split('.').pop()?.toLowerCase();

  return (
    <select
      value={mode}
      onChange={e => onModeChange(e.target.value as RenderMode)}
      style={{
        padding: '4px 8px', borderRadius: '6px', fontSize: '11px',
        cursor: 'pointer', border: '1px solid var(--border)',
        background: 'var(--bg-tertiary)', color: 'var(--text-secondary)',
        outline: 'none',
      }}
    >
      <option value="auto">自动</option>
      {ext && <option value="md">Markdown</option>}
      {ext === 'py' && <option value="py">Python</option>}
      <option value="text">源文本</option>
    </select>
  );
}
