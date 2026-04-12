import os
import signal
import shutil
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from app.core.manager import init_agent_workspace, start_agent_process
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CreateAgentRequest(BaseModel):
    agent_id: str
    template: Optional[str] = "default"

@router.post("/create")
async def create_agent(request: CreateAgentRequest):
    """创建并初始化一个新的 Agent Workspace"""
    try:
        path = init_agent_workspace(request.agent_id, request.template)
        return {"status": "success", "agent_id": request.agent_id, "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, request: Request):
    """删除 Agent 工作区并停止其进程"""
    processes = request.app.state.processes

    if agent_id in processes:
        try:
            os.kill(processes[agent_id]["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
        del processes[agent_id]

    workspace_path = f"workspace/{agent_id}"
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)
        return {"status": "success", "message": f"Agent {agent_id} deleted"}
    raise HTTPException(status_code=404, detail="Agent workspace not found")

@router.post("/{agent_id}/start")
async def start_agent(agent_id: str, request: Request, port: Optional[str] = None):
    """启动指定 Agent 的进程并注册到网关"""
    try:
        # 1. 端口与初步准备
        actual_port = None
        if port is not None and port.lower() != "null" and port != "":
            actual_port = int(port)

        processes = request.app.state.processes
        
        if actual_port is None:
            existing_ports = [p["port"] for p in processes.values()]
            actual_port = 8001
            while actual_port in existing_ports:
                actual_port += 1
        
        # 2. 调用核心启动（现在异步启动并立即返回 PID）
        pid = start_agent_process(agent_id, actual_port)
        
        # 3. 在网关记录“启动中”状态，前端可据此展示 Loading 或尝试连接
        processes[agent_id] = {
            "port": actual_port,
            "pid": pid,
            "status": "Running" # 先记为启动成功，网关的 /api/agents 会将其推送给前端
        }
        
        # 4. 可选：在此处增加一个短暂的等待，尝试探测 Agent 端口是否已经 Listen (暂简略)
        return {
            "status": "started", 
            "agent_id": agent_id, 
            "pid": pid, 
            "port": actual_port,
            "message": f"Agent {agent_id} process spawned successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str, request: Request):
    """停止 Agent 进程"""
    processes = request.app.state.processes
    if agent_id in processes:
        try:
            os.kill(processes[agent_id]["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass # 进程已经不存在了
        
        # 从活跃进程中移除，这样前端就不会再尝试连接它了
        del processes[agent_id]
        
        return {"status": "stopped", "agent_id": agent_id}
    raise HTTPException(status_code=404, detail="Agent not running")

@router.get("/{agent_id}/logs")
async def get_agent_logs(agent_id: str, type: str = "server"):
    """获取 Agent 的运行日志"""
    try:
        if type == "thought":
            log_path = f"workspace/{agent_id}/logs/thoughts.md"
        else:
            log_path = f"workspace/{agent_id}/logs/server.log"
            
        if not os.path.exists(log_path):
            return {"logs": f"Log file not found at {log_path}"}
        
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            if type == "thought":
                return {"thoughts": log_content}
            return {"logs": log_content}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/thoughts")
async def get_agent_thoughts(agent_id: str):
    """单独的思维日志接口"""
    return await get_agent_logs(agent_id, type="thought")

@router.get("/shared/files")
async def list_shared_files():
    """获取公共文件区的文件列表"""
    shared_root = "workspace/.shared"
    if not os.path.exists(shared_root):
        os.makedirs(shared_root, exist_ok=True)
    
    files = []
    for f in os.listdir(shared_root):
        path = os.path.join(shared_root, f)
        if os.path.isfile(path):
            files.append({
                "name": f,
                "path": f,
                "size": os.path.getsize(path),
                "mtime": os.path.getmtime(path)
            })
    return {"files": files}

@router.get("/{agent_id}/thoughts")
async def get_agent_thoughts(agent_id: str):
    """获取 Agent 的内部思维日志 (thoughts.md)"""
    thought_path = f"workspace/{agent_id}/logs/thoughts.md"
    if not os.path.exists(thought_path):
        return {"thoughts": f"Thought log not found at {thought_path}"}
    
    try:
        with open(thought_path, "r", encoding="utf-8") as f:
            content = f.read()
            return {"thoughts": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/shared/files/upload")
async def upload_shared_file(file: UploadFile = File(...)):
    """上传文件到公共文件区"""
    shared_root = "workspace/.shared"
    os.makedirs(shared_root, exist_ok=True)
    
    dest_path = os.path.join(shared_root, file.filename)
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "status": "success",
        "name": file.filename,
        "path": file.filename,
        "size": len(content),
        "mtime": os.path.getmtime(dest_path)
    }

from fastapi.responses import FileResponse

@router.get("/shared/files/download")
async def download_shared_file(path: str):
    """下载公共文件区的文件"""
    file_full_path = os.path.join("workspace/.shared", path)
    if not os.path.exists(file_full_path) or not os.path.isfile(file_full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_full_path, filename=os.path.basename(file_full_path))

@router.get("/{agent_id}/files")
async def list_agent_files(agent_id: str):
    """获取 Agent 工作目录下的文件列表"""
    agent_root = f"workspace/{agent_id}"
    if not os.path.exists(agent_root):
        raise HTTPException(status_code=404, detail="Agent workspace not found")
    
    files = []
    for root, dirs, filenames in os.walk(agent_root):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
            
        for f in filenames:
            rel_path = os.path.relpath(os.path.join(root, f), agent_root)
            files.append({
                "name": f,
                "path": rel_path,
                "size": os.path.getsize(os.path.join(root, f)),
                "mtime": os.path.getmtime(os.path.join(root, f))
            })
    return {"files": files}

@router.get("/{agent_id}/files/download")
async def download_agent_file(agent_id: str, path: str):
    """下载 Agent 生成的文件"""
    file_full_path = os.path.join(f"workspace/{agent_id}", path)
    if not os.path.exists(file_full_path) or not os.path.isfile(file_full_path):
        raise HTTPException(status_code=404, detail="File not found")
    # 安全检查：防止目录穿越
    if not os.path.abspath(file_full_path).startswith(os.path.abspath(f"workspace/{agent_id}")):
        raise HTTPException(status_code=403, detail="Access denied")
        
    return FileResponse(file_full_path, filename=os.path.basename(file_full_path))

class AgentConfigUpdate(BaseModel):
    allow_cors: Optional[bool] = None

@router.get("/{agent_id}/config")
async def get_agent_config(agent_id: str):
    """读取 Agent 的持久化配置 (.env)"""
    env_path = f"workspace/{agent_id}/.env"
    # 默认值
    config = {"allow_cors": False}
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip().startswith("ALLOW_CORS="):
                    val = line.split("=")[1].strip().lower()
                    config["allow_cors"] = (val == "true")
    
    return config

@router.post("/{agent_id}/config")
async def update_agent_config(agent_id: str, config: AgentConfigUpdate):
    """更新 Agent 的持久化配置 (.env)"""
    env_path = f"workspace/{agent_id}/.env"
    lines = []
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    
    if config.allow_cors is not None:
        new_line = f"ALLOW_CORS={'true' if config.allow_cors else 'false'}\n"
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("ALLOW_CORS="):
                lines[i] = new_line
                found = True
                break
        if not found:
            lines.append(new_line)
            
    os.makedirs(os.path.dirname(env_path), exist_ok=True)
    with open(env_path, "w") as f:
        f.writelines(lines)
        
    return {"status": "success", "message": "Config updated. Restart agent to apply."}
