# Design Document: AI Healthcare Compliance Copilot

## Overview

The AI Healthcare Compliance Copilot is a stateless web application that analyzes healthcare documents for privacy and compliance risks. The system follows a pipeline architecture where documents flow through preprocessing, sensitive data detection, LLM-based compliance analysis, scoring, and structured output generation. The frontend is built with Streamlit for rapid UI development, while the backend uses FastAPI for high-performance API handling. Amazon Bedrock with Nova models provides the AI analysis capabilities with built-in guardrails for responsible AI.

### Key Design Principles

1. **Stateless Processing**: No document storage - all processing happens in memory and results are discarded after delivery
2. **Modular Architecture**: Independent components that can be updated or replaced without affecting others
3. **Responsible AI**: Built-in guardrails prevent medical advice, diagnosis, or treatment recommendations
4. **Performance First**: Target <5 second response time through efficient processing and parallel operations where possible
5. **Extensibility**: Easy to add new sensitive data patterns or compliance checks

### Technology Stack

- **Backend Framework**: FastAPI (Python 3.9+) - High-performance async API framework
- **Frontend**: Streamlit - Rapid UI development for data applications
- **AI/ML**: Amazon Bedrock with Nova Lite model - Cost-effective, fast inference for text analysis
- **Document Processing**: PyPDF2 for PDF extraction, standard Python text processing
- **Sensitive Data Detection**: Regex patterns with spaCy NER (Named Entity Recognition) for enhanced accuracy
- **Deployment**: Containerized with Docker for consistent environments

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ Input Form   │  │ Results      │  │ Disclaimer &       │   │
│  │ - Text paste │  │ Dashboard    │  │ Warnings           │   │
│  │ - File upload│  │ - Score      │  │                    │   │
│  └──────────────┘  │ - Risk level │  └────────────────────┘   │
│                     │ - Findings   │                            │
│                     └──────────────┘                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP POST /analyze
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  Analysis Pipeline                      │    │
│  │                                                          │    │
│  │  1. Preprocessing      2. Sensitive Data    3. LLM      │    │
│  │     Module                Scanner             Analyzer  │    │
│  │     ↓                     ↓                   ↓         │    │
│  │  - Normalize text     - Regex patterns    - Bedrock    │    │
│  │  - Extract from PDF   - spaCy NER         - Nova Lite  │    │
│  │  - Validate input     - Pattern matching  - Guardrails │    │
│  │                                                          │    │
│  │  4. Score Generator    5. Output Formatter              │    │
│  │     ↓                     ↓                              │    │
│  │  - Calculate score    - JSON structure                  │    │
│  │  - Assign risk level  - Add disclaimer                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │   Amazon Bedrock          │
                    │   - Nova Lite Model       │
                    │   - Guardrails API        │
                    └───────────────────────────┘
```

### Component Interaction Flow

1. **User Input** → Streamlit captures text or file upload
2. **API Request** → Streamlit sends POST request to FastAPI `/analyze` endpoint
3. **Preprocessing** → FastAPI normalizes text and validates input
4. **Parallel Processing**:
   - Sensitive Data Scanner runs regex + NER detection
   - LLM Analyzer sends prompt to Bedrock Nova Lite
5. **Score Calculation** → Score Generator combines findings into compliance score
6. **Response** → FastAPI returns JSON with all findings
7. **Display** → Streamlit renders results in dashboard

## Components and Interfaces

### 1. Preprocessing Module

**Responsibility**: Normalize and validate document input before analysis

**Interface**:
```python
class PreprocessingModule:
    def preprocess_text(self, text: str) -> str:
        """
        Normalize text input for consistent analysis
        
        Args:
            text: Raw text input from user
            
        Returns:
            Normalized text with consistent whitespace and formatting
            
        Raises:
            ValueError: If text is empty or exceeds size limits
        """
        
    def extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """
        Extract text content from PDF file
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If PDF is invalid or cannot be parsed
        """
        
    def validate_input(self, text: str) -> bool:
        """
        Validate input meets requirements
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid, False otherwise
        """
