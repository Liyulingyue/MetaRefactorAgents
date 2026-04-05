import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  input: string;
  setInput: (val: string) => void;
  handleSend: () => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;
  selectedAgent: string;
  loading: boolean;
}

export function ChatInput({
  input,
  setInput,
  handleSend,
  handleKeyDown,
  selectedAgent,
  loading
}: ChatInputProps) {
  return (
    <div style={{
      padding: '16px 24px', borderTop: '1px solid var(--border)',
      display: 'flex', gap: '12px', alignItems: 'flex-end',
    }}>
      <textarea
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={selectedAgent ? `Message ${selectedAgent}...` : 'Select an agent first'}
        disabled={!selectedAgent}
        style={{
          flex: 1, minHeight: '44px', maxHeight: '200px', padding: '12px 16px',
          background: 'var(--bg-secondary)', color: 'var(--text-primary)',
          border: '1px solid var(--border)', borderRadius: '12px',
          fontSize: '14px', resize: 'none', lineHeight: '1.5',
          outline: 'none', transition: 'border-color 0.2s',
        }}
        rows={1}
      />
      <button
        onClick={handleSend}
        disabled={!input.trim() || !selectedAgent || loading}
        style={{
          width: '44px', height: '44px', borderRadius: '12px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: (!input.trim() || !selectedAgent || loading) ? 'var(--bg-tertiary)' : 'var(--accent)',
          color: 'white', border: 'none', cursor: 'pointer',
          transition: 'all 0.2s', flexShrink: 0,
        }}
      >
        {loading ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={18} />}
      </button>
    </div>
  );
}
