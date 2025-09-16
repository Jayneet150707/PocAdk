"""
FastAPI backend service for Credit Assessment Agent POC.

This is the main entry point for the credit assessment API service.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends

# Check for python-multipart availability
try:
    import multipart
    from fastapi import UploadFile, File, Form
    MULTIPART_AVAILABLE = True
except ImportError:
    UploadFile = None
    File = None
    Form = None
    MULTIPART_AVAILABLE = False
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from credit_assessment_agent import CreditAssessmentAgent
from credit_assessment_agent.shared_libraries.data_models import (
    CreditApplication,
    CreditAssessmentResult,
    AssessmentRequest
)
from credit_assessment_agent.shared_libraries.vertex_ai_client import VertexAIClient
from api.routes import router as api_router
from api.dependencies import get_credit_agent, get_vertex_ai_client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Credit Assessment Agent API")
    
    # Initialize services
    try:
        # Test Vertex AI connection
        vertex_client = VertexAIClient()
        logger.info("Vertex AI client initialized successfully")
        
        # Initialize main agent
        credit_agent = CreditAssessmentAgent(vertex_ai_client=vertex_client)
        logger.info("Credit Assessment Agent initialized successfully")
        
        # Store in app state
        app.state.vertex_client = vertex_client
        app.state.credit_agent = credit_agent
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        # Continue without AI services for basic functionality
        app.state.vertex_client = None
        app.state.credit_agent = None
    
    yield
    
    logger.info("Shutting down Credit Assessment Agent API")


# Create FastAPI application
app = FastAPI(
    title="Credit Assessment Agent API",
    description="POC for intelligent credit application assessment using Google ADK with Vertex AI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Credit Assessment Agent API",
        "version": "0.1.0",
        "description": "POC for intelligent credit application assessment",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if services are available
        vertex_available = app.state.vertex_client is not None
        agent_available = app.state.credit_agent is not None
        
        return {
            "status": "healthy",
            "services": {
                "vertex_ai": "available" if vertex_available else "unavailable",
                "credit_agent": "available" if agent_available else "unavailable"
            },
            "timestamp": "2024-09-16T11:30:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/api/v1/assess-credit", response_model=Dict[str, Any])
async def assess_credit_application(
    request: AssessmentRequest,
    credit_agent: CreditAssessmentAgent = Depends(get_credit_agent)
):
    """
    Assess a credit application.
    
    This endpoint processes a complete credit application and returns
    an assessment with credibility score and confidence metrics.
    """
    try:
        logger.info(f"Processing credit assessment for application {request.credit_application.application_id}")
        
        # Perform credit assessment
        assessment_result = await credit_agent.assess_credit_application(
            application=request.credit_application,
            bank_transactions=request.bank_statement_data,
            priority=request.priority
        )
        
        return {
            "success": True,
            "assessment": assessment_result.dict(),
            "message": "Credit assessment completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Credit assessment failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Assessment failed: {str(e)}"
        )


# Define upload function separately to avoid import-time evaluation
async def upload_bank_statement_impl(
    file, applicant_id: str, credit_agent: CreditAssessmentAgent
):
    """
    Upload and process a bank statement PDF.
    
    This endpoint accepts a PDF bank statement, extracts transaction data,
    and returns analysis results.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # Save temporary file
        import tempfile
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_content)
            temp_path = Path(temp_file.name)
        
        try:
            # Process bank statement
            analysis_result = await credit_agent.analyze_bank_statement(
                pdf_path=temp_path,
                applicant_id=applicant_id
            )
            
            return {
                "success": True,
                "analysis": analysis_result,
                "message": "Bank statement processed successfully"
            }
            
        finally:
            # Clean up temporary file
            temp_path.unlink(missing_ok=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bank statement processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.get("/api/v1/assessment/{assessment_id}")
async def get_assessment_result(
    assessment_id: str,
    credit_agent: CreditAssessmentAgent = Depends(get_credit_agent)
):
    """
    Retrieve a specific assessment result by ID.
    """
    try:
        # This would typically query a database
        # For POC, return a placeholder response
        return {
            "success": True,
            "assessment_id": assessment_id,
            "message": "Assessment retrieval not implemented in POC",
            "note": "In production, this would query stored assessment results"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve assessment {assessment_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


# Conditionally add file upload endpoint if multipart is available
if MULTIPART_AVAILABLE:
    @app.post("/api/v1/upload-bank-statement")
    async def upload_bank_statement(
        file: UploadFile = File(...),
        applicant_id: str = Form(...),
        credit_agent: CreditAssessmentAgent = Depends(get_credit_agent)
    ):
        return await upload_bank_statement_impl(file, applicant_id, credit_agent)
else:
    @app.post("/api/v1/upload-bank-statement")
    async def upload_bank_statement_unavailable():
        raise HTTPException(
            status_code=501,
            detail="File upload functionality requires python-multipart. Install with: pip install python-multipart"
        )


if __name__ == "__main__":
    # Configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
