import { useEffect, useRef, useState, useId } from 'react';
import mermaid from 'mermaid';

// Initialize mermaid once
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'inherit',
});

interface MermaidRenderProps {
  code: string;
}

function MermaidErrorCard({ message, code }: { message: string; code: string }) {
  return (
    <div style={{
      maxWidth: '100%',
      padding: '10px 12px',
      borderRadius: '10px',
      background: 'rgba(239, 68, 68, 0.08)',
      border: '1px solid rgba(239, 68, 68, 0.25)',
      color: '#fca5a5',
      fontSize: '12px',
      lineHeight: 1.5,
    }}>
      <div style={{ fontWeight: 700, marginBottom: '4px' }}>Mermaid 图解析失败</div>
      <div style={{ color: 'var(--text-secondary)' }}>{message}</div>
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
        }}>{code}</pre>
      </details>
    </div>
  );
}

export const MermaidRender = ({ code }: MermaidRenderProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const id = useId().replace(/:/g, ''); // Generate a safe ID for mermaid

  useEffect(() => {
    const render = async () => {
      if (!containerRef.current || !code) return;
      
      try {
        // Clear previous error
        setError(null);
        
        // Parse first so syntax errors never produce a rendered SVG.
        await mermaid.parse(code.trim());

        // Use mermaid.render instead of mermaid.contentLoaded.
        // This is safer for React components.
        const { svg: renderedSvg } = await mermaid.render(`mermaid-${id}`, code.trim());
        setSvg(renderedSvg);
      } catch (err: any) {
        console.error('Mermaid render error:', err);
        setError(err.message || 'Failed to render mermaid diagram');
        
        // Cleanup mermaid generated elements if any
        const el = document.getElementById(`mermaid-${id}`);
        if (el) el.remove();
      }
    };

    render();
  }, [code, id]);

  if (error) {
    return (
      <MermaidErrorCard message={error} code={code.trim()} />
    );
  }

  return (
    <div 
      ref={containerRef} 
      style={{ 
        background: 'rgba(0,0,0,0.2)', 
        padding: '16px', 
        borderRadius: '8px',
        display: 'flex',
        justifyContent: 'center',
        margin: '8px 0',
        overflowX: 'auto'
      }}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
