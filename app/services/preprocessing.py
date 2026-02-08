"""
Preprocessing module for document normalization and validation.

This module handles text normalization, PDF extraction, and input validation
to prepare documents for compliance analysis.
"""

import re
from typing import Optional
import PyPDF2
from io import BytesIO


class InputValidationError(Exception):
    """Raised when input fails validation."""
    
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class PreprocessingModule:
    """
    Handles document preprocessing including text normalization,
    PDF extraction, and input validation.
    """
    
    # Configuration constants
    MAX_DOCUMENT_LENGTH = 50000
    MIN_DOCUMENT_LENGTH = 10
    
    def __init__(self):
        """Initialize the preprocessing module."""
        pass
    
    def preprocess_text(self, text: str) -> str:
        """
        Normalize text input for consistent analysis.
        
        This method:
        - Validates input length
        - Strips leading/trailing whitespace
        - Normalizes multiple spaces to single spaces
        - Preserves paragraph breaks (line breaks)
        
        Args:
            text: Raw text input from user
            
        Returns:
            Normalized text with consistent whitespace and formatting
            
        Raises:
            InputValidationError: If text is empty or exceeds size limits
        """
        # Validate input is not None
        if text is None:
            raise InputValidationError(
                "Document text cannot be None",
                "DOCUMENT_NONE"
            )
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Validate input length
        if not self.validate_input(text):
            if len(text) < self.MIN_DOCUMENT_LENGTH:
                raise InputValidationError(
                    f"Document must be at least {self.MIN_DOCUMENT_LENGTH} characters",
                    "DOCUMENT_TOO_SHORT"
                )
            elif len(text) > self.MAX_DOCUMENT_LENGTH:
                raise InputValidationError(
                    f"Document exceeds {self.MAX_DOCUMENT_LENGTH} character limit",
                    "DOCUMENT_TOO_LARGE"
                )
        
        # Normalize whitespace while preserving paragraph breaks
        # First, normalize line breaks to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into lines to preserve paragraph structure
        lines = text.split('\n')
        
        # Normalize spaces within each line (multiple spaces -> single space)
        normalized_lines = []
        for line in lines:
            # Replace multiple spaces with single space
            normalized_line = re.sub(r' +', ' ', line)
            # Strip leading/trailing spaces from each line
            normalized_line = normalized_line.strip()
            normalized_lines.append(normalized_line)
        
        # Join lines back together, preserving paragraph breaks
        # Remove excessive blank lines (more than 2 consecutive)
        result = '\n'.join(normalized_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
    
    def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """
        Extract text content from PDF file.
        
        This method uses PyPDF2 to extract text from PDF files while
        attempting to preserve document structure (paragraphs, sections).
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
            
        Raises:
            InputValidationError: If PDF is invalid or cannot be parsed
        """
        if not pdf_bytes:
            raise InputValidationError(
                "PDF content is empty",
                "PDF_EMPTY"
            )
        
        try:
            # Create a BytesIO object from the bytes
            pdf_file = BytesIO(pdf_bytes)
            
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Check if PDF has pages
            if len(pdf_reader.pages) == 0:
                raise InputValidationError(
                    "PDF file contains no pages",
                    "PDF_NO_PAGES"
                )
            
            # Extract text from all pages
            extracted_text = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text.append(page_text)
                except Exception as e:
                    # Log the error but continue with other pages
                    # In production, this would use proper logging
                    print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
            
            # Join all page texts
            full_text = '\n\n'.join(extracted_text)
            
            # Check if any text was extracted
            if not full_text.strip():
                raise InputValidationError(
                    "No text could be extracted from PDF",
                    "PDF_NO_TEXT"
                )
            
            return full_text
            
        except PyPDF2.errors.PdfReadError as e:
            raise InputValidationError(
                f"Invalid PDF file: {str(e)}",
                "PDF_INVALID"
            )
        except Exception as e:
            # Catch any other unexpected errors
            if isinstance(e, InputValidationError):
                raise
            raise InputValidationError(
                f"Failed to extract text from PDF: {str(e)}",
                "PDF_EXTRACTION_FAILED"
            )
    
    def validate_input(self, text: str) -> bool:
        """
        Validate input meets requirements.
        
        Checks:
        - Text is not empty
        - Text length is within allowed range (10-50,000 characters)
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not text:
            return False
        
        text_length = len(text)
        
        if text_length < self.MIN_DOCUMENT_LENGTH:
            return False
        
        if text_length > self.MAX_DOCUMENT_LENGTH:
            return False
        
        return True
