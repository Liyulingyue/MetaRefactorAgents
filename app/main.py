from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from app.core.config import settings
from app.routers import manager, system, backup

app = FastAPI(title="MRA Gateway")

# 活跃进程管理：{agent_id: {"port": int, "pid": int, "status": str}}
AGENT_PROCESSES = {}

app.state.processes = AGENT_PROCESSES

@app.on_event("shutdown")
async def shutdown_event():
    """网关关闭时，清理所有运行中的 Agent 进程"""
    import signal
    for agent_id, info in AGENT_PROCESSES.items():
        if info.get("status") == "Running":
            pid = info.get("pid")
            try:
                print(f"🛑 Terminating Agent {agent_id} (PID: {pid})...")
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

# 注册管理路由
app.include_router(manager.router, prefix="/api/admin", tags=["admin"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(backup.router, prefix="/api/backup", tags=["backup"])

@app.get("/api/agents")
async def list_agents():
    """获取所有 Agent 及其运行状态，增加实时健康检查与自动发现逻辑"""
    workspace_dir = settings.WORKSPACE_DIR
    all_agents = []
    
    # 预先扫描所有端口，用于发现已经运行但未注册的进程
    active_ports = {}
    try:
        import subprocess
        import re
        cmd = "ss -ltpn"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "LISTEN" in line:
                port_match = re.search(r':(\d+)\s+', line)
                pid_match = re.search(r'pid=(\d+)', line)
                if port_match and pid_match:
                    active_ports[int(port_match.group(1))] = int(pid_match.group(1))
    except:
        pass

    if os.path.exists(workspace_dir):
        for folder in os.listdir(workspace_dir):
            # 过滤逻辑：排除非 Agent 目录或特定的 .shared 目录
            if folder == ".shared" or folder.startswith("."):
                continue
                
            if os.path.isdir(os.path.join(workspace_dir, folder)):
                proc_info = AGENT_PROCESSES.get(folder, {})
                status = proc_info.get("status", "Stopped")
                port = proc_info.get("port")
                
                # 自动发现逻辑：如果记录为停止，但相应端口已有进程在跑，则自动关联
                if status == "Stopped":
                    # 规则：Agent-01 -> 8001, Agent-02 -> 8002
                    guess_port = 8000 + int(folder.split('-')[-1]) if '-' in folder else None
                    if guess_port and guess_port in active_ports:
                        port = guess_port
                        pid = active_ports[guess_port]
                        AGENT_PROCESSES[folder] = {"port": port, "pid": pid, "status": "Running"}
                        status = "Running"

                health = "Unreachable"
                # 如果记录为 Running，尝试真实探测端口连通性
                if status == "Running" and port:
                    try:
                        async with httpx.AsyncClient() as client:
                            resp = await client.get(f"http://localhost:{port}/api/v1/health", timeout=0.5)
                            if resp.status_code == 200:
                                health = "Healthy"
                    except:
                        health = "Unreachable"

                all_agents.append({
                    "id": folder,
                    "port": port,
                    "status": status,
                    "health": health
                })
    
    return all_agents

@app.api_route("/api/agents/{agent_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_agent(agent_id: str, path: str, request: Request):
    """路由网关"""
    if agent_id == "admin":
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent_id not in AGENT_PROCESSES or AGENT_PROCESSES[agent_id]["status"] != "Running":
         raise HTTPException(status_code=404, detail=f"Agent {agent_id} is not running")
    
    port = AGENT_PROCESSES[agent_id]["port"]
    target_url = f"http://localhost:{port}/api/v1/{path}"
    
    async with httpx.AsyncClient() as client:
        # 复制请求方法、内容和查询参数
        content = await request.body()
        params = request.query_params
        headers = dict(request.headers)
        # 移除 host 以免冲突
        headers.pop("host", None)
        
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=params,
                content=content,
                headers=headers,
                timeout=60.0 # Agent 任务可能较长
            )
            return JSONResponse(
                content=resp.json(),
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error forwarding to agent: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
