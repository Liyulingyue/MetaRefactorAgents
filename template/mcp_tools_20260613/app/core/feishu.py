from lark_oapi.api.im.v1 import CreateMessageRequest
import lark_oapi as lark
import json
import asyncio
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
                    .content(json.dumps({"text": str(content)}))
                    .build())\
                .build()
            
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

async def start_feishu_ws():
    """启动飞书 WebSocket 长连接监听"""
    from app.core.agent import Agent
    agent = Agent()
    
    if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
        print("⚠️ Feishu credentials not found, WebSocket listener skipped.")
        return

    def do_process_message(data) -> None:
        """从自动生成的事件对象中处理飞书消息 (同步回调)"""
        try:
            import json
            # SDK 1.5.3 的事件处理器会自动反序列化为 P2ImMessageReceiveV1 对象
            event = data.event
            if event:
                message = event.message
                # 兼容性修复：message_type 替代 msg_type
                if message and (getattr(message, "message_type", None) == "text" or getattr(message, "msg_type", None) == "text"):
                    chat_id = message.chat_id
                    content_raw = message.content or "{}"
                    try:
                        text = json.loads(content_raw).get("text", "").strip()
                    except:
                        text = content_raw
                    
                    if text:
                        print(f"📩 Received Feishu message: {text}")
                        # 使用线程运行 Agent 以免阻塞 WS 线程
                        def _run_agent_task():
                            try:
                                from app.core.agent import Agent
                                resp = Agent().run(text)
                                if resp:
                                    feishu_client.send_text(chat_id, "chat_id", resp)
                            except Exception as ex:
                                print(f"❌ Template Agent Error: {ex}")

                        import threading
                        threading.Thread(target=_run_agent_task, daemon=True).start()
        except Exception as e:
            print(f"❌ Error in message processing: {e}")

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
            print(f"🛠️ SDK global loop redirected to {id(new_loop)}")
            
            # 3. 阻塞运行
            ws_client.start()
        except Exception as e:
            print(f"❌ Feishu WebSocket thread error: {e}")

    import threading
    # 延迟 2 秒启动
    timer = threading.Timer(2.0, _run_ws_client)
    timer.daemon = True
    timer.start()
    print("⏳ Feishu WebSocket (Global Patch Mode) scheduled...")
    print("✅ Feishu WebSocket thread started with isolated event loop.")

