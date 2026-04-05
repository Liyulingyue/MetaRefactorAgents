from fastapi import APIRouter, HTTPException, Request
import subprocess
import os
import signal
from typing import List, Dict

router = APIRouter()

@router.get("/ports")
async def list_occupied_ports(request: Request, start_port: int = 8000, end_port: int = 8100):
    """扫描并列出指定范围内被占用的端口及其关联进程，关联 Agent 信息"""
    occupied = []
    # 从网关状态中获取已知的 Agent 映射
    known_agents = request.app.state.processes
    
    try:
        cmd = "ss -ltpn"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        lines = result.stdout.splitlines()
        for line in lines:
            if "LISTEN" in line:
                for port_candidate in range(start_port, end_port + 1):
                    if f":{port_candidate} " in line:
                        pid = None
                        process_name = "Unknown"
                        description = "External Process"
                        
                        if "pid=" in line:
                            import re
                            match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', line)
                            if match:
                                process_name = match.group(1)
                                pid = int(match.group(2))
                        
                        # 检查是否是网关已知的 Agent
                        agent_id = None
                        for aid, info in known_agents.items():
                            if info.get("port") == port_candidate:
                                agent_id = aid
                                description = f"MRA Agent: {aid}"
                                break
                        
                        if port_candidate == 8000:
                            description = "MRA Gateway (Master Control)"

                        occupied.append({
                            "port": port_candidate,
                            "pid": pid,
                            "process": process_name,
                            "agent_id": agent_id,
                            "description": description
                        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return occupied

@router.post("/kill/{pid}")
async def kill_process(pid: int):
    """强制杀掉指定 PID 的进程（用于释放端口）"""
    try:
        os.kill(pid, signal.SIGKILL)
        return {"status": "success", "message": f"Process {pid} terminated."}
    except ProcessLookupError:
        raise HTTPException(status_code=404, detail="Process not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-logs/{agent_id}")
async def clear_agent_logs(agent_id: str):
    """清空指定 Agent 的 logs 目录下所有内容（保留目录）"""
    from app.core.config import settings
    logs_dir = os.path.join(settings.WORKSPACE_DIR, agent_id, "logs")
    
    if not os.path.exists(logs_dir):
        return {"status": "success", "message": f"Agent {agent_id} logs directory does not exist."}
    
    try:
        for item in os.listdir(logs_dir):
            item_path = os.path.join(logs_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                import shutil
                shutil.rmtree(item_path)
        
        os.makedirs(logs_dir, exist_ok=True)
        return {"status": "success", "message": f"Logs for {agent_id} cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
