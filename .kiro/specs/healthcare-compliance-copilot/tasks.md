# Implementation Plan: AI Healthcare Compliance Copilot

## Overview

This implementation plan breaks down the Healthcare Compliance Copilot into discrete coding tasks. The approach follows a bottom-up strategy: build core components first (preprocessing, detection, scoring), then integrate them into the API pipeline, and finally add the UI layer. Each task builds on previous work, with testing integrated throughout to catch issues early.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create Python project with Poetry or pip requirements
  - Install core dependencies: FastAPI, Streamlit, boto3 (Bedrock), PyPDF2, spaCy, hypothesis, pytest
  - Download spaCy English model: `python -m spacy download en_core_web_sm`
  - Create directory structure: `app/`, `app/models/`, `app/services/`, `app/api/`, `app/ui/`, `tests/`
  - Set up configuration management for Bedrock credentials and app settings
  - _Requirements: 10.1_

- [x] 2. Implement data models
  - [x] 2.1 Create core data models in `app/models/data_models.py`
    - Implement enums: `RiskLevel`, `SeverityLevel`, `SensitiveDataType`, `ComplianceRiskType`
    - Implement dataclasses: `SensitiveDataFinding`, `ComplianceRisk`, `ComplianceAnalysis`, `ScoreDeduction`, `ScoringResult`, `AnalysisOutput`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 2.2 Create API request/response models in `app/models/api_models.py`
    - Implement Pydantic models: `AnalysisRequest`, `AnalysisResponse`, `ErrorResponse`
    - Add validation rules (score 0-100, risk level pattern, etc.)
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 2.3 Create configuration models in `app/models/config.py`
    - Implement `BedrockConfig` and `AppConfig` dataclasses
    - Load configuration from environment variables
    - _Requirements: 10.1_

- [x] 3. Implement preprocessing module
  - [x] 3.1 Create `PreprocessingModule` class in `app/services/preprocessing.py`
    - Implement `preprocess_text()` method for text normalization
    - Implement `extract_pdf_text()` method using PyPDF2
    - Implement `validate_input()` method for size and content validation
    - Handle edge cases: empty documents, oversized documents, invalid PDFs
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2, 11.3, 11.4_
  
  - [ ]* 3.2 Write property test for text normalization
    - **Property 11: Whitespace Normalization**
    - **Validates: Requirements 11.1, 11.2**
  
  - [ ]* 3.3 Write property test for file format handling
    - **Property 2: File Format Extraction**
    - **Validates: Requirements 1.2, 1.3**
  
  - [ ]* 3.4 Write unit tests for edge cases
    - Test empty document rejection
    - Test oversized document rejection
    - Test invalid PDF handling
    - _Requirements: 1.4, 1.5_

- [x] 4. Implement sensitive data scanner
  - [x] 4.1 Create `SensitiveDataScanner` class in `app/services/sensitive_data_scanner.py`
    - Implement regex patterns for email, phone, SSN, MRN, insurance ID, ZIP code
    - Implement `detect_with_regex()` method
    - Implement `detect_with_ner()` method using spaCy
    - Implement `scan_document()` method that combines both approaches
    - Redact detected values in findings (e.g., "***@***.com")
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [ ]* 4.2 Write property test for sensitive data detection
    - **Property 3: Sensitive Data Detection Completeness**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**
  
  - [ ]* 4.3 Write unit tests for specific detection patterns
    - Test email detection with various formats
    - Test phone number detection with various formats
    - Test SSN detection
    - Test name detection with spaCy NER
    - Test health condition detection
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 5. Checkpoint - Ensure preprocessing and detection tests pass
  - Run all tests for preprocessing and sensitive data scanner
  - Verify test coverage meets 80% goal for these modules
  - Ask the user if questions arise

