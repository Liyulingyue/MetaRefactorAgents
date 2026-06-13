from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatRequest, ChatResponse, Message
from app.core.agent import Agent
from typing import List

router = APIRouter()
agent = Agent()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """通过 Agent 执行用户任务并返回响应和历史记录"""
    history = []
    if request.history:
        history = [msg.dict(exclude_unset=True) for msg in request.history]
    
    try:
        # 执行 Agent 循环
        response = agent.run(request.prompt, history=history)
        
        # 将历史记录转换回 Pydantic 对象
        history_objs = [Message(**msg) for msg in history]
        
        return ChatResponse(response=response, history=history_objs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
