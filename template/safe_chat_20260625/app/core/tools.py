import subprocess
import os
import requests
import json
import uuid
import time
from typing import Dict, Any, List, Optional
from .plan import PlanService
from .registry import Tool, get_tool_registry
from .config import settings

_plan_service: Optional[PlanService] = None

PROTECTED_PATHS = ["./app/", "./app", "app/"]
TRUSTED_PATHS_FILE = "./trusted_paths.json"

def get_plan_service() -> PlanService:
    global _plan_service
    if _plan_service is None:
        _plan_service = PlanService()
    return _plan_service


def _load_trusted_paths() -> dict:
    if os.path.exists(TRUSTED_PATHS_FILE):
        try:
            with open(TRUSTED_PATHS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"trusted_files": [], "trusted_patterns": []}


def _save_trusted_paths(data: dict) -> None:
    with open(TRUSTED_PATHS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _is_protected_path(path: str) -> bool:
    abs_path = os.path.abspath(path)
    for protected in PROTECTED_PATHS:
        protected_abs = os.path.abspath(protected)
        if abs_path.startswith(protected_abs):
            return True
    return False


def _is_trusted_path(path: str) -> bool:
    trusted = _load_trusted_paths()
    abs_path = os.path.abspath(path)
    for pattern in trusted.get("trusted_files", []):
        if os.path.abspath(pattern) == abs_path:
            return True
    for pattern in trusted.get("trusted_patterns", []):
        if pattern.endswith("*"):
            prefix = os.path.abspath(pattern[:-1])
            if abs_path.startswith(prefix):
                return True
    return False


PENDING_CONFIRMS: dict[str, dict] = {}


def create_confirm_request(tool: str, action: str, path: str, details: str = "") -> str:
    confirm_id = str(uuid.uuid4())[:8]
    PENDING_CONFIRMS[confirm_id] = {
        "tool": tool,
        "action": action,
        "path": path,
        "details": details,
        "created_at": time.time(),
        "used": False,
    }
    return confirm_id


def check_and_confirm_path(tool: str, action: str, path: str, details: str = "") -> str:
    if not _is_protected_path(path):
        return ""
    if _is_trusted_path(path):
        return ""
    confirm_id = create_confirm_request(tool, action, path, details)
    return f"[ACTION_REQUIRES_CONFIRM:confirm_id={confirm_id},tool={tool},path={path},action={action}]"


def consume_confirm(confirm_id: str, mode: str) -> tuple[bool, str]:
    if confirm_id not in PENDING_CONFIRMS:
        return False, "Confirmation not found or expired"
    confirm = PENDING_CONFIRMS[confirm_id]
    if confirm["used"]:
        return False, "Confirmation already used"
    confirm["used"] = True
    if mode == "always":
        trusted = _load_trusted_paths()
        path = confirm["path"]
        abs_path = os.path.abspath(path)
        if abs_path not in trusted["trusted_files"]:
            trusted["trusted_files"].append(abs_path)
            _save_trusted_paths(trusted)
    return True, "Confirmed"


def get_pending_confirm(confirm_id: str) -> dict | None:
    return PENDING_CONFIRMS.get(confirm_id)


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
        "create_cron": AgentTools.create_cron,
        "list_crons": AgentTools.list_crons,
        "delete_cron": AgentTools.delete_cron,
        "enable_cron": AgentTools.enable_cron,
        "disable_cron": AgentTools.disable_cron,
        "send_alert": AgentTools.send_alert,
    }
    for schema in TOOL_SCHEMAS:
        name = schema["name"]
        if name in mapping:
            registry.register(_tool_schema_to_tool(schema, mapping[name]))
        elif name == "reload_mcp_tools":
            registry.register(_tool_schema_to_tool(schema, reload_mcp_tools))


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
        protected_check = check_and_confirm_path("write_file", "write", file_path)
        if protected_check:
            return protected_check
        try:
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
        protected_check = check_and_confirm_path("replace_string_in_file", "replace", file_path)
        if protected_check:
            return protected_check
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
        protected_check = check_and_confirm_path("append_to_file", "append", file_path)
        if protected_check:
            return protected_check
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
        gateway_url = settings.GATEWAY_URL or os.getenv("GATEWAY_URL", "")
        if not gateway_url:
            return "Gateway not configured; peer calls are disabled in standalone mode."
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
        gateway_url = settings.GATEWAY_URL or os.getenv("GATEWAY_URL", "")
        if not gateway_url:
            return "Gateway not configured; peer listing is disabled in standalone mode."
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

    @staticmethod
    def create_cron(name: str, kind: str, message: str, session_key: Optional[str] = None, every_ms: Optional[int] = None, at_ms: Optional[int] = None, expr: Optional[str] = None, tz: Optional[str] = None, silent: bool = False, notify_on_error: bool = True) -> str:
        """创建一个新的定时任务"""
        try:
            from app.core.cron_service import CronService
            from app.core.cron_types import CronSchedule
            from pathlib import Path
            from app.core.config import settings
            from app.core.session_context import get_current_session

            if session_key is None:
                session_key = get_current_session()

            if session_key is None:
                return "Error: No session_key provided and no active session context. Please specify session_key explicitly."

            service = CronService(Path(settings.CRON_STORAGE_PATH) / "jobs.json")
            schedule = CronSchedule(kind=kind, every_ms=every_ms, at_ms=at_ms, expr=expr, tz=tz)
            job = service.add_job(name=name, schedule=schedule, message=message, session_key=session_key, silent=silent, notify_on_error=notify_on_error)
            return f"Cron job created: ID={job.id}, Name={job.name}"
        except Exception as e:
            return f"Error creating cron: {str(e)}"

    @staticmethod
    def list_crons(include_disabled: bool = False) -> str:
        """列出所有定时任务"""
        try:
            from app.core.cron_service import CronService
            from pathlib import Path
            from app.core.config import settings

            service = CronService(Path(settings.CRON_STORAGE_PATH) / "jobs.json")
            jobs = service.list_jobs(include_disabled=include_disabled)
            if not jobs:
                return "No cron jobs found."
            result = [f"- {j.name} (ID: {j.id}, enabled: {j.enabled}, next_run: {j.state.next_run_at_ms})" for j in jobs]
            return "Cron jobs:\n" + "\n".join(result)
        except Exception as e:
            return f"Error listing crons: {str(e)}"

    @staticmethod
    def delete_cron(job_id: str) -> str:
        """删除指定的定时任务"""
        try:
            from app.core.cron_service import CronService
            from pathlib import Path
            from app.core.config import settings

            service = CronService(Path(settings.CRON_STORAGE_PATH) / "jobs.json")
            result = service.remove_job(job_id)
            if result == "removed":
                return f"Cron job {job_id} deleted."
            elif result == "protected":
                return f"Cannot delete protected system job {job_id}."
            else:
                return f"Cron job {job_id} not found."
        except Exception as e:
            return f"Error deleting cron: {str(e)}"

    @staticmethod
    def enable_cron(job_id: str) -> str:
        """启用指定的定时任务"""
        try:
            from app.core.cron_service import CronService
            from pathlib import Path
            from app.core.config import settings

            service = CronService(Path(settings.CRON_STORAGE_PATH) / "jobs.json")
            job = service.enable_job(job_id, enabled=True)
            if job:
                return f"Cron job {job_id} enabled."
            return f"Cron job {job_id} not found."
        except Exception as e:
            return f"Error enabling cron: {str(e)}"

    @staticmethod
    def disable_cron(job_id: str) -> str:
        """禁用指定的定时任务"""
        try:
            from app.core.cron_service import CronService
            from pathlib import Path
            from app.core.config import settings

            service = CronService(Path(settings.CRON_STORAGE_PATH) / "jobs.json")
            job = service.enable_job(job_id, enabled=False)
            if job:
                return f"Cron job {job_id} disabled."
            return f"Cron job {job_id} not found."
        except Exception as e:
            return f"Error disabling cron: {str(e)}"

    @staticmethod
    def send_alert(message: str) -> str:
        """Send an alert message to the user from a silent cron task.

        This tool is only effective when the current task is running under a
        silent cron job. The alert is queued and delivered by the cron runner
        after the Agent finishes. Outside of a silent cron context this is a
        no-op.
        """
        try:
            from .cron_context import ALERT_SINK_CTX
            sink = ALERT_SINK_CTX.get()
            if sink is None:
                return "send_alert is only available inside a silent cron job; this call was ignored."
            sink.append(str(message))
            return f"Alert queued (total: {len(sink)})"
        except Exception as e:
            return f"Error sending alert: {str(e)}"


