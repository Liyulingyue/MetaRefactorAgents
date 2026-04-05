import { User, Bot } from 'lucide-react';
import type { Message } from '../../types';

interface MessageItemProps {
  msg: Message;
}

export function MessageItem({ msg }: MessageItemProps) {
  const isUser = msg.role === 'user';
  
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
        {isUser ? <User size={15} /> : <Bot size={15} />}
      </div>
      <div style={{
        maxWidth: '85%', padding: '10px 14px', borderRadius: '12px',
        background: isUser ? 'var(--accent)' : 'var(--bg-tertiary)',
        border: '1px solid var(--border)',
        color: isUser ? 'white' : 'var(--text-primary)',
        fontSize: '13px', lineHeight: 1.6,
        whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {msg.content}
      </div>
    </div>
  );
}
