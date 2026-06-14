import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from .tools import TOOL_SCHEMAS, handle_tool_call, get_plan_service
from .registry import get_tool_registry
from .config import settings
from .skills import SkillsLoader
from .memory import MemoryLoader
from .autocompact import ConversationCompactor

MAX_THOUGHTS_SIZE = 100 * 1024

class Agent:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.client = OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url or settings.OPENAI_URL
        )
        self.model = model or settings.OPENAI_MODEL_NAME
        self.agent_id = os.getenv("AGENT_ID", "unknown")
        self.thought_log_path = f"logs/thoughts.md"
        self.error_log_path = f"logs/error.log"
        os.makedirs("logs", exist_ok=True)

        self.skills_loader = SkillsLoader(workspace_dir=".")
        self.memory_loader = MemoryLoader(workspace_dir=".")

        self._mcp_loaded = False
        if getattr(settings, "MCP_ENABLED", True):
            try:
                from .mcp_client import load_mcp_tools
                result = load_mcp_tools()
                self._mcp_loaded = True
                mcp_count = sum(len(v) for v in result.values())
                if mcp_count > 0:
                    print(f"MCP tools loaded: {mcp_count} from {len(result)} servers")
            except Exception as e:
                print(f"Warning: Failed to load MCP tools: {e}")

        self.compactor = ConversationCompactor(threshold=settings.HISTORY_SUMMARY_THRESHOLD)

        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        path = settings.SYSTEM_FILE_PATH
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return (
            "You are a versatile and autonomous general-purpose agent (MRA).\n"
            "MRA (MetaRefactorAgents) is a system where agents collaborate to refactor code across the fleet.\n"
            "\n"
            "FLEET COLLABORATION PROTOCOL:\n"
            "1. DISCOVERY: Use 'list_peers' to see other active agents in the workspace.\n"
            "2. COOPERATION: Use 'call_peer_agent' to delegate or sync with other agents via API.\n"
            "3. REFACTOR: You are explicitly allowed and encouraged to use 'write_file' or 'execute_bash' to read/edit the code of PEER agents (e.g., in '../Agent-02/').\n"
            "4. EVOLUTION: You can optimize your own code or your peers' code to improve the overall system performance.\n"
            "5. FILE SHARING: You have a private workspace (./) and access to a shared workspace (../shared_files/).\n"
            "   - Place final reports, patents, or assets intended for the user in your root directory or '../shared_files/'.\n"
            "   - The user can view and download files from these areas via the Dashboard.\n"
            "\n"
            "ENGINEERING PLANNER PROTOCOL:\n"
            "1. STRUCTURE: For multi-step tasks (e.g., patent writing), you MUST use 'create_plan' to define the workflow.\n"
            "2. EXECUTION: Use 'execute_next_plan_task' to fetch the next instruction from your active plan.\n"
            "3. UPDATING: After EACH task, you MUST call 'update_task_progress' to mark it as 'completed' (or 'failed') and provide findings.\n"
            "4. ADAPTATION: If a task's result changes the project scope, use 'add_task_to_plan' to modify your remaining work.\n"
            "5. COMPLETION: Once all plan tasks are done, provide a final summary to the user.\n"
            "\n"
            "CORE PROTOCOL:\n"
            "1. ANALYZE: Understand the mission and identification of the target agent.\n"
            "2. ACTION: Leverage standard tools and P2P tools for cross-agent refactoring.\n"
            "3. LOG: Your internal reasoning process will be logged. Be explicit about which peer you are refactoring.\n"
            "4. RESPONSE: Provide clear, concise reports on your changes."
        )

    def _archive_and_reset(self):
        os.makedirs("logs/archived", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = f"logs/archived/thoughts_{ts}.md"
        os.rename(self.thought_log_path, archive_path)
        with open(self.thought_log_path, "w", encoding="utf-8") as f:
            f.write(f"# Thoughts Log (archived: {ts})\n\n")

    def log_thought(self, role: str, content: str):
        if os.path.exists(self.thought_log_path):
            size = os.path.getsize(self.thought_log_path)
            if size >= MAX_THOUGHTS_SIZE:
                self._archive_and_reset()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.thought_log_path, "a", encoding="utf-8") as f:
            f.write(f"## [{timestamp}] {role.upper()}\n{content}\n\n")

    def log_error(self, context: str, exc: Exception):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.error_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {context}: {type(exc).__name__}: {exc}\n")

    def _get_tool_definitions(self) -> list[dict]:
        """Get all tool definitions: built-in TOOL_SCHEMAS + dynamic MCP tools from registry."""
        if settings.MCP_INJECTION_MODE == "dynamic":
            from .mcp_client import reload_mcp_tools as _reload
            _reload()
        registry = get_tool_registry()
        mcp_defs = registry.get_definitions()
        all_defs = {d["name"]: d for d in TOOL_SCHEMAS}
        for d in mcp_defs:
            all_defs[d["name"]] = d
        return list(all_defs.values())

    def run(self, prompt: str, history: List[Dict] = None, on_update: Optional[Callable[[Dict], None]] = None, on_compact: Optional[Callable[[str], None]] = None):
        if history is None:
            history = []
        
        history.append({"role": "user", "content": prompt})
        self.log_thought("user", prompt)
        
        if on_update:
            on_update(history[-1])

        plan_service = get_plan_service()
        skills_context_static = "\n" + self.skills_loader.build_skills_summary()
        memory_context_static = self.memory_loader.build_memory_summary()

        if settings.PLAN_INJECTION_MODE == "static":
            active_plans = [p for p in plan_service.list_plans() if p["status"] in ("pending", "running")]
            plan_context_static = ""
            if active_plans:
                plan_context_static = "\nACTIVE ENGINEERING PLANS:\n"
                for p in active_plans:
                    plan_context_static += f"- Plan [{p['name']}] (ID: {p['id']}): Current Task Index: {p.get('current_task_index', 0)} / {len(p.get('tasks', []))}\n"
                plan_context_static += "\nNOTE: If you are currently working on a plan, use 'execute_next_plan_task' to proceed."
        else:
            plan_context_static = None

        while True:
            if settings.SYSTEM_INJECTION_MODE == "dynamic":
                system_msg = self._load_system_prompt()
            else:
                system_msg = self.system_prompt

            if settings.SKILLS_INJECTION_MODE == "dynamic":
                skills_context = "\n" + self.skills_loader.build_skills_summary()
            else:
                skills_context = skills_context_static
            if skills_context:
                system_msg += skills_context

            if settings.MEMORY_INJECTION_MODE == "dynamic":
                memory_context = self.memory_loader.build_memory_summary()
            else:
                memory_context = memory_context_static
            if memory_context:
                system_msg += memory_context

            if settings.PLAN_INJECTION_MODE == "dynamic":
                active_plans = [p for p in plan_service.list_plans() if p["status"] in ("pending", "running")]
                plan_context = ""
                if active_plans:
                    plan_context = "\nACTIVE ENGINEERING PLANS:\n"
                    for p in active_plans:
                        plan_context += f"- Plan [{p['name']}] (ID: {p['id']}): Current Task Index: {p.get('current_task_index', 0)} / {len(p.get('tasks', []))}\n"
                    plan_context += "\nNOTE: If you are currently working on a plan, use 'execute_next_plan_task' to proceed."
                if plan_context:
                    system_msg += plan_context
            else:
                if plan_context_static:
                    system_msg += plan_context_static

            if self.compactor.threshold > 0:
                prev_len = len(history)
                history = self.compactor.check_and_compact(history, self.client, self.model)
                if len(history) != prev_len and on_compact and self.compactor.last_summary:
                    on_compact(self.compactor.last_summary)

            messages = [{"role": "system", "content": system_msg}] + history

            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"]
                    }
                } for t in self._get_tool_definitions()
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )

            assistant_msg = response.choices[0].message
            content = assistant_msg.content
            tool_calls = assistant_msg.tool_calls

            history_entry = {
                "role": "assistant",
                "content": content,
            }
            if tool_calls:
                history_entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            
            history.append(history_entry)
            self.log_thought("assistant", f"Content: {content}\nTool Calls: {json.dumps(history_entry.get('tool_calls'), indent=2) if tool_calls else 'None'}")
            
            if on_update:
                on_update(history[-1])

            if tool_calls:
                for tool_call in tool_calls:
                    name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except Exception as e:
                        self.log_error(f"Parse args for {name}", e)
                        result = f"Error parsing arguments: {e}"
                    else:
                        self.log_thought("tool_call", f"Calling {name} with {json.dumps(args)}")
                        try:
                            result = handle_tool_call(name, args)
                        except Exception as e:
                            self.log_error(f"execute tool {name}", e)
                            result = f"Error executing {name}: {e}"
                        self.log_thought("tool_result", f"Result: {result}")

                    history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": result
                    })
                    if on_update:
                        on_update(history[-1])
            else:
                return content
