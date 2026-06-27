import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict

router = APIRouter()

@router.get("/")
async def list_files():
    """Agent 自理：列出自己工作区的文件"""
    files = []
    # 允许访问当前目录
    root_path = os.getcwd()
    for root, dirs, filenames in os.walk(root_path):
        # 排除内部目录
        if "logs" in dirs:
            dirs.remove("logs")
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        if ".git" in dirs:
            dirs.remove(".git")
            
        for f in filenames:
            rel_path = os.path.relpath(os.path.join(root, f), root_path)
            files.append({
                "name": f,
                "path": rel_path,
                "size": os.path.getsize(os.path.join(root, f)),
                "mtime": os.path.getmtime(os.path.join(root, f))
            })
    return {"files": files}

@router.post("/publish")
async def publish_file(path: str):
    """Agent 自理：将文件发布到公共共享区"""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 确保共享目录存在 (相对于 agent 来说是 ../.shared_files/)
    shared_dir = os.path.abspath(os.path.join(os.getcwd(), "../.shared_files"))
    os.makedirs(shared_dir, exist_ok=True)
    
    filename = os.path.basename(path)
    # 给文件名加上来源前缀，防止冲突
    agent_id = os.getenv("AGENT_ID", "unknown")
    target_path = os.path.join(shared_dir, f"{agent_id}_{filename}")
    
    try:
        import shutil
        shutil.copy2(path, target_path)
        return {"status": "success", "published_as": f"{agent_id}_{filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download")
async def download_file(path: str):
    """Agent 自理：允许从 Agent 自身的端口下载文件"""
    if not os.path.exists(path) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 安全性：确保不超出工作区
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.getcwd()):
        raise HTTPException(status_code=403, detail="Access denied")
        
    return FileResponse(path, filename=os.path.basename(path))
