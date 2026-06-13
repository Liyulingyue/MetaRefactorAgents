import subprocess
import os
import requests
import json
from typing import Dict, Any, List, Optional
from .plan import PlanService
from .registry import Tool, get_tool_registry

_plan_service: Optional[PlanService] = None

def get_plan_service() -> PlanService:
    global _plan_service
    if _plan_service is None:
        _plan_service = PlanService()
    return _plan_service


def _tool_schema_to_tool(schema: Dict[str, Any], impl_fn) -> Tool:
    class WrappedTool(Tool):
        name = schema["name"]
        description = schema["description"]
        parameters = schema["parameters"]

        def execute(self, **kwargs) -> str:
            return impl_fn(**kwargs)

    return WrappedTool()


def _register_builtin_tools() -> None:
    registry = get_tool_registry()
    mapping = {
        "execute_bash": AgentTools.execute_bash,
        "write_file": AgentTools.write_file,
        "read_file": AgentTools.read_file,
        "replace_string_in_file": AgentTools.replace_string_in_file,
        "append_to_file": AgentTools.append_to_file,
        "read_file_range": AgentTools.read_file_range,
        "tail_file": AgentTools.tail_file,
        "grep_file": AgentTools.grep_file,
        "call_peer_agent": AgentTools.call_peer_agent,
        "list_peers": AgentTools.list_peers,
        "publish_to_shared": AgentTools.publish_to_shared,
        "create_plan": AgentTools.create_plan,
        "add_task_to_plan": AgentTools.add_task_to_plan,
        "get_plan_status": AgentTools.get_plan_status,
        "update_task_progress": AgentTools.update_task_progress,
        "execute_next_plan_task": AgentTools.execute_next_plan_task,
    }
    for schema in TOOL_SCHEMAS:
        name = schema["name"]
        if name in mapping:
            registry.register(_tool_schema_to_tool(schema, mapping[name]))



def register_tool(tool: Tool) -> None:
    get_tool_registry().register(tool)


