"""Tests for configuration module."""

import os
import pytest
from app.models.config import BedrockConfig, AppConfig


def test_bedrock_config_defaults():
    """Test BedrockConfig with default values."""
    config = BedrockConfig()
    
    assert config.model_id == "amazon.nova-lite-v1:0"
    assert config.region == "us-east-1"
    assert config.max_tokens == 2000
    assert config.temperature == 0.3
    assert config.guardrail_id is None
    assert config.guardrail_version is None


def test_app_config_defaults():
    """Test AppConfig with default values."""
    config = AppConfig()
    
    assert config.max_document_length == 50000
    assert config.min_document_length == 10
    assert config.api_timeout_seconds == 30
    assert config.enable_ner is True
    assert config.enable_regex is True
    assert config.bedrock_config is not None
    assert isinstance(config.bedrock_config, BedrockConfig)


def test_bedrock_config_from_env(monkeypatch):
    """Test BedrockConfig loading from environment variables."""
    monkeypatch.setenv("BEDROCK_MODEL_ID", "custom-model")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("BEDROCK_MAX_TOKENS", "3000")
    monkeypatch.setenv("BEDROCK_TEMPERATURE", "0.5")
    
    config = BedrockConfig.from_env()
    
    assert config.model_id == "custom-model"
    assert config.region == "us-west-2"
    assert config.max_tokens == 3000
    assert config.temperature == 0.5


def test_app_config_from_env(monkeypatch):
    """Test AppConfig loading from environment variables."""
    monkeypatch.setenv("MAX_DOCUMENT_LENGTH", "100000")
    monkeypatch.setenv("MIN_DOCUMENT_LENGTH", "20")
    monkeypatch.setenv("API_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("ENABLE_NER", "false")
    monkeypatch.setenv("ENABLE_REGEX", "false")
    
    config = AppConfig.from_env()
    
    assert config.max_document_length == 100000
    assert config.min_document_length == 20
    assert config.api_timeout_seconds == 60
    assert config.enable_ner is False
    assert config.enable_regex is False
