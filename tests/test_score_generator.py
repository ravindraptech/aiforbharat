"""
Unit tests for the Score Generator module.

Tests cover:
- Score calculation with various risk combinations
- Risk level assignment
- Deduction tracking
- Edge cases (no findings, maximum deductions)
"""

import pytest
from datetime import datetime

from app.services.score_generator import ScoreGenerator
from app.models.data_models import (
    SensitiveDataFinding,
    SensitiveDataType,
    ComplianceAnalysis,
    ComplianceRisk,
    ComplianceRiskType,
    SeverityLevel,
    RiskLevel,
)


class TestScoreGenerator:
    """Test suite for ScoreGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a ScoreGenerator instance."""
        return ScoreGenerator()

    @pytest.fixture
    def empty_analysis(self):
        """Create an empty compliance analysis."""
        return ComplianceAnalysis(
            risks=[],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )

    def test_clean_document_scores_high(self, generator, empty_analysis):
        """Test that a clean document (no findings, no risks) scores 90+."""
        result = generator.calculate_score([], empty_analysis)
        
        assert result.score >= 90
        assert result.score == 100  # Should be perfect score
        assert result.risk_level == RiskLevel.LOW
        assert len(result.deductions) == 0

    def test_high_severity_risk_deduction(self, generator):
        """Test deduction for high-severity compliance risk."""
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description="No consent found",
                    severity=SeverityLevel.HIGH
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score([], analysis)
        
        assert result.score == 85  # 100 - 15
        assert result.risk_level == RiskLevel.LOW
        assert len(result.deductions) == 1
        assert result.deductions[0].points == 15

    def test_medium_severity_risk_deduction(self, generator):
        """Test deduction for medium-severity compliance risk."""
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_PRIVACY_NOTICE,
                    description="No privacy notice",
                    severity=SeverityLevel.MEDIUM
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score([], analysis)
        
        assert result.score == 90  # 100 - 10
        assert result.risk_level == RiskLevel.LOW
        assert len(result.deductions) == 1
        assert result.deductions[0].points == 10

    def test_low_severity_risk_deduction(self, generator):
        """Test deduction for low-severity compliance risk."""
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONFIDENTIALITY,
                    description="No confidentiality statement",
                    severity=SeverityLevel.LOW
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score([], analysis)
        
        assert result.score == 95  # 100 - 5
        assert result.risk_level == RiskLevel.LOW
        assert len(result.deductions) == 1
        assert result.deductions[0].points == 5

    def test_multiple_compliance_risks(self, generator):
        """Test deductions for multiple compliance risks."""
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description="No consent",
                    severity=SeverityLevel.HIGH
                ),
                ComplianceRisk(
                    type=ComplianceRiskType.UNSAFE_SHARING,
                    description="Unsafe sharing language",
                    severity=SeverityLevel.MEDIUM
                ),
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_PRIVACY_NOTICE,
                    description="No privacy notice",
                    severity=SeverityLevel.LOW
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score([], analysis)
        
        # 100 - 15 (high) - 10 (medium) - 5 (low) = 70
        assert result.score == 70
        assert result.risk_level == RiskLevel.MEDIUM
        assert len(result.deductions) == 3

    def test_sensitive_data_with_safeguards(self, generator, empty_analysis):
        """Test that sensitive data with safeguards doesn't deduct points."""
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
            )
        ]
        
        # Empty analysis means no missing safeguards
        result = generator.calculate_score(findings, empty_analysis)
        
        # Should not deduct for sensitive data if safeguards present
        assert result.score == 100
        assert result.risk_level == RiskLevel.LOW

    def test_sensitive_data_without_safeguards(self, generator):
        """Test deductions for sensitive data without safeguards."""
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
            )
        ]
        
        # Analysis with missing consent = no safeguards
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description="No consent",
                    severity=SeverityLevel.HIGH
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score(findings, analysis)
        
        # 100 - 15 (high risk) - 8 (email) - 8 (name) = 69
        assert result.score == 69
        assert result.risk_level == RiskLevel.MEDIUM
        # 1 for compliance risk + 2 for sensitive data types
        assert len(result.deductions) == 3

    def test_health_condition_with_identifiers(self, generator):
        """Test extra deduction for health condition + identifiers."""
        findings = [
            SensitiveDataFinding(
                type=SensitiveDataType.HEALTH_CONDITION,
                value="diabetes",
                location=20,
                confidence=0.9,
                detection_method="ner"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.NAME,
                value="John ***",
                location=0,
                confidence=0.95,
                detection_method="ner"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value="***@***.com",
                location=10,
                confidence=1.0,
                detection_method="regex"
            )
        ]
        
        # Analysis with missing consent
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description="No consent",
                    severity=SeverityLevel.HIGH
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score(findings, analysis)
        
        # 100 - 15 (high risk) - 8 (health) - 8 (name) - 8 (email) - 20 (combo) = 41
        assert result.score == 41
        assert result.risk_level == RiskLevel.HIGH
        # 1 compliance + 3 sensitive types + 1 combo = 5 deductions
        assert len(result.deductions) == 5

    def test_high_risk_scenario(self, generator):
        """Test high-risk scenario: name + disease + email without consent."""
        findings = [
            SensitiveDataFinding(
                type=SensitiveDataType.NAME,
                value="John ***",
                location=0,
                confidence=0.95,
                detection_method="ner"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.HEALTH_CONDITION,
                value="diabetes",
                location=20,
                confidence=0.9,
                detection_method="ner"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value="***@***.com",
                location=30,
                confidence=1.0,
                detection_method="regex"
            )
        ]
        
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description="No patient consent",
                    severity=SeverityLevel.HIGH
                ),
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_PRIVACY_NOTICE,
                    description="No privacy notice",
                    severity=SeverityLevel.MEDIUM
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score(findings, analysis)
        
        # Should be high risk (score < 50)
        assert result.score < 50
        assert result.risk_level == RiskLevel.HIGH

    def test_risk_level_low(self, generator, empty_analysis):
        """Test risk level assignment for Low (80-100)."""
        result = generator.calculate_score([], empty_analysis)
        assert result.score >= 80
        assert result.risk_level == RiskLevel.LOW

    def test_risk_level_medium(self, generator):
        """Test risk level assignment for Medium (50-79)."""
        # Create scenario that scores in medium range
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
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score([], analysis)
        
        # 100 - 15 - 10 = 75
        assert 50 <= result.score < 80
        assert result.risk_level == RiskLevel.MEDIUM

    def test_risk_level_high(self, generator):
        """Test risk level assignment for High (0-49)."""
        # Create scenario with many risks
        findings = [
            SensitiveDataFinding(
                type=SensitiveDataType.NAME,
                value="***",
                location=0,
                confidence=1.0,
                detection_method="ner"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value="***@***.com",
                location=10,
                confidence=1.0,
                detection_method="regex"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.PHONE,
                value="***-***-****",
                location=20,
                confidence=1.0,
                detection_method="regex"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.HEALTH_CONDITION,
                value="diabetes",
                location=30,
                confidence=0.9,
                detection_method="ner"
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
                    type=ComplianceRiskType.UNSAFE_SHARING,
                    description="Unsafe sharing",
                    severity=SeverityLevel.HIGH
                ),
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_PRIVACY_NOTICE,
                    description="No privacy notice",
                    severity=SeverityLevel.MEDIUM
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score(findings, analysis)
        
        assert result.score < 50
        assert result.risk_level == RiskLevel.HIGH

    def test_score_never_negative(self, generator):
        """Test that score never goes below 0."""
        # Create extreme scenario with many high-severity risks
        findings = [
            SensitiveDataFinding(
                type=SensitiveDataType.NAME,
                value="***",
                location=i * 10,
                confidence=1.0,
                detection_method="ner"
            )
            for i in range(10)
        ]
        
        analysis = ComplianceAnalysis(
            risks=[
                ComplianceRisk(
                    type=ComplianceRiskType.MISSING_CONSENT,
                    description=f"Risk {i}",
                    severity=SeverityLevel.HIGH
                )
                for i in range(10)
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score(findings, analysis)
        
        assert result.score >= 0
        assert result.score <= 100

    def test_deduction_tracking(self, generator):
        """Test that all deductions are properly tracked."""
        findings = [
            SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value="***@***.com",
                location=10,
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
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score(findings, analysis)
        
        # Should have deductions for: 1 compliance risk + 1 sensitive data type
        assert len(result.deductions) == 2
        
        # Verify deduction details
        for deduction in result.deductions:
            assert deduction.reason is not None
            assert deduction.points > 0
            assert isinstance(deduction.reason, str)

    def test_unique_sensitive_types_only(self, generator):
        """Test that duplicate sensitive data types are counted once."""
        findings = [
            SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value="email1@example.com",
                location=10,
                confidence=1.0,
                detection_method="regex"
            ),
            SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value="email2@example.com",
                location=30,
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
                )
            ],
            suggestions=[],
            analysis_timestamp=datetime.now()
        )
        
        result = generator.calculate_score(findings, analysis)
        
        # 100 - 15 (risk) - 8 (email, counted once) = 77
        assert result.score == 77
        # 1 compliance risk + 1 unique sensitive type = 2 deductions
        assert len(result.deductions) == 2
