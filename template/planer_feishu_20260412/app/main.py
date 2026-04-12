from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.core.config import settings
from app.routers import agent, health, files, plan, feishu

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
    """启动时初始化飞书长连接监听器"""
    from app.core.feishu import start_feishu_ws
    # 异步开启监听，不阻塞主应用启动
    asyncio.create_task(start_feishu_ws())


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

@app.get("/", tags=["root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

