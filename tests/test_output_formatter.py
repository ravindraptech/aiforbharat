"""
Unit tests for the Output Formatter module.

Tests cover:
- Output structure completeness
- JSON serialization
- Disclaimer presence
- Field formatting
"""

import pytest
from datetime import datetime

from app.services.output_formatter import OutputFormatter
from app.models.data_models import (
    SensitiveDataFinding,
    SensitiveDataType,
    ComplianceAnalysis,
    ComplianceRisk,
    ComplianceRiskType,
    SeverityLevel,
    ScoringResult,
    ScoreDeduction,
    RiskLevel,
)


class TestOutputFormatter:
    """Test suite for OutputFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create an OutputFormatter instance."""
        return OutputFormatter()

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

    @pytest.fixture
    def sample_analysis(self):
        """Create sample compliance analysis."""
        return ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description="No patient consent found",
                    severity=SeverityLevel.HIGH,
                    location="Section 1"
                )
            ],
            suggestions=["Add explicit consent statement", "Include privacy notice"],
            analysis_timestamp=datetime.now()
        )

    @pytest.fixture
    def sample_scoring(self):
        """Create sample scoring result."""
        return ScoringResult(
            score=75,
            risk_level=RiskLevel.MEDIUM,
            deductions=[
                ScoreDeduction(
                    reason="High severity risk",
                    points=15,
                    related_finding="missing_consent"
                )
            ]
        )

    def test_format_output_structure(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that output contains all required fields."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring,
            processing_time_ms=1500
        )
        
        # Verify all required fields are present
        assert hasattr(output, 'compliance_score')
        assert hasattr(output, 'risk_level')
        assert hasattr(output, 'sensitive_data')
        assert hasattr(output, 'compliance_risks')
        assert hasattr(output, 'suggestions')
        assert hasattr(output, 'disclaimer')
        assert hasattr(output, 'timestamp')
        assert hasattr(output, 'processing_time_ms')

    def test_compliance_score_included(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that compliance score is included in output."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        assert output.compliance_score == 75
        assert isinstance(output.compliance_score, int)

    def test_risk_level_included(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that risk level is included as string."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        assert output.risk_level == "Medium"
        assert isinstance(output.risk_level, str)

    def test_sensitive_data_formatting(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that sensitive data is formatted as list of dictionaries."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        assert isinstance(output.sensitive_data, list)
        assert len(output.sensitive_data) == 2
        
        # Check first finding
        finding = output.sensitive_data[0]
        assert isinstance(finding, dict)
        assert "type" in finding
        assert "value" in finding
        assert "location" in finding
        assert "confidence" in finding
        assert "detection_method" in finding
        
        assert finding["type"] == "email"
        assert finding["value"] == "***@***.com"
        assert finding["location"] == 10
        assert finding["confidence"] == 1.0
        assert finding["detection_method"] == "regex"

    def test_compliance_risks_formatting(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that compliance risks are formatted as list of dictionaries."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        assert isinstance(output.compliance_risks, list)
        assert len(output.compliance_risks) == 1
        
        # Check risk structure
        risk = output.compliance_risks[0]
        assert isinstance(risk, dict)
        assert "type" in risk
        assert "description" in risk
        assert "severity" in risk
        assert "location" in risk
        
        assert risk["type"] == "missing_consent"
        assert risk["description"] == "No patient consent found"
        assert risk["severity"] == "high"
        assert risk["location"] == "Section 1"

    def test_compliance_risk_without_location(self, formatter, sample_findings, sample_scoring):
        """Test formatting of compliance risk without location field."""
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_PRIVACY_NOTICE,
                    description="No privacy notice",
                    severity=SeverityLevel.MEDIUM,
                    location=None
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        output = formatter.format_output(
            sample_findings,
            analysis,
            sample_scoring
        )
        
        risk = output.compliance_risks[0]
        # Location should not be in dict if None
        assert "type" in risk
        assert "description" in risk
        assert "severity" in risk

    def test_suggestions_included(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that suggestions are included in output."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        assert isinstance(output.suggestions, list)
        assert len(output.suggestions) == 2
        assert "Add explicit consent statement" in output.suggestions
        assert "Include privacy notice" in output.suggestions

    def test_disclaimer_present(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that disclaimer is present in output."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        assert output.disclaimer is not None
        assert isinstance(output.disclaimer, str)
        assert len(output.disclaimer) > 0
        
        # Check for key disclaimer phrases
        assert "educational" in output.disclaimer.lower()
        assert "legal advice" in output.disclaimer.lower()
        assert "medical advice" in output.disclaimer.lower()
        assert "synthetic or public data" in output.disclaimer.lower()
        assert "PHI" in output.disclaimer

    def test_disclaimer_content(self, formatter):
        """Test that disclaimer contains all required warnings."""
        disclaimer = formatter.DISCLAIMER
        
        # Verify all required elements
        assert "educational and internal compliance awareness purposes only" in disclaimer
        assert "does not constitute legal advice" in disclaimer
        assert "medical advice" in disclaimer
        assert "professional compliance consultation" in disclaimer
        assert "automated analysis" in disclaimer
        assert "may not capture all risks" in disclaimer
        assert "consult qualified legal and compliance professionals" in disclaimer
        assert "synthetic or public data" in disclaimer
        assert "never upload real protected health information" in disclaimer
        assert "PHI" in disclaimer

    def test_timestamp_included(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that timestamp is included in ISO format."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        assert output.timestamp is not None
        assert isinstance(output.timestamp, str)
        
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(output.timestamp)

    def test_processing_time_included(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that processing time is included."""
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring,
            processing_time_ms=2500
        )
        
        assert output.processing_time_ms == 2500
        assert isinstance(output.processing_time_ms, int)

    def test_empty_findings(self, formatter, sample_analysis, sample_scoring):
        """Test formatting with no sensitive data findings."""
        output = formatter.format_output(
            [],
            sample_analysis,
            sample_scoring
        )
        
        assert isinstance(output.sensitive_data, list)
        assert len(output.sensitive_data) == 0
        assert output.compliance_score == 75

    def test_empty_risks(self, formatter, sample_findings, sample_scoring):
        """Test formatting with no compliance risks."""
        analysis = ComplianceAnalysis(
            risks=[],
            suggestions=["Document looks good"],
            analysis_timestamp=datetime.now()
        )
        
        output = formatter.format_output(
            sample_findings,
            analysis,
            sample_scoring
        )
        
        assert isinstance(output.compliance_risks, list)
        assert len(output.compliance_risks) == 0
        assert len(output.suggestions) == 1

    def test_multiple_findings_and_risks(self, formatter, sample_scoring):
        """Test formatting with multiple findings and risks."""
        findings = [
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
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.PHONE,
                value="***-***-****",
                location=20,
                confidence=1.0,
                detection_method="regex"
            )
        ]
        
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description="No consent",
                    severity=SeverityLevel.HIGH
                ),
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_PRIVACY_NOTICE,
                    description="No privacy notice",
                    severity=SeverityLevel.MEDIUM
                ),
                ComplianceRisk(
                    type=ComplianceRiskType.UNSAFE_SHARING,
                    description="Unsafe sharing language",
                    severity=SeverityLevel.HIGH
                )
            ],
            suggestions=["Add consent", "Add privacy notice", "Review sharing policies"],
            analysis_timestamp=datetime.now()
        )
        
        output = formatter.format_output(
            findings,
            analysis,
            sample_scoring
        )
        
        assert len(output.sensitive_data) == 3
        assert len(output.compliance_risks) == 3
        assert len(output.suggestions) == 3

    def test_output_json_serializable(self, formatter, sample_findings, sample_analysis, sample_scoring):
        """Test that output can be converted to JSON."""
        import json
        
        output = formatter.format_output(
            sample_findings,
            sample_analysis,
            sample_scoring
        )
        
        # Convert to dict and then to JSON
        output_dict = {
            "compliance_score": output.compliance_score,
            "risk_level": output.risk_level,
            "sensitive_data": output.sensitive_data,
            "compliance_risks": output.compliance_risks,
            "suggestions": output.suggestions,
            "disclaimer": output.disclaimer,
            "timestamp": output.timestamp,
            "processing_time_ms": output.processing_time_ms
        }
        
        # Should not raise exception
        json_str = json.dumps(output_dict)
        assert isinstance(json_str, str)
        
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed["compliance_score"] == 75
        assert parsed["risk_level"] == "Medium"
