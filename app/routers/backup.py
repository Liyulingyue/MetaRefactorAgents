from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import shutil
import datetime
import zipfile
from typing import List, Optional
from app.core.config import settings

router = APIRouter()

# 备份目录相对于 workspace 的位置
BACKUP_DIR = os.path.join(settings.WORKSPACE_DIR, ".bakup")

class BackupInfo(BaseModel):
    name: str
    size: int
    created_at: str
    path: str

def get_dir_size(path: str) -> int:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

@router.post("/create", response_model=BackupInfo)
async def create_backup(name: Optional[str] = None):
    """创建当前 workspace 的备份（排除 .bakup 目录自身）"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        with open(os.path.join(BACKUP_DIR, ".gitkeep"), "w") as f:
            pass

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = name if name else f"backup_{timestamp}"
    backup_filename = f"{backup_name}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    if os.path.exists(backup_path):
        raise HTTPException(status_code=400, detail="Backup with this name already exists")

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(settings.WORKSPACE_DIR):
                # 排除 .bakup 目录自身
                if BACKUP_DIR in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, settings.WORKSPACE_DIR)
                    zipf.write(file_path, arcname)
        
        stat = os.stat(backup_path)
        return BackupInfo(
            name=backup_filename,
            size=stat.st_size,
            created_at=datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            path=backup_path
        )
    except Exception as e:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.get("/list", response_model=List[BackupInfo])
async def list_backups():
    """获取所有已存在的备份"""
    if not os.path.exists(BACKUP_DIR):
        return []
    
    backups = []
    for file in os.listdir(BACKUP_DIR):
        if file.endswith(".zip"):
            path = os.path.join(BACKUP_DIR, file)
            stat = os.stat(path)
            backups.append(BackupInfo(
                name=file,
                size=stat.st_size,
                created_at=datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                path=path
            ))
    
    # 按时间降序排序
    backups.sort(key=lambda x: x.created_at, reverse=True)
    return backups

@router.post("/restore/{name}")
async def restore_backup(name: str):
    """从指定的备份恢复 workspace"""
    backup_path = os.path.join(BACKUP_DIR, name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    try:
        # 1. 清理当前 workspace (保留 .bakup)
        for item in os.listdir(settings.WORKSPACE_DIR):
            item_path = os.path.join(settings.WORKSPACE_DIR, item)
            if item == ".bakup":
                continue
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        # 2. 解压备份
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(settings.WORKSPACE_DIR)
            
        return {"status": "success", "message": f"Restored from {name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.get("/download/{name}")
async def download_backup(name: str):
    """下载备份文件"""
    backup_path = os.path.join(BACKUP_DIR, name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(backup_path, filename=name)


@router.delete("/delete/{name}")
async def delete_backup(name: str):
    """删除备份文件"""
    backup_path = os.path.join(BACKUP_DIR, name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    
    try:
        os.remove(backup_path)
        return {"status": "success", "message": f"Deleted {name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
