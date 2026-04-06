from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import shutil
import datetime
import zipfile
import json
from typing import List, Optional
from app.core.config import settings

router = APIRouter()

BACKUP_DIR = os.path.join(settings.WORKSPACE_DIR, ".backup")


class BackupInfo(BaseModel):
    name: str
    size: int
    created_at: str
    path: str
    agent_id: str


class CreateBackupRequest(BaseModel):
    agent_id: str
    file_paths: Optional[List[str]] = None
    name: Optional[str] = None


def get_dir_size(path: str) -> int:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def ensure_backup_dir(agent_id: str) -> str:
    agent_backup_dir = os.path.join(BACKUP_DIR, agent_id)
    os.makedirs(agent_backup_dir, exist_ok=True)
    return agent_backup_dir


@router.post("/create", response_model=BackupInfo)
async def create_backup(req: CreateBackupRequest):
    agent_root = os.path.join(settings.WORKSPACE_DIR, req.agent_id)
    if not os.path.exists(agent_root):
        raise HTTPException(status_code=404, detail=f"Agent {req.agent_id} not found")

    agent_backup_dir = ensure_backup_dir(req.agent_id)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = req.name if req.name else f"backup_{timestamp}"
    backup_filename = f"{backup_name}.zip"
    backup_path = os.path.join(agent_backup_dir, backup_filename)

    if os.path.exists(backup_path):
        raise HTTPException(status_code=400, detail="Backup with this name already exists")

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if req.file_paths:
                for file_path in req.file_paths:
                    full_path = os.path.join(agent_root, file_path)
                    abs_full = os.path.abspath(full_path)
                    abs_root = os.path.abspath(agent_root)
                    if not abs_full.startswith(abs_root + os.sep) and abs_full != abs_root:
                        continue
                    if os.path.isfile(full_path):
                        zipf.write(full_path, file_path)
                    elif os.path.isdir(full_path):
                        for root, dirs, files in os.walk(full_path):
                            for f in files:
                                fp = os.path.join(root, f)
                                arcname = os.path.relpath(fp, agent_root)
                                zipf.write(fp, arcname)
            else:
                for root, dirs, files in os.walk(agent_root):
                    if "logs" in dirs:
                        dirs.remove("logs")
                    if "__pycache__" in dirs:
                        dirs.remove("__pycache__")
                    for f in files:
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, agent_root)
                        zipf.write(fp, arcname)

        stat = os.stat(backup_path)
        return BackupInfo(
            name=backup_filename,
            size=stat.st_size,
            created_at=datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            path=backup_path,
            agent_id=req.agent_id
        )
    except Exception as e:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/list", response_model=List[BackupInfo])
async def list_backups():
    if not os.path.exists(BACKUP_DIR):
        return []

    backups = []
    for agent_id in os.listdir(BACKUP_DIR):
        agent_backup_dir = os.path.join(BACKUP_DIR, agent_id)
        if not os.path.isdir(agent_backup_dir):
            continue
        for file in os.listdir(agent_backup_dir):
            if file.endswith(".zip"):
                path = os.path.join(agent_backup_dir, file)
                stat = os.stat(path)
                backups.append(BackupInfo(
                    name=file,
                    size=stat.st_size,
                    created_at=datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    path=path,
                    agent_id=agent_id
                ))

    backups.sort(key=lambda x: x.created_at, reverse=True)
    return backups


@router.post("/restore/{name}")
async def restore_backup(name: str, agent_id: str):
    backup_path = os.path.join(BACKUP_DIR, agent_id, name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    agent_root = os.path.join(settings.WORKSPACE_DIR, agent_id)

    try:
        if os.path.exists(agent_root):
            for item in os.listdir(agent_root):
                if item in ("logs", ".backup"):
                    continue
                item_path = os.path.join(agent_root, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(agent_root)

        return {"status": "success", "message": f"Restored {name} to {agent_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.get("/download/{agent_id}/{name}")
async def download_backup(agent_id: str, name: str):
    backup_path = os.path.join(BACKUP_DIR, agent_id, name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(backup_path, filename=name)


@router.delete("/delete/{agent_id}/{name}")
async def delete_backup(agent_id: str, name: str):
    backup_path = os.path.join(BACKUP_DIR, agent_id, name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    try:
        os.remove(backup_path)
        return {"status": "success", "message": f"Deleted {name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


class TemplateInfo(BaseModel):
    name: str
    description: str
    path: str
    replace: List[str]
    exclude: List[str]


@router.get("/templates", response_model=List[TemplateInfo])
async def list_templates():
    if not os.path.exists(settings.TEMPLATE_DIR):
        return []
    templates = []
    for name in os.listdir(settings.TEMPLATE_DIR):
        tpl_path = os.path.join(settings.TEMPLATE_DIR, name)
        if os.path.isdir(tpl_path):
            desc_file = os.path.join(tpl_path, "readme.md")
            description = ""
            if os.path.exists(desc_file):
                with open(desc_file, "r", encoding="utf-8") as f:
                    description = f.read().strip()
            config_path = os.path.join(tpl_path, ".template")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    replace = cfg.get("replace", ["app"])
                    exclude = cfg.get("exclude", [])
            else:
                replace = ["app"]
                exclude = []
            templates.append(TemplateInfo(name=name, description=description, path=tpl_path, replace=replace, exclude=exclude))
    return templates


class ApplyTemplateRequest(BaseModel):
    template_name: str
    auto_backup: bool = True


@router.post("/apply-template/{agent_id}")
async def apply_template(agent_id: str, req: ApplyTemplateRequest):
    tpl_path = os.path.join(settings.TEMPLATE_DIR, req.template_name)
    if not os.path.exists(tpl_path):
        raise HTTPException(status_code=404, detail=f"Template {req.template_name} not found")

    agent_root = os.path.join(settings.WORKSPACE_DIR, agent_id)
    if not os.path.exists(agent_root):
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    config_path = os.path.join(tpl_path, ".template")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        replace_items = cfg.get("replace", ["app"])
        exclude = set(cfg.get("exclude", []))
    else:
        replace_items = ["app"]
        exclude = set()

    try:
        for item in replace_items:
            tpl_src = os.path.join(tpl_path, item)
            agent_dst = os.path.join(agent_root, item)
            if not os.path.exists(tpl_src):
                raise HTTPException(status_code=400,
                    detail=f"Template {req.template_name} item '{item}' not found")

            if req.auto_backup and os.path.exists(agent_dst):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = ensure_backup_dir(agent_id)
                backup_path = os.path.join(backup_dir, f"auto_before_{item}_{req.template_name}_{timestamp}.zip")
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(agent_dst):
                        dirs[:] = [d for d in dirs if d not in exclude and d != "__pycache__"]
                        for f in files:
                            fp = os.path.join(root, f)
                            arcname = os.path.relpath(fp, agent_dst)
                            zipf.write(fp, arcname)

            if os.path.isdir(tpl_src):
                if os.path.exists(agent_dst):
                    shutil.rmtree(agent_dst)
                shutil.copytree(tpl_src, agent_dst)
            else:
                if os.path.exists(agent_dst):
                    os.remove(agent_dst)
                shutil.copy2(tpl_src, agent_dst)

        return {"status": "success", "message": f"Applied template {req.template_name} to {agent_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apply template failed: {str(e)}")