- [x] 6. Implement LLM analyzer with Bedrock
  - [x] 6.1 Create `LLMAnalyzer` class in `app/services/llm_analyzer.py`
    - Initialize boto3 Bedrock client with configuration
    - Implement `build_prompt()` method to construct analysis prompt
    - Implement `analyze_compliance()` method to call Bedrock Nova Lite
    - Parse JSON response into `ComplianceAnalysis` object
    - Configure guardrails to prevent medical advice, diagnosis, and treatment recommendations
    - Handle API errors and timeouts with retry logic
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 8.1, 8.2, 8.3, 8.5_
  
  - [ ]* 6.2 Write property test for compliance risk detection
    - **Property 4: Compliance Risk Detection**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
  
  - [ ]* 6.3 Write property test for guardrail effectiveness
    - **Property 9: Guardrail Effectiveness**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.5**
  
  - [ ]* 6.4 Write unit tests with mocked Bedrock API
    - Test missing consent detection
    - Test unsafe sharing language detection
    - Test missing privacy notice detection
    - Test API error handling
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 7. Implement score generator
  - [x] 7.1 Create `ScoreGenerator` class in `app/services/score_generator.py`
    - Implement `calculate_score()` method with deduction algorithm
    - Deduct points for high-severity risks (-15), medium (-10), low (-5)
    - Deduct points for sensitive data without safeguards (-8 per type)
    - Deduct points for health conditions + identifiers (-20)
    - Implement risk level assignment: Low (80-100), Medium (50-79), High (0-49)
    - Track deductions with reasons for transparency
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 7.2 Write property test for score range invariant
    - **Property 5: Score Range Invariant**
    - **Validates: Requirements 4.1**
  
  - [ ]* 7.3 Write property test for risk level mapping
    - **Property 6: Risk Level Mapping**
    - **Validates: Requirements 4.5**
  
  - [ ]* 7.4 Write property test for relative scoring consistency
    - **Property 14: Relative Scoring Consistency**
    - **Validates: Requirements 12.4**
  
  - [ ]* 7.5 Write unit tests for scoring scenarios
    - Test clean document scores 90+
    - Test document with sensitive data + safeguards scores 60-89
    - Test document with sensitive data - safeguards scores <60
    - Test high-risk scenario: name + disease + email without consent
    - _Requirements: 4.2, 4.3, 4.4, 12.1_

- [x] 8. Implement output formatter
  - [x] 8.1 Create `OutputFormatter` class in `app/services/output_formatter.py`
    - Implement `format_output()` method to create `AnalysisOutput`
    - Convert findings to dictionaries for JSON serialization
    - Add mandatory disclaimer text
    - Add timestamp and processing time
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 8.4_
  
  - [ ]* 8.2 Write property test for output structure completeness
    - **Property 7: Output Structure Completeness**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**
  
  - [ ]* 8.3 Write property test for disclaimer presence
    - **Property 10: Disclaimer Presence**
    - **Validates: Requirements 8.4**
  
  - [ ]* 8.4 Write unit tests for output formatting
    - Test JSON serialization
    - Test all required fields present
    - Test disclaimer text content
    - _Requirements: 5.1, 5.7, 8.4_

- [x] 9. Checkpoint - Ensure all service layer tests pass
  - Run all tests for LLM analyzer, score generator, and output formatter
  - Verify integration between components
  - Ask the user if questions arise

