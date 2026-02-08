"""
Score Generator for Healthcare Compliance Copilot.

This module provides the ScoreGenerator class that calculates compliance scores
and risk levels based on sensitive data findings and compliance analysis results.
"""

import logging
from typing import List, Set

from app.models.data_models import (
    SensitiveDataFinding,
    SensitiveDataType,
    ComplianceAnalysis,
    ScoringResult,
    ScoreDeduction,
    RiskLevel,
    SeverityLevel,
)

# Configure logging
logger = logging.getLogger(__name__)


class ScoreGenerator:
    """
    Calculates compliance scores and assigns risk levels.
    
    The scoring algorithm starts with a base score of 100 and applies deductions
    based on:
    - Compliance risks (by severity)
    - Sensitive data types present
    - Combination of health conditions with identifiers
    
    Risk levels are assigned based on final score:
    - Low: 80-100
    - Medium: 50-79
    - High: 0-49
    """
    
    # Scoring constants
    BASE_SCORE = 100
    
    # Deduction amounts by severity
    HIGH_SEVERITY_DEDUCTION = 15
    MEDIUM_SEVERITY_DEDUCTION = 10
    LOW_SEVERITY_DEDUCTION = 5
    
    # Sensitive data deductions
    SENSITIVE_DATA_TYPE_DEDUCTION = 8
    HEALTH_CONDITION_WITH_IDENTIFIER_DEDUCTION = 20
    
    # Risk level thresholds
    LOW_RISK_THRESHOLD = 80
    MEDIUM_RISK_THRESHOLD = 50
    
    def __init__(self):
        """Initialize the Score Generator."""
        logger.info("ScoreGenerator initialized")
    
    def calculate_score(
        self,
        sensitive_findings: List[SensitiveDataFinding],
        compliance_analysis: ComplianceAnalysis
    ) -> ScoringResult:
        """
        Calculate compliance score and risk level.
        
        Args:
            sensitive_findings: List of detected sensitive data
            compliance_analysis: LLM compliance analysis with risks
            
        Returns:
            ScoringResult with score, risk level, and deduction details
        """
        logger.info(
            f"Calculating score for {len(sensitive_findings)} findings "
            f"and {len(compliance_analysis.risks)} compliance risks"
        )
        
        score = self.BASE_SCORE
        deductions = []
        
        # Deduct points for compliance risks
        score, risk_deductions = self._deduct_for_compliance_risks(
            score, compliance_analysis.risks
        )
        deductions.extend(risk_deductions)
        
        # Deduct points for sensitive data
        score, data_deductions = self._deduct_for_sensitive_data(
            score, sensitive_findings, compliance_analysis
        )
        deductions.extend(data_deductions)
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        # Assign risk level
        risk_level = self._assign_risk_level(score)
        
        logger.info(
            f"Score calculation complete: {score}/100, Risk Level: {risk_level.value}"
        )
        
        return ScoringResult(
            score=score,
            risk_level=risk_level,
            deductions=deductions
        )
    
    def _deduct_for_compliance_risks(
        self,
        score: int,
        risks: List
    ) -> tuple[int, List[ScoreDeduction]]:
        """
        Deduct points based on compliance risks and their severity.
        
        Args:
            score: Current score
            risks: List of ComplianceRisk objects
            
        Returns:
            Tuple of (updated_score, list_of_deductions)
        """
        deductions = []
        
        for risk in risks:
            if risk.severity == SeverityLevel.HIGH:
                points = self.HIGH_SEVERITY_DEDUCTION
            elif risk.severity == SeverityLevel.MEDIUM:
                points = self.MEDIUM_SEVERITY_DEDUCTION
            else:  # LOW
                points = self.LOW_SEVERITY_DEDUCTION
            
            score -= points
            deductions.append(
                ScoreDeduction(
                    reason=f"{risk.severity.value.capitalize()} severity compliance risk: {risk.type.value}",
                    points=points,
                    related_finding=risk.description
                )
            )
            logger.debug(f"Deducted {points} points for {risk.severity.value} risk: {risk.type.value}")
        
        return score, deductions
    
    def _deduct_for_sensitive_data(
        self,
        score: int,
        sensitive_findings: List[SensitiveDataFinding],
        compliance_analysis: ComplianceAnalysis
    ) -> tuple[int, List[ScoreDeduction]]:
        """
        Deduct points based on sensitive data findings.
        
        Deductions are applied for:
        1. Each unique sensitive data type (if no safeguards present)
        2. Extra deduction if health conditions + identifiers are both present
        
        Args:
            score: Current score
            sensitive_findings: List of sensitive data findings
            compliance_analysis: Compliance analysis (to check for safeguards)
            
        Returns:
            Tuple of (updated_score, list_of_deductions)
        """
        deductions = []
        
        if not sensitive_findings:
            return score, deductions
        
        # Get unique sensitive data types
        unique_types = self._get_unique_sensitive_types(sensitive_findings)
        
        # Check if document has safeguards (consent, privacy notice, etc.)
        has_safeguards = self._has_safeguards(compliance_analysis)
        
        # Deduct for each sensitive data type if no safeguards
        if not has_safeguards:
            for data_type in unique_types:
                score -= self.SENSITIVE_DATA_TYPE_DEDUCTION
                deductions.append(
                    ScoreDeduction(
                        reason=f"Sensitive data type ({data_type.value}) without adequate safeguards",
                        points=self.SENSITIVE_DATA_TYPE_DEDUCTION,
                        related_finding=data_type.value
                    )
                )
                logger.debug(f"Deducted {self.SENSITIVE_DATA_TYPE_DEDUCTION} points for {data_type.value} without safeguards")
        
        # Extra deduction if health conditions + identifiers are present
        if self._has_health_condition_with_identifiers(unique_types):
            score -= self.HEALTH_CONDITION_WITH_IDENTIFIER_DEDUCTION
            deductions.append(
                ScoreDeduction(
                    reason="Health condition combined with personal identifiers",
                    points=self.HEALTH_CONDITION_WITH_IDENTIFIER_DEDUCTION,
                    related_finding="health_condition + identifiers"
                )
            )
            logger.debug(f"Deducted {self.HEALTH_CONDITION_WITH_IDENTIFIER_DEDUCTION} points for health condition + identifiers")
        
        return score, deductions
    
    def _get_unique_sensitive_types(
        self,
        sensitive_findings: List[SensitiveDataFinding]
    ) -> Set[SensitiveDataType]:
        """
        Extract unique sensitive data types from findings.
        
        Args:
            sensitive_findings: List of sensitive data findings
            
        Returns:
            Set of unique SensitiveDataType values
        """
        return set(finding.type for finding in sensitive_findings)
    
    def _has_safeguards(self, compliance_analysis: ComplianceAnalysis) -> bool:
        """
        Check if document has adequate safeguards.
        
        A document is considered to have safeguards if it does NOT have
        missing consent, missing privacy notice, or missing confidentiality risks.
        
        Args:
            compliance_analysis: Compliance analysis results
            
        Returns:
            True if document has safeguards, False otherwise
        """
        from app.models.data_models import ComplianceRiskType
        
        # Check for missing safeguard risks
        missing_safeguard_types = {
            ComplianceRiskType.MISSING_CONSENT,
            ComplianceRiskType.MISSING_PRIVACY_NOTICE,
            ComplianceRiskType.MISSING_CONFIDENTIALITY
        }
        
        for risk in compliance_analysis.risks:
            if risk.type in missing_safeguard_types:
                return False
        
        return True
    
    def _has_health_condition_with_identifiers(
        self,
        unique_types: Set[SensitiveDataType]
    ) -> bool:
        """
        Check if health conditions are combined with personal identifiers.
        
        Args:
            unique_types: Set of unique sensitive data types
            
        Returns:
            True if health condition + identifiers present, False otherwise
        """
        has_health_condition = SensitiveDataType.HEALTH_CONDITION in unique_types
        
        # Identifier types
        identifier_types = {
            SensitiveDataType.NAME,
            SensitiveDataType.EMAIL,
            SensitiveDataType.PHONE,
            SensitiveDataType.SSN,
            SensitiveDataType.MEDICAL_RECORD_NUMBER,
            SensitiveDataType.INSURANCE_ID,
            SensitiveDataType.ADDRESS,
            SensitiveDataType.DATE_OF_BIRTH
        }
        
        has_identifiers = bool(unique_types & identifier_types)
        
        return has_health_condition and has_identifiers
    
    def _assign_risk_level(self, score: int) -> RiskLevel:
        """
        Assign risk level based on score.
        
        Risk levels:
        - Low: 80-100
        - Medium: 50-79
        - High: 0-49
        
        Args:
            score: Compliance score (0-100)
            
        Returns:
            RiskLevel enum value
        """
        if score >= self.LOW_RISK_THRESHOLD:
            return RiskLevel.LOW
        elif score >= self.MEDIUM_RISK_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
