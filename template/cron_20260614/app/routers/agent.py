from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.core.agent import Agent
from app.core.config import settings
from typing import List
import re

router = APIRouter()
agent = Agent()

def filter_think_tags(text: str) -> str:
    """Remove <think>...</think> tags from text if HIDE_THINK_TAGS is enabled"""
    if settings.HIDE_THINK_TAGS and text:
        return re.sub(r'<think>[\s\S]*?</think>', '', text)
    return text

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """通过 Agent 执行用户任务并返回响应和历史记录"""
    history = []
    if request.history:
        history = [msg.dict(exclude_unset=True) for msg in request.history]
    
    try:
        # 执行 Agent 循环
        response = agent.run(request.prompt, history=history)
        
        # 过滤 think 标签
        response = filter_think_tags(response)
        
        # 将历史记录转换回 Pydantic 对象（同时过滤历史中的 think 标签）
        history_objs = []
        for msg in history:
            filtered_msg = msg.copy()
            if filtered_msg.get("content"):
                filtered_msg["content"] = filter_think_tags(filtered_msg["content"])
            history_objs.append(Message(**filtered_msg))
        
        return ChatResponse(response=response, history=history_objs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
