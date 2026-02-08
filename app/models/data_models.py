"""
Core data models for the Healthcare Compliance Copilot.

This module defines the data structures used throughout the application for
representing sensitive data findings, compliance risks, scoring results, and
analysis outputs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk level classification for compliance analysis."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class SeverityLevel(Enum):
    """Severity level for compliance risks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SensitiveDataType(Enum):
    """Types of sensitive data that can be detected in documents."""
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    SSN = "ssn"
    MEDICAL_RECORD_NUMBER = "medical_record_number"
    INSURANCE_ID = "insurance_id"
    HEALTH_CONDITION = "health_condition"
    AGE = "age"
    DATE_OF_BIRTH = "date_of_birth"


class ComplianceRiskType(Enum):
    """Types of compliance risks that can be identified."""
    MISSING_CONSENT = "missing_consent"
    UNSAFE_SHARING = "unsafe_data_sharing"
    MISSING_PRIVACY_NOTICE = "missing_privacy_notice"
    MISSING_CONFIDENTIALITY = "missing_confidentiality_statement"


@dataclass
class SensitiveDataFinding:
    """
    Represents a detected instance of sensitive data in a document.
    
    Attributes:
        type: The type of sensitive data detected
        value: Redacted value (e.g., "***@***.com" for emails)
        location: Character position in the document where data was found
        confidence: Confidence score from 0.0 to 1.0
        detection_method: Method used to detect the data ("regex" or "ner")
    """
    type: SensitiveDataType
    value: str
    location: int
    confidence: float
    detection_method: str


@dataclass
class ComplianceRisk:
    """
    Represents an identified compliance risk in a document.
    
    Attributes:
        type: The type of compliance risk
        description: Detailed description of the risk
        severity: Severity level of the risk
        location: Optional section of document where risk was found
    """
    type: ComplianceRiskType
    description: str
    severity: SeverityLevel
    location: Optional[str] = None


@dataclass
class ComplianceAnalysis:
    """
    Results from LLM-based compliance analysis.
    
    Attributes:
        risks: List of identified compliance risks
        suggestions: List of actionable improvement suggestions
        analysis_timestamp: Timestamp when analysis was performed
    """
    risks: List[ComplianceRisk]
    suggestions: List[str]
    analysis_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ScoreDeduction:
    """
    Represents a deduction from the base compliance score.
    
    Attributes:
        reason: Explanation for the deduction
        points: Number of points deducted
        related_finding: Optional reference to the finding that caused the deduction
    """
    reason: str
    points: int
    related_finding: Optional[str] = None


@dataclass
class ScoringResult:
    """
    Compliance score calculation results.
    
    Attributes:
        score: Compliance score from 0 to 100
        risk_level: Overall risk level classification
        deductions: List of score deductions with explanations
    """
    score: int
    risk_level: RiskLevel
    deductions: List[ScoreDeduction]


@dataclass
class AnalysisOutput:
    """
    Complete analysis output returned to the user.
    
    Attributes:
        compliance_score: Final compliance score (0-100)
        risk_level: Overall risk level as string
        sensitive_data: List of detected sensitive data as dictionaries
        compliance_risks: List of identified compliance risks as dictionaries
        suggestions: List of improvement suggestions
        disclaimer: Mandatory disclaimer text
        timestamp: ISO format timestamp of analysis
        processing_time_ms: Processing time in milliseconds
    """
    compliance_score: int
    risk_level: str
    sensitive_data: List[Dict[str, Any]]
    compliance_risks: List[Dict[str, Any]]
    suggestions: List[str]
    disclaimer: str
    timestamp: str
    processing_time_ms: int
