import { useEffect, useState } from 'react';
import { FileText, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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

function MermaidDiagram({ code }: { code: string }) {
  const [svg, setSvg] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const escapePipesInNodeLabels = (input: string) => {
    return input
      .split('\n')
      .map((line) => line
        .replace(/(\[[^\]\n]*?)\|(.*?\])/g, '$1&#124;$2')
        .replace(/(\([^\)\n]*?)\|(.*?\))/g, '$1&#124;$2')
        .replace(/(\{[^\}\n]*?)\|(.*?\})/g, '$1&#124;$2'))
      .join('\n');
  };

  useEffect(() => {
    let cancelled = false;
    const normalizedCode = code.trim();
    setSvg('');
    setErrorMessage(null);

    const getErrorMessage = (err: unknown) => {
      if (err instanceof Error && err.message) {
        return err.message;
      }

      if (typeof err === 'string' && err.trim()) {
        return err;
      }

      return 'Mermaid 图解析失败';
    };

    import('mermaid').then((mermaid) => {
      if (cancelled) return;
      mermaid.default.initialize({
        startOnLoad: false,
        securityLevel: 'loose',
        theme: 'default',
      });

      const renderMermaid = async (mermaidCode: string) => {
        const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;
        await mermaid.default.parse(mermaidCode);
        const result = await mermaid.default.render(id, mermaidCode);
        if (cancelled) return;

        setSvg(result.svg);
      };

      renderMermaid(normalizedCode).catch((err) => {
        const fallbackCode = escapePipesInNodeLabels(normalizedCode);
        if (fallbackCode === normalizedCode) {
          if (!cancelled) setErrorMessage(getErrorMessage(err));
          return;
        }

        renderMermaid(fallbackCode).catch((fallbackErr) => {
          if (!cancelled) setErrorMessage(getErrorMessage(fallbackErr));
        });
      });
    });

    return () => {
      cancelled = true;
    };
  }, [code]);

  if (errorMessage) {
    return (
      <div style={{
        margin: '8px 0',
        padding: '10px 12px',
        borderRadius: '10px',
        background: 'rgba(239, 68, 68, 0.08)',
        border: '1px solid rgba(239, 68, 68, 0.25)',
        color: '#fca5a5',
        fontSize: '12px',
        lineHeight: 1.5,
      }}>
        <div style={{ fontWeight: 700, marginBottom: '4px' }}>Mermaid 图解析失败</div>
        <div style={{ color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{errorMessage}</div>
        <details style={{ marginTop: '8px' }}>
          <summary style={{ cursor: 'pointer', color: '#fda4af' }}>查看原始图内容</summary>
          <pre style={{
            margin: '8px 0 0',
            padding: '8px',
            borderRadius: '8px',
            background: 'rgba(0,0,0,0.18)',
            color: 'var(--text-secondary)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            overflowX: 'auto',
          }}>{code.trim()}</pre>
        </details>
      </div>
    );
  }

  return (
    <div style={{ background: 'rgba(0,0,0,0.15)', borderRadius: '8px', padding: '12px', margin: '8px 0', overflowX: 'auto' }}>
      {svg ? (
        <div dangerouslySetInnerHTML={{ __html: svg }} />
      ) : (
        <pre style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{code.trim()}</pre>
      )}
    </div>
  );
}

const markdownComponents = {
  code({ inline, className, children, ...props }: any) {
    if (inline) {
      return <code style={{
        padding: '2px 5px', borderRadius: '4px', background: 'rgba(0,0,0,0.2)',
        fontFamily: 'monospace', fontSize: '0.9em',
      }} {...props}>{children}</code>;
    }

    if (/language-mermaid/.test(className || '')) {
      return <MermaidDiagram code={String(children)} />;
    }

    return <pre style={{ margin: '8px 0', padding: 0, background: 'transparent', border: 'none' }}>
      <code className={className} style={{
        padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.25)',
        display: 'block', overflowX: 'auto', fontSize: '12px', lineHeight: 1.5,
        whiteSpace: 'pre-wrap',
      }} {...props}>{children}</code>
    </pre>;
  },
};

function MarkdownPreview({ content }: { content: string }) {
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
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
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
