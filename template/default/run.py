import uvicorn
import argparse
from app.core.config import settings

def main():
    """启动 Agent 服务的入口函数"""
    
    parser = argparse.ArgumentParser(description="Start the Agent server.")
    parser.add_argument("--host", type=str, default=settings.HOST, help="Host to bind")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind")
    parser.add_argument("--reload", action="store_true", default=settings.RELOAD, help="Enable auto-reload")
    
    args = parser.parse_args()

    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"🛠️  Reload: {args.reload}")
    
    # 直接运行应用实例，支持热重载
    uvicorn.run(
        "app.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
