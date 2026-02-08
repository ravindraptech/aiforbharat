"""
Unit tests for core data models.

Tests verify that all enums and dataclasses can be instantiated correctly
and have the expected attributes and values.
"""

import pytest
from datetime import datetime
from app.models.data_models import (
    RiskLevel,
    SeverityLevel,
    SensitiveDataType,
    ComplianceRiskType,
    SensitiveDataFinding,
    ComplianceRisk,
    ComplianceAnalysis,
    ScoreDeduction,
    ScoringResult,
    AnalysisOutput,
)


class TestEnums:
    """Test enum definitions."""

    def test_risk_level_enum(self):
        """Test RiskLevel enum has correct values."""
        assert RiskLevel.LOW.value == "Low"
        assert RiskLevel.MEDIUM.value == "Medium"
        assert RiskLevel.HIGH.value == "High"

    def test_severity_level_enum(self):
        """Test SeverityLevel enum has correct values."""
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.HIGH.value == "high"

    def test_sensitive_data_type_enum(self):
        """Test SensitiveDataType enum has all required types."""
        expected_types = {
            "email", "phone", "name", "address", "ssn",
            "medical_record_number", "insurance_id", "health_condition",
            "age", "date_of_birth"
        }
        actual_types = {member.value for member in SensitiveDataType}
        assert actual_types == expected_types

    def test_compliance_risk_type_enum(self):
        """Test ComplianceRiskType enum has all required types."""
        expected_types = {
            "missing_consent", "unsafe_data_sharing",
            "missing_privacy_notice", "missing_confidentiality_statement"
        }
        actual_types = {member.value for member in ComplianceRiskType}
        assert actual_types == expected_types


class TestDataclasses:
    """Test dataclass instantiation and attributes."""

    def test_sensitive_data_finding(self):
        """Test SensitiveDataFinding can be instantiated."""
        finding = SensitiveDataFinding(
            type=SensitiveDataType.EMAIL,
            value="***@***.com",
            location=42,
            confidence=0.95,
            detection_method="regex"
        )
        assert finding.type == SensitiveDataType.EMAIL
        assert finding.value == "***@***.com"
        assert finding.location == 42
        assert finding.confidence == 0.95
        assert finding.detection_method == "regex"

    def test_compliance_risk(self):
        """Test ComplianceRisk can be instantiated."""
        risk = ComplianceRisk(
            type=ComplianceRiskType.MISSING_CONSENT,
            description="No consent statement found",
            severity=SeverityLevel.HIGH,
            location="Section 1"
        )
        assert risk.type == ComplianceRiskType.MISSING_CONSENT
        assert risk.description == "No consent statement found"
        assert risk.severity == SeverityLevel.HIGH
        assert risk.location == "Section 1"

    def test_compliance_risk_optional_location(self):
        """Test ComplianceRisk with optional location."""
        risk = ComplianceRisk(
            type=ComplianceRiskType.MISSING_CONSENT,
            description="No consent statement found",
            severity=SeverityLevel.HIGH
        )
        assert risk.location is None

    def test_compliance_analysis(self):
        """Test ComplianceAnalysis can be instantiated."""
        risk = ComplianceRisk(
            type=ComplianceRiskType.MISSING_CONSENT,
            description="No consent",
            severity=SeverityLevel.HIGH
        )
        analysis = ComplianceAnalysis(
            risks=[risk],
            suggestions=["Add consent statement"]
        )
        assert len(analysis.risks) == 1
        assert len(analysis.suggestions) == 1
        assert isinstance(analysis.analysis_timestamp, datetime)

    def test_score_deduction(self):
        """Test ScoreDeduction can be instantiated."""
        deduction = ScoreDeduction(
            reason="High severity risk",
            points=15,
            related_finding="missing_consent"
        )
        assert deduction.reason == "High severity risk"
        assert deduction.points == 15
        assert deduction.related_finding == "missing_consent"

    def test_score_deduction_optional_finding(self):
        """Test ScoreDeduction with optional related_finding."""
        deduction = ScoreDeduction(
            reason="General deduction",
            points=10
        )
        assert deduction.related_finding is None

    def test_scoring_result(self):
        """Test ScoringResult can be instantiated."""
        deduction = ScoreDeduction(reason="Test", points=10)
        result = ScoringResult(
            score=75,
            risk_level=RiskLevel.MEDIUM,
            deductions=[deduction]
        )
        assert result.score == 75
        assert result.risk_level == RiskLevel.MEDIUM
        assert len(result.deductions) == 1

    def test_analysis_output(self):
        """Test AnalysisOutput can be instantiated."""
        output = AnalysisOutput(
            compliance_score=85,
            risk_level="Low",
            sensitive_data=[{"type": "email", "value": "***@***.com"}],
            compliance_risks=[{"type": "missing_consent", "severity": "low"}],
            suggestions=["Add privacy notice"],
            disclaimer="This is for educational purposes only.",
            timestamp="2024-01-01T00:00:00Z",
            processing_time_ms=1500
        )
        assert output.compliance_score == 85
        assert output.risk_level == "Low"
        assert len(output.sensitive_data) == 1
        assert len(output.compliance_risks) == 1
        assert len(output.suggestions) == 1
        assert output.disclaimer == "This is for educational purposes only."
        assert output.timestamp == "2024-01-01T00:00:00Z"
        assert output.processing_time_ms == 1500


class TestDataModelIntegration:
    """Test that data models work together correctly."""

    def test_complete_analysis_workflow(self):
        """Test creating a complete analysis output with all components."""
        # Create sensitive data finding
        finding = SensitiveDataFinding(
            type=SensitiveDataType.EMAIL,
            value="***@***.com",
            location=100,
            confidence=0.95,
            detection_method="regex"
        )

        # Create compliance risk
        risk = ComplianceRisk(
            type=ComplianceRiskType.MISSING_CONSENT,
            description="No consent statement found",
            severity=SeverityLevel.HIGH
        )

        # Create compliance analysis
        analysis = ComplianceAnalysis(
            risks=[risk],
            suggestions=["Add consent statement", "Include privacy notice"]
        )

        # Create score deduction
        deduction = ScoreDeduction(
            reason="High severity compliance risk",
            points=15,
            related_finding="missing_consent"
        )

        # Create scoring result
        scoring = ScoringResult(
            score=70,
            risk_level=RiskLevel.MEDIUM,
            deductions=[deduction]
        )

        # Create final output
        output = AnalysisOutput(
            compliance_score=scoring.score,
            risk_level=scoring.risk_level.value,
            sensitive_data=[{
                "type": finding.type.value,
                "value": finding.value,
                "location": finding.location,
                "confidence": finding.confidence
            }],
            compliance_risks=[{
                "type": risk.type.value,
                "description": risk.description,
                "severity": risk.severity.value
            }],
            suggestions=analysis.suggestions,
            disclaimer="Educational purposes only",
            timestamp=datetime.now().isoformat(),
            processing_time_ms=2000
        )

        # Verify the complete workflow
        assert output.compliance_score == 70
        assert output.risk_level == "Medium"
        assert len(output.sensitive_data) == 1
        assert len(output.compliance_risks) == 1
        assert len(output.suggestions) == 2
        assert output.processing_time_ms == 2000
