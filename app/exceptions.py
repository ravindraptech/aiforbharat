"""
Custom exception classes for Healthcare Compliance Copilot.

This module defines custom exceptions for better error handling and reporting.
"""


class InputValidationError(Exception):
    """
    Raised when input validation fails.
    
    Examples:
    - Document too short or too long
    - Invalid file format
    - Missing required fields
    """
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ProcessingError(Exception):
    """
    Raised when document processing fails.
    
    Examples:
    - PDF extraction failure
    - Text preprocessing error
    - Analysis pipeline failure
    """
    
    def __init__(self, message: str, error_code: str = "PROCESSING_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class APIError(Exception):
    """
    Raised when external API calls fail.
    
    Examples:
    - Bedrock API timeout
    - AWS credentials invalid
    - Network connectivity issues
    """
    
    def __init__(self, message: str, error_code: str = "API_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
