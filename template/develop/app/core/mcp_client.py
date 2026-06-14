import asyncio
import json
import logging
import os
import subprocess
import urllib.parse
from typing import Any, Optional

import httpx

from .registry import Tool, get_tool_registry

logger = logging.getLogger("mcp_client")


class MCPTool(Tool):
    """Wrapper that converts an MCP tool definition into a MRA Tool."""

    def __init__(self, mcp_client: "MCPClient", server_name: str, tool_def: dict):
        self._client = mcp_client
        self._server_name = server_name
        raw_name = tool_def.get("name", "")
        self.name = f"mcp_{server_name}_{raw_name}"
        self.description = tool_def.get("description", "")
        schema = tool_def.get("inputSchema", {})
        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except json.JSONDecodeError:
                schema = {}
        self.parameters = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
        }
        self._tool_def = tool_def

    def execute(self, **kwargs) -> str:
        return asyncio.run(self._client.call_tool(self._server_name, self._tool_def["name"], kwargs))


class MCPClient:
    """
    Minimal MCP client supporting HTTP/SSE and stdio transports.

    Config file: .mcp.json in agent workspace
    """

    def __init__(self, config_path: str = ".mcp.json"):
        self._config_path = config_path
        self._servers: dict[str, Any] = {}
        self._http_clients: dict[str, httpx.AsyncClient] = {}
        self._stdio_processes: dict[str, subprocess.Popen] = {}
        self._tools: dict[str, list[MCPTool]] = {}
        self._loaded = False

    def _load_config(self) -> dict:
        if not os.path.exists(self._config_path):
            return {}
        with open(self._config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def _probe_http(self, url: str, timeout: float = 5.0) -> bool:
        host = ""
        port = 80
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _list_http_tools(self, server_name: str, config: dict) -> list[MCPTool]:
        url = config["url"]
        headers = {"Content-Type": "application/json"}
        if "headers" in config:
            headers.update(config["headers"])
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{url.rstrip('/')}/tools/list",
                    headers=headers,
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                )
                if resp.status_code != 200:
                    logger.warning(f"MCP server {server_name} /tools/list returned {resp.status_code}")
                    return []
                data = resp.json()
                tools = []
                for tool_def in data.get("tools", []):
                    tools.append(MCPTool(self, server_name, tool_def))
                return tools
            except Exception as e:
                logger.error(f"Failed to list tools from {server_name}: {e}")
                return []

    async def _call_http_tool(
        self, server_name: str, tool_name: str, arguments: dict
    ) -> str:
        config = self._servers.get(server_name, {})
        url = config["url"]
        headers = {"Content-Type": "application/json"}
        if "headers" in config:
            headers.update(config["headers"])
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(
                    f"{url.rstrip('/')}/tools/call",
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "id": 2,
                        "params": {"name": tool_name, "arguments": arguments},
                    },
                )
                if resp.status_code != 200:
                    return f"Error: MCP server returned {resp.status_code}"
                result = resp.json()
                content = result.get("content", [])
                if isinstance(content, list):
                    return "\n".join(
                        c.get("text", str(c)) for c in content if c.get("type") == "text"
                    )
                return str(result.get("result", result))
            except Exception as e:
                return f"Error calling {tool_name} on {server_name}: {e}"

    def _load_stdio_server(self, server_name: str, config: dict) -> bool:
        command = config.get("command", "")
        args = config.get("args", [])
        if not command:
            return False
        cmd = [command] + args
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self._stdio_processes[server_name] = proc
            return True
        except Exception as e:
            logger.error(f"Failed to start stdio MCP server {server_name}: {e}")
            return False

    def _list_stdio_tools(self, server_name: str) -> list[MCPTool]:
        proc = self._stdio_processes.get(server_name)
        if not proc or proc.poll() is not None:
            return []
        try:
            req = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1,
            }
            proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            if not line:
                return []
            resp = json.loads(line)
            tools = []
            for tool_def in resp.get("tools", []):
                tools.append(MCPTool(self, server_name, tool_def))
            return tools
        except Exception as e:
            logger.error(f"Failed to list stdio tools from {server_name}: {e}")
            return []

    def _call_stdio_tool(
        self, server_name: str, tool_name: str, arguments: dict
    ) -> str:
        proc = self._stdio_processes.get(server_name)
        if not proc or proc.poll() is not None:
            return f"Error: MCP server {server_name} is not running"
        try:
            req = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 2,
                "params": {"name": tool_name, "arguments": arguments},
            }
            proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            if not line:
                return "Error: No response from MCP server"
            resp = json.loads(line)
            content = resp.get("content", [])
            if isinstance(content, list):
                return "\n".join(
                    c.get("text", str(c)) for c in content if c.get("type") == "text"
                )
            return str(resp.get("result", resp))
        except Exception as e:
            return f"Error calling stdio tool {tool_name}: {e}"

    async def list_tools(self, server_name: str) -> list[MCPTool]:
        config = self._servers.get(server_name, {})
        transport = config.get("transport", "http")
        if transport == "stdio":
            return self._list_stdio_tools(server_name)
        return await self._list_http_tools(server_name, config)

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict
    ) -> str:
        config = self._servers.get(server_name, {})
        transport = config.get("transport", "http")
        if transport == "stdio":
            return self._call_stdio_tool(server_name, tool_name, arguments)
        return await self._call_http_tool(server_name, tool_name, arguments)

    def _unload_tools(self) -> None:
        registry = get_tool_registry()
        for server_tools in self._tools.values():
            for tool in server_tools:
                if registry.has(tool.name):
                    registry.unregister(tool.name)
        self._tools.clear()

    def _stop_servers(self) -> None:
        for proc in self._stdio_processes.values():
            try:
                proc.terminate()
            except Exception:
                pass
        self._stdio_processes.clear()

    async def load(self) -> dict[str, list[str]]:
        """
        Load all enabled MCP servers and register their tools.
        Returns a dict mapping server name to list of registered tool names.
        """
        config = self._load_config()
        servers_config = config.get("mcpServers", {})
        results: dict[str, list[str]] = {}

        self._unload_tools()
        self._stop_servers()

        for name, srv_config in servers_config.items():
            if not srv_config.get("enabled", True):
                continue
            self._servers[name] = srv_config
            transport = srv_config.get("transport", "http")

            if transport == "stdio":
                self._load_stdio_server(name, srv_config)

            tools = await self.list_tools(name)
            registered = []
            for tool in tools:
                get_tool_registry().register(tool)
                registered.append(tool.name)
            results[name] = registered
            self._tools[name] = tools
            logger.info(f"MCP server '{name}': registered {len(registered)} tools")

        self._loaded = True
        return results

    def unload(self) -> None:
        """Stop all MCP servers and unregister all tools."""
        self._unload_tools()
        self._stop_servers()
        self._loaded = False

    def reload(self) -> dict[str, list[str]]:
        """Hot-reload all MCP servers. Synchronous wrapper."""
        return asyncio.run(self.load())


_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


def load_mcp_tools() -> dict[str, list[str]]:
    """Load all MCP tools from .mcp.json config."""
    return asyncio.run(get_mcp_client().load())


def reload_mcp_tools() -> dict[str, list[str]]:
    """Hot-reload all MCP tools."""
    return get_mcp_client().reload()
