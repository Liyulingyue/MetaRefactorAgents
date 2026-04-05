import { Bot, Loader2 } from 'lucide-react';
import type { Message } from '../../types';
import { MessageItem } from './MessageItem';

interface MessageListProps {
  messages: Message[];
  loading: boolean;
  selectedAgent: string;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

export function MessageList({ messages, loading, selectedAgent, messagesEndRef }: MessageListProps) {
  return (
    <div style={{
      flex: 1, overflow: 'auto', padding: '20px 24px',
      display: 'flex', flexDirection: 'column', gap: '16px',
    }}>
      {messages.length === 0 && (
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-muted)', gap: '12px',
        }}>
          <Bot size={40} style={{ opacity: 0.4 }} />
          <div style={{ fontSize: '14px' }}>
            {selectedAgent ? `Send a message to ${selectedAgent}` : 'Select an agent above to start'}
          </div>
        </div>
      )}
      {messages.map((msg, i) => (
        <MessageItem key={i} msg={msg} />
      ))}
      {loading && (
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'var(--bg-tertiary)',
          }}>
            <Bot size={15} />
          </div>
          <div style={{
            padding: '10px 14px', borderRadius: '12px',
            background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Agent is thinking...</span>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}
