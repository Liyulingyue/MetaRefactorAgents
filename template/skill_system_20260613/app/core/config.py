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
    ACTIVE_TEMPLATE: str = "planer_20260408"

    # Feishu Settings
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_BOT_NAME: str = "MRA Bot"
    FEISHU_WEBHOOK_PATH: str = "/feishu/webhook"

    model_config = {
        "env_file": [".env", "../../.env"],
        "case_sensitive": True,
        "extra": "ignore",
        "env_file_encoding": "utf-8"
    }

settings = Settings()
