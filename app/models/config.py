"""Configuration models for the Healthcare Compliance Copilot."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class BedrockConfig:
    """Configuration for Amazon Bedrock."""
    model_id: str = "amazon.nova-lite-v1:0"
    region: str = "us-east-1"
    max_tokens: int = 2000
    temperature: float = 0.3  # Lower temperature for consistent analysis
    guardrail_id: Optional[str] = None
    guardrail_version: Optional[str] = None

    @classmethod
    def from_env(cls) -> "BedrockConfig":
        """Load Bedrock configuration from environment variables."""
        return cls(
            model_id=os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
            region=os.getenv("AWS_REGION", "us-east-1"),
            max_tokens=int(os.getenv("BEDROCK_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("BEDROCK_TEMPERATURE", "0.3")),
            guardrail_id=os.getenv("BEDROCK_GUARDRAIL_ID"),
            guardrail_version=os.getenv("BEDROCK_GUARDRAIL_VERSION"),
        )


@dataclass
class AppConfig:
    """Application configuration."""
    max_document_length: int = 50000
    min_document_length: int = 10
    api_timeout_seconds: int = 30
    bedrock_config: BedrockConfig = None
    enable_ner: bool = True  # Toggle spaCy NER
    enable_regex: bool = True  # Toggle regex detection

    def __post_init__(self):
        """Initialize nested configurations."""
        if self.bedrock_config is None:
            self.bedrock_config = BedrockConfig.from_env()

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load application configuration from environment variables."""
        return cls(
            max_document_length=int(os.getenv("MAX_DOCUMENT_LENGTH", "50000")),
            min_document_length=int(os.getenv("MIN_DOCUMENT_LENGTH", "10")),
            api_timeout_seconds=int(os.getenv("API_TIMEOUT_SECONDS", "30")),
            bedrock_config=BedrockConfig.from_env(),
            enable_ner=os.getenv("ENABLE_NER", "true").lower() == "true",
            enable_regex=os.getenv("ENABLE_REGEX", "true").lower() == "true",
        )
