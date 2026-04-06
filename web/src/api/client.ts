import axios from 'axios';
import type { Agent, ChatRequest, ChatResponse, CreateAgentRequest } from '../types';

const gateway = axios.create({ baseURL: '/api' });

export const agentApi = {
  listAgents: async (): Promise<Agent[]> => {
    const res = await gateway.get<Agent[]>('/agents');
    return res.data;
  },

  createAgent: async (data: CreateAgentRequest) => {
    const res = await gateway.post('/admin/create', data);
    return res.data;
  },

  startAgent: async (agentId: string, port: number) => {
    const res = await gateway.post(`/admin/${agentId}/start?port=${port}`);
    return res.data;
  },

  stopAgent: async (agentId: string) => {
    const res = await gateway.post(`/admin/${agentId}/stop`);
    return res.data;
  },

  getAgentLogs: async (agentId: string): Promise<string> => {
    const res = await gateway.get<{ logs: string }>(`/admin/${agentId}/logs`);
    return res.data.logs;
  },

  getAgentThoughts: async (agentId: string): Promise<string> => {
    const res = await gateway.get<{ thoughts: string }>(`/admin/${agentId}/thoughts`);
    return res.data.thoughts;
  },

  getAgentFiles: async (agentId: string): Promise<any[]> => {
    const res = await gateway.get<{ files: any[] }>(`/admin/${agentId}/files`);
    return res.data.files;
  },

  getSharedFiles: async (): Promise<any[]> => {
    const res = await gateway.get<{ files: any[] }>(`/admin/shared/files`);
    return res.data.files;
  },

  uploadSharedFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await gateway.post('/admin/shared/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  getDownloadUrl: (agentId: string, path: string): string => {
    return `/api/admin/${agentId}/files/download?path=${encodeURIComponent(path)}`;
  },

  getSharedDownloadUrl: (path: string): string => {
    return `/api/admin/shared/files/download?path=${encodeURIComponent(path)}`;
  },

  getAgentConfig: async (agentId: string): Promise<{ allow_cors: boolean }> => {
    const res = await gateway.get(`/admin/${agentId}/config`);
    return res.data;
  },

  updateAgentConfig: async (agentId: string, config: { allow_cors: boolean }) => {
    const res = await gateway.post(`/admin/${agentId}/config`, config);
    return res.data;
  },

  chat: async (agentId: string, data: ChatRequest): Promise<ChatResponse> => {
    const res = await gateway.post<ChatResponse>(`/agents/${agentId}/agent/chat`, data);
    return res.data;
  },

  health: async (agentId: string): Promise<{ status: string }> => {
    const res = await gateway.get(`/agents/${agentId}/health`);
    return res.data;
  },

  checkAgentHealth: async (agentId: string): Promise<boolean> => {
    try {
      // 通过网关代理进行健康检查，而不是直接访问 localhost 端口
      await gateway.get(`/agents/${agentId}/health`, { timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  },
};

export const systemApi = {
  clearLogs: async (agentId: string) => {
    const res = await gateway.post(`/system/clear-logs/${agentId}`);
    return res.data;
  },
};

export const backupApi = {
  listBackups: async () => {
    const res = await gateway.get('/backup/list');
    return res.data;
  },
  createBackup: async (agentId: string, name?: string, filePaths?: string[]) => {
    const res = await gateway.post('/backup/create', {
      agent_id: agentId,
      name,
      file_paths: filePaths,
    });
    return res.data;
  },
  restoreBackup: async (name: string, agentId: string) => {
    const res = await gateway.post(`/backup/restore/${encodeURIComponent(name)}?agent_id=${agentId}`);
    return res.data;
  },
  deleteBackup: async (name: string, agentId: string) => {
    const res = await gateway.delete(`/backup/delete/${encodeURIComponent(agentId)}/${encodeURIComponent(name)}`);
    return res.data;
  },

  getDownloadUrl: (name: string, agentId: string): string => {
    return `/api/backup/download/${encodeURIComponent(agentId)}/${encodeURIComponent(name)}`;
  },

  listTemplates: async () => {
    const res = await gateway.get('/backup/templates');
    return res.data;
  },

  applyTemplate: async (agentId: string, templateName: string, autoBackup: boolean = true) => {
    const res = await gateway.post(`/backup/apply-template/${agentId}`, {
      template_name: templateName,
      auto_backup: autoBackup,
    });
    return res.data;
  },
};
