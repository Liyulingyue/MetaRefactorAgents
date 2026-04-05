import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  Eye, X,
  Folder, RefreshCw
} from 'lucide-react';
import { agentApi, systemApi } from '../api/client';
import type { Agent, Message } from '../types';
import { Resizer } from '../components/Resizer';
import { FileTree } from '../components/FileTree';
import { CodePreview, RenderModeToggle } from '../components/CodePreview';
import { useChatHistory } from '../hooks/useChatHistory';
import { ChatHeader } from '../components/chat/ChatHeader';
import { MessageList } from '../components/chat/MessageList';
import { ChatInput } from '../components/chat/ChatInput';

export default function Chat() {
  const { agentId } = useParams<{ agentId?: string }>();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [agentHealthy, setAgentHealthy] = useState(false);
  const [histories, setHistories] = useState<Record<string, Message[]>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [showFiles, setShowFiles] = useState(true);
  const [showPreview, setShowPreview] = useState(true);
  const [agentFiles, setAgentFiles] = useState<any[]>([]);
  const [previewFile, setPreviewFile] = useState<{ name: string, content: string } | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const [renderMode, setRenderMode] = useState<'auto' | 'md' | 'text'>('auto');

  const [previewWidth, setPreviewWidth] = useState(500);
  const [filesWidth, setFilesWidth] = useState(260);
  const previewWidthRef = useRef(previewWidth);
  const filesWidthRef = useRef(filesWidth);

  const { load, save, clear } = useChatHistory();

  useEffect(() => { previewWidthRef.current = previewWidth; }, [previewWidth]);
  useEffect(() => { filesWidthRef.current = filesWidth; }, [filesWidth]);

  const switchAgent = useCallback((agentId: string) => {
    setSelectedAgent(agentId);
    const loadedHistories = load();
    setHistories(loadedHistories);
    setMessages(loadedHistories[agentId] || []);
    setPreviewFile(null);
  }, [load]);

  const fetchFiles = useCallback(async (id: string) => {
    if (!id) return;
    try {
      const files = await agentApi.getAgentFiles(id);
      setAgentFiles(files);
    } catch (e) {
      console.error('Failed to fetch agent files', e);
    }
  }, []);

  const handlePreviewFile = async (path: string, name: string) => {
    if (!selectedAgent) return;
    setLoadingFile(true);
    try {
      const url = agentApi.getDownloadUrl(selectedAgent, path);
      const res = await fetch(url);
      const text = await res.text();
      setPreviewFile({ name, content: text });
      setShowPreview(true);
    } catch (e) {
      console.error('Failed to preview file', e);
    } finally {
      setLoadingFile(false);
    }
  };

  const refreshPreviewFile = async () => {
    if (!previewFile || !selectedAgent) return;
    const fileEntry = agentFiles.find(f => f.name === previewFile.name);
    if (fileEntry) {
      await handlePreviewFile(fileEntry.path, fileEntry.name);
    }
  };

  useEffect(() => {
    if (selectedAgent) fetchFiles(selectedAgent);
  }, [selectedAgent, fetchFiles]);

  useEffect(() => {
    agentApi.listAgents().then(async (list) => {
      const withStatus = await Promise.all(
        list.map(async (a) => {
          const healthy = await agentApi.checkAgentHealth(a.id);
          return { ...a, status: healthy ? 'running' : 'stopped' } as Agent;
        })
      );
      setAgents(withStatus);
      const loadedHistories = load();
      setHistories(loadedHistories);
      if (agentId) {
        switchAgent(agentId);
      } else if (withStatus.length > 0) {
        switchAgent(withStatus[0].id);
      }
    });
  }, [agentId, switchAgent, load]);

  useEffect(() => {
    const agent = agents.find(a => a.id === selectedAgent);
    setAgentHealthy(agent?.status === 'running');
  }, [selectedAgent, agents]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleClearChat = () => {
    const newHistories = clear(histories, selectedAgent);
    setHistories(newHistories);
    setMessages([]);
  };

  const handleDeepClear = async () => {
    if (!confirm('This will clear all chat history and logs. Continue?')) return;
    try {
      await systemApi.clearLogs(selectedAgent);
      localStorage.removeItem('chat_histories');
      setHistories({});
      setMessages([]);
      alert('Deep clear completed.');
    } catch (e) {
      console.error('Failed to deep clear:', e);
      alert('Deep clear failed.');
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedAgent || loading) return;
    const userMsg: Message = { role: 'user', content: input };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    const currentInput = input;
    setInput('');
    setLoading(true);
    try {
      const res = await agentApi.chat(selectedAgent, { prompt: currentInput, history: messages });
      const assistantMsg = { role: 'assistant' as const, content: res.response };
      const newMessages = [...updatedMessages, assistantMsg];
      setMessages(newMessages);
      const newHistories = { ...histories, [selectedAgent]: newMessages };
      setHistories(newHistories);
      save(newHistories);
      fetchFiles(selectedAgent);
    } catch (e: unknown) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e instanceof Error ? e.message : 'Request failed'}` }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const selectedPath = previewFile?.name
    ? agentFiles.find(f => f.name === previewFile.name)?.path || ''
    : '';

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: '24px', gap: '16px', maxWidth: '100%', overflow: 'hidden' }}>
      <ChatHeader
        agentId={agentId}
        selectedAgent={selectedAgent}
        agentHealthy={agentHealthy}
        showFiles={showFiles}
        setShowFiles={setShowFiles}
        showPreview={showPreview}
        setShowPreview={setShowPreview}
        agents={agents}
        switchAgent={switchAgent}
        handleClearChat={handleClearChat}
        handleDeepClear={handleDeepClear}
      />

      <div style={{ flex: 1, display: 'flex', gap: '0', minHeight: 0 }}>
        <div style={{
          flex: 1, minWidth: '350px',
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}>
          <MessageList
            messages={messages}
            loading={loading}
            selectedAgent={selectedAgent}
            messagesEndRef={messagesEndRef}
          />

          <ChatInput
            input={input}
            setInput={setInput}
            handleSend={handleSend}
            handleKeyDown={handleKeyDown}
            selectedAgent={selectedAgent}
            loading={loading}
          />
        </div>

        {showPreview && (
          <>
            <div style={{ width: '8px', flexShrink: 0, display: 'flex', justifyContent: 'center' }}>
              <Resizer onDrag={delta => {
                const nextPreview = Math.max(300, Math.min(1000, previewWidthRef.current - delta));
                previewWidthRef.current = nextPreview;
                setPreviewWidth(nextPreview);
              }} />
            </div>
            <div style={{
              width: `${previewWidth}px`, flexShrink: 0,
              background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}>
              <div style={{
                padding: '12px 16px', borderBottom: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: 'var(--bg-secondary)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 500 }}>
                  <Eye size={14} />
                  Preview: {previewFile?.name || 'No file selected'}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {previewFile && (
                    <RenderModeToggle
                      fileName={previewFile.name}
                      mode={renderMode}
                      onModeChange={setRenderMode}
                    />
                  )}
                  <button onClick={refreshPreviewFile} disabled={loadingFile} style={{ border: 'none', background: 'transparent', cursor: loadingFile ? 'default' : 'pointer', color: 'var(--text-muted)' }}>
                    <RefreshCw size={14} style={loadingFile ? { animation: 'spin 1s linear infinite' } : {}} />
                  </button>
                  <button onClick={() => setShowPreview(false)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}>
                  <X size={14} />
                </button>
                </div>
              </div>
              <div style={{ flex: 1, overflow: 'auto' }}>
                <CodePreview
                  fileName={previewFile?.name}
                  content={previewFile?.content}
                  loading={loadingFile}
                  mode={renderMode}
                />
              </div>
            </div>
          </>
        )}

        {showFiles && (
          <>
            <div style={{ width: '8px', flexShrink: 0, display: 'flex', justifyContent: 'center' }}>
              <Resizer onDrag={delta => {
                if (showPreview) {
                  const MIN_PREVIEW = 300;
                  const MAX_PREVIEW = 1000;
                  const MIN_FILES = 160;
                  const MAX_FILES = 400;

                  const currentPreview = previewWidthRef.current;
                  const currentFiles = filesWidthRef.current;
                  const growPreviewLimit = Math.min(MAX_PREVIEW - currentPreview, currentFiles - MIN_FILES);
                  const shrinkPreviewLimit = Math.max(MIN_PREVIEW - currentPreview, currentFiles - MAX_FILES);
                  const safeDelta = Math.max(shrinkPreviewLimit, Math.min(growPreviewLimit, delta));

                  if (safeDelta === 0) return;

                  const nextPreview = currentPreview + safeDelta;
                  const nextFiles = currentFiles - safeDelta;

                  previewWidthRef.current = nextPreview;
                  filesWidthRef.current = nextFiles;
                  setPreviewWidth(nextPreview);
                  setFilesWidth(nextFiles);
                } else {
                  const nextFiles = Math.max(160, Math.min(400, filesWidthRef.current - delta));
                  filesWidthRef.current = nextFiles;
                  setFilesWidth(nextFiles);
                }
              }} />
            </div>
            <div style={{
              width: `${filesWidth}px`, flexShrink: 0,
              background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
            }}>
              <div style={{
                padding: '12px 16px', borderBottom: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: 'var(--bg-secondary)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', fontWeight: 500 }}>
                  <Folder size={14} />
                  Files
                </div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button onClick={() => selectedAgent && fetchFiles(selectedAgent)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }} title="Refresh">
                    <RefreshCw size={12} />
                  </button>
                  <button onClick={() => setShowFiles(false)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}>
                    <X size={12} />
                  </button>
                </div>
              </div>
              <div style={{ flex: 1, overflow: 'auto', padding: '6px' }}>
                <FileTree
                  files={agentFiles}
                  onSelect={handlePreviewFile}
                  selectedPath={selectedPath}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
