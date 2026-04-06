export interface Agent {
  id: string;
  port: number;
  url: string;
  status?: 'running' | 'stopped' | 'unknown';
  pid?: number;
  template?: string;
  template_id?: string;
  template_version?: string;
  createdAt?: string;
}

export interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface ChatRequest {
  prompt: string;
  history?: Message[];
}

export interface ChatResponse {
  response: string;
  history: Message[];
}

export interface CreateAgentRequest {
  agent_id: string;
  template?: string;
}

export interface LineageNode {
  id: string;
  parentId?: string;
  name: string;
  status: 'running' | 'stopped' | 'unknown';
  port?: number;
}

export interface TemplateLineage {
  version: string;
  parent: string | null;
  created_at: string;
  note: string;
}

export interface Template {
  name: string;
  id: string;
  lineage: TemplateLineage;
  replace: string[];
  exclude: string[];
}
