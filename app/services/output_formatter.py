"""
Output Formatter for Healthcare Compliance Copilot.

This module provides the OutputFormatter class that formats analysis results
into structured JSON output with mandatory disclaimer text.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from app.models.data_models import (
    SensitiveDataFinding,
    ComplianceAnalysis,
    ScoringResult,
    AnalysisOutput,
)

# Configure logging
logger = logging.getLogger(__name__)


class OutputFormatter:
    """
    Formats analysis results into structured output.
    
    This class converts internal data structures into JSON-serializable
    dictionaries and adds mandatory disclaimer text and timestamps.
    """
    
    # Mandatory disclaimer text
    DISCLAIMER = (
        "DISCLAIMER: This tool is for educational and internal compliance awareness purposes only. "
        "It does not constitute legal advice, medical advice, or professional compliance consultation. "
        "Results are based on automated analysis and may not capture all risks. "
        "Always consult qualified legal and compliance professionals for official guidance. "
        "Use only synthetic or public data - never upload real protected health information (PHI)."
    )
    
    def __init__(self):
        """Initialize the Output Formatter."""
        logger.info("OutputFormatter initialized")
    
    def format_output(
        self,
        sensitive_findings: List[SensitiveDataFinding],
        compliance_analysis: ComplianceAnalysis,
        scoring_result: ScoringResult,
        processing_time_ms: int = 0
    ) -> AnalysisOutput:
        """
        Format all analysis results into structured output.
        
        Args:
            sensitive_findings: List of detected sensitive data
            compliance_analysis: Compliance risks and suggestions
            scoring_result: Score and risk level
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            AnalysisOutput with all results formatted for JSON serialization
        """
        logger.info("Formatting analysis output")
        
        # Convert sensitive findings to dictionaries
        sensitive_data_dicts = self._format_sensitive_findings(sensitive_findings)
        
        # Convert compliance risks to dictionaries
        compliance_risks_dicts = self._format_compliance_risks(compliance_analysis.risks)
        
        # Get timestamp
        timestamp = datetime.now().isoformat()
        
        output = AnalysisOutput(
            compliance_score=scoring_result.score,
            risk_level=scoring_result.risk_level.value,
            sensitive_data=sensitive_data_dicts,
            compliance_risks=compliance_risks_dicts,
            suggestions=compliance_analysis.suggestions,
            disclaimer=self.DISCLAIMER,
            timestamp=timestamp,
            processing_time_ms=processing_time_ms
        )
        
        logger.info(
            f"Output formatted: score={output.compliance_score}, "
            f"risk_level={output.risk_level}, "
            f"sensitive_data_count={len(output.sensitive_data)}, "
            f"compliance_risks_count={len(output.compliance_risks)}"
        )
        
        return output
    
    def _format_sensitive_findings(
        self,
        findings: List[SensitiveDataFinding]
    ) -> List[Dict[str, Any]]:
        """
        Convert sensitive data findings to dictionaries.
        
        Args:
            findings: List of SensitiveDataFinding objects
            
        Returns:
            List of dictionaries with finding details
        """
        formatted = []
        
        for finding in findings:
            formatted.append({
                "type": finding.type.value,
                "value": finding.value,
                "location": finding.location,
                "confidence": finding.confidence,
                "detection_method": finding.detection_method
            })
        
        logger.debug(f"Formatted {len(formatted)} sensitive data findings")
        return formatted
    
    def _format_compliance_risks(
        self,
        risks: List
    ) -> List[Dict[str, Any]]:
        """
        Convert compliance risks to dictionaries.
        
        Args:
            risks: List of ComplianceRisk objects
            
        Returns:
            List of dictionaries with risk details
        """
        formatted = []
        
        for risk in risks:
            risk_dict = {
                "type": risk.type.value,
                "description": risk.description,
                "severity": risk.severity.value
            }
            
            # Add location if present
            if risk.location:
                risk_dict["location"] = risk.location
            
            formatted.append(risk_dict)
        
        logger.debug(f"Formatted {len(formatted)} compliance risks")
        return formatted
