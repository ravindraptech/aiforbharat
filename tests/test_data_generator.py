"""
Synthetic test data generator for Healthcare Compliance Copilot.

This module generates realistic synthetic healthcare documents for testing
and evaluation purposes.
"""

from faker import Faker
from typing import Optional
import random


class TestDataGenerator:
    """
    Generates synthetic healthcare documents with configurable parameters.
    
    Uses the Faker library to create realistic PII while ensuring
    no real patient data is used.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the test data generator.
        
        Args:
            seed: Random seed for reproducible test data
        """
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
    
    def generate_test_document(
        self,
        include_pii: bool = True,
        include_consent: bool = False,
        include_health_condition: bool = False,
        include_privacy_notice: bool = False,
        include_confidentiality: bool = False,
        include_unsafe_sharing: bool = False
    ) -> str:
        """
        Generate a synthetic healthcare document.
        
        Args:
            include_pii: Include personal identifiable information
            include_consent: Include patient consent statement
            include_health_condition: Include health condition/diagnosis
            include_privacy_notice: Include privacy notice
            include_confidentiality: Include confidentiality statement
            include_unsafe_sharing: Include unsafe data sharing language
            
        Returns:
            Synthetic document text
        """
        doc_parts = []
        
        # Document header
        doc_parts.append("MEDICAL RECORD\n")
        doc_parts.append("=" * 50 + "\n\n")
        
        # Patient information section
        if include_pii:
            doc_parts.append("PATIENT INFORMATION\n")
            doc_parts.append(f"Name: {self.fake.name()}\n")
            doc_parts.append(f"Date of Birth: {self.fake.date_of_birth(minimum_age=18, maximum_age=90)}\n")
            doc_parts.append(f"Email: {self.fake.email()}\n")
            doc_parts.append(f"Phone: {self.fake.phone_number()}\n")
            doc_parts.append(f"Address: {self.fake.address().replace(chr(10), ', ')}\n")
            doc_parts.append(f"Medical Record Number: MRN{random.randint(100000, 999999)}\n")
            doc_parts.append(f"Insurance ID: INS{random.randint(10000000, 99999999)}\n")
            doc_parts.append("\n")
        
        # Clinical information
        if include_health_condition:
            doc_parts.append("CLINICAL INFORMATION\n")
            conditions = [
                "Type 2 Diabetes Mellitus",
                "Hypertension",
                "Coronary Artery Disease",
                "Chronic Kidney Disease",
                "Asthma",
                "Depression",
                "Rheumatoid Arthritis"
            ]
            condition = random.choice(conditions)
            doc_parts.append(f"Primary Diagnosis: {condition}\n")
            doc_parts.append(f"Date of Diagnosis: {self.fake.date_between(start_date='-5y', end_date='today')}\n")
            doc_parts.append(f"Treating Physician: Dr. {self.fake.last_name()}\n")
            doc_parts.append("\n")
        
        # Consent statement
        if include_consent:
            doc_parts.append("PATIENT CONSENT\n")
            doc_parts.append(
                "I hereby give my informed consent for the collection, use, and disclosure "
                "of my personal health information for the purposes of treatment, payment, "
                "and healthcare operations. I understand my rights regarding my health "
                "information and how it may be used.\n\n"
                f"Patient Signature: {self.fake.name()}\n"
                f"Date: {self.fake.date_between(start_date='-30d', end_date='today')}\n\n"
            )
        
        # Privacy notice
        if include_privacy_notice:
            doc_parts.append("NOTICE OF PRIVACY PRACTICES\n")
            doc_parts.append(
                "This notice describes how medical information about you may be used and "
                "disclosed and how you can get access to this information. Please review "
                "it carefully. We are required by law to maintain the privacy of your "
                "protected health information and to provide you with this notice of our "
                "legal duties and privacy practices.\n\n"
            )
        
        # Confidentiality statement
        if include_confidentiality:
            doc_parts.append("CONFIDENTIALITY STATEMENT\n")
            doc_parts.append(
                "This document contains confidential patient information protected by "
                "federal and state privacy laws. Unauthorized disclosure or use of this "
                "information is strictly prohibited and may result in civil and criminal "
                "penalties.\n\n"
            )
        
        # Unsafe sharing language (for testing risk detection)
        if include_unsafe_sharing:
            doc_parts.append("DATA SHARING POLICY\n")
            doc_parts.append(
                "We may share your personal health information with third-party marketing "
                "partners, data brokers, and other organizations for commercial purposes. "
                "Your information may be sold or transferred to affiliated companies without "
                "additional notice or consent.\n\n"
            )
        
        # Document footer
        doc_parts.append("=" * 50 + "\n")
        doc_parts.append(f"Document Generated: {self.fake.date_time_this_year()}\n")
        doc_parts.append(f"Facility: {self.fake.company()} Medical Center\n")
        
        return "".join(doc_parts)
    
    def generate_high_risk_document(self) -> str:
        """
        Generate a high-risk document with PII, health conditions, but no safeguards.
        
        Returns:
            High-risk synthetic document
        """
        return self.generate_test_document(
            include_pii=True,
            include_consent=False,
            include_health_condition=True,
            include_privacy_notice=False,
            include_confidentiality=False,
            include_unsafe_sharing=True
        )
    
    def generate_medium_risk_document(self) -> str:
        """
        Generate a medium-risk document with PII but some safeguards.
        
        Returns:
            Medium-risk synthetic document
        """
        return self.generate_test_document(
            include_pii=True,
            include_consent=False,
            include_health_condition=False,
            include_privacy_notice=True,
            include_confidentiality=False,
            include_unsafe_sharing=False
        )
    
    def generate_low_risk_document(self) -> str:
        """
        Generate a low-risk document with anonymized data and safeguards.
        
        Returns:
            Low-risk synthetic document
        """
        return self.generate_test_document(
            include_pii=False,
            include_consent=True,
            include_health_condition=False,
            include_privacy_notice=True,
            include_confidentiality=True,
            include_unsafe_sharing=False
        )
    
    def generate_clean_document(self) -> str:
        """
        Generate a clean document with no PII or health conditions.
        
        Returns:
            Clean synthetic document
        """
        doc = """HEALTHCARE POLICY DOCUMENT
========================================

GENERAL INFORMATION

This document outlines our healthcare facility's general policies and procedures
for patient care and administrative operations.

QUALITY ASSURANCE

Our facility is committed to providing high-quality healthcare services. We
regularly review our processes and outcomes to ensure we meet industry standards
and regulatory requirements.

STAFF TRAINING

All healthcare staff members receive ongoing training in:
- Patient safety protocols
- Infection control procedures
- Emergency response procedures
- Professional ethics and conduct

FACILITY OPERATIONS

Operating Hours: Monday-Friday, 8:00 AM - 5:00 PM
Emergency Services: Available 24/7
Appointment Scheduling: Call our main office

========================================
Document Type: Policy Manual
Version: 2.0
Last Updated: 2024
"""
        return doc


# Example usage and tests
if __name__ == "__main__":
    generator = TestDataGenerator(seed=42)
    
    print("=== HIGH RISK DOCUMENT ===")
    print(generator.generate_high_risk_document())
    print("\n\n")
    
    print("=== MEDIUM RISK DOCUMENT ===")
    print(generator.generate_medium_risk_document())
    print("\n\n")
    
    print("=== LOW RISK DOCUMENT ===")
    print(generator.generate_low_risk_document())
