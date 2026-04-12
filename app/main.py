from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import json
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
    
    # 2. 预先扫描所有端口及其所属的 cwd (工作目录)，确保精确识别哪个进程对应哪个 workspace
    active_workspaces = {} # {abs_path: {"port": int, "pid": int}}
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
                    p_port = int(port_match.group(1))
                    p_pid = int(pid_match.group(1))
                    # 通过 /proc/pid/cwd 获取真实工作路径
                    try:
                        p_cwd = os.readlink(f"/proc/{p_pid}/cwd")
                        active_workspaces[p_cwd] = {"port": p_port, "pid": p_pid}
                    except:
                        continue
    except:
        pass

    if os.path.exists(workspace_dir):
        for folder in os.listdir(workspace_dir):
            if folder == ".shared" or folder.startswith("."):
                continue
            
            abs_folder_path = os.path.abspath(os.path.join(workspace_dir, folder))
            proc_info = AGENT_PROCESSES.get(folder, {})
            status = proc_info.get("status", "Stopped")
            port = proc_info.get("port")
            
            # 自动发现逻辑：以 /proc 系统信息的物理路径为准
            if abs_folder_path in active_workspaces:
                real_info = active_workspaces[abs_folder_path]
                port = real_info["port"]
                pid = real_info["pid"]
                AGENT_PROCESSES[folder] = {"port": port, "pid": pid, "status": "Running"}
                status = "Running"
            else:
                # 如果记录是在运行但实际上物理路径查不到进程，则重置为停止
                if status == "Running":
                    status = "Stopped"
                    if folder in AGENT_PROCESSES:
                        del AGENT_PROCESSES[folder]

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

            # 读取 template meta 信息
            meta_path = os.path.join(workspace_dir, folder, ".meta")
            template_info = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    template_info = json.load(f)
            
            all_agents.append({
                "id": folder,
                "port": port,
                "status": status,
                "health": health,
                "template": template_info.get("template_name"),
                "template_id": template_info.get("template_id"),
                "template_version": template_info.get("template_version"),
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
                timeout=None  # 不设置超时，允许 Agent 长时间运行（如撰写专利）
            )
            return JSONResponse(
                content=resp.json(),
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error forwarding to agent: {str(e)}")

@app.get("/api/templates")
async def list_templates():
    """获取所有模板及其 lineage 信息"""
    import json
    template_dir = settings.TEMPLATE_DIR
    templates = []
    
    if os.path.exists(template_dir):
        for folder in os.listdir(template_dir):
            tpl_path = os.path.join(template_dir, folder)
            config_path = os.path.join(tpl_path, ".template")
            
            if os.path.isdir(tpl_path) and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    templates.append({
                        "name": folder,
                        "id": config.get("id", folder),
                        "lineage": config.get("lineage", {}),
                        "replace": config.get("replace", []),
                        "exclude": config.get("exclude", [])
                    })
    
    return {"templates": templates}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
