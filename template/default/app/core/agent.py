import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from .tools import TOOL_SCHEMAS, handle_tool_call
from .config import settings

class Agent:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.client = OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url or settings.OPENAI_URL
        )
        self.model = model or settings.OPENAI_MODEL_NAME
        self.agent_id = os.getenv("AGENT_ID", "unknown")
        self.thought_log_path = f"logs/thoughts.md"
        
        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)
        
        self.system_prompt = (
            "You are a versatile and autonomous general-purpose agent (MRA).\n"
            "MRA (MetaRefactorAgents) is a system where agents collaborate to refactor code across the fleet.\n"
            "\n"
            "FLEET COLLABORATION PROTOCOL:\n"
            "1. DISCOVERY: Use 'list_peers' to see other active agents in the workspace.\n"
            "2. COOPERATION: Use 'call_peer_agent' to delegate or sync with other agents via API.\n"
            "3. REFACTOR: You are explicitly allowed and encouraged to use 'write_file' or 'execute_bash' to read/edit the code of PEER agents (e.g., in '../Agent-02/').\n"
            "4. EVOLUTION: You can optimize your own code or your peers' code to improve the overall system performance.\n"
            "5. FILE SHARING: You have a private workspace (./) and access to a shared workspace (../.shared/).\n"
            "   - Place final reports, patents, or assets intended for the user in your root directory or '../.shared/'.\n"
            "   - The user can view and download files from these areas via the Dashboard.\n"
            "\n"
            "CORE PROTOCOL:\n"
            "1. ANALYZE: Understand the mission and identification of the target agent.\n"
            "2. ACTION: Leverage standard tools and P2P tools for cross-agent refactoring.\n"
            "3. LOG: Your internal reasoning process will be logged. Be explicit about which peer you are refactoring.\n"
            "4. RESPONSE: Provide clear, concise reports on your changes."
        )

    def log_thought(self, role: str, content: str):
        """记录思维日志到本地文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.thought_log_path, "a", encoding="utf-8") as f:
            f.write(f"## [{timestamp}] {role.upper()}\n{content}\n\n")

    def run(self, prompt: str, history: List[Dict] = None, on_update: Optional[Callable[[Dict], None]] = None):
        if history is None:
            history = []
        
        history.append({"role": "user", "content": prompt})
        self.log_thought("user", prompt)
        
        if on_update:
            on_update(history[-1])

        while True:
            messages = [{"role": "system", "content": self.system_prompt}] + history
            
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
                    args = json.loads(tool_call.function.arguments)
                    
                    self.log_thought("tool_call", f"Calling {name} with {json.dumps(args)}")
                    result = handle_tool_call(name, args)
                    self.log_thought("tool_result", f"Result: {result}")
                    print(f"Tool Call: {name}({args})")
                    print(f"Result: {result[:100]}...")

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
