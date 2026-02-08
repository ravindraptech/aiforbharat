"""
API request and response models for the Healthcare Compliance Copilot.

This module defines Pydantic models used for FastAPI request validation
and response serialization. These models ensure proper data validation
and provide automatic API documentation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AnalysisRequest(BaseModel):
    """
    Request model for document analysis endpoint.
    
    Attributes:
        text: Document text to analyze (optional if file provided)
        file_content: Base64 encoded file content (optional if text provided)
        file_type: File type - must be "txt" or "pdf" (required if file provided)
    
    Validation:
        - At least one of text or file_content must be provided
        - If file_content is provided, file_type must be specified
        - file_type must be either "txt" or "pdf"
    """
    text: Optional[str] = Field(
        None,
        description="Document text to analyze",
        examples=["Patient John Doe was diagnosed with diabetes..."]
    )
    file_content: Optional[str] = Field(
        None,
        description="Base64 encoded file content"
    )
    file_type: Optional[str] = Field(
        None,
        description="File type: txt or pdf",
        pattern="^(txt|pdf)$"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "Patient John Doe was diagnosed with diabetes. Contact: john@example.com"
                },
                {
                    "file_content": "UGF0aWVudCBKb2huIERvZQ==",
                    "file_type": "txt"
                }
            ]
        }
    )
    
    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that file_type is provided when file_content is present."""
        if v is not None and v not in ['txt', 'pdf']:
            raise ValueError("file_type must be 'txt' or 'pdf'")
        return v
    
    def model_post_init(self, __context) -> None:
        """Validate that at least one input method is provided."""
        if self.text is None and self.file_content is None:
            raise ValueError("Either 'text' or 'file_content' must be provided")
        
        if self.file_content is not None and self.file_type is None:
            raise ValueError("'file_type' must be provided when 'file_content' is specified")


class AnalysisResponse(BaseModel):
    """
    Response model for document analysis endpoint.
    
    Attributes:
        compliance_score: Compliance score from 0 to 100
        risk_level: Risk level classification (Low, Medium, or High)
        sensitive_data: List of detected sensitive data findings
        compliance_risks: List of identified compliance risks
        suggestions: List of actionable improvement suggestions
        disclaimer: Mandatory disclaimer text
        timestamp: ISO format timestamp of analysis
        processing_time_ms: Processing time in milliseconds
    
    Validation:
        - compliance_score must be between 0 and 100 inclusive
        - risk_level must match pattern "Low", "Medium", or "High"
    """
    compliance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Compliance score from 0 to 100",
        examples=[75]
    )
    risk_level: str = Field(
        ...,
        pattern="^(Low|Medium|High)$",
        description="Risk level classification",
        examples=["Medium"]
    )
    sensitive_data: List[Dict[str, Any]] = Field(
        ...,
        description="List of detected sensitive data findings",
        examples=[[
            {
                "type": "email",
                "value": "***@***.com",
                "location": 45,
                "confidence": 1.0,
                "detection_method": "regex"
            }
        ]]
    )
    compliance_risks: List[Dict[str, Any]] = Field(
        ...,
        description="List of identified compliance risks",
        examples=[[
            {
                "type": "missing_consent",
                "description": "No patient consent statement found",
                "severity": "high",
                "location": None
            }
        ]]
    )
    suggestions: List[str] = Field(
        ...,
        description="List of actionable improvement suggestions",
        examples=[["Add explicit patient consent statement", "Include privacy notice"]]
    )
    disclaimer: str = Field(
        ...,
        description="Mandatory disclaimer text",
        examples=["DISCLAIMER: This tool is for educational purposes only..."]
    )
    timestamp: str = Field(
        ...,
        description="ISO format timestamp of analysis",
        examples=["2024-01-15T10:30:00.000Z"]
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds",
        examples=[1250]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "compliance_score": 65,
                "risk_level": "Medium",
                "sensitive_data": [
                    {
                        "type": "email",
                        "value": "***@***.com",
                        "location": 45,
                        "confidence": 1.0,
                        "detection_method": "regex"
                    },
                    {
                        "type": "name",
                        "value": "John ***",
                        "location": 8,
                        "confidence": 0.95,
                        "detection_method": "ner"
                    }
                ],
                "compliance_risks": [
                    {
                        "type": "missing_consent",
                        "description": "No patient consent statement found in document",
                        "severity": "high",
                        "location": None
                    }
                ],
                "suggestions": [
                    "Add explicit patient consent statement",
                    "Include privacy notice regarding data handling",
                    "Add confidentiality statement"
                ],
                "disclaimer": "DISCLAIMER: This tool is for educational and internal compliance awareness purposes only...",
                "timestamp": "2024-01-15T10:30:00.000Z",
                "processing_time_ms": 1250
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Error response model for API error handling.
    
    Attributes:
        error: User-friendly error message
        error_code: Machine-readable error code
        details: Optional additional context about the error
        timestamp: ISO format timestamp when error occurred
    
    Error Codes:
        - DOCUMENT_TOO_SHORT: Document is less than 10 characters
        - DOCUMENT_TOO_LARGE: Document exceeds 50,000 character limit
        - INVALID_FILE_FORMAT: File format is not .txt or .pdf
        - PDF_EXTRACTION_FAILED: Unable to extract text from PDF
        - BEDROCK_API_ERROR: AI analysis service temporarily unavailable
        - INVALID_REQUEST: Request missing required fields
        - PROCESSING_ERROR: Unexpected error during processing
    """
    error: str = Field(
        ...,
        description="User-friendly error message",
        examples=["Document must be at least 10 characters"]
    )
    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["DOCUMENT_TOO_SHORT"]
    )
    details: Optional[str] = Field(
        None,
        description="Optional additional context about the error",
        examples=["Received document with 5 characters"]
    )
    timestamp: str = Field(
        ...,
        description="ISO format timestamp when error occurred",
        examples=["2024-01-15T10:30:00.000Z"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "Document must be at least 10 characters",
                    "error_code": "DOCUMENT_TOO_SHORT",
                    "details": "Received document with 5 characters",
                    "timestamp": "2024-01-15T10:30:00.000Z"
                },
                {
                    "error": "Document exceeds 50,000 character limit",
                    "error_code": "DOCUMENT_TOO_LARGE",
                    "details": "Received document with 75,000 characters",
                    "timestamp": "2024-01-15T10:30:00.000Z"
                },
                {
                    "error": "Only .txt and .pdf files are supported",
                    "error_code": "INVALID_FILE_FORMAT",
                    "details": "Received file type: docx",
                    "timestamp": "2024-01-15T10:30:00.000Z"
                }
            ]
        }
    )
