from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MRA-Gateway"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # 以后可以扩展为从数据库或文件读取
    WORKSPACE_DIR: str = "workspace"
    TEMPLATE_DIR: str = "template"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