```

**Implementation Details**:
- Use PyPDF2 for PDF text extraction
- Normalize whitespace: convert multiple spaces to single space, preserve paragraph breaks
- Character limit: 50,000 characters maximum
- Minimum length: 10 characters
- Strip leading/trailing whitespace

### 2. Sensitive Data Scanner

**Responsibility**: Detect personally identifiable information and protected health information

**Interface**:
```python
class SensitiveDataScanner:
    def scan_document(self, text: str) -> List[SensitiveDataFinding]:
        """
        Scan document for sensitive data
        
        Args:
            text: Preprocessed document text
            
        Returns:
            List of detected sensitive data findings with type and location
        """
        
    def detect_with_regex(self, text: str) -> List[SensitiveDataFinding]:
        """
        Use regex patterns to detect structured PII
        
        Args:
            text: Document text
            
        Returns:
            List of findings from regex matching
        """
        
    def detect_with_ner(self, text: str) -> List[SensitiveDataFinding]:
        """
        Use spaCy NER to detect contextual PII
        
        Args:
            text: Document text
            
        Returns:
            List of findings from NER analysis
        """
```

**Detection Patterns**:

Based on research findings ([datasunrise.com](https://www.datasunrise.com/knowledge-center/ai-security/sensitive-data-discovery-in-ai-systems/)), the system uses dual detection:

1. **Regex Patterns** (for structured data):
   - Email: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
   - Phone: `\b(\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b`
   - SSN: `\b\d{3}-\d{2}-\d{4}\b`
   - Medical Record Number: `\bMRN[:\s]?\d{6,10}\b`
   - Insurance ID: `\b[A-Z]{2,3}\d{8,12}\b`
   - ZIP Code: `\b\d{5}(-\d{4})?\b`

2. **spaCy NER** (for contextual data):
   - PERSON entities (names)
   - GPE entities (locations/addresses)
   - DATE entities (birthdates, ages)
   - ORG entities (healthcare organizations)
   - Custom medical condition patterns

**Data Structure**:
```python
@dataclass
class SensitiveDataFinding:
    type: str  # "email", "phone", "name", "health_condition", etc.
    value: str  # Redacted value (e.g., "***@***.com")
    location: int  # Character position in document
    confidence: float  # 0.0-1.0 confidence score
```

### 3. LLM Analyzer

**Responsibility**: Analyze document for compliance risks using Amazon Bedrock Nova Lite

**Interface**:
```python
class LLMAnalyzer:
    def analyze_compliance(
        self, 
        text: str, 
        sensitive_findings: List[SensitiveDataFinding]
    ) -> ComplianceAnalysis:
        """
        Analyze document for compliance risks
        
        Args:
            text: Preprocessed document text
            sensitive_findings: List of detected sensitive data
            
        Returns:
            Compliance analysis with identified risks and suggestions
        """
        
    def build_prompt(
        self, 
        text: str, 
        sensitive_findings: List[SensitiveDataFinding]
    ) -> str:
        """
        Construct analysis prompt for Bedrock
        
        Args:
            text: Document text
            sensitive_findings: Detected sensitive data
            
        Returns:
            Formatted prompt string
        """
```

**Bedrock Integration**:

Based on AWS documentation ([aws.amazon.com/bedrock](https://aws.amazon.com/blogs/publicsector/how-to-safeguard-healthcare-data-privacy-using-amazon-bedrock-guardrails/)), the system uses:

- **Model**: Nova Lite (cost-effective, fast inference for text analysis)
- **Guardrails**: Configured to block medical advice, diagnosis, and treatment recommendations
- **API**: Bedrock Runtime `invoke_model` with JSON response format

**Prompt Structure**:
```
You are a healthcare compliance analyzer. Review the following document and identify:

1. Missing consent statements
2. Unsafe data sharing language
3. Missing privacy notices
4. Missing confidentiality statements

Document contains the following sensitive data types: {sensitive_data_types}

Document text:
{document_text}

Provide your analysis in JSON format:
{
  "risks": [
    {"type": "missing_consent", "description": "...", "severity": "high|medium|low"}
  ],
  "suggestions": ["..."]
}

IMPORTANT: Do not provide medical advice, diagnosis, or treatment recommendations.
```

**Data Structure**:
```python
@dataclass
class ComplianceRisk:
    type: str  # "missing_consent", "unsafe_sharing", etc.
    description: str
    severity: str  # "high", "medium", "low"

@dataclass
class ComplianceAnalysis:
    risks: List[ComplianceRisk]
    suggestions: List[str]
```

### 4. Score Generator

**Responsibility**: Calculate compliance score and risk level based on findings

**Interface**:
```python
class ScoreGenerator:
    def calculate_score(
        self,
        sensitive_findings: List[SensitiveDataFinding],
        compliance_analysis: ComplianceAnalysis
    ) -> ScoringResult:
        """
        Calculate compliance score and risk level
        
        Args:
            sensitive_findings: Detected sensitive data
            compliance_analysis: LLM compliance analysis
            
        Returns:
            Score (0-100) and risk level (Low/Medium/High)
        """
```

**Scoring Algorithm**:

```
Base Score: 100

Deductions:
- Each high-severity compliance risk: -15 points
- Each medium-severity compliance risk: -10 points
- Each low-severity compliance risk: -5 points
- Each sensitive data type without safeguards: -8 points
- Presence of health conditions + identifiers: -20 points

Risk Level Assignment:
- 80-100: Low Risk
- 50-79: Medium Risk
- 0-49: High Risk

Minimum Score: 0
```

**Data Structure**:
```python
@dataclass
class ScoringResult:
    score: int  # 0-100
    risk_level: str  # "Low", "Medium", "High"
    deductions: List[ScoreDeduction]

@dataclass
class ScoreDeduction:
    reason: str
    points: int
```

### 5. Output Formatter

**Responsibility**: Format analysis results into structured JSON with disclaimer

**Interface**:
```python
class OutputFormatter:
    def format_output(
        self,
        sensitive_findings: List[SensitiveDataFinding],
        compliance_analysis: ComplianceAnalysis,
        scoring_result: ScoringResult
    ) -> AnalysisOutput:
        """
        Format all analysis results into structured output
        
        Args:
            sensitive_findings: Detected sensitive data
            compliance_analysis: Compliance risks and suggestions
            scoring_result: Score and risk level
            
        Returns:
            Complete analysis output with disclaimer
        """
```

**Output Structure**:
```python
@dataclass
class AnalysisOutput:
    compliance_score: int
    risk_level: str
    sensitive_data: List[Dict[str, Any]]
    compliance_risks: List[Dict[str, Any]]
    suggestions: List[str]
    disclaimer: str
    timestamp: str
```

**Disclaimer Text**:
```
DISCLAIMER: This tool is for educational and internal compliance awareness purposes only. 
It does not constitute legal advice, medical advice, or professional compliance consultation. 
Results are based on automated analysis and may not capture all risks. 
Always consult qualified legal and compliance professionals for official guidance. 
Use only synthetic or public data - never upload real protected health information (PHI).
```

### 6. FastAPI Backend

**Responsibility**: Orchestrate analysis pipeline and provide REST API

**API Endpoints**:

```python
@app.post("/analyze")
async def analyze_document(request: AnalysisRequest) -> AnalysisOutput:
    """
    Analyze document for compliance and privacy risks
    
    Request Body:
        {
            "text": "document text" (optional if file provided),
            "file_content": "base64 encoded file" (optional),
            "file_type": "txt" or "pdf" (required if file provided)
        }
    
    Response:
        AnalysisOutput JSON structure
        
    Status Codes:
        200: Success
        400: Invalid input (empty, too large, invalid format)
        500: Internal processing error
    """

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint
    
    Returns:
        {"status": "healthy"}
    """
```

**Pipeline Orchestration**:
```python
async def run_analysis_pipeline(text: str) -> AnalysisOutput:
    # 1. Preprocess
    preprocessed = preprocessing_module.preprocess_text(text)
    
    # 2. Parallel detection (async)
    sensitive_task = asyncio.create_task(
        sensitive_scanner.scan_document(preprocessed)
    )
    
    # 3. Wait for sensitive data, then run LLM
    sensitive_findings = await sensitive_task
    compliance_analysis = await llm_analyzer.analyze_compliance(
        preprocessed, sensitive_findings
    )
    
    # 4. Calculate score
    scoring_result = score_generator.calculate_score(
        sensitive_findings, compliance_analysis
    )
    
    # 5. Format output
    output = output_formatter.format_output(
        sensitive_findings, compliance_analysis, scoring_result
    )
    
    return output
```

### 7. Streamlit Frontend

**Responsibility**: Provide user interface for document submission and results display

**UI Components**:

1. **Header Section**:
   - Application title and description
   - Prominent warning: "Use only synthetic or public data"
   - Disclaimer notice

2. **Input Section**:
   - Text area for pasting document text
   - File uploader for .txt and .pdf files
   - "Analyze Document" button
   - Character count display

3. **Results Section** (displayed after analysis):
   - **Score Card**: Large display of compliance score with color coding
     - Green (80-100): Low Risk
     - Yellow (50-79): Medium Risk
     - Red (0-49): High Risk
   - **Sensitive Data Table**: List of detected PII/PHI with types
   - **Compliance Risks**: Expandable list of identified risks with severity
   - **Suggestions**: Actionable recommendations for improvement
   - **Disclaimer**: Repeated at bottom of results

**Implementation Pattern**:

Based on research ([restack.io](https://www.restack.io/docs/streamlit-knowledge-streamlit-fastapi-postgresql-integration)), Streamlit calls FastAPI backend via HTTP:

```python
import streamlit as st
import requests

# Input
text_input = st.text_area("Paste document text", height=300)
uploaded_file = st.file_uploader("Or upload file", type=["txt", "pdf"])

if st.button("Analyze Document"):
    # Prepare request
    if uploaded_file:
        file_content = base64.b64encode(uploaded_file.read()).decode()
        payload = {
            "file_content": file_content,
            "file_type": uploaded_file.name.split(".")[-1]
        }
    else:
        payload = {"text": text_input}
    
    # Call API
    response = requests.post("http://localhost:8000/analyze", json=payload)
    results = response.json()
    
    # Display results
    st.metric("Compliance Score", results["compliance_score"])
    # ... render other components
```

## Data Models

### Core Data Models

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SensitiveDataType(Enum):
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    ADDRESS = "address"
    SSN = "ssn"
    MEDICAL_RECORD_NUMBER = "medical_record_number"
    INSURANCE_ID = "insurance_id"
    HEALTH_CONDITION = "health_condition"
    AGE = "age"
    DATE_OF_BIRTH = "date_of_birth"

class ComplianceRiskType(Enum):
    MISSING_CONSENT = "missing_consent"
    UNSAFE_SHARING = "unsafe_data_sharing"
    MISSING_PRIVACY_NOTICE = "missing_privacy_notice"
    MISSING_CONFIDENTIALITY = "missing_confidentiality_statement"

@dataclass
class SensitiveDataFinding:
    """Represents a detected instance of sensitive data"""
    type: SensitiveDataType
    value: str  # Redacted value
    location: int  # Character position
    confidence: float  # 0.0-1.0
    detection_method: str  # "regex" or "ner"

@dataclass
class ComplianceRisk:
    """Represents an identified compliance risk"""
    type: ComplianceRiskType
    description: str
    severity: SeverityLevel
    location: Optional[str]  # Section of document where risk was found

@dataclass
class ComplianceAnalysis:
    """Results from LLM compliance analysis"""
    risks: List[ComplianceRisk]
    suggestions: List[str]
    analysis_timestamp: datetime

@dataclass
class ScoreDeduction:
    """Represents a deduction from the base compliance score"""
    reason: str
    points: int
    related_finding: Optional[str]

@dataclass
class ScoringResult:
    """Compliance score calculation results"""
    score: int  # 0-100
    risk_level: RiskLevel
    deductions: List[ScoreDeduction]

@dataclass
class AnalysisOutput:
    """Complete analysis output returned to user"""
    compliance_score: int
    risk_level: str
    sensitive_data: List[Dict[str, Any]]
    compliance_risks: List[Dict[str, Any]]
    suggestions: List[str]
    disclaimer: str
    timestamp: str
    processing_time_ms: int

# Request/Response Models for FastAPI
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    """Request model for document analysis"""
    text: Optional[str] = Field(None, description="Document text to analyze")
    file_content: Optional[str] = Field(None, description="Base64 encoded file content")
    file_type: Optional[str] = Field(None, description="File type: txt or pdf")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Patient John Doe was diagnosed with diabetes..."
            }
        }

class AnalysisResponse(BaseModel):
    """Response model for document analysis"""
    compliance_score: int = Field(..., ge=0, le=100)
    risk_level: str = Field(..., pattern="^(Low|Medium|High)$")
    sensitive_data: List[Dict[str, Any]]
    compliance_risks: List[Dict[str, Any]]
    suggestions: List[str]
    disclaimer: str
    timestamp: str
    processing_time_ms: int
```

### Configuration Models

```python
@dataclass
class BedrockConfig:
    """Configuration for Amazon Bedrock"""
    model_id: str = "amazon.nova-lite-v1:0"
    region: str = "us-east-1"
    max_tokens: int = 2000
    temperature: float = 0.3  # Lower temperature for consistent analysis
    guardrail_id: Optional[str] = None
    guardrail_version: Optional[str] = None

@dataclass
class AppConfig:
    """Application configuration"""
    max_document_length: int = 50000
    min_document_length: int = 10
    api_timeout_seconds: int = 30
    bedrock_config: BedrockConfig
    enable_ner: bool = True  # Toggle spaCy NER
    enable_regex: bool = True  # Toggle regex detection
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Text Input Acceptance

*For any* valid text string between 10 and 50,000 characters, the preprocessing module should successfully accept and normalize the text without errors.

**Validates: Requirements 1.1**

### Property 2: File Format Extraction

*For any* valid .txt or .pdf file containing text, the preprocessing module should successfully extract the text content.

**Validates: Requirements 1.2, 1.3**

### Property 3: Sensitive Data Detection Completeness

*For any* document containing sensitive data (names, age, phone, email, addresses, health conditions, or ID numbers), the Sensitive Data Scanner should detect and flag at least one instance of each sensitive data type present in the document.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

### Property 4: Compliance Risk Detection

*For any* document missing compliance safeguards (consent statements, privacy notices, or confidentiality statements) or containing unsafe data sharing language, the LLM Analyzer should identify at least one compliance risk.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 5: Score Range Invariant

*For any* set of analysis findings (sensitive data and compliance risks), the Score Generator should produce a compliance score between 0 and 100 inclusive.

**Validates: Requirements 4.1**

### Property 6: Risk Level Mapping

*For any* compliance score, the system should assign the correct risk level: Low for scores 80-100, Medium for scores 50-79, and High for scores 0-49.

**Validates: Requirements 4.5**

### Property 7: Output Structure Completeness

*For any* analyzed document, the structured output should be valid JSON and include all required fields: compliance_score, risk_level, sensitive_data list, compliance_risks list, suggestions list, disclaimer text, and timestamp.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**

### Property 8: UI Display Completeness

*For any* analysis result, the UI dashboard should render all required elements: compliance score, risk level with color coding, sensitive data list, compliance risks list, suggestions, and disclaimer.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

### Property 9: Guardrail Effectiveness

*For any* LLM analysis output, the system should not contain medical diagnosis suggestions, medical treatment recommendations, or legal advice statements.

**Validates: Requirements 8.1, 8.2, 8.3, 8.5**

### Property 10: Disclaimer Presence

*For any* analysis output, the system should include the mandatory disclaimer text stating the tool is for educational purposes only.

**Validates: Requirements 8.4**

### Property 11: Whitespace Normalization

*For any* document with multiple consecutive spaces, the preprocessing module should normalize them to single spaces while preserving paragraph breaks.

**Validates: Requirements 11.1, 11.2**

### Property 12: PDF Structure Preservation

*For any* PDF file with structured text (paragraphs, sections), the extraction process should preserve the document structure in the extracted text.

**Validates: Requirements 11.3**

### Property 13: Unsupported Format Rejection

*For any* file with an unsupported format (not .txt or .pdf), the preprocessing module should reject the file and return an appropriate error.

**Validates: Requirements 11.4**

### Property 14: Relative Scoring Consistency

*For any* pair of documents where one contains privacy safeguards (consent, privacy notice, confidentiality statement) and the other does not, the document with safeguards should receive a higher compliance score.

**Validates: Requirements 12.4**

## Error Handling

### Error Categories

1. **Input Validation Errors**:
   - Empty document (< 10 characters)
   - Document too large (> 50,000 characters)
   - Invalid file format
   - Corrupted PDF file
   - Missing required fields in API request

2. **Processing Errors**:
   - PDF extraction failure
   - Bedrock API timeout or failure
   - Invalid JSON response from LLM
   - spaCy NER model loading failure

3. **System Errors**:
   - AWS credentials invalid or expired
   - Network connectivity issues
   - Out of memory errors
   - Unexpected exceptions

### Error Handling Strategy

**Input Validation Errors**:
```python
class InputValidationError(Exception):
    """Raised when input fails validation"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

# Example usage
if len(text) < 10:
    raise InputValidationError(
        "Document must be at least 10 characters",
        "DOCUMENT_TOO_SHORT"
    )
```

**Processing Errors**:
- Implement retry logic for transient failures (Bedrock API timeouts)
- Graceful degradation: If spaCy NER fails, fall back to regex-only detection
- Log all processing errors with context for debugging
- Return partial results when possible with warning flags

**System Errors**:
- Catch all unexpected exceptions at API boundary
- Return 500 status code with generic error message (don't expose internals)
- Log full stack trace for debugging
- Display user-friendly error message in UI

### Error Response Format

```python
@dataclass
class ErrorResponse:
    error: str  # User-friendly error message
    error_code: str  # Machine-readable error code
    details: Optional[str]  # Additional context (optional)
    timestamp: str

# Example error codes
ERROR_CODES = {
    "DOCUMENT_TOO_SHORT": "Document must be at least 10 characters",
    "DOCUMENT_TOO_LARGE": "Document exceeds 50,000 character limit",
    "INVALID_FILE_FORMAT": "Only .txt and .pdf files are supported",
    "PDF_EXTRACTION_FAILED": "Unable to extract text from PDF",
    "BEDROCK_API_ERROR": "AI analysis service temporarily unavailable",
    "INVALID_REQUEST": "Request missing required fields"
}
```

### Retry Strategy

For transient failures (Bedrock API timeouts):
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_bedrock_api(prompt: str) -> dict:
    """Call Bedrock API with retry logic"""
    # Implementation
```

## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using randomized test data

Both approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing

**Framework**: Use `hypothesis` library for Python property-based testing

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: healthcare-compliance-copilot, Property {number}: {property_text}`

**Example Property Test**:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: healthcare-compliance-copilot, Property 5: Score Range Invariant
@given(
    sensitive_findings=st.lists(st.builds(SensitiveDataFinding)),
    compliance_risks=st.lists(st.builds(ComplianceRisk))
)
def test_score_always_in_valid_range(sensitive_findings, compliance_risks):
    """
    Property 5: For any set of findings, score should be 0-100
    """
    analysis = ComplianceAnalysis(risks=compliance_risks, suggestions=[])
    result = score_generator.calculate_score(sensitive_findings, analysis)
    
    assert 0 <= result.score <= 100, f"Score {result.score} out of range"
```

### Unit Testing

**Framework**: Use `pytest` for unit testing

**Test Categories**:

1. **Input Validation Tests**:
   - Test empty document rejection
   - Test oversized document rejection
   - Test valid input acceptance
   - Test file format validation

2. **Sensitive Data Detection Tests**:
   - Test email detection with various formats
   - Test phone number detection with various formats
   - Test SSN detection
   - Test name detection with NER
   - Test health condition detection

3. **Compliance Analysis Tests**:
   - Test missing consent detection
   - Test unsafe sharing language detection
   - Test missing privacy notice detection
   - Test guardrail effectiveness (no medical advice)

4. **Scoring Tests**:
   - Test clean document scores high (90+)
   - Test document with sensitive data + safeguards scores medium (60-89)
   - Test document with sensitive data - safeguards scores low (<60)
   - Test risk level assignment

5. **Integration Tests**:
   - Test full pipeline with sample documents
   - Test API endpoint responses
   - Test error handling paths

**Example Unit Test**:
```python
def test_email_detection():
    """Test that email addresses are detected"""
    scanner = SensitiveDataScanner()
    text = "Contact us at john.doe@example.com for more info"
    
    findings = scanner.scan_document(text)
    
    email_findings = [f for f in findings if f.type == SensitiveDataType.EMAIL]
    assert len(email_findings) == 1
    assert "example.com" in email_findings[0].value
```

### Test Data Strategy

**Synthetic Test Data**:
- Generate synthetic healthcare documents with known sensitive data
- Use faker library to generate realistic PII (names, emails, phones)
- Create document templates with/without compliance safeguards

**Example Test Data Generator**:
```python
from faker import Faker

def generate_test_document(
    include_pii: bool = True,
    include_consent: bool = False,
    include_health_condition: bool = False
) -> str:
    """Generate synthetic test document"""
    fake = Faker()
    
    doc = "Medical Record\n\n"
    
    if include_pii:
        doc += f"Patient: {fake.name()}\n"
        doc += f"Email: {fake.email()}\n"
        doc += f"Phone: {fake.phone_number()}\n"
    
    if include_health_condition:
        doc += f"Diagnosis: Type 2 Diabetes\n"
    
    if include_consent:
        doc += "\nPatient has provided written consent for data sharing.\n"
    
    return doc
```

### Mocking Strategy

**Mock Bedrock API**:
- Use `moto` library to mock AWS Bedrock calls in tests
- Create deterministic mock responses for consistent testing
- Test both success and failure scenarios

**Example Mock**:
```python
from unittest.mock import Mock, patch

@patch('boto3.client')
def test_llm_analyzer_with_mock(mock_boto_client):
    """Test LLM analyzer with mocked Bedrock"""
    mock_bedrock = Mock()
    mock_bedrock.invoke_model.return_value = {
        'body': json.dumps({
            'risks': [
                {'type': 'missing_consent', 'description': 'No consent found', 'severity': 'high'}
            ],
            'suggestions': ['Add consent statement']
        })
    }
    mock_boto_client.return_value = mock_bedrock
    
    analyzer = LLMAnalyzer()
    result = analyzer.analyze_compliance("test document", [])
    
    assert len(result.risks) == 1
    assert result.risks[0].type == ComplianceRiskType.MISSING_CONSENT
```

### Test Coverage Goals

- **Line Coverage**: Minimum 80% for all modules
- **Branch Coverage**: Minimum 75% for conditional logic
- **Property Test Coverage**: All 14 correctness properties must have corresponding property tests
- **Critical Path Coverage**: 100% coverage of main analysis pipeline

### Continuous Testing

- Run unit tests on every commit
- Run property tests (with reduced iterations) on every commit
- Run full property test suite (100+ iterations) nightly
- Run integration tests before deployment
- Monitor test execution time and optimize slow tests
