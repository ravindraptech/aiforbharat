"""
Unit tests for the LLM Analyzer module.

Tests cover:
- Prompt building
- Bedrock API integration (mocked)
- JSON response parsing
- Error handling and retry logic
- Guardrail configuration
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.llm_analyzer import LLMAnalyzer
from app.models.data_models import (
    SensitiveDataFinding,
    SensitiveDataType,
    ComplianceRiskType,
    SeverityLevel,
)
from app.models.config import BedrockConfig
from botocore.exceptions import ClientError


class TestLLMAnalyzer:
    """Test suite for LLMAnalyzer class."""

    @pytest.fixture
    def bedrock_config(self):
        """Create a test Bedrock configuration."""
        return BedrockConfig(
            model_id="amazon.nova-lite-v1:0",
            region="us-east-1",
            max_tokens=2000,
            temperature=0.3,
            guardrail_id="test-guardrail-id",
            guardrail_version="1"
        )

    @pytest.fixture
    def analyzer(self, bedrock_config):
        """Create an LLMAnalyzer instance with mocked boto3 client."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_boto.return_value = mock_client
            analyzer = LLMAnalyzer(bedrock_config)
            analyzer.bedrock_client = mock_client
            return analyzer

    @pytest.fixture
    def sample_findings(self):
        """Create sample sensitive data findings."""
        return [
            SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value="***@***.com",
                location=10,
                confidence=1.0,
                detection_method="regex"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.NAME,
                value="John ***",
                location=0,
                confidence=0.95,
                detection_method="ner"
            )
        ]

    def test_build_prompt(self, analyzer, sample_findings):
        """Test that build_prompt creates a properly formatted prompt."""
        text = "Patient John Doe has diabetes. Contact: john@example.com"
        
        prompt = analyzer.build_prompt(text, sample_findings)
        
        # Verify prompt contains key elements
        assert "healthcare compliance analyzer" in prompt.lower()
        assert "missing consent" in prompt.lower()
        assert "unsafe data sharing" in prompt.lower()
        assert "missing privacy notice" in prompt.lower()
        assert "missing confidentiality" in prompt.lower()
        assert text in prompt
        assert "email" in prompt.lower()
        assert "name" in prompt.lower()
        assert "Do not provide medical advice" in prompt

    def test_build_prompt_no_sensitive_data(self, analyzer):
        """Test prompt building with no sensitive data findings."""
        text = "This is a general healthcare policy document."
        
        prompt = analyzer.build_prompt(text, [])
        
        assert text in prompt
        assert "none" in prompt.lower()

    def test_parse_llm_response_valid_json(self, analyzer):
        """Test parsing a valid JSON response from LLM."""
        response_text = json.dumps({
            "risks": [
                {
                    "type": "missing_consent",
                    "description": "No patient consent statement found",
                    "severity": "high"
                }
            ],
            "suggestions": ["Add explicit consent statement"]
        })
        
        parsed = analyzer._parse_llm_response(response_text)
        
        assert "risks" in parsed
        assert "suggestions" in parsed
        assert len(parsed["risks"]) == 1
        assert parsed["risks"][0]["type"] == "missing_consent"

    def test_parse_llm_response_with_extra_text(self, analyzer):
        """Test parsing JSON when LLM adds extra text around it."""
        response_text = """Here is my analysis:
        {
            "risks": [{"type": "missing_privacy_notice", "description": "No privacy notice", "severity": "medium"}],
            "suggestions": ["Add privacy notice"]
        }
        I hope this helps!"""
        
        parsed = analyzer._parse_llm_response(response_text)
        
        assert "risks" in parsed
        assert len(parsed["risks"]) == 1

    def test_parse_llm_response_invalid_json(self, analyzer):
        """Test that invalid JSON raises ValueError."""
        response_text = "This is not JSON at all"
        
        with pytest.raises(ValueError, match="No JSON object found"):
            analyzer._parse_llm_response(response_text)

    def test_convert_to_compliance_analysis(self, analyzer):
        """Test conversion of parsed JSON to ComplianceAnalysis object."""
        parsed_response = {
            "risks": [
                {
                    "type": "missing_consent",
                    "description": "No consent found",
                    "severity": "high"
                },
                {
                    "type": "unsafe_data_sharing",
                    "description": "Unsafe sharing language detected",
                    "severity": "medium"
                }
            ],
            "suggestions": ["Add consent", "Review sharing policies"]
        }
        
        analysis = analyzer._convert_to_compliance_analysis(parsed_response)
        
        assert len(analysis.risks) == 2
        assert analysis.risks[0].type == ComplianceRiskType.MISSING_CONSENT
        assert analysis.risks[0].severity == SeverityLevel.HIGH
        assert analysis.risks[1].type == ComplianceRiskType.UNSAFE_SHARING
        assert analysis.risks[1].severity == SeverityLevel.MEDIUM
        assert len(analysis.suggestions) == 2
        assert analysis.analysis_timestamp is not None

    def test_convert_handles_unknown_risk_type(self, analyzer):
        """Test that unknown risk types are handled gracefully."""
        parsed_response = {
            "risks": [
                {
                    "type": "unknown_risk_type",
                    "description": "Some risk",
                    "severity": "low"
                }
            ],
            "suggestions": []
        }
        
        analysis = analyzer._convert_to_compliance_analysis(parsed_response)
        
        # Should default to MISSING_CONSENT
        assert len(analysis.risks) == 1
        assert analysis.risks[0].type == ComplianceRiskType.MISSING_CONSENT

    def test_analyze_compliance_success(self, analyzer, sample_findings):
        """Test successful compliance analysis with mocked Bedrock."""
        text = "Patient data without consent"
        
        # Mock Bedrock response
        mock_response = {
            'output': {
                'message': {
                    'content': [
                        {
                            'text': json.dumps({
                                "risks": [
                                    {
                                        "type": "missing_consent",
                                        "description": "No consent statement",
                                        "severity": "high"
                                    }
                                ],
                                "suggestions": ["Add consent statement"]
                            })
                        }
                    ]
                }
            }
        }
        analyzer.bedrock_client.converse = Mock(return_value=mock_response)
        
        analysis = analyzer.analyze_compliance(text, sample_findings)
        
        assert len(analysis.risks) == 1
        assert analysis.risks[0].type == ComplianceRiskType.MISSING_CONSENT
        assert len(analysis.suggestions) == 1
        assert analyzer.bedrock_client.converse.called

    def test_analyze_compliance_with_guardrails(self, bedrock_config, sample_findings):
        """Test that guardrails are included in API call when configured."""
        with patch('boto3.client') as mock_boto:
            mock_client = Mock()
            mock_boto.return_value = mock_client
            
            # Mock successful response
            mock_response = {
                'output': {
                    'message': {
                        'content': [
                            {
                                'text': json.dumps({
                                    "risks": [],
                                    "suggestions": []
                                })
                            }
                        ]
                    }
                }
            }
            mock_client.converse = Mock(return_value=mock_response)
            
            analyzer = LLMAnalyzer(bedrock_config)
            analyzer.analyze_compliance("test text", sample_findings)
            
            # Verify guardrails were passed
            call_args = mock_client.converse.call_args
            assert 'guardrailConfig' in call_args[1]
            assert call_args[1]['guardrailConfig']['guardrailIdentifier'] == "test-guardrail-id"

    def test_analyze_compliance_api_error_returns_empty(self, analyzer, sample_findings):
        """Test that API errors return empty analysis instead of crashing."""
        text = "Test document"
        
        # Mock API error
        analyzer.bedrock_client.converse = Mock(
            side_effect=ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'converse'
            )
        )
        
        analysis = analyzer.analyze_compliance(text, sample_findings)
        
        # Should return empty analysis with error message
        assert len(analysis.risks) == 0
        assert len(analysis.suggestions) == 1
        assert "technical error" in analysis.suggestions[0].lower()

    def test_missing_consent_detection(self, analyzer):
        """Test detection of missing consent statements."""
        text = "Patient John Doe has diabetes. Email: john@example.com"
        findings = [
            SensitiveDataFinding(
                type=SensitiveDataType.NAME,
                value="John ***",
                location=0,
                confidence=0.95,
                detection_method="ner"
            )
        ]
        
        mock_response = {
            'output': {
                'message': {
                    'content': [
                        {
                            'text': json.dumps({
                                "risks": [
                                    {
                                        "type": "missing_consent",
                                        "description": "Document contains PII without consent",
                                        "severity": "high"
                                    }
                                ],
                                "suggestions": ["Add patient consent statement"]
                            })
                        }
                    ]
                }
            }
        }
        analyzer.bedrock_client.converse = Mock(return_value=mock_response)
        
        analysis = analyzer.analyze_compliance(text, findings)
        
        assert any(risk.type == ComplianceRiskType.MISSING_CONSENT for risk in analysis.risks)

    def test_unsafe_sharing_detection(self, analyzer):
        """Test detection of unsafe data sharing language."""
        text = "We may share your data with third parties for marketing purposes."
        
        mock_response = {
            'output': {
                'message': {
                    'content': [
                        {
                            'text': json.dumps({
                                "risks": [
                                    {
                                        "type": "unsafe_data_sharing",
                                        "description": "Unsafe data sharing language detected",
                                        "severity": "high"
                                    }
                                ],
                                "suggestions": ["Clarify data sharing policies"]
                            })
                        }
                    ]
                }
            }
        }
        analyzer.bedrock_client.converse = Mock(return_value=mock_response)
        
        analysis = analyzer.analyze_compliance(text, [])
        
        assert any(risk.type == ComplianceRiskType.UNSAFE_SHARING for risk in analysis.risks)

    def test_missing_privacy_notice_detection(self, analyzer):
        """Test detection of missing privacy notices."""
        text = "Patient data collection form without privacy information."
        
        mock_response = {
            'output': {
                'message': {
                    'content': [
                        {
                            'text': json.dumps({
                                "risks": [
                                    {
                                        "type": "missing_privacy_notice",
                                        "description": "No privacy notice found",
                                        "severity": "medium"
                                    }
                                ],
                                "suggestions": ["Add privacy notice"]
                            })
                        }
                    ]
                }
            }
        }
        analyzer.bedrock_client.converse = Mock(return_value=mock_response)
        
        analysis = analyzer.analyze_compliance(text, [])
        
        assert any(risk.type == ComplianceRiskType.MISSING_PRIVACY_NOTICE for risk in analysis.risks)