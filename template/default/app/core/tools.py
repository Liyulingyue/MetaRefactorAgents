import subprocess
import os
import requests
import json
from typing import Dict, Any, List

class AgentTools:
    @staticmethod
    def execute_bash(command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def write_file(file_path: str, content: str) -> str:
        try:
            # 安全逻辑：允许操作当前 Agent 目录或其他 Agent 的 workspace 目录
            abs_path = os.path.abspath(file_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def read_file(file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def call_peer_agent(agent_id: str, prompt: str) -> str:
        """
        向另一个 Agent 发送指令并获取回复。
        MRA 互操作核心：通过 Gateway 转发到目标 Agent 的端口。
        """
        gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8000")
        try:
            url = f"{gateway_url}/api/agents/{agent_id}/agent/chat"
            response = requests.post(
                url, 
                json={"prompt": prompt, "history": []},
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                return f"Response from {agent_id}:\n{data.get('response', '')}"
            else:
                return f"Error calling {agent_id}: Status {response.status_code} - {response.text}"
        except Exception as e:
            return f"Network Error calling {agent_id}: {str(e)}"

    @staticmethod
    def list_peers() -> str:
        """查看当前系统中活跃的同伴 Agent"""
        gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8000")
        try:
            response = requests.get(f"{gateway_url}/api/agents")
            if response.status_code == 200:
                agents = response.json()
                peer_list = []
                for a in agents:
                    peer_list.append(f"- ID: {a['id']} (Port: {a['port']})")
                return "Available Peer Agents:\n" + "\n".join(peer_list)
            return f"Error listing peers: {response.status_code}"
        except Exception as e:
            return f"Error listing peers: {str(e)}"

    @staticmethod
    def publish_to_shared(file_path: str) -> str:
        """MRA 自理：将生成的文件发布到公共共享区，方便用户下载"""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found"
        
        # 建立共享目录，确保在根目录级别 (../../workspace/.shared/)
        shared_dir = os.path.abspath(os.path.join(os.getcwd(), "../.shared"))
        os.makedirs(shared_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        agent_id = os.getenv("AGENT_ID", "unknown")
        # 采用前缀方案避免同名冲突
        target_name = f"{agent_id}_{filename}"
        target_path = os.path.join(shared_dir, target_name)
        
        try:
            import shutil
            shutil.copy2(file_path, target_path)
            return f"Successfully published {file_path} to shared area as {target_name}"
        except Exception as e:
            return f"Error publishing file: {str(e)}"

TOOL_SCHEMAS = [
    {
        "name": "execute_bash",
        "description": "Execute a bash command in the terminal and return its output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to run"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "write_file",
        "description": "MRA Core: Write/Edit code in current agent or PEER agent workspace. Use relative paths like '../Agent-02/app/main.py' to refactor peers.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "read_file",
        "description": "Read file content. Can read code from self or Peer agents.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "call_peer_agent",
        "description": "Send a chat message to another MRA agent to collaborate or delegate tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Target agent ID (e.g., Agent-02)"},
                "prompt": {"type": "string", "description": "Task description or question"}
            },
            "required": ["agent_id", "prompt"]
        }
    },
    {
        "name": "list_peers",
        "description": "List all active agents in the MRA system to identify potential refactoring targets.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "publish_to_shared",
        "description": "MRA Agent Autonomy: Move/Copy a generated file (like a patent, report, or binary) to the public shared area for user access.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Local path of the file within the agent's workspace"}
            },
            "required": ["file_path"]
        }
    }
]

def handle_tool_call(name: str, args: Dict[str, Any]) -> str:
    if name == "execute_bash":
        return AgentTools.execute_bash(args["command"])
    elif name == "write_file":
        return AgentTools.write_file(args["file_path"], args["content"])
    elif name == "read_file":
        return AgentTools.read_file(args["file_path"])
    elif name == "call_peer_agent":
        return AgentTools.call_peer_agent(args["agent_id"], args["prompt"])
    elif name == "list_peers":
        return AgentTools.list_peers()
    elif name == "publish_to_shared":
        return AgentTools.publish_to_shared(args["file_path"])
    return f"Unknown tool: {name}"
