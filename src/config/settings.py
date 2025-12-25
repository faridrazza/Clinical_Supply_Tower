"""
Configuration settings for the Clinical Supply Chain Control Tower.
"""
import os
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = Field(
        default="postgresql://localhost:5432/clinical_supply_chain",
        description="PostgreSQL connection string"
    )
    
    # LLM Configuration
    llm_provider: Literal["openai", "anthropic"] = Field(
        default="openai",
        description="LLM provider to use"
    )
    llm_model: str = Field(
        default="gpt-4-turbo-preview",
        description="LLM model name"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    

    
    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")
    max_sql_retries: int = Field(default=3, description="Maximum SQL retry attempts")
    query_timeout: int = Field(default=30, description="Query timeout in seconds")

    
    # Workflow Settings
    expiry_alert_days: int = Field(
        default=90,
        description="Days threshold for expiry alerts"
    )
    shortfall_prediction_weeks: int = Field(
        default=8,
        description="Weeks to predict for shortfall analysis"
    )
    enrollment_lookback_weeks: int = Field(
        default=4,
        description="Weeks to look back for enrollment rate calculation"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