def reload_mcp_tools() -> str:
    """Hot-reload all MCP tools from .mcp.json config. Use after editing MCP server config."""
    try:
        from .mcp_client import reload_mcp_tools as _reload
        result = _reload()
        lines = []
        for server, tools in result.items():
            lines.append(f"  {server}: {len(tools)} tools reloaded")
        if not lines:
            return "No MCP servers loaded."
        return "MCP tools reloaded:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error reloading MCP tools: {str(e)}"


TOOL_SCHEMAS = [
    {
        "name": "create_cron",
        "description": "Create a new scheduled cron job that runs an Agent and sends result to Feishu. If session_key is not provided, it will use the current chat session. Set silent=True to suppress the result message on success (alerts via send_alert still work).",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name for the cron job"},
                "kind": {"type": "string", "enum": ["every", "at", "cron"], "description": "Schedule type: 'every' for interval, 'at' for one-time, 'cron' for cron expression"},
                "every_ms": {"type": "integer", "description": "Interval in milliseconds (for kind='every')"},
                "at_ms": {"type": "integer", "description": "Timestamp in ms for one-time execution (for kind='at')"},
                "expr": {"type": "string", "description": "Cron expression like '0 9 * * *' (for kind='cron')"},
                "tz": {"type": "string", "description": "Timezone like 'Asia/Shanghai' (for kind='cron')"},
                "message": {"type": "string", "description": "Prompt for the Agent to execute (will be sent as Agent input)"},
                "session_key": {"type": "string", "description": "Feishu chat_id to send the Agent's result to. If not provided, uses current session."},
                "silent": {"type": "boolean", "description": "If true, the Agent's final response is NOT sent to the user on success. Errors are still reported unless notify_on_error is also false. The Agent can call send_alert to push urgent messages even in silent mode.", "default": False},
                "notify_on_error": {"type": "boolean", "description": "When silent=true, still send a message to the user if the Agent raises an exception. Defaults to true.", "default": True},
            },
            "required": ["name", "kind", "message"]
        }
    },
    {
        "name": "list_crons",
        "description": "List all scheduled cron jobs.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_disabled": {"type": "boolean", "description": "Include disabled jobs", "default": False}
            }
        }
    },
    {
        "name": "delete_cron",
        "description": "Delete a cron job by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "The cron job ID to delete"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "enable_cron",
        "description": "Enable a disabled cron job.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "The cron job ID to enable"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "disable_cron",
        "description": "Disable an active cron job.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "The cron job ID to disable"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "send_alert",
        "description": "Queue an alert message to the user from a silent cron task. The alert is delivered after the Agent finishes. Only effective inside a silent cron job; in normal conversations this is a no-op. Use sparingly for genuine exceptions or situations requiring user attention.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Alert content to deliver to the user"}
            },
            "required": ["message"]
        }
    },
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
    },
    {
        "name": "reload_mcp_tools",
        "description": "Hot-reload all MCP tools. Call this after editing .mcp.json to apply changes.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]

_register_builtin_tools()


def handle_tool_call(name: str, args: Dict[str, Any]) -> str:
    return get_tool_registry().execute(name, args)
