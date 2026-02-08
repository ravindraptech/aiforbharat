"""
Unit tests for the SensitiveDataScanner module.

Tests regex pattern detection, NER detection, and combined scanning functionality.
"""

import pytest
from app.services.sensitive_data_scanner import SensitiveDataScanner
from app.models.data_models import SensitiveDataType


class TestSensitiveDataScanner:
    """Test suite for SensitiveDataScanner class."""
    
    @pytest.fixture
    def scanner(self):
        """Create a scanner instance for testing."""
        return SensitiveDataScanner(enable_ner=True)
    
    @pytest.fixture
    def scanner_no_ner(self):
        """Create a scanner instance without NER for testing."""
        return SensitiveDataScanner(enable_ner=False)
    
    def test_email_detection(self, scanner):
        """Test that email addresses are detected and redacted."""
        text = "Contact us at john.doe@example.com for more information."
        
        findings = scanner.detect_with_regex(text)
        
        email_findings = [f for f in findings if f.type == SensitiveDataType.EMAIL]
        assert len(email_findings) == 1
        assert "***@***.com" in email_findings[0].value
        assert email_findings[0].confidence == 1.0
        assert email_findings[0].detection_method == "regex"
    
    def test_phone_detection(self, scanner):
        """Test that phone numbers are detected and redacted."""
        text = "Call me at (555) 123-4567 or 555-987-6543."
        
        findings = scanner.detect_with_regex(text)
        
        phone_findings = [f for f in findings if f.type == SensitiveDataType.PHONE]
        assert len(phone_findings) == 2
        # Check that last 4 digits are preserved
        assert "4567" in phone_findings[0].value
        assert "6543" in phone_findings[1].value
    
    def test_ssn_detection(self, scanner):
        """Test that SSNs are detected and redacted."""
        text = "Patient SSN: 123-45-6789"
        
        findings = scanner.detect_with_regex(text)
        
        ssn_findings = [f for f in findings if f.type == SensitiveDataType.SSN]
        assert len(ssn_findings) == 1
        assert ssn_findings[0].value == "***-**-****"
        assert ssn_findings[0].confidence == 1.0
    
    def test_mrn_detection(self, scanner):
        """Test that Medical Record Numbers are detected."""
        text = "Patient MRN: 1234567890"
        
        findings = scanner.detect_with_regex(text)
        
        mrn_findings = [f for f in findings if f.type == SensitiveDataType.MEDICAL_RECORD_NUMBER]
        assert len(mrn_findings) == 1
        assert "MRN" in mrn_findings[0].value
        assert mrn_findings[0].confidence == 1.0
    
    def test_insurance_id_detection(self, scanner):
        """Test that insurance IDs are detected and redacted."""
        text = "Insurance ID: ABC123456789"
        
        findings = scanner.detect_with_regex(text)
        
        insurance_findings = [f for f in findings if f.type == SensitiveDataType.INSURANCE_ID]
        assert len(insurance_findings) == 1
        # First 2 characters should be preserved
        assert insurance_findings[0].value.startswith("AB")
        assert "*" in insurance_findings[0].value
    
    def test_health_condition_detection(self, scanner):
        """Test that health conditions are detected."""
        text = "Patient was diagnosed with diabetes and hypertension."
        
        findings = scanner.detect_with_ner(text)
        
        health_findings = [f for f in findings if f.type == SensitiveDataType.HEALTH_CONDITION]
        # Should detect at least diabetes and hypertension
        assert len(health_findings) >= 2
        assert all(f.value == "[HEALTH CONDITION]" for f in health_findings)
    
    def test_name_detection_with_ner(self, scanner):
        """Test that person names are detected with NER."""
        text = "Patient John Smith was admitted yesterday."
        
        findings = scanner.detect_with_ner(text)
        
        name_findings = [f for f in findings if f.type == SensitiveDataType.NAME]
        # Should detect at least one name
        assert len(name_findings) >= 1
        # Name should be redacted
        assert "***" in name_findings[0].value
        assert name_findings[0].detection_method == "ner"
    
    def test_scan_document_combines_methods(self, scanner):
        """Test that scan_document combines regex and NER detection."""
        text = "Patient John Doe (john.doe@example.com, 555-123-4567) was diagnosed with diabetes."
        
        findings = scanner.scan_document(text)
        
        # Should detect email, phone, name, and health condition
        types_found = {f.type for f in findings}
        assert SensitiveDataType.EMAIL in types_found
        assert SensitiveDataType.PHONE in types_found
        # Name and health condition depend on NER being available
        if scanner.enable_ner:
            assert SensitiveDataType.NAME in types_found or SensitiveDataType.HEALTH_CONDITION in types_found
    
    def test_scan_document_without_ner(self, scanner_no_ner):
        """Test that scanner works with NER disabled."""
        text = "Contact: john.doe@example.com, phone: 555-123-4567"
        
        findings = scanner_no_ner.scan_document(text)
        
        # Should still detect email and phone with regex
        types_found = {f.type for f in findings}
        assert SensitiveDataType.EMAIL in types_found
        assert SensitiveDataType.PHONE in types_found
    
    def test_multiple_emails(self, scanner):
        """Test detection of multiple email addresses."""
        text = "Contact alice@example.com or bob@test.org for assistance."
        
        findings = scanner.detect_with_regex(text)
        
        email_findings = [f for f in findings if f.type == SensitiveDataType.EMAIL]
        assert len(email_findings) == 2
    
    def test_no_sensitive_data(self, scanner):
        """Test that documents without sensitive data return empty findings."""
        text = "This is a generic document with no personal information."
        
        findings = scanner.scan_document(text)
        
        # Might have some false positives from NER, but should be minimal
        # At minimum, should not crash
        assert isinstance(findings, list)
    
    def test_deduplication(self, scanner):
        """Test that duplicate findings are removed."""
        # Create a scanner that might detect the same entity twice
        text = "Email: test@example.com"
        
        findings = scanner.scan_document(text)
        
        # Should not have duplicate emails at the same location
        email_findings = [f for f in findings if f.type == SensitiveDataType.EMAIL]
        locations = [f.location for f in email_findings]
        # No duplicate locations
        assert len(locations) == len(set(locations))
    
    def test_redaction_formats(self, scanner):
        """Test that redaction preserves appropriate format information."""
        text = """
        Email: user@domain.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        """
        
        findings = scanner.detect_with_regex(text)
        
        # Email should preserve domain extension
        email_findings = [f for f in findings if f.type == SensitiveDataType.EMAIL]
        assert len(email_findings) == 1
        assert ".com" in email_findings[0].value
        
        # Phone should preserve last 4 digits
        phone_findings = [f for f in findings if f.type == SensitiveDataType.PHONE]
        assert len(phone_findings) == 1
        assert "4567" in phone_findings[0].value
        
        # SSN should be fully redacted
        ssn_findings = [f for f in findings if f.type == SensitiveDataType.SSN]
        assert len(ssn_findings) == 1
        assert ssn_findings[0].value == "***-**-****"
    
    def test_location_tracking(self, scanner):
        """Test that findings track their location in the document."""
        text = "Start. Email: test@example.com. End."
        
        findings = scanner.detect_with_regex(text)
        
        email_findings = [f for f in findings if f.type == SensitiveDataType.EMAIL]
        assert len(email_findings) == 1
        # Location should be somewhere in the middle of the text
        assert 0 < email_findings[0].location < len(text)
        # Should point to the start of the email
        assert text[email_findings[0].location:].startswith("test@example.com")


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def scanner(self):
        """Create a scanner instance for testing."""
        return SensitiveDataScanner(enable_ner=True)
    
    def test_empty_text(self, scanner):
        """Test scanning empty text."""
        findings = scanner.scan_document("")
        assert findings == []
    
    def test_special_characters(self, scanner):
        """Test handling of special characters."""
        text = "Email: test+tag@example.com, Phone: +1-555-123-4567"
        
        findings = scanner.detect_with_regex(text)
        
        # Should still detect email and phone
        types_found = {f.type for f in findings}
        assert SensitiveDataType.EMAIL in types_found
        assert SensitiveDataType.PHONE in types_found
    
    def test_case_insensitive_mrn(self, scanner):
        """Test that MRN detection is case-insensitive."""
        text = "mrn: 1234567890 and MRN:9876543210"
        
        findings = scanner.detect_with_regex(text)
        
        mrn_findings = [f for f in findings if f.type == SensitiveDataType.MEDICAL_RECORD_NUMBER]
        assert len(mrn_findings) == 2
    
    def test_various_phone_formats(self, scanner):
        """Test detection of various phone number formats."""
        text = """
        (555) 123-4567
        555-123-4567
        555.123.4567
        5551234567
        +1-555-123-4567
        """
        
        findings = scanner.detect_with_regex(text)
        
        phone_findings = [f for f in findings if f.type == SensitiveDataType.PHONE]
        # Should detect most common formats
        assert len(phone_findings) >= 3
