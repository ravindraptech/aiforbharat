"""
Unit tests for API request and response models.

Tests verify Pydantic model validation, field constraints, and error handling
for the FastAPI request/response models.
"""

import pytest
from pydantic import ValidationError
from app.models.api_models import (
    AnalysisRequest,
    AnalysisResponse,
    ErrorResponse,
)


class TestAnalysisRequest:
    """Test AnalysisRequest model validation."""

    def test_valid_text_request(self):
        """Test valid request with text input."""
        request = AnalysisRequest(
            text="Patient John Doe was diagnosed with diabetes."
        )
        assert request.text == "Patient John Doe was diagnosed with diabetes."
        assert request.file_content is None
        assert request.file_type is None

    def test_valid_file_request(self):
        """Test valid request with file content."""
        request = AnalysisRequest(
            file_content="UGF0aWVudCBKb2huIERvZQ==",
            file_type="txt"
        )
        assert request.file_content == "UGF0aWVudCBKb2huIERvZQ=="
        assert request.file_type == "txt"
        assert request.text is None

    def test_valid_pdf_file_request(self):
        """Test valid request with PDF file."""
        request = AnalysisRequest(
            file_content="JVBERi0xLjQK",
            file_type="pdf"
        )
        assert request.file_type == "pdf"

    def test_both_text_and_file_allowed(self):
        """Test that both text and file can be provided."""
        request = AnalysisRequest(
            text="Some text",
            file_content="base64content",
            file_type="txt"
        )
        assert request.text == "Some text"
        assert request.file_content == "base64content"

    def test_missing_both_text_and_file_raises_error(self):
        """Test that missing both text and file raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest()
        
        error_msg = str(exc_info.value)
        assert "Either 'text' or 'file_content' must be provided" in error_msg

    def test_file_content_without_file_type_raises_error(self):
        """Test that file_content without file_type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest(file_content="base64content")
        
        error_msg = str(exc_info.value)
        assert "'file_type' must be provided when 'file_content' is specified" in error_msg

    def test_invalid_file_type_raises_error(self):
        """Test that invalid file_type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest(
                file_content="base64content",
                file_type="docx"
            )
        
        error_msg = str(exc_info.value)
        # Pydantic pattern validation error message
        assert "String should match pattern" in error_msg or "file_type must be 'txt' or 'pdf'" in error_msg

    def test_file_type_pattern_validation(self):
        """Test that file_type pattern validation works."""
        # Valid file types
        request1 = AnalysisRequest(file_content="content", file_type="txt")
        assert request1.file_type == "txt"
        
        request2 = AnalysisRequest(file_content="content", file_type="pdf")
        assert request2.file_type == "pdf"
        
        # Invalid file types
        with pytest.raises(ValidationError):
            AnalysisRequest(file_content="content", file_type="doc")
        
        with pytest.raises(ValidationError):
            AnalysisRequest(file_content="content", file_type="TXT")

    def test_empty_text_is_valid(self):
        """Test that empty text string is accepted (validation happens in preprocessing)."""
        request = AnalysisRequest(text="")
        assert request.text == ""


class TestAnalysisResponse:
    """Test AnalysisResponse model validation."""

    def test_valid_response(self):
        """Test valid response with all required fields."""
        response = AnalysisResponse(
            compliance_score=75,
            risk_level="Medium",
            sensitive_data=[
                {
                    "type": "email",
                    "value": "***@***.com",
                    "location": 45,
                    "confidence": 1.0,
                    "detection_method": "regex"
                }
            ],
            compliance_risks=[
                {
                    "type": "missing_consent",
                    "description": "No consent found",
                    "severity": "high",
                    "location": None
                }
            ],
            suggestions=["Add consent statement"],
            disclaimer="Educational purposes only",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=1250
        )
        assert response.compliance_score == 75
        assert response.risk_level == "Medium"
        assert len(response.sensitive_data) == 1
        assert len(response.compliance_risks) == 1
        assert len(response.suggestions) == 1

    def test_compliance_score_range_validation(self):
        """Test that compliance_score must be between 0 and 100."""
        # Valid scores
        response_min = AnalysisResponse(
            compliance_score=0,
            risk_level="High",
            sensitive_data=[],
            compliance_risks=[],
            suggestions=[],
            disclaimer="Test",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=1000
        )
        assert response_min.compliance_score == 0

        response_max = AnalysisResponse(
            compliance_score=100,
            risk_level="Low",
            sensitive_data=[],
            compliance_risks=[],
            suggestions=[],
            disclaimer="Test",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=1000
        )
        assert response_max.compliance_score == 100

        # Invalid scores
        with pytest.raises(ValidationError) as exc_info:
            AnalysisResponse(
                compliance_score=-1,
                risk_level="High",
                sensitive_data=[],
                compliance_risks=[],
                suggestions=[],
                disclaimer="Test",
                timestamp="2024-01-15T10:30:00.000Z",
                processing_time_ms=1000
            )
        assert "greater than or equal to 0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            AnalysisResponse(
                compliance_score=101,
                risk_level="Low",
                sensitive_data=[],
                compliance_risks=[],
                suggestions=[],
                disclaimer="Test",
                timestamp="2024-01-15T10:30:00.000Z",
                processing_time_ms=1000
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_risk_level_pattern_validation(self):
        """Test that risk_level must match pattern Low/Medium/High."""
        # Valid risk levels
        for risk_level in ["Low", "Medium", "High"]:
            response = AnalysisResponse(
                compliance_score=50,
                risk_level=risk_level,
                sensitive_data=[],
                compliance_risks=[],
                suggestions=[],
                disclaimer="Test",
                timestamp="2024-01-15T10:30:00.000Z",
                processing_time_ms=1000
            )
            assert response.risk_level == risk_level

        # Invalid risk levels
        invalid_levels = ["low", "MEDIUM", "high", "Critical", "Unknown", ""]
        for invalid_level in invalid_levels:
            with pytest.raises(ValidationError) as exc_info:
                AnalysisResponse(
                    compliance_score=50,
                    risk_level=invalid_level,
                    sensitive_data=[],
                    compliance_risks=[],
                    suggestions=[],
                    disclaimer="Test",
                    timestamp="2024-01-15T10:30:00.000Z",
                    processing_time_ms=1000
                )
            assert "String should match pattern" in str(exc_info.value)

    def test_empty_lists_allowed(self):
        """Test that empty lists are valid for sensitive_data, compliance_risks, and suggestions."""
        response = AnalysisResponse(
            compliance_score=95,
            risk_level="Low",
            sensitive_data=[],
            compliance_risks=[],
            suggestions=[],
            disclaimer="Test",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=500
        )
        assert response.sensitive_data == []
        assert response.compliance_risks == []
        assert response.suggestions == []

    def test_processing_time_must_be_non_negative(self):
        """Test that processing_time_ms must be >= 0."""
        # Valid processing time
        response = AnalysisResponse(
            compliance_score=50,
            risk_level="Medium",
            sensitive_data=[],
            compliance_risks=[],
            suggestions=[],
            disclaimer="Test",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=0
        )
        assert response.processing_time_ms == 0

        # Invalid processing time
        with pytest.raises(ValidationError) as exc_info:
            AnalysisResponse(
                compliance_score=50,
                risk_level="Medium",
                sensitive_data=[],
                compliance_risks=[],
                suggestions=[],
                disclaimer="Test",
                timestamp="2024-01-15T10:30:00.000Z",
                processing_time_ms=-100
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_complex_response_with_multiple_findings(self):
        """Test response with multiple sensitive data and compliance risks."""
        response = AnalysisResponse(
            compliance_score=65,
            risk_level="Medium",
            sensitive_data=[
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
                },
                {
                    "type": "phone",
                    "value": "***-***-1234",
                    "location": 60,
                    "confidence": 1.0,
                    "detection_method": "regex"
                }
            ],
            compliance_risks=[
                {
                    "type": "missing_consent",
                    "description": "No patient consent statement found",
                    "severity": "high",
                    "location": None
                },
                {
                    "type": "missing_privacy_notice",
                    "description": "Privacy notice not included",
                    "severity": "medium",
                    "location": None
                }
            ],
            suggestions=[
                "Add explicit patient consent statement",
                "Include privacy notice regarding data handling",
                "Add confidentiality statement"
            ],
            disclaimer="DISCLAIMER: This tool is for educational purposes only...",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=1250
        )
        assert len(response.sensitive_data) == 3
        assert len(response.compliance_risks) == 2
        assert len(response.suggestions) == 3


class TestErrorResponse:
    """Test ErrorResponse model validation."""

    def test_valid_error_response(self):
        """Test valid error response with all fields."""
        error = ErrorResponse(
            error="Document must be at least 10 characters",
            error_code="DOCUMENT_TOO_SHORT",
            details="Received document with 5 characters",
            timestamp="2024-01-15T10:30:00.000Z"
        )
        assert error.error == "Document must be at least 10 characters"
        assert error.error_code == "DOCUMENT_TOO_SHORT"
        assert error.details == "Received document with 5 characters"
        assert error.timestamp == "2024-01-15T10:30:00.000Z"

    def test_error_response_without_details(self):
        """Test error response with optional details field omitted."""
        error = ErrorResponse(
            error="Internal server error",
            error_code="PROCESSING_ERROR",
            timestamp="2024-01-15T10:30:00.000Z"
        )
        assert error.error == "Internal server error"
        assert error.error_code == "PROCESSING_ERROR"
        assert error.details is None
        assert error.timestamp == "2024-01-15T10:30:00.000Z"

    def test_various_error_codes(self):
        """Test error response with various error codes."""
        error_codes = [
            "DOCUMENT_TOO_SHORT",
            "DOCUMENT_TOO_LARGE",
            "INVALID_FILE_FORMAT",
            "PDF_EXTRACTION_FAILED",
            "BEDROCK_API_ERROR",
            "INVALID_REQUEST",
            "PROCESSING_ERROR"
        ]
        
        for code in error_codes:
            error = ErrorResponse(
                error=f"Error for {code}",
                error_code=code,
                timestamp="2024-01-15T10:30:00.000Z"
            )
            assert error.error_code == code

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raises validation error."""
        # Missing error field
        with pytest.raises(ValidationError):
            ErrorResponse(
                error_code="TEST_ERROR",
                timestamp="2024-01-15T10:30:00.000Z"
            )

        # Missing error_code field
        with pytest.raises(ValidationError):
            ErrorResponse(
                error="Test error",
                timestamp="2024-01-15T10:30:00.000Z"
            )

        # Missing timestamp field
        with pytest.raises(ValidationError):
            ErrorResponse(
                error="Test error",
                error_code="TEST_ERROR"
            )


