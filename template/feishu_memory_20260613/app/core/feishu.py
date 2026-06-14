from lark_oapi.api.im.v1 import CreateMessageRequest
import lark_oapi as lark
import json
import threading
import time
from collections import deque
from typing import Dict, Deque, Optional
from .config import settings


class FeishuClient:
    def __init__(self):
        self.app_id = settings.FEISHU_APP_ID
        self.app_secret = settings.FEISHU_APP_SECRET
        self.client = None
        if self.app_id and self.app_secret:
            self.client = lark.Client.builder()\
                .app_id(self.app_id)\
                .app_secret(self.app_secret)\
                .build()

    def is_enabled(self) -> bool:
        return self.client is not None

    def send_text(self, receive_id: str, receive_id_type: str, content: str) -> dict:
        if not self.is_enabled():
            return {"error": "Feishu client not configured"}

        try:
            from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
            request = CreateMessageRequest.builder()\
                .receive_id_type(receive_id_type)\
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("text")
                    .content(json.dumps({"text": str(content)})
                    .build())\
                .build())

            response = self.client.im.v1.message.create(request)

            if not response.success():
                print(f"❌ Feishu send failed: {response.code} - {response.msg}")
            else:
                print(f"✅ Feishu reply sent: {receive_id}")

            return response.body if response else {"error": "No response"}
        except Exception as e:
            print(f"❌ Feishu API error: {e}")
            return {"error": str(e)}


feishu_client = FeishuClient()


class ChatWorker:
    """
    Manages per-chat_id message queue and worker thread.
    Thread-safe singleton.
    """

    _instance: Optional["ChatWorker"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._queues: Dict[str, Deque] = {}
                    cls._instance._workers: Dict[str, threading.Thread] = {}
                    cls._instance._queue_lock = threading.Lock()
                    cls._instance._workers_lock = threading.Lock()
                    cls._instance._stop_flags: Dict[str, bool] = {}
                    cls._instance._feishu_client = None
        return cls._instance

    def _ensure_feishu(self):
        if self._feishu_client is None:
            self._feishu_client = feishu_client
        return self._feishu_client

    def enqueue(self, chat_id: str, text: str) -> None:
        with self._queue_lock:
            if chat_id not in self._queues:
                self._queues[chat_id] = deque()
                self._stop_flags[chat_id] = False
            self._queues[chat_id].append(text)

        with self._workers_lock:
            if chat_id not in self._workers or not self._workers[chat_id].is_alive():
                t = threading.Thread(target=self._worker_loop, args=(chat_id,), daemon=True)
                self._workers[chat_id] = t
                t.start()
            elif len(self._queues[chat_id]) > 1:
                self._notify_queue_status(chat_id, len(self._queues[chat_id]))

    def _notify_queue_status(self, chat_id: str, queue_depth: int):
        fc = self._ensure_feishu()
        fc.send_text(chat_id, "chat_id", f"⏳ 当前排队消息: {queue_depth - 1} 条，正在处理中...")

    def _handle_command(self, chat_id: str, text: str) -> bool:
        """Returns True if text was a command handled."""
        fc = self._ensure_feishu()
        if text == "/new":
            with self._queue_lock:
                if chat_id in self._queues:
                    self._queues[chat_id].clear()
            from app.core.session import get_session_manager
            sm = get_session_manager()
            sm.clear_session(chat_id)
            self._stop_flags[chat_id] = True
            fc.send_text(chat_id, "chat_id", "🆗 已开启新对话，上下文已清空")
            return True
        elif text == "/stop":
            self._stop_flags[chat_id] = True
            with self._queue_lock:
                if chat_id in self._queues:
                    self._queues[chat_id].clear()
            fc.send_text(chat_id, "chat_id", "⏹ 已停止当前任务")
            return True
        return False

    def _worker_loop(self, chat_id: str):
        from app.core.session import get_session_manager
        sm = get_session_manager()
        fc = self._feishu_client or feishu_client
        history = sm.get_history(chat_id)
        stop_flag = False

        while not stop_flag:
            text = None
            with self._queue_lock:
                if chat_id in self._queues and self._queues[chat_id]:
                    text = self._queues[chat_id].popleft()
                stop_flag = self._stop_flags.get(chat_id, True)

            if not text:
                break

            if self._handle_command(chat_id, text):
                continue

            try:
                from app.core.agent import Agent

                def on_compact(summary: str):
                    sm.append_summary(chat_id, summary)

                resp = Agent().run(text, history=history, on_compact=on_compact)
                if resp:
                    fc.send_text(chat_id, "chat_id", resp)
            except Exception as ex:
                fc.send_text(chat_id, "chat_id", f"❌ 处理出错: {ex}")
                print(f"❌ Agent error for {chat_id}: {ex}")

            stop_flag = self._stop_flags.get(chat_id, True)

        with self._queue_lock:
            if chat_id in self._queues:
                del self._queues[chat_id]
        with self._workers_lock:
            if chat_id in self._workers:
                del self._workers[chat_id]
        if chat_id in self._stop_flags:
            del self._stop_flags[chat_id]


def get_chat_worker() -> ChatWorker:
    return ChatWorker()


async def start_feishu_ws():
    """启动飞书 WebSocket 长连接监听"""
    if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
        print("⚠️ Feishu credentials not found, WebSocket listener skipped.")
        return

    print("📡 Feishu WS handler ready (queue-based, /new and /stop supported).")

    def do_process_message(data) -> None:
        """从自动生成的事件对象中处理飞书消息 (同步回调)"""
        try:
            # SDK 1.5.3 的事件处理器会自动反序列化为 P2ImMessageReceiveV1 对象
            event = data.event
            if not event:
                return
            message = event.message
            if not message:
                return
            # 兼容性修复：message_type 替代 msg_type
            if getattr(message, "message_type", None) == "text" or getattr(message, "msg_type", None) == "text":
                chat_id = message.chat_id
                content_raw = message.content or "{}"
                try:
                    text = json.loads(content_raw).get("text", "").strip()
                except Exception:
                    text = content_raw

                if text:
                    # 使用线程运行 Agent 以免阻塞 WS 线程
                    print(f"📩 Feishu [{chat_id}]: {text}")
                    worker = get_chat_worker()
                    worker.enqueue(chat_id, text)
        except Exception as e:
            print(f"❌ Message processing error: {e}")

    # 注册事件处理器
    event_handler = lark.EventDispatcherHandler.builder("", "")\
        .register_p2_im_message_receive_v1(do_process_message)\
        .build()

    # 创建长连接客户端 (适配 lark-oapi 1.x 版本)
    from lark_oapi.ws import Client as WSClient
    ws_client = WSClient(
        settings.FEISHU_APP_ID,
        settings.FEISHU_APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO
    )

    print("🔌 Starting Feishu WebSocket Connection...")

    # 终极方案：手动入侵 SDK 的全局变量变量。
    def _run_ws_client():
        try:
            import asyncio
            import lark_oapi.ws.client as sdk_module

            # 1. 创建属于这个线程的全新环境
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)

            # 2. **核心操作**：强行覆盖 SDK 模块级别的全局变量 loop
            sdk_module.loop = new_loop

            # 3. 阻塞运行
            ws_client.start()
        except Exception as e:
            print(f"❌ Feishu WebSocket thread error: {e}")

    # 延迟 2 秒启动
    timer = threading.Timer(2.0, _run_ws_client)
    timer.daemon = True
    timer.start()
    print("⏳ Feishu WebSocket (queue-mode) scheduled...")
