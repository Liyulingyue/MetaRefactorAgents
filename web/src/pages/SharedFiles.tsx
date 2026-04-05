import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen, Download, RefreshCw, ArrowLeft, Eye, Upload } from 'lucide-react';
import { agentApi } from '../api/client';
import { CodePreview, RenderModeToggle } from '../components/CodePreview';
import { Resizer } from '../components/Resizer';
import { FileTree } from '../components/FileTree';

export default function SharedFiles() {
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [previewFile, setPreviewFile] = useState<{ name: string, content: string } | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const [filesWidth, setFilesWidth] = useState(300);
  const filesWidthRef = useRef(filesWidth);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedPath, setSelectedPath] = useState('');
  const [renderMode, setRenderMode] = useState<'auto' | 'md' | 'py' | 'text'>('auto');

  useEffect(() => { filesWidthRef.current = filesWidth; }, [filesWidth]);

  const fetchFiles = async () => {
    try {
      const data = await agentApi.getSharedFiles();
      setFiles(data);
    } catch (e) {
      console.error('Failed to fetch shared files', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchFiles(); }, []);

  const handleRefresh = () => { setRefreshing(true); fetchFiles(); };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await agentApi.uploadSharedFile(file);
      fetchFiles();
    } catch (err) {
      console.error('Upload failed', err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handlePreviewFile = async (path: string, name: string) => {
    setSelectedPath(path);
    setLoadingFile(true);
    try {
      const url = agentApi.getSharedDownloadUrl(path);
      const res = await fetch(url);
      const text = await res.text();
      setPreviewFile({ name, content: text });
    } catch (e) {
      console.error('Failed to preview file', e);
    } finally {
      setLoadingFile(false);
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', padding: '24px', gap: '16px', maxWidth: '100%', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Link to="/" style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
            <ArrowLeft size={18} />
          </Link>
          <div>
            <h1>Shared Files</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Files published by agents for user download</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button onClick={handleRefresh} style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', background: 'var(--bg-secondary)', color: 'var(--text-secondary)',
            border: '1px solid var(--border)', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
          }}>
            <RefreshCw size={14} style={refreshing ? { animation: 'spin 1s linear infinite' } : {}} />
            Refresh
          </button>
          <input
            ref={fileInputRef}
            type="file"
            style={{ display: 'none' }}
            onChange={handleUpload}
          />
          <button onClick={() => fileInputRef.current?.click()} disabled={uploading} style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', background: 'var(--accent)', color: '#fff',
            border: 'none', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
          }}>
            <Upload size={14} />
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </div>

      {(loading || files.length === 0) ? (
        <div style={{ flex: 1, display: 'flex', gap: '0', minHeight: 0 }}>
          <div style={{
            flex: 1, minWidth: '400px',
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
                Preview: No file selected
              </div>
            </div>
            <div style={{ flex: 1, overflow: 'auto' }}>
              <CodePreview fileName={undefined} content={undefined} loading={false} />
            </div>
          </div>

          <div style={{ width: '8px', flexShrink: 0 }} />

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
                <FolderOpen size={14} style={{ color: 'var(--accent)' }} />
                Files ({files.length})
              </div>
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', gap: '12px' }}>
              {loading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
                  Loading...
                </div>
              ) : (
                <>
                  <FolderOpen size={32} style={{ opacity: 0.4 }} />
                  <div style={{ fontSize: '13px' }}>No shared files yet.</div>
                  <div style={{ fontSize: '12px', textAlign: 'center', maxWidth: '200px' }}>
                    Upload or agent publish via <code style={{ background: 'var(--bg-tertiary)', padding: '2px 6px', borderRadius: '4px' }}>publish_to_shared</code>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', gap: '0', minHeight: 0 }}>
          <div style={{
            flex: 1, minWidth: '400px',
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
              {previewFile && (
                <>
                <RenderModeToggle
                  fileName={previewFile.name}
                  mode={renderMode}
                  onModeChange={setRenderMode}
                />
                <a
                  href={agentApi.getSharedDownloadUrl(selectedPath)}
                  download
                  style={{
                    display: 'flex', alignItems: 'center', gap: '6px',
                    padding: '4px 10px', background: 'var(--accent-dim)', color: 'var(--accent)',
                    borderRadius: '6px', fontSize: '12px', textDecoration: 'none', fontWeight: 500,
                    marginLeft: 'auto',
                  }}
                >
                  <Download size={12} />
                  Download
                </a>
                </>
              )}
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

          <div style={{ width: '8px', flexShrink: 0, display: 'flex', justifyContent: 'center' }}>
            <Resizer onDrag={delta => {
              const next = Math.max(200, Math.min(500, filesWidthRef.current - delta));
              filesWidthRef.current = next;
              setFilesWidth(next);
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
                <FolderOpen size={14} style={{ color: 'var(--accent)' }} />
                Files ({files.length})
              </div>
            </div>
            <div style={{ flex: 1, overflow: 'auto' }}>
              <FileTree
                files={files}
                onSelect={handlePreviewFile}
                selectedPath={selectedPath}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
