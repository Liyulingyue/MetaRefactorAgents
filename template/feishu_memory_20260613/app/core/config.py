from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MetaRefactorAgents"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # LLM Settings
    OPENAI_API_KEY: str = "EMPTY"
    OPENAI_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # Workspace Settings
    WORKSPACE_ROOT: str = "./workspace"
    ACTIVE_TEMPLATE: str = "mcp_tools_20260613"

    # Feishu Settings
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_BOT_NAME: str = "MRA Bot"
    FEISHU_WEBHOOK_PATH: str = "/feishu/webhook"

    # Skills Settings
    # "static": inject skills summary once at startup (low token cost)
    # "dynamic": rebuild skills summary every LLM call (reflects latest skill state)
    SKILLS_INJECTION_MODE: str = "static"

    # Plan Settings
    # "static": inject plan context once per run() call (conversation start)
    # "dynamic": rebuild plan context every LLM call (reflects latest task status)
    PLAN_INJECTION_MODE: str = "dynamic"

    # MCP Settings
    # "static": load MCP tools once at startup, use reload_mcp_tools tool to manually reload
    # "dynamic": re-load MCP tools on every LLM call (auto-refresh)
    MCP_INJECTION_MODE: str = "static"

    # Conversation Compression Settings
    # Token threshold to trigger automatic history compression (0 to disable)
    # Recommended: 25000 tokens for MiniMax 32K context
    HISTORY_SUMMARY_THRESHOLD: int = 25000

    # Session storage path (NDJSON files per chat_id)
    SESSION_STORAGE_PATH: str = "./sessions"

    # Long-term Memory Settings
    # Path relative to workspace for MEMORY.md file
    MEMORY_FILE_PATH: str = "MEMORY.md"
    # "static": load memory once at startup
    # "dynamic": re-read memory on every LLM call
    MEMORY_INJECTION_MODE: str = "dynamic"

    # System Prompt Settings
    # Path relative to workspace for SYSTEM.md file (agent's own definition)
    SYSTEM_FILE_PATH: str = "SYSTEM.md"
    # "static": load system prompt once at startup
    # "dynamic": re-read system prompt on every LLM call (for self-modification)
    SYSTEM_INJECTION_MODE: str = "dynamic"

    model_config = {
        "env_file": [".env", "../../.env"],
        "case_sensitive": True,
        "extra": "ignore",
        "env_file_encoding": "utf-8"
    }

settings = Settings()
