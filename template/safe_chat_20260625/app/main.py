from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pathlib import Path
from app.core.config import settings
from app.routers import agent, health, files, plan, feishu, cron
from app.routers.cron import set_cron_service
from app.core.cron_service import CronService

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MetaRefactorAgents - A flexible agent refactoring framework",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

@app.on_event("startup")
async def startup_event():
    """启动时初始化飞书长连接监听器和定时任务服务"""
    from app.core.feishu import start_feishu_ws

    # 异步开启飞书监听，不阻塞主应用启动
    asyncio.create_task(start_feishu_ws())

    # 初始化并启动 Cron 服务
    if settings.CRON_ENABLED:
        cron_path = Path(settings.CRON_STORAGE_PATH)

        async def on_cron_job(job):
            """Cron job 触发时的回调：运行 Agent 并按 silent 策略发送结果到飞书"""
            from app.core.cron_service import CronJobSkippedError
            from app.core.cron_context import SILENT_CRON_CTX, ALERT_SINK_CTX
            from app.core.feishu import feishu_client
            from app.core.agent import Agent

            if job.payload.kind == "system_event":
                raise CronJobSkippedError("system_event not implemented")

            if not job.payload.message:
                print(f"Cron: job {job.id} has no message, skipping")
                return

            if not job.payload.session_key:
                print(f"Cron: job {job.id} has no session_key, skipping")
                return

            silent = getattr(job.payload, 'silent', False)
            notify_on_error = getattr(job.payload, 'notify_on_error', True)
            alerts: list[str] = []

            silent_token = SILENT_CRON_CTX.set(silent)
            sink_token = ALERT_SINK_CTX.set(alerts if silent else None)
            agent_failed = False
            try:
                try:
                    result = Agent().run(job.payload.message)
                except Exception as e:
                    result = f"Agent execution error: {e}"
                    agent_failed = True
            finally:
                SILENT_CRON_CTX.reset(silent_token)
                ALERT_SINK_CTX.reset(sink_token)

            fc = feishu_client
            if not fc.is_enabled():
                print(f"Cron: Feishu not configured, result: {result}, alerts: {alerts}")
                return

            if silent:
                for alert_msg in alerts:
                    fc.send_text(
                        receive_id=job.payload.session_key,
                        receive_id_type="chat_id",
                        content=f"[定时任务告警] {job.name}\n{alert_msg}",
                    )
                if agent_failed and notify_on_error:
                    fc.send_text(
                        receive_id=job.payload.session_key,
                        receive_id_type="chat_id",
                        content=f"[定时任务异常] {job.name}\n{result}",
                    )
                return

            fc.send_text(
                receive_id=job.payload.session_key,
                receive_id_type="chat_id",
                content=result or "No response"
            )

        cron_service = CronService(cron_path / "jobs.json", on_job=on_cron_job)
        try:
            await cron_service.start()
            set_cron_service(cron_service)
            print(f"Cron service started, storage: {cron_path}")
        except Exception as e:
            print(f"Warning: Failed to start cron service: {e}")


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["system"])
app.include_router(agent.router, prefix=f"{settings.API_V1_STR}/agent", tags=["agent"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])
app.include_router(plan.router, prefix=f"{settings.API_V1_STR}/plans", tags=["plans"])
app.include_router(feishu.router, prefix=f"{settings.API_V1_STR}/feishu", tags=["feishu"])
app.include_router(cron.router, prefix=settings.API_V1_STR, tags=["cron"])


@app.on_event("shutdown")
async def shutdown_event():
    """停止 Cron 服务"""
    from app.routers.cron import get_cron_service
    try:
        service = get_cron_service()
        service.stop()
        print("Cron service stopped")
    except Exception:
        pass


@app.get("/", tags=["root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

