"""
LLM Analyzer for Healthcare Compliance Copilot.

This module provides the LLMAnalyzer class that uses Amazon Bedrock Nova Lite
to analyze documents for compliance risks. It identifies missing consent statements,
unsafe data sharing language, missing privacy notices, and missing confidentiality
statements.
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.models.data_models import (
    ComplianceAnalysis,
    ComplianceRisk,
    ComplianceRiskType,
    SeverityLevel,
    SensitiveDataFinding,
)
from app.models.config import BedrockConfig

# Configure logging
logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    Analyzes documents for compliance risks using Amazon Bedrock Nova Lite.
    
    This class handles:
    - Building prompts for compliance analysis
    - Calling Amazon Bedrock with guardrails
    - Parsing JSON responses into ComplianceAnalysis objects
    - Retry logic for API errors and timeouts
    """

    def __init__(self, config: BedrockConfig = None):
        """
        Initialize the LLM Analyzer with Bedrock configuration.
        
        Args:
            config: BedrockConfig object with model and API settings.
                   If None, loads from environment variables.
        """
        self.config = config or BedrockConfig.from_env()
        
        # Initialize boto3 Bedrock Runtime client
        try:
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.config.region
            )
            logger.info(f"Initialized Bedrock client in region {self.config.region}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise

    def build_prompt(
        self,
        text: str,
        sensitive_findings: List[SensitiveDataFinding]
    ) -> str:
        """
        Construct analysis prompt for Bedrock.
        
        Args:
            text: Preprocessed document text to analyze
            sensitive_findings: List of detected sensitive data findings
            
        Returns:
            Formatted prompt string for the LLM
        """
        # Extract unique sensitive data types
        sensitive_types = list(set([
            finding.type.value for finding in sensitive_findings
        ]))
        
        # Build the prompt following the design specification
        prompt = f"""You are a healthcare compliance analyzer. Review the following document and identify:

1. Missing consent statements
2. Unsafe data sharing language
3. Missing privacy notices
4. Missing confidentiality statements

Document contains the following sensitive data types: {', '.join(sensitive_types) if sensitive_types else 'none'}

Document text:
{text}

Provide your analysis in JSON format with the following structure:
{{
  "risks": [
    {{"type": "missing_consent|unsafe_data_sharing|missing_privacy_notice|missing_confidentiality_statement", "description": "detailed description", "severity": "high|medium|low"}}
  ],
  "suggestions": ["actionable suggestion 1", "actionable suggestion 2"]
}}

IMPORTANT: 
- Do not provide medical advice, diagnosis, or treatment recommendations.
- Focus only on compliance and privacy risks.
- Be specific in your descriptions.
- Provide actionable suggestions for improvement.
"""
        
        return prompt

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError)),
        reraise=True
    )
    def _call_bedrock_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Bedrock API with retry logic.
        
        Args:
            prompt: The prompt to send to Bedrock
            
        Returns:
            Parsed JSON response from Bedrock
            
        Raises:
            ClientError: If API call fails after retries
            ValueError: If response cannot be parsed
        """
        try:
            # Prepare the request body for Nova Lite
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                }
            }
            
            # Add guardrails if configured
            if self.config.guardrail_id and self.config.guardrail_version:
                request_body["guardrailConfig"] = {
                    "guardrailIdentifier": self.config.guardrail_id,
                    "guardrailVersion": self.config.guardrail_version
                }
            
            logger.info(f"Calling Bedrock API with model {self.config.model_id}")
            
            # Call Bedrock
            response = self.bedrock_client.converse(
                modelId=self.config.model_id,
                messages=request_body["messages"],
                inferenceConfig=request_body["inferenceConfig"],
                guardrailConfig=request_body.get("guardrailConfig")
            )
            
            # Extract the response text
            response_text = response['output']['message']['content'][0]['text']
            logger.debug(f"Received response from Bedrock: {response_text[:200]}...")
            
            return response_text
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Bedrock API error ({error_code}): {error_message}")
            raise
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Bedrock: {e}")
            raise

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.
        
        Args:
            response_text: Raw text response from Bedrock
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        try:
            # Try to find JSON in the response (LLM might add extra text)
            # Look for content between curly braces
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON object found in response")
            
            json_str = response_text[start_idx:end_idx + 1]
            parsed = json.loads(json_str)
            
            # Validate required fields
            if 'risks' not in parsed:
                parsed['risks'] = []
            if 'suggestions' not in parsed:
                parsed['suggestions'] = []
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def _convert_to_compliance_analysis(
        self,
        parsed_response: Dict[str, Any]
    ) -> ComplianceAnalysis:
        """
        Convert parsed JSON response to ComplianceAnalysis object.
        
        Args:
            parsed_response: Parsed JSON dictionary from LLM
            
        Returns:
            ComplianceAnalysis object with risks and suggestions
        """
        risks = []
        
        for risk_data in parsed_response.get('risks', []):
            try:
                # Map risk type string to enum
                risk_type_str = risk_data.get('type', '').lower()
                
                # Handle variations in risk type naming
                if 'consent' in risk_type_str:
                    risk_type = ComplianceRiskType.MISSING_CONSENT
                elif 'sharing' in risk_type_str or 'unsafe' in risk_type_str:
                    risk_type = ComplianceRiskType.UNSAFE_SHARING
                elif 'privacy' in risk_type_str:
                    risk_type = ComplianceRiskType.MISSING_PRIVACY_NOTICE
                elif 'confidentiality' in risk_type_str:
                    risk_type = ComplianceRiskType.MISSING_CONFIDENTIALITY
                else:
                    logger.warning(f"Unknown risk type: {risk_type_str}, defaulting to MISSING_CONSENT")
                    risk_type = ComplianceRiskType.MISSING_CONSENT
                
                # Map severity string to enum
                severity_str = risk_data.get('severity', 'medium').lower()
                if severity_str == 'high':
                    severity = SeverityLevel.HIGH
                elif severity_str == 'low':
                    severity = SeverityLevel.LOW
                else:
                    severity = SeverityLevel.MEDIUM
                
                risk = ComplianceRisk(
                    type=risk_type,
                    description=risk_data.get('description', 'No description provided'),
                    severity=severity,
                    location=risk_data.get('location')
                )
                risks.append(risk)
                
            except Exception as e:
                logger.warning(f"Failed to parse risk: {risk_data}, error: {e}")
                continue
        
        suggestions = parsed_response.get('suggestions', [])
        
        return ComplianceAnalysis(
            risks=risks,
            suggestions=suggestions,
            analysis_timestamp=datetime.now()
        )

    def analyze_compliance(
        self,
        text: str,
        sensitive_findings: List[SensitiveDataFinding]
    ) -> ComplianceAnalysis:
        """
        Analyze document for compliance risks using Bedrock.
        
        This is the main entry point for compliance analysis. It:
        1. Builds the analysis prompt
        2. Calls Bedrock API with retry logic
        3. Parses the JSON response
        4. Converts to ComplianceAnalysis object
        
        Args:
            text: Preprocessed document text to analyze
            sensitive_findings: List of detected sensitive data findings
            
        Returns:
            ComplianceAnalysis object with identified risks and suggestions
            
        Raises:
            ValueError: If response cannot be parsed
            ClientError: If Bedrock API fails after retries
        """
        try:
            # Build the prompt
            prompt = self.build_prompt(text, sensitive_findings)
            logger.info("Built compliance analysis prompt")
            
            # Call Bedrock API with retry logic
            response_text = self._call_bedrock_api(prompt)
            
            # Parse JSON response
            parsed_response = self._parse_llm_response(response_text)
            logger.info(f"Parsed response with {len(parsed_response.get('risks', []))} risks")
            
            # Convert to ComplianceAnalysis object
            analysis = self._convert_to_compliance_analysis(parsed_response)
            
            logger.info(f"Compliance analysis complete: {len(analysis.risks)} risks identified")
            return analysis
            
        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            # Return empty analysis rather than failing completely
            return ComplianceAnalysis(
                risks=[],
                suggestions=["Unable to complete compliance analysis due to technical error"],
                analysis_timestamp=datetime.now()
            )
