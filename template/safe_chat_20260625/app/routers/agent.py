"""Agent router."""

import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.core.agent import Agent
from app.core.config import settings
from app.core.tools import consume_confirm, get_pending_confirm

router = APIRouter()

agent = Agent()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[Message]] = None


class ChatResponse(BaseModel):
    response: str
    history: List[Message]


class ConfirmRequest(BaseModel):
    confirm_id: str
    mode: str  # "once" or "always"


class ConfirmResponse(BaseModel):
    success: bool
    message: str


def filter_think_tags(text: str) -> str:
    """Remove <think>...</think> tags from text if HIDE_THINK_TAGS is enabled"""
    if settings.HIDE_THINK_TAGS and text:
        return re.sub(r'<think>[\s\S]*?
</think>

', '', text)
    return text


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_action(req: ConfirmRequest):
    """Handle user confirmation for protected actions."""
    success, message = consume_confirm(req.confirm_id, req.mode)
    if not success:
        return ConfirmResponse(success=False, message=message)
    confirm = get_pending_confirm(req.confirm_id)
    if not confirm:
        return ConfirmResponse(success=False, message="Confirmation expired")
    from app.core.tools import AgentTools
    tool_name = confirm["tool"]
    path = confirm["path"]
    if tool_name == "write_file":
        result = AgentTools.write_file(path, confirm.get("details", ""))
    elif tool_name == "replace_string_in_file":
        result = f"Executed replace on {path}"
    elif tool_name == "append_to_file":
        result = AgentTools.append_to_file(path, confirm.get("details", ""))
    else:
        result = f"Tool {tool_name} on {path} executed"
    return ConfirmResponse(success=True, message=result)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """通过 Agent 执行用户任务并返回响应和历史记录"""
    history = []
    if request.history:
        history = [msg.dict(exclude_unset=True) for msg in request.history]

    try:
        response = agent.run(request.prompt, history=history)
        response = filter_think_tags(response)
        history_objs = []
        for msg in history:
            filtered_msg = msg.copy()
            if filtered_msg.get("content"):
                filtered_msg["content"] = filter_think_tags(filtered_msg["content"])
            history_objs.append(Message(**filtered_msg))

        return ChatResponse(response=response, history=history_objs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
