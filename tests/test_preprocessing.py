"""
Unit tests for the PreprocessingModule.

Tests cover text normalization, PDF extraction, input validation,
and edge case handling.
"""

import pytest
import PyPDF2
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.services.preprocessing import PreprocessingModule, InputValidationError


class TestPreprocessingModule:
    """Test suite for PreprocessingModule."""
    
    @pytest.fixture
    def preprocessing_module(self):
        """Create a PreprocessingModule instance for testing."""
        return PreprocessingModule()
    
    # ===== Text Normalization Tests =====
    
    def test_preprocess_text_basic(self, preprocessing_module):
        """Test basic text preprocessing."""
        text = "This is a test document."
        result = preprocessing_module.preprocess_text(text)
        assert result == "This is a test document."
    
    def test_preprocess_text_strips_whitespace(self, preprocessing_module):
        """Test that leading and trailing whitespace is removed."""
        text = "   This is a test document.   "
        result = preprocessing_module.preprocess_text(text)
        assert result == "This is a test document."
    
    def test_preprocess_text_normalizes_multiple_spaces(self, preprocessing_module):
        """Test that multiple spaces are normalized to single spaces."""
        text = "This  is   a    test     document."
        result = preprocessing_module.preprocess_text(text)
        assert result == "This is a test document."
    
    def test_preprocess_text_preserves_line_breaks(self, preprocessing_module):
        """Test that paragraph breaks (line breaks) are preserved."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = preprocessing_module.preprocess_text(text)
        assert "First paragraph." in result
        assert "Second paragraph." in result
        assert "Third paragraph." in result
        # Should have line breaks between paragraphs
        assert "\n" in result
    
    def test_preprocess_text_normalizes_line_breaks(self, preprocessing_module):
        """Test that different line break formats are normalized."""
        text = "Line 1\r\nLine 2\rLine 3\nLine 4"
        result = preprocessing_module.preprocess_text(text)
        # All line breaks should be normalized to \n
        assert "\r" not in result
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert "Line 4" in result
    
    def test_preprocess_text_removes_excessive_blank_lines(self, preprocessing_module):
        """Test that excessive blank lines are reduced."""
        text = "Paragraph 1\n\n\n\n\nParagraph 2"
        result = preprocessing_module.preprocess_text(text)
        # Should reduce to maximum 2 consecutive newlines
        assert "\n\n\n" not in result
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
    
    def test_preprocess_text_with_mixed_whitespace(self, preprocessing_module):
        """Test preprocessing with mixed whitespace issues."""
        text = "  Line 1  with   spaces  \n\n  Line 2  \n\n\n  Line 3  "
        result = preprocessing_module.preprocess_text(text)
        assert "Line 1 with spaces" in result
        assert "Line 2" in result
        assert "Line 3" in result
        # Should not have leading/trailing spaces on lines
        assert "  Line" not in result
    
    # ===== Input Validation Tests =====
    
    def test_validate_input_valid_text(self, preprocessing_module):
        """Test validation with valid text."""
        text = "This is a valid document with enough characters."
        assert preprocessing_module.validate_input(text) is True
    
    def test_validate_input_empty_string(self, preprocessing_module):
        """Test validation rejects empty string."""
        assert preprocessing_module.validate_input("") is False
    
    def test_validate_input_too_short(self, preprocessing_module):
        """Test validation rejects text that's too short."""
        text = "Short"  # Less than 10 characters
        assert preprocessing_module.validate_input(text) is False
    
    def test_validate_input_minimum_length(self, preprocessing_module):
        """Test validation accepts text at minimum length."""
        text = "1234567890"  # Exactly 10 characters
        assert preprocessing_module.validate_input(text) is True
    
    def test_validate_input_too_long(self, preprocessing_module):
        """Test validation rejects text that's too long."""
        text = "a" * 50001  # Exceeds 50,000 character limit
        assert preprocessing_module.validate_input(text) is False
    
    def test_validate_input_maximum_length(self, preprocessing_module):
        """Test validation accepts text at maximum length."""
        text = "a" * 50000  # Exactly 50,000 characters
        assert preprocessing_module.validate_input(text) is True
    
    # ===== Error Handling Tests =====
    
    def test_preprocess_text_raises_on_none(self, preprocessing_module):
        """Test that None input raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            preprocessing_module.preprocess_text(None)
        assert exc_info.value.error_code == "DOCUMENT_NONE"
    
    def test_preprocess_text_raises_on_empty(self, preprocessing_module):
        """Test that empty text raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            preprocessing_module.preprocess_text("")
        assert exc_info.value.error_code == "DOCUMENT_TOO_SHORT"
        assert "at least 10 characters" in exc_info.value.message
    
    def test_preprocess_text_raises_on_too_short(self, preprocessing_module):
        """Test that text below minimum length raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            preprocessing_module.preprocess_text("Short")
        assert exc_info.value.error_code == "DOCUMENT_TOO_SHORT"
    
    def test_preprocess_text_raises_on_too_long(self, preprocessing_module):
        """Test that text exceeding maximum length raises InputValidationError."""
        text = "a" * 50001
        with pytest.raises(InputValidationError) as exc_info:
            preprocessing_module.preprocess_text(text)
        assert exc_info.value.error_code == "DOCUMENT_TOO_LARGE"
        assert "50000 character limit" in exc_info.value.message
    
    # ===== PDF Extraction Tests =====
    
    def test_extract_pdf_text_basic(self, preprocessing_module):
        """Test basic PDF text extraction."""
        # Create a simple PDF with text
        pdf_bytes = self._create_test_pdf("This is a test PDF document with some content.")
        
        result = preprocessing_module.extract_pdf_text(pdf_bytes)
        
        assert "test PDF document" in result
        assert len(result) > 0
    
    def test_extract_pdf_text_multiple_pages(self, preprocessing_module):
        """Test PDF extraction with multiple pages."""
        # Create a PDF with multiple pages
        pdf_bytes = self._create_test_pdf_multipage([
            "Page 1 content",
            "Page 2 content",
            "Page 3 content"
        ])
        
        result = preprocessing_module.extract_pdf_text(pdf_bytes)
        
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "Page 3 content" in result
    
    def test_extract_pdf_text_preserves_structure(self, preprocessing_module):
        """Test that PDF extraction preserves document structure."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        pdf_bytes = self._create_test_pdf(text)
        
        result = preprocessing_module.extract_pdf_text(pdf_bytes)
        
        # Should contain the text content
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "Third paragraph" in result
    
    def test_extract_pdf_text_empty_bytes(self, preprocessing_module):
        """Test that empty PDF bytes raises InputValidationError."""
        with pytest.raises(InputValidationError) as exc_info:
            preprocessing_module.extract_pdf_text(b"")
        assert exc_info.value.error_code == "PDF_EMPTY"
    
    def test_extract_pdf_text_invalid_pdf(self, preprocessing_module):
        """Test that invalid PDF data raises InputValidationError."""
        invalid_pdf = b"This is not a valid PDF file"
        
        with pytest.raises(InputValidationError) as exc_info:
            preprocessing_module.extract_pdf_text(invalid_pdf)
        assert exc_info.value.error_code == "PDF_INVALID"
    
    def test_extract_pdf_text_empty_pdf(self, preprocessing_module):
        """Test that PDF with no text raises InputValidationError."""
        # Create a PDF with no text content
        pdf_bytes = self._create_empty_pdf()
        
        with pytest.raises(InputValidationError) as exc_info:
            preprocessing_module.extract_pdf_text(pdf_bytes)
        # Should raise error about no text extracted
        assert exc_info.value.error_code in ["PDF_NO_TEXT", "PDF_NO_PAGES"]
    
    # ===== Integration Tests =====
    
    def test_full_workflow_text_input(self, preprocessing_module):
        """Test complete workflow with text input."""
        text = "  Patient  John   Doe  was  diagnosed  with  diabetes.  \n\n  Treatment  plan  follows.  "
        
        # Preprocess
        result = preprocessing_module.preprocess_text(text)
        
        # Should be normalized
        assert "Patient John Doe was diagnosed with diabetes." in result
        assert "Treatment plan follows." in result
        # Should not have excessive spaces
        assert "  " not in result
    
    def test_full_workflow_pdf_input(self, preprocessing_module):
        """Test complete workflow with PDF input."""
        # Create PDF
        text = "Medical Record\n\nPatient: John Doe\nDiagnosis: Type 2 Diabetes"
        pdf_bytes = self._create_test_pdf(text)
        
        # Extract
        extracted = preprocessing_module.extract_pdf_text(pdf_bytes)
        
        # Preprocess
        result = preprocessing_module.preprocess_text(extracted)
        
        # Should contain the content
        assert "Medical Record" in result
        assert "John Doe" in result
        assert "Diabetes" in result
    
    # ===== Helper Methods =====
    
    def _create_test_pdf(self, text: str) -> bytes:
        """
        Create a simple PDF with the given text for testing.
        
        Args:
            text: Text content to include in the PDF
            
        Returns:
            PDF file as bytes
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Split text into lines and write to PDF
        y_position = 750
        for line in text.split('\n'):
            if line.strip():
                c.drawString(100, y_position, line)
                y_position -= 20
        
        c.save()
        buffer.seek(0)
        return buffer.read()
    
    def _create_test_pdf_multipage(self, pages: list) -> bytes:
        """
        Create a PDF with multiple pages.
        
        Args:
            pages: List of text content for each page
            
        Returns:
            PDF file as bytes
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        for page_text in pages:
            c.drawString(100, 750, page_text)
            c.showPage()
        
        c.save()
        buffer.seek(0)
        return buffer.read()
    
    def _create_empty_pdf(self) -> bytes:
        """
        Create an empty PDF with no text content.
        
        Returns:
            PDF file as bytes
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        # Create a page but don't add any text
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()
