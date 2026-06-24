import asyncio
import json
import hashlib
import hmac
import time
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.core.feishu import feishu_client
from app.core.agent import Agent

router = APIRouter()
agent_instance = None


def get_agent() -> Agent:
    global agent_instance
    if agent_instance is None:
        agent_instance = Agent()
    return agent_instance


class FeishuEvent(BaseModel):
    schema: str = ""
    header: dict = {}
    event: dict = {}


def verify_sign(encrypt_key: str, timestamp: str, sign: str) -> bool:
    if not encrypt_key:
        return True
    string_to_sign = f"{timestamp}{encrypt_key}"
    calculated_sign = hashlib.sha1(string_to_sign.encode()).hexdigest()
    return calculated_sign == sign


async def process_message(event: dict, chat_id: str = None) -> str:
    message_content = event.get("message", {})
    content = message_content.get("content", "{}")
    
    try:
        content_obj = json.loads(content)
    except json.JSONDecodeError:
        content_obj = {"text": content}
    
    text = content_obj.get("text", "").strip()
    if not text:
        return "Received empty message"
    
    def on_compact_start():
        if chat_id:
            feishu_client.send_text(
                receive_id=chat_id,
                receive_id_type="chat_id",
                content="📝 正在压缩上下文，请稍候..."
            )
    
    def on_compact(summary: str):
        if chat_id:
            feishu_client.send_text(
                receive_id=chat_id,
                receive_id_type="chat_id",
                content="✅ 上下文已压缩完成"
            )
    
    agent = get_agent()
    response = await asyncio.to_thread(
        agent.run, text, on_compact=on_compact, on_compact_start=on_compact_start
    )
    
    return response or "处理完成"


@router.post("/webhook")
async def feishu_webhook(request: Request):
    if not feishu_client.is_enabled():
        raise HTTPException(status_code=503, detail="Feishu integration not configured")
    
    body = await request.json()
    header = body.get("header", {})
    event_type = header.get("event_type", "")
    
    if event_type == "im.message.receive_v1":
        event = body.get("event", {})
        message = event.get("message", {})
        
        if message.get("msg_type") != "text":
            return {"code": 0}
        
        sender = event.get("sender", {})
        if sender.get("sender_type") == "bot":
            return {"code": 0}
        
        chat_id = message.get("chat_id")
        response = await process_message(event, chat_id=chat_id)
        feishu_client.send_text(
            receive_id=chat_id,
            receive_id_type="chat_id",
            content=response
        )
    
    return {"code": 0}


@router.get("/webhook")
async def feishu_verify(request: Request):
    challenge = request.query_params.get("challenge")
    if challenge:
        return {"challenge": challenge}
    return {"code": 0}
