from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from app.core.config import settings

app = FastAPI(title="MRA Gateway")

# 存储活跃 Agent 的映射: {agent_id: port}
AGENT_REGISTRY = {
    "Agent-01": 8001,
    "Agent-02": 8002,
}

@app.get("/api/agents")
async def list_agents():
    """获取所有活跃 Agent 列表"""
    return [{"id": k, "port": v, "url": f"http://localhost:{v}"} for k, v in AGENT_REGISTRY.items()]

@app.api_route("/api/agents/{agent_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_agent(agent_id: str, path: str, request: Request):
    """路由网关：将请求转发到对应 Agent 的端口"""
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    port = AGENT_REGISTRY[agent_id]
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
