"""
Sensitive data scanner for detecting PII and PHI in healthcare documents.

This module implements dual detection using regex patterns for structured data
and spaCy NER for contextual data detection.
"""

import re
from typing import List, Set
import spacy
from app.models.data_models import SensitiveDataFinding, SensitiveDataType


class SensitiveDataScanner:
    """
    Detects personally identifiable information (PII) and protected health
    information (PHI) in documents using regex patterns and NER.
    """
    
    # Regex patterns for structured data detection
    PATTERNS = {
        SensitiveDataType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        SensitiveDataType.PHONE: r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        SensitiveDataType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        SensitiveDataType.MEDICAL_RECORD_NUMBER: r'\b[Mm][Rr][Nn][:\s]*\d{6,10}\b',
        SensitiveDataType.INSURANCE_ID: r'\b[A-Z]{2,3}\d{8,12}\b',
        # ZIP code pattern - 5 digits or 5+4 format
        'ZIP_CODE': r'\b\d{5}(-\d{4})?\b',
    }
    
    def __init__(self, enable_ner: bool = True):
        """
        Initialize the sensitive data scanner.
        
        Args:
            enable_ner: Whether to enable spaCy NER detection (default: True)
        """
        self.enable_ner = enable_ner
        
        # Load spaCy model if NER is enabled
        if self.enable_ner:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Model not found, disable NER
                print("Warning: spaCy model 'en_core_web_sm' not found. NER detection disabled.")
                print("Install with: python -m spacy download en_core_web_sm")
                self.enable_ner = False
                self.nlp = None
        else:
            self.nlp = None
    
    def scan_document(self, text: str) -> List[SensitiveDataFinding]:
        """
        Scan document for sensitive data using both regex and NER.
        
        This method combines regex pattern matching for structured data
        (emails, phones, SSNs, etc.) with spaCy NER for contextual data
        (names, locations, health conditions).
        
        Args:
            text: Preprocessed document text
            
        Returns:
            List of detected sensitive data findings with type and location
        """
        findings = []
        
        # Detect with regex patterns
        regex_findings = self.detect_with_regex(text)
        findings.extend(regex_findings)
        
        # Detect with NER if enabled
        if self.enable_ner:
            ner_findings = self.detect_with_ner(text)
            findings.extend(ner_findings)
        
        # Remove duplicates based on location and type
        findings = self._deduplicate_findings(findings)
        
        return findings
    
    def detect_with_regex(self, text: str) -> List[SensitiveDataFinding]:
        """
        Use regex patterns to detect structured PII.
        
        Detects:
        - Email addresses
        - Phone numbers
        - Social Security Numbers (SSN)
        - Medical Record Numbers (MRN)
        - Insurance IDs
        - ZIP codes (as part of addresses)
        
        Args:
            text: Document text
            
        Returns:
            List of findings from regex matching
        """
        findings = []
        
        # Email detection
        for match in re.finditer(self.PATTERNS[SensitiveDataType.EMAIL], text):
            redacted = self._redact_email(match.group())
            findings.append(SensitiveDataFinding(
                type=SensitiveDataType.EMAIL,
                value=redacted,
                location=match.start(),
                confidence=1.0,
                detection_method="regex"
            ))
        
        # Phone detection
        for match in re.finditer(self.PATTERNS[SensitiveDataType.PHONE], text):
            redacted = self._redact_phone(match.group())
            findings.append(SensitiveDataFinding(
                type=SensitiveDataType.PHONE,
                value=redacted,
                location=match.start(),
                confidence=1.0,
                detection_method="regex"
            ))
        
        # SSN detection
        for match in re.finditer(self.PATTERNS[SensitiveDataType.SSN], text):
            redacted = "***-**-****"
            findings.append(SensitiveDataFinding(
                type=SensitiveDataType.SSN,
                value=redacted,
                location=match.start(),
                confidence=1.0,
                detection_method="regex"
            ))
        
        # Medical Record Number detection
        for match in re.finditer(self.PATTERNS[SensitiveDataType.MEDICAL_RECORD_NUMBER], text):
            redacted = "MRN: ******"
            findings.append(SensitiveDataFinding(
                type=SensitiveDataType.MEDICAL_RECORD_NUMBER,
                value=redacted,
                location=match.start(),
                confidence=1.0,
                detection_method="regex"
            ))
        
        # Insurance ID detection
        for match in re.finditer(self.PATTERNS[SensitiveDataType.INSURANCE_ID], text):
            redacted = self._redact_insurance_id(match.group())
            findings.append(SensitiveDataFinding(
                type=SensitiveDataType.INSURANCE_ID,
                value=redacted,
                location=match.start(),
                confidence=1.0,
                detection_method="regex"
            ))
        
        # ZIP code detection (part of address detection)
        for match in re.finditer(self.PATTERNS['ZIP_CODE'], text):
            # Only flag as address if it looks like a ZIP code in context
            # We'll use a simple heuristic: if preceded by state abbreviation or "ZIP"
            start = match.start()
            context_start = max(0, start - 20)
            context = text[context_start:start].lower()
            
            # Check if this looks like a ZIP code in an address context
            if any(indicator in context for indicator in ['zip', 'state', ',']):
                redacted = "*****"
                findings.append(SensitiveDataFinding(
                    type=SensitiveDataType.ADDRESS,
                    value=f"ZIP: {redacted}",
                    location=match.start(),
                    confidence=0.8,
                    detection_method="regex"
                ))
        
        return findings
    
    def detect_with_ner(self, text: str) -> List[SensitiveDataFinding]:
        """
        Use spaCy NER to detect contextual PII.
        
        Detects:
        - PERSON entities (names)
        - GPE entities (locations/addresses)
        - DATE entities (birthdates, ages)
        - ORG entities (healthcare organizations)
        - Health conditions (custom patterns)
        
        Args:
            text: Document text
            
        Returns:
            List of findings from NER analysis
        """
        if not self.enable_ner or self.nlp is None:
            return []
        
        findings = []
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Redact person names
                redacted = self._redact_name(ent.text)
                findings.append(SensitiveDataFinding(
                    type=SensitiveDataType.NAME,
                    value=redacted,
                    location=ent.start_char,
                    confidence=0.9,
                    detection_method="ner"
                ))
            
            elif ent.label_ == "GPE":
                # Geographic/political entities (cities, states, countries)
                # These are part of addresses
                redacted = "***"
                findings.append(SensitiveDataFinding(
                    type=SensitiveDataType.ADDRESS,
                    value=f"Location: {redacted}",
                    location=ent.start_char,
                    confidence=0.7,
                    detection_method="ner"
                ))
            
            elif ent.label_ == "DATE":
                # Dates could be birthdates or ages
                # Check if it looks like an age
                if self._is_age_mention(ent.text, text[max(0, ent.start_char-10):ent.end_char+10]):
                    findings.append(SensitiveDataFinding(
                        type=SensitiveDataType.AGE,
                        value="** years old",
                        location=ent.start_char,
                        confidence=0.8,
                        detection_method="ner"
                    ))
                else:
                    # Might be a date of birth
                    findings.append(SensitiveDataFinding(
                        type=SensitiveDataType.DATE_OF_BIRTH,
                        value="**/**/****",
                        location=ent.start_char,
                        confidence=0.6,
                        detection_method="ner"
                    ))
        
        # Detect health conditions using custom patterns
        health_findings = self._detect_health_conditions(text)
        findings.extend(health_findings)
        
        return findings
    
    def _detect_health_conditions(self, text: str) -> List[SensitiveDataFinding]:
        """
        Detect health conditions and diagnoses using pattern matching.
        
        Args:
            text: Document text
            
        Returns:
            List of health condition findings
        """
        findings = []
        
        # Common health condition keywords and patterns
        condition_patterns = [
            r'\b(diabetes|diabetic)\b',
            r'\b(cancer|carcinoma|tumor|malignancy)\b',
            r'\b(hypertension|high blood pressure)\b',
            r'\b(heart disease|cardiac|cardiovascular)\b',
            r'\b(asthma|copd|respiratory)\b',
            r'\b(depression|anxiety|mental health)\b',
            r'\b(hiv|aids)\b',
            r'\b(hepatitis)\b',
            r'\b(stroke|cerebrovascular)\b',
            r'\b(arthritis|rheumatoid)\b',
            r'\bdiagnosed with\s+(\w+)\b',
            r'\bsuffering from\s+(\w+)\b',
            r'\bcondition:\s*(\w+)\b',
            r'\bdiagnosis:\s*(\w+)\b',
        ]
        
        for pattern in condition_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Extract the condition name
                condition_text = match.group()
                redacted = "[HEALTH CONDITION]"
                
                findings.append(SensitiveDataFinding(
                    type=SensitiveDataType.HEALTH_CONDITION,
                    value=redacted,
                    location=match.start(),
                    confidence=0.85,
                    detection_method="ner"
                ))
        
        return findings
    
    def _redact_email(self, email: str) -> str:
        """
        Redact email address while preserving format.
        
        Args:
            email: Email address to redact
            
        Returns:
            Redacted email (e.g., "***@***.com")
        """
        parts = email.split('@')
        if len(parts) == 2:
            domain_parts = parts[1].split('.')
            if len(domain_parts) >= 2:
                return f"***@***.{domain_parts[-1]}"
        return "***@***.***"
    
    def _redact_phone(self, phone: str) -> str:
        """
        Redact phone number while preserving format.
        
        Args:
            phone: Phone number to redact
            
        Returns:
            Redacted phone (e.g., "***-***-1234")
        """
        # Extract just the digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 4:
            # Show last 4 digits
            return f"***-***-{digits[-4:]}"
        return "***-***-****"
    
    def _redact_name(self, name: str) -> str:
        """
        Redact person name while preserving structure.
        
        Args:
            name: Person name to redact
            
        Returns:
            Redacted name (e.g., "John D***")
        """
        parts = name.split()
        if len(parts) == 1:
            # Single name
            if len(parts[0]) > 1:
                return parts[0][0] + "***"
            return "***"
        elif len(parts) >= 2:
            # First and last name
            first = parts[0][0] + "***" if len(parts[0]) > 1 else "***"
            last = parts[-1][0] + "***" if len(parts[-1]) > 1 else "***"
            return f"{first} {last}"
        return "***"
    
    def _redact_insurance_id(self, insurance_id: str) -> str:
        """
        Redact insurance ID while preserving format.
        
        Args:
            insurance_id: Insurance ID to redact
            
        Returns:
            Redacted insurance ID (e.g., "AB********")
        """
        # Show first 2 characters (usually letters)
        if len(insurance_id) >= 2:
            return insurance_id[:2] + "*" * (len(insurance_id) - 2)
        return "***"
    
    def _is_age_mention(self, date_text: str, context: str) -> bool:
        """
        Determine if a date entity is actually an age mention.
        
        Args:
            date_text: The date text extracted by NER
            context: Surrounding text context
            
        Returns:
            True if this appears to be an age mention
        """
        # Check for age indicators in context
        age_indicators = ['years old', 'year old', 'age', 'aged', 'y/o', 'yo']
        context_lower = context.lower()
        
        # Check if date text is just a number (likely age)
        if date_text.strip().isdigit():
            return True
        
        # Check for age indicators in context
        for indicator in age_indicators:
            if indicator in context_lower:
                return True
        
        return False
    
    def _deduplicate_findings(self, findings: List[SensitiveDataFinding]) -> List[SensitiveDataFinding]:
        """
        Remove duplicate findings based on location and type.
        
        When both regex and NER detect the same entity, keep the one with
        higher confidence.
        
        Args:
            findings: List of all findings
            
        Returns:
            Deduplicated list of findings
        """
        if not findings:
            return []
        
        # Group findings by location range (within 5 characters)
        unique_findings = []
        seen_locations: Set[tuple] = set()
        
        # Sort by confidence (descending) to keep higher confidence findings
        sorted_findings = sorted(findings, key=lambda f: f.confidence, reverse=True)
        
        for finding in sorted_findings:
            # Create a location key (type, approximate location)
            location_key = (finding.type, finding.location // 5)
            
            if location_key not in seen_locations:
                unique_findings.append(finding)
                seen_locations.add(location_key)
        
        # Sort by location for consistent output
        unique_findings.sort(key=lambda f: f.location)
        
        return unique_findings
