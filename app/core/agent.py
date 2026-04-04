import json
import os
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from .tools import TOOL_SCHEMAS, handle_tool_call
from .config import settings

class Agent:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.client = OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url or settings.OPENAI_BASE_URL
        )
        self.model = model or settings.DEFAULT_MODEL
        self.system_prompt = (
            "You are a versatile and autonomous general-purpose agent.\n"
            "Your goal is to assist the user with any task, leveraging available tools when necessary.\n"
            "CORE PROTOCOL:\n"
            "1. ANALYZE: Understand the user's intent and break it down into steps.\n"
            "2. ACTION: Use 'execute_bash' for terminal commands, 'write_file' to create/edit files, and 'read_file' to inspect the environment.\n"
            "3. REFLECT: Observe tool outputs and adjust your plan accordingly.\n"
            "4. RESPONSE: Provide clear, concise, and helpful final answers."
        )

    def run(self, prompt: str, history: List[Dict] = None, on_update: Optional[Callable[[Dict], None]] = None):
        if history is None:
            history = []
        
        history.append({"role": "user", "content": prompt})
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
            if on_update:
                on_update(history[-1])

            if tool_calls:
                for tool_call in tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    print(f"Tool Call: {name}({args})")
                    result = handle_tool_call(name, args)
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
