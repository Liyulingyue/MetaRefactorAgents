import shutil
import os
import subprocess
from app.core.config import settings

def init_agent_workspace(agent_id: str, template_name: str = "default") -> str:
    """从 template 目录克隆一个新的 Agent 到 workspace"""
    template_path = os.path.join(settings.TEMPLATE_DIR, template_name)
    workspace_path = os.path.join(settings.WORKSPACE_DIR, agent_id)
    
    if os.path.exists(workspace_path):
        raise Exception(f"Workspace for agent {agent_id} already exists.")
    
    if not os.path.exists(template_path):
        raise Exception(f"Template {template_name} does not exist.")
    
    # 递归复制
    shutil.copytree(template_path, workspace_path)
    return workspace_path

def start_agent_process(agent_id: str, port: int):
    """启动 Agent 进程 (使用 subprocess 异步启动，并重定向日志)"""
    # 物理路径用于检查文件是否存在
    workspace_path = os.path.join(settings.WORKSPACE_DIR, agent_id)
    # run_script 使用绝对路径以确保 subprocess 能正确找到
    run_script = os.path.abspath(os.path.join(workspace_path, "run.py"))
    
    if not os.path.exists(run_script):
        raise Exception(f"Run script not found at {run_script}")
    
    # 建立日志目录
    log_dir = os.path.abspath(os.path.join(workspace_path, "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "server.log")
    log_file = open(log_file_path, "a")
    
    command = [
        "python3", run_script,
        "--port", str(port),
        "--host", "0.0.0.0"
    ]
    
    # 使用绝对路径作为工作目录
    abs_workspace_path = os.path.abspath(workspace_path)
    
    process = subprocess.Popen(
        command,
        stdout=log_file,
        stderr=log_file,
        cwd=abs_workspace_path
    )
    return process.pid
