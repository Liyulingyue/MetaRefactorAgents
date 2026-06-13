import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from .tools import TOOL_SCHEMAS, handle_tool_call, get_plan_service
from .config import settings
from .skills import SkillsLoader

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

        self.system_prompt = (
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

    def run(self, prompt: str, history: List[Dict] = None, on_update: Optional[Callable[[Dict], None]] = None):
        if history is None:
            history = []
        
        history.append({"role": "user", "content": prompt})
        self.log_thought("user", prompt)
        
        if on_update:
            on_update(history[-1])

        plan_service = get_plan_service()
        skills_context_static = "\n" + self.skills_loader.build_skills_summary()

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
            system_msg = self.system_prompt

            if settings.SKILLS_INJECTION_MODE == "dynamic":
                skills_context = "\n" + self.skills_loader.build_skills_summary()
            else:
                skills_context = skills_context_static
            if skills_context:
                system_msg += skills_context

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

            messages = [{"role": "system", "content": system_msg}] + history
            
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"]
                    }
                } for t in TOOL_SCHEMAS
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