def unregister_tool(name: str) -> None:
    get_tool_registry().unregister(name)


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
    def replace_string_in_file(file_path: str, old_string: str, new_string: str) -> str:
        try:
            abs_path = os.path.abspath(file_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if old_string not in content:
                return f"Error: old_string not found in {file_path}"
            new_content = content.replace(old_string, new_string, 1)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return f"Successfully replaced 1 occurrence in {file_path}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def append_to_file(file_path: str, content: str) -> str:
        try:
            abs_path = os.path.abspath(file_path)
            with open(abs_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully appended to {file_path}"
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def read_file_range(file_path: str, start_line: int, end_line: int) -> str:
        try:
            abs_path = os.path.abspath(file_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            start = max(0, start_line - 1)
            end = min(len(lines), end_line)
            if start >= end:
                return f"Error: start_line ({start_line}) must be less than end_line ({end_line})"
            selected = lines[start:end]
            return f"Lines {start_line}-{end_line} of {file_path}:\n" + "".join(selected)
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def tail_file(file_path: str, num_lines: int) -> str:
        try:
            abs_path = os.path.abspath(file_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            tail = lines[-num_lines:] if num_lines <= len(lines) else lines
            return f"Last {len(tail)} lines of {file_path}:\n" + "".join(tail)
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def grep_file(file_path: str, pattern: str) -> str:
        try:
            import re
            abs_path = os.path.abspath(file_path)
            results = []
            with open(abs_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if re.search(pattern, line):
                        results.append(f"{i}: {line.rstrip()}")
            if not results:
                return f"No matches for '{pattern}' in {file_path}"
            return f"Matches ({len(results)}) in {file_path}:\n" + "\n".join(results)
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
        
        # 建立共享目录，确保在根目录级别 (../../workspace/shared_files/)
        shared_dir = os.path.abspath(os.path.join(os.getcwd(), "../shared_files"))
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



    @staticmethod
    def create_plan(name: str, description: str = "", tasks: Optional[List[dict]] = None) -> str:
        """创建一个新的任务计划"""
        try:
            service = get_plan_service()
            plan = service.create_plan(name=name, description=description, tasks=tasks)
            return f"Plan created successfully. ID: {plan.id}, Name: {plan.name}"
        except Exception as e:
            return f"Error creating plan: {str(e)}"

    @staticmethod
    def add_task_to_plan(plan_id: str, name: str, action: str, params: Optional[dict] = None, depends_on: Optional[List[str]] = None) -> str:
        """向现有计划添加任务"""
        try:
            service = get_plan_service()
            task_data = {
                "name": name,
                "action": action,
                "params": params or {},
                "depends_on": depends_on or []
            }
            task = service.add_task(plan_id, task_data)
            if not task:
                return f"Error: Plan {plan_id} not found"
            return f"Task added to plan {plan_id}. Task ID: {task.id}"
        except Exception as e:
            return f"Error adding task: {str(e)}"

    @staticmethod
    def get_plan_status(plan_id: str) -> str:
        """获取计划的当前状态和进度"""
        try:
            service = get_plan_service()
            plan = service.get_plan(plan_id)
            if not plan:
                return f"Error: Plan {plan_id} not found"
            return json.dumps(plan.to_dict(), indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error getting plan: {str(e)}"

    @staticmethod
    def update_task_progress(plan_id: str, task_id: str, status: str, result: Optional[dict] = None) -> str:
        """更新任务状态 (pending, running, completed, failed)"""
        try:
            service = get_plan_service()
            task = service.update_task_status(plan_id, task_id, status, result)
            if not task:
                return f"Error: Plan or task not found"
            return f"Task {task_id} in Plan {plan_id} updated to {status}"
        except Exception as e:
            return f"Error updating task: {str(e)}"

    @staticmethod
    def execute_next_plan_task(plan_id: str) -> str:
        """执行计划中的下一个待办任务。这会返回任务详情。"""
        try:
            service = get_plan_service()
            result = service.execute_next_task(plan_id)
            if not result:
                return f"No more pending tasks in Plan {plan_id} or Plan completed."
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error executing next task: {str(e)}"

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
    },
    {
        "name": "replace_string_in_file",
        "description": "Atomically replace the first occurrence of a string in a file. Use this instead of write_file for small edits to avoid large token waste.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "old_string": {"type": "string", "description": "Exact string to search for and replace"},
                "new_string": {"type": "string", "description": "Replacement string"}
            },
            "required": ["file_path", "old_string", "new_string"]
        }
    },
    {
        "name": "append_to_file",
        "description": "Append content to the end of a file. Useful for logs, long documents, or appending new sections.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to append"}
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "read_file_range",
        "description": "Read a specific range of lines from a file by line numbers. Use for navigating large files without loading everything into context.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "start_line": {"type": "integer", "description": "Starting line number (1-indexed)"},
                "end_line": {"type": "integer", "description": "Ending line number (1-indexed, exclusive)"}
            },
            "required": ["file_path", "start_line", "end_line"]
        }
    },
    {
        "name": "tail_file",
        "description": "Get the last N lines of a file. Ideal for reading recent log entries without loading the entire file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "num_lines": {"type": "integer", "description": "Number of lines to read from the end", "default": 50}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "grep_file",
        "description": "Search for a regex pattern within a file and return matching lines with line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"},
                "pattern": {"type": "string", "description": "Regex pattern to search for"}
            },
            "required": ["file_path", "pattern"]
        }
    },
    {
        "name": "create_plan",
        "description": "Create a new multi-step engineering plan. Use for complex tasks like patent writing or code refactoring.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short name for the plan"},
                "description": {"type": "string", "description": "Detailed goal of the plan"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Task name"},
                            "action": {"type": "string", "description": "Tool name (e.g., execute_bash, write_file)"},
                            "params": {"type": "object", "description": "Tool parameters"},
                            "depends_on": {"type": "array", "items": {"type": "string"}, "description": "Task IDs this task depends on"}
                        }
                    }
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "add_task_to_plan",
        "description": "Append a new task to an existing plan.",
        "parameters": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "Plan ID"},
                "name": {"type": "string", "description": "Task name"},
                "action": {"type": "string", "description": "Tool name"},
                "params": {"type": "object", "description": "Tool parameters", "nullable": True},
                "depends_on": {"type": "array", "items": {"type": "string"}, "nullable": True}
            },
            "required": ["plan_id", "name", "action"]
        }
    },
    {
        "name": "get_plan_status",
        "description": "Inspect the overall status and detailed task results of a plan.",
        "parameters": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "Plan ID"}
            },
            "required": ["plan_id"]
        }
    },
    {
        "name": "update_task_progress",
        "description": "MUST CALL: Update a task's status (running, completed, failed) and attach results for subsequent tasks to use.",
        "parameters": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "Plan ID"},
                "task_id": {"type": "string", "description": "Task ID"},
                "status": {"type": "string", "enum": ["pending", "running", "completed", "failed"]},
                "result": {"type": "object", "description": "Outcome of the task execution"}
            },
            "required": ["plan_id", "task_id", "status"]
        }
    },
    {
        "name": "execute_next_plan_task",
        "description": "ENGINEERING ENGINE: Request the next high-priority pending task from the plan and set it to 'running'.",
        "parameters": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "Plan ID"}
            },
            "required": ["plan_id"]
        }
    }
]

_register_builtin_tools()


def handle_tool_call(name: str, args: Dict[str, Any]) -> str:
    return get_tool_registry().execute(name, args)
