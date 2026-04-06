import { useState } from 'react';
import type { SVGProps } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message, ToolCall } from '../../types';
import { MermaidRender } from './MermaidRender';

interface MessageItemProps {
  msg: Message;
}

const IconUser = (props: SVGProps<SVGSVGElement>) => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
);

const IconBot = (props: SVGProps<SVGSVGElement>) => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>
  </svg>
);

const IconWrench = (props: SVGProps<SVGSVGElement>) => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
  </svg>
);

const IconChevronDown = (props: SVGProps<SVGSVGElement>) => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="m6 9 6 6 6-6"/>
  </svg>
);

const IconChevronUp = (props: SVGProps<SVGSVGElement>) => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="m18 15-6-6-6 6"/>
  </svg>
);

const IconBrain = (props: SVGProps<SVGSVGElement>) => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/>
  </svg>
);

const IconTerminal = (props: SVGProps<SVGSVGElement>) => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <polyline points="4 17 10 11 4 5"></polyline>
    <line x1="12" y1="19" x2="20" y2="19"></line>
  </svg>
);

function ToolCallCard({ tc }: { tc: ToolCall }) {
  const [expanded, setExpanded] = useState(false);
  let args: Record<string, unknown> = {};
  try { args = JSON.parse(tc.function.arguments); } catch {}

  return (
    <div style={{
      marginBottom: '6px', padding: '6px 10px', borderRadius: '8px',
      background: 'rgba(100,116,139,0.15)', border: '1px solid rgba(100,116,139,0.25)',
      fontSize: '12px', color: 'var(--text-muted)', cursor: 'pointer',
      display: 'flex', alignItems: 'flex-start', gap: '6px',
    }} onClick={() => setExpanded(!expanded)}>
      <IconWrench style={{ flexShrink: 0, marginTop: '2px' }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: expanded ? '4px' : 0 }}>
          <span style={{ fontWeight: 600, fontSize: '11px', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {tc.function.name}
          </span>
          {expanded ? <IconChevronUp /> : <IconChevronDown />}
        </div>
        {expanded && (
          <pre style={{
            margin: '6px 0 0', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            color: 'var(--text-secondary)', background: 'transparent', border: 'none',
            fontFamily: 'monospace', padding: 0
          }}>
            {JSON.stringify(args, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

function ThoughtBlock({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div style={{
      marginBottom: '6px', padding: '6px 10px', borderRadius: '8px',
      background: 'rgba(100,116,139,0.15)', border: '1px solid rgba(100,116,139,0.25)',
      fontSize: '12px', color: 'var(--text-muted)', cursor: 'pointer',
      display: 'flex', alignItems: 'flex-start', gap: '6px',
    }} onClick={() => setExpanded(!expanded)}>
      <IconBrain style={{ flexShrink: 0, marginTop: '2px' }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: expanded ? '4px' : 0 }}>
          <span style={{ fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {'<think>'}
          </span>
          {expanded ? <IconChevronUp /> : <IconChevronDown />}
        </div>
        {expanded && <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.5 }}>{content}</div>}
      </div>
    </div>
  );
}

function parseThoughts(content: string): { thought: string | null; body: string } {
  const match = content.match(/^<think>([\s\S]*?)<\/think>\n?/);
  if (match) {
    return { thought: match[1].trim(), body: content.slice(match[0].length) };
  }
  return { thought: null, body: content };
}

const markdownComponents = {
  code({ node: _node, inline, className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || '');
    const isMermaid = match?.[1] === 'mermaid';

    if (inline) {
      return <code style={{
        padding: '2px 5px', borderRadius: '4px', background: 'rgba(0,0,0,0.2)',
        fontFamily: 'monospace', fontSize: '0.9em',
      }} {...props}>{children}</code>;
    }

    if (isMermaid) {
      return <MermaidRender code={String(children).replace(/\n$/, '')} />;
    }

    return <code className={className} style={{
      padding: '12px', borderRadius: '8px', background: 'rgba(0,0,0,0.25)',
      display: 'block', overflowX: 'auto', fontSize: '12px', lineHeight: 1.5,
    }} {...props}>{children}</code>;
  },
  pre({ children }: any) {
    return <pre style={{ margin: '8px 0', padding: 0, background: 'transparent', border: 'none' }}>{children}</pre>;
  },
  a({ href, children }: any) {
    return <a href={href} target="_blank" rel="noopener noreferrer"
               style={{ color: '#60a5fa', textDecoration: 'underline' }}>{children}</a>;
  },
  table({ children }: any) {
    return <table style={{ borderCollapse: 'collapse', width: '100%', margin: '8px 0', fontSize: '13px' }}>{children}</table>;
  },
  th({ children }: any) {
    return <th style={{ border: '1px solid rgba(255,255,255,0.15)', padding: '6px 10px', background: 'rgba(0,0,0,0.2)' }}>{children}</th>;
  },
  td({ children }: any) {
    return <td style={{ border: '1px solid rgba(255,255,255,0.1)', padding: '6px 10px' }}>{children}</td>;
  },
};

export function MessageItem({ msg }: MessageItemProps) {
  const isUser = msg.role === 'user';
  const isTool = msg.role === 'tool';

  if (isTool) {
    const [expanded, setExpanded] = useState(false);
    const content = msg.content || '';

    return (
      <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', paddingLeft: '44px' }}>
        <div style={{
          maxWidth: '85%', marginBottom: '6px', padding: '6px 10px', borderRadius: '8px',
          background: 'rgba(100,116,139,0.15)', border: '1px solid rgba(100,116,139,0.25)',
          fontSize: '12px', color: 'var(--text-muted)', cursor: 'pointer',
          display: 'flex', alignItems: 'flex-start', gap: '6px',
        }} onClick={() => setExpanded(!expanded)}>
          <IconTerminal style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: expanded ? '4px' : 0 }}>
              <span style={{ fontWeight: 600, fontSize: '11px', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {msg.name}
              </span>
              {expanded ? <IconChevronUp /> : <IconChevronDown />}
            </div>
            {expanded && (
              <div style={{
                whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.5,
                marginTop: '4px', color: 'var(--text-secondary)'
              }}>
                {content}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  const { thought, body } = parseThoughts(msg.content || '');
  const bodyContent = body.trim();

  return (
    <div style={{
      display: 'flex', gap: '12px', alignItems: 'flex-start',
      flexDirection: isUser ? 'row-reverse' : 'row',
    }}>
      <div style={{
        width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: isUser ? 'var(--accent)' : 'var(--bg-tertiary)',
        color: isUser ? 'white' : 'var(--text-secondary)',
      }}>
        {isUser ? <IconUser /> : <IconBot />}
      </div>
      <div style={{ maxWidth: '85%' }}>
        {thought && <ThoughtBlock content={thought} />}
        {bodyContent && (
          <div style={{
            padding: '10px 14px', borderRadius: '12px',
            background: isUser ? 'var(--accent)' : 'var(--bg-tertiary)',
            border: '1px solid var(--border)',
            color: isUser ? 'white' : 'var(--text-primary)',
            fontSize: '13px', lineHeight: 1.6,
          }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {bodyContent}
            </ReactMarkdown>
          </div>
        )}
        {msg.tool_calls && msg.tool_calls.length > 0 && (
          <div style={{ marginTop: '6px' }}>
            {msg.tool_calls.map(tc => <ToolCallCard key={tc.id} tc={tc} />)}
          </div>
        )}
      </div>
    </div>
  );
}