class TestAPIModelIntegration:
    """Test API models work together in realistic scenarios."""

    def test_request_response_workflow(self):
        """Test complete request-response workflow."""
        # Create request
        request = AnalysisRequest(
            text="Patient John Doe, age 45, was diagnosed with Type 2 Diabetes. Contact: john.doe@example.com"
        )
        assert request.text is not None

        # Simulate successful response
        response = AnalysisResponse(
            compliance_score=70,
            risk_level="Medium",
            sensitive_data=[
                {"type": "name", "value": "John ***", "location": 8, "confidence": 0.95, "detection_method": "ner"},
                {"type": "age", "value": "**", "location": 23, "confidence": 1.0, "detection_method": "regex"},
                {"type": "email", "value": "***@***.com", "location": 75, "confidence": 1.0, "detection_method": "regex"}
            ],
            compliance_risks=[
                {"type": "missing_consent", "description": "No consent found", "severity": "high", "location": None}
            ],
            suggestions=["Add patient consent statement", "Include privacy notice"],
            disclaimer="Educational purposes only",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=1500
        )
        assert response.compliance_score == 70
        assert len(response.sensitive_data) == 3

    def test_request_error_workflow(self):
        """Test request with error response."""
        # Create invalid request (will be caught by validation)
        with pytest.raises(ValidationError):
            AnalysisRequest()

        # Simulate error response for valid request with processing error
        error = ErrorResponse(
            error="Document exceeds 50,000 character limit",
            error_code="DOCUMENT_TOO_LARGE",
            details="Received document with 75,000 characters",
            timestamp="2024-01-15T10:30:00.000Z"
        )
        assert error.error_code == "DOCUMENT_TOO_LARGE"

    def test_file_upload_workflow(self):
        """Test file upload request and response."""
        # Create file upload request
        request = AnalysisRequest(
            file_content="UGF0aWVudCBKb2huIERvZSB3YXMgZGlhZ25vc2VkIHdpdGggZGlhYmV0ZXMu",
            file_type="txt"
        )
        assert request.file_content is not None
        assert request.file_type == "txt"

        # Simulate response
        response = AnalysisResponse(
            compliance_score=85,
            risk_level="Low",
            sensitive_data=[],
            compliance_risks=[],
            suggestions=["Document looks good"],
            disclaimer="Educational purposes only",
            timestamp="2024-01-15T10:30:00.000Z",
            processing_time_ms=800
        )
        assert response.risk_level == "Low"