- [x] 10. Implement FastAPI backend
  - [x] 10.1 Create FastAPI application in `app/api/main.py`
    - Initialize FastAPI app with CORS middleware
    - Create service instances (preprocessing, scanner, analyzer, scorer, formatter)
    - Implement `/health` endpoint for health checks
    - _Requirements: 10.1_
  
  - [x] 10.2 Implement analysis pipeline orchestration
    - Create `run_analysis_pipeline()` async function
    - Orchestrate: preprocess → scan → analyze → score → format
    - Use asyncio for parallel operations where possible
    - Track processing time
    - _Requirements: 10.1, 10.2_
  
  - [x] 10.3 Implement `/analyze` POST endpoint
    - Accept `AnalysisRequest` with text or file content
    - Handle text input and file upload (base64 encoded)
    - Call analysis pipeline
    - Return `AnalysisResponse` JSON
    - Handle errors and return appropriate status codes (400, 500)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 10.4 Write integration tests for API endpoints
    - Test `/analyze` with text input
    - Test `/analyze` with .txt file
    - Test `/analyze` with .pdf file
    - Test error handling for invalid inputs
    - Test `/health` endpoint
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 11. Implement Streamlit frontend
  - [x] 11.1 Create Streamlit app in `app/ui/streamlit_app.py`
    - Set up page configuration and title
    - Display header with application description
    - Display prominent warning: "Use only synthetic or public data"
    - Display disclaimer at top of page
    - _Requirements: 6.1, 6.6, 7.3_
  
  - [x] 11.2 Implement input section
    - Create text area for pasting document text
    - Create file uploader for .txt and .pdf files
    - Display character count
    - Add "Analyze Document" button
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 11.3 Implement API integration
    - Send POST request to FastAPI `/analyze` endpoint
    - Handle text input and file upload
    - Display loading spinner during analysis
    - Handle API errors and display user-friendly messages
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [x] 11.4 Implement results display section
    - Display compliance score in large metric card
    - Color code score: Green (80-100), Yellow (50-79), Red (0-49)
    - Display risk level with visual indicator
    - Display sensitive data in expandable table
    - Display compliance risks in expandable list with severity badges
    - Display improvement suggestions in bullet list
    - Display disclaimer at bottom of results
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 11.5 Write property test for UI display completeness
    - **Property 8: UI Display Completeness**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**

- [x] 12. Implement error handling and logging
  - [x] 12.1 Add comprehensive error handling
    - Implement custom exception classes: `InputValidationError`, `ProcessingError`
    - Add try-catch blocks in all service methods
    - Return structured error responses from API
    - Display user-friendly error messages in UI
    - _Requirements: 1.4, 1.5, 11.4_
  
  - [x] 12.2 Add logging throughout application
    - Configure Python logging with appropriate levels
    - Log all API requests and responses
    - Log processing errors with stack traces
    - Log Bedrock API calls and responses
    - Do NOT log document content (privacy requirement)
    - _Requirements: 7.1, 7.2_

- [x] 13. Create synthetic test data generator
  - [x] 13.1 Create test data generator in `tests/test_data_generator.py`
    - Use faker library to generate realistic PII
    - Create `generate_test_document()` function with parameters
    - Generate documents with/without PII, consent, health conditions
    - Create document templates for various scenarios
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [ ]* 13.2 Write example tests for evaluation scenarios
    - Test high-risk scenario: name + disease + email without consent
    - Test medium-risk scenario: sensitive data without consent
    - Test low-risk scenario: anonymized data only
    - _Requirements: 12.1, 12.2, 12.3_

- [x] 14. Checkpoint - End-to-end integration testing
  - Run full application (FastAPI + Streamlit)
  - Test complete workflow with synthetic documents
  - Verify all components work together correctly
  - Ensure all tests pass
  - Ask the user if questions arise

- [ ] 15. Add deployment configuration
  - [x] 15.1 Create Dockerfile for containerization
    - Multi-stage build for FastAPI and Streamlit
    - Install all dependencies
    - Download spaCy model
    - Set up environment variables
    - _Requirements: 10.1_
  
  - [x] 15.2 Create docker-compose.yml
    - Define FastAPI service on port 8000
    - Define Streamlit service on port 8501
    - Set up networking between services
    - Configure environment variables
    - _Requirements: 10.1_
  
  - [ ] 15.3 Create README with setup instructions
    - Document prerequisites (Python 3.9+, AWS credentials)
    - Document installation steps
    - Document how to run locally
    - Document how to run with Docker
    - Document environment variables
    - Include usage examples
    - _Requirements: 10.1_

- [ ] 16. Final checkpoint - Complete system verification
  - Run all unit tests and property tests
  - Verify test coverage meets 80% goal
  - Test deployment with Docker
  - Verify all requirements are met
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with 100+ iterations
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: core services → API → UI
- All document content processing happens in memory (no persistent storage per Requirements 7.1, 7.2)
