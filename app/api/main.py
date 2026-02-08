"""
FastAPI Backend for Healthcare Compliance Copilot.

This module provides the REST API for document compliance analysis.
It orchestrates the analysis pipeline: preprocessing → scanning → analysis → scoring → formatting.
"""

import logging
import time
import base64
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from app.services.preprocessing import PreprocessingModule
from app.services.sensitive_data_scanner import SensitiveDataScanner
from app.services.llm_analyzer import LLMAnalyzer
from app.services.score_generator import ScoreGenerator
from app.services.output_formatter import OutputFormatter
from app.models.config import AppConfig
from app.models.data_models import AnalysisOutput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Compliance Copilot API",
    description="AI-powered document analysis for healthcare compliance and privacy risks",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config = AppConfig.from_env()

# Initialize service instances
preprocessing_module = PreprocessingModule(config)
sensitive_scanner = SensitiveDataScanner()
llm_analyzer = LLMAnalyzer(config.bedrock_config)
score_generator = ScoreGenerator()
output_formatter = OutputFormatter()

logger.info("FastAPI application initialized with all services")


# Request/Response Models
class AnalysisRequest(BaseModel):
    """Request model for document analysis."""
    text: Optional[str] = Field(None, description="Document text to analyze")
    file_content: Optional[str] = Field(None, description="Base64 encoded file content")
    file_type: Optional[str] = Field(None, description="File type: txt or pdf")
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file type is txt or pdf."""
        if v and v.lower() not in ['txt', 'pdf']:
            raise ValueError("file_type must be 'txt' or 'pdf'")
        return v.lower() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Patient John Doe was diagnosed with diabetes. Contact: john@example.com"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status message indicating the API is healthy
    """
    return {
        "status": "healthy",
        "service": "Healthcare Compliance Copilot API",
        "version": "1.0.0"
    }


# Analysis pipeline orchestration
async def run_analysis_pipeline(text: str) -> AnalysisOutput:
    """
    Run the complete analysis pipeline.
    
    Pipeline steps:
    1. Preprocess text
    2. Scan for sensitive data
    3. Analyze compliance with LLM
    4. Calculate score
    5. Format output
    
    Args:
        text: Document text to analyze
        
    Returns:
        AnalysisOutput with complete analysis results
        
    Raises:
        HTTPException: If any step in the pipeline fails
    """
    start_time = time.time()
    
    try:
        # Step 1: Preprocess
        logger.info("Step 1: Preprocessing document")
        preprocessed_text = preprocessing_module.preprocess_text(text)
        
        # Step 2: Scan for sensitive data
        logger.info("Step 2: Scanning for sensitive data")
        sensitive_findings = sensitive_scanner.scan_document(preprocessed_text)
        logger.info(f"Found {len(sensitive_findings)} sensitive data instances")
        
        # Step 3: Analyze compliance with LLM
        logger.info("Step 3: Analyzing compliance with LLM")
        compliance_analysis = llm_analyzer.analyze_compliance(
            preprocessed_text,
            sensitive_findings
        )
        logger.info(f"Identified {len(compliance_analysis.risks)} compliance risks")
        
        # Step 4: Calculate score
        logger.info("Step 4: Calculating compliance score")
        scoring_result = score_generator.calculate_score(
            sensitive_findings,
            compliance_analysis
        )
        logger.info(f"Score: {scoring_result.score}, Risk Level: {scoring_result.risk_level.value}")
        
        # Step 5: Format output
        logger.info("Step 5: Formatting output")
        processing_time_ms = int((time.time() - start_time) * 1000)
        output = output_formatter.format_output(
            sensitive_findings,
            compliance_analysis,
            scoring_result,
            processing_time_ms
        )
        
        logger.info(f"Analysis complete in {processing_time_ms}ms")
        return output
        
    except ValueError as e:
        logger.error(f"Validation error in pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during analysis. Please try again."
        )


# Main analysis endpoint
@app.post(
    "/analyze",
    response_model=AnalysisOutput,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    tags=["Analysis"]
)
async def analyze_document(request: AnalysisRequest):
    """
    Analyze document for compliance and privacy risks.
    
    Accepts either text input or file upload (base64 encoded).
    Returns comprehensive analysis with compliance score, risk level,
    detected sensitive data, compliance risks, and improvement suggestions.
    
    Args:
        request: AnalysisRequest with text or file content
        
    Returns:
        AnalysisOutput with complete analysis results
        
    Raises:
        HTTPException: 400 for invalid input, 500 for server errors
    """
    logger.info("Received analysis request")
    
    # Validate that either text or file is provided
    if not request.text and not request.file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'text' or 'file_content' must be provided"
        )
    
    # If file is provided, validate file_type is also provided
    if request.file_content and not request.file_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'file_type' must be provided when 'file_content' is present"
        )
    
    try:
        # Extract text from input
        if request.text:
            text = request.text
            logger.info("Processing text input")
        else:
            # Decode base64 file content
            logger.info(f"Processing {request.file_type} file")
            try:
                file_bytes = base64.b64decode(request.file_content)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid base64 encoding: {str(e)}"
                )
            
            # Extract text based on file type
            if request.file_type == 'pdf':
                text = preprocessing_module.extract_pdf_text(file_bytes)
            else:  # txt
                text = file_bytes.decode('utf-8')
        
        # Validate input
        if not preprocessing_module.validate_input(text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document validation failed. Check size and content requirements."
            )
        
        # Run analysis pipeline
        output = await run_analysis_pipeline(text)
        
        return output
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        API information and available endpoints
    """
    return {
        "service": "Healthcare Compliance Copilot API",
        "version": "1.0.0",
        "description": "AI-powered document analysis for healthcare compliance and privacy risks",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze (POST)",
            "docs": "/docs"
        },
        "warning": "Use only synthetic or public data - never upload real PHI"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
