"""
API配置模块
管理Tushare、OpenAI、Claude等API的配置
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class TushareConfig:
    """Tushare API配置"""
    TOKEN: str = os.getenv("TUSHARE_TOKEN", "")
    BASE_URL: str = "http://api.tushare.pro"
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        return bool(cls.TOKEN)

class OpenAIConfig:
    """OpenAI API配置"""
    API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        return bool(cls.API_KEY)

class ClaudeConfig:
    """Claude API配置"""
    API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    MODEL: str = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
    BASE_URL: str = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com")
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        return bool(cls.API_KEY)

class AppConfig:
    """应用配置"""
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DATA_PATH: str = os.getenv("DATA_PATH", "data")
    OUTPUT_PATH: str = os.getenv("OUTPUT_PATH", "data/output")
    
    # 数据处理配置
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    RETRY_TIMES: int = int(os.getenv("RETRY_TIMES", "3"))
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "0.2"))

def validate_all_configs() -> dict:
    """验证所有配置"""
    return {
        "tushare": TushareConfig.validate(),
        "openai": OpenAIConfig.validate(),
        "claude": ClaudeConfig.validate()
    } 