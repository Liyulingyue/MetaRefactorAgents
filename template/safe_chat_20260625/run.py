import uvicorn
import argparse
import logging
from app.core.config import settings

def main():
    """启动 Agent 服务的入口函数"""
    
    parser = argparse.ArgumentParser(description="Start the Agent server.")
    parser.add_argument("--host", type=str, default=settings.HOST, help="Host to bind")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind")
    parser.add_argument("--reload", action="store_true", default=settings.RELOAD, help="Enable auto-reload")
    
    args = parser.parse_args()

    # 配置 Uvicorn 的日志格式，增加时间戳
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["access"]["fmt"] = '%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'

    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"🛠️  Reload: {args.reload}")
    
    # 直接运行应用实例，支持热重载
    uvicorn.run(
        "app.main:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload,
        log_level="info",
        log_config=log_config
    )

if __name__ == "__main__":
    main()
