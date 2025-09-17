#!/usr/bin/env python3
"""
Paisalo Credit Assessment API

FastAPI backend service for credit application assessment using Google ADK
and Vertex AI with Paisalo-specific business rules.
"""

import asyncio
import logging
import json
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import our credit assessment components
from credit_assessment_agent.agent import CreditAssessmentAgent
from credit_assessment_agent.shared_libraries.data_models import (
    CreditApplication,
    ApplicantInfo,
    DocumentType,
    EmploymentStatus,
    LoanPurpose,
    CreditAssessmentResult,
    AssessmentRequest,
    BankTransaction
)
from credit_assessment_agent.shared_libraries.vertex_ai_client import VertexAIClient
from credit_assessment_agent.shared_libraries.paisalo_rules import PaisaloBusinessRules

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Paisalo Credit Assessment API",
    description="AI-powered credit assessment service with Paisalo business rules",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for agents
credit_agent: Optional[CreditAssessmentAgent] = None
vertex_client: Optional[VertexAIClient] = None


# Response models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    paisalo_rules_loaded: bool
    vertex_ai_available: bool


class AssessmentResponse(BaseModel):
    """Credit assessment response."""
    success: bool
    assessment_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_seconds: float
    paisalo_validation: Optional[Dict[str, Any]] = None


class ValidationResponse(BaseModel):
    """Paisalo rules validation response."""
    is_valid: bool
    risk_level: str
    validations: Dict[str, Dict[str, Any]]
    rejection_reasons: List[str]
    warnings: List[str]
    emi_details: Optional[Dict[str, Any]] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application components."""
    global credit_agent, vertex_client
    
    logger.info("🚀 Starting Paisalo Credit Assessment API...")
    
    try:
        # Initialize Vertex AI client (optional)
        try:
            vertex_client = VertexAIClient()
            logger.info("✅ Vertex AI client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Vertex AI client initialization failed: {e}")
            vertex_client = None
        
        # Initialize credit assessment agent
        credit_agent = CreditAssessmentAgent(vertex_ai_client=vertex_client)
        logger.info("✅ Credit Assessment Agent initialized")
        
        # Test Paisalo rules
        test_validation = PaisaloBusinessRules.validate_age(30)
        if test_validation[0]:
            logger.info("✅ Paisalo business rules loaded successfully")
        else:
            logger.error("❌ Paisalo business rules validation failed")
        
        logger.info("🎉 Paisalo Credit Assessment API started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        paisalo_rules_loaded=True,
        vertex_ai_available=vertex_client is not None
    )


# Main assessment endpoint
@app.post("/assess", response_model=AssessmentResponse)
async def assess_credit_application(request: AssessmentRequest):
    """
    Assess a credit application using Paisalo business rules and AI.
    
    This endpoint performs comprehensive credit assessment including:
    - Paisalo business rules validation
    - AI-powered risk assessment (if available)
    - EMI calculation using SLM method
    - Detailed recommendations
    """
    start_time = datetime.utcnow()
    
    try:
        if not credit_agent:
            raise HTTPException(status_code=500, detail="Credit assessment agent not initialized")
        
        logger.info(f"📋 Processing credit assessment for application {request.credit_application.application_id}")
        
        # Perform Paisalo validation first
        paisalo_validation = PaisaloBusinessRules.perform_complete_validation(request.credit_application)
        
        # Perform full assessment
        assessment_result = await credit_agent.assess_credit_application(
            application=request.credit_application,
            bank_transactions=request.bank_statement_data,
            priority=request.priority
        )
        
        # Convert result to dict for JSON response
        result_dict = {
            "application_id": assessment_result.application_id,
            "assessment_id": assessment_result.assessment_id,
            "approved": assessment_result.approved,
            "risk_level": assessment_result.risk_level.value,
            "recommended_loan_amount": float(assessment_result.recommended_loan_amount) if assessment_result.recommended_loan_amount else None,
            "recommended_interest_rate": assessment_result.recommended_interest_rate,
            "confidence_scores": {
                "overall_confidence": assessment_result.confidence_scores.overall_confidence,
                "credit_score_confidence": assessment_result.confidence_scores.credit_score_confidence,
                "income_confidence": assessment_result.confidence_scores.income_confidence,
                "transaction_confidence": assessment_result.confidence_scores.transaction_confidence,
                "application_confidence": assessment_result.confidence_scores.application_confidence,
                "data_quality_score": assessment_result.confidence_scores.data_quality_score
            },
            "risk_factors": {
                "high_debt_to_income": assessment_result.risk_factors.high_debt_to_income,
                "insufficient_income": assessment_result.risk_factors.insufficient_income,
                "poor_credit_history": assessment_result.risk_factors.poor_credit_history,
                "irregular_income": assessment_result.risk_factors.irregular_income,
                "excessive_expenses": assessment_result.risk_factors.excessive_expenses,
                "frequent_overdrafts": assessment_result.risk_factors.frequent_overdrafts,
                "short_employment_history": assessment_result.risk_factors.short_employment_history,
                "high_loan_to_value": assessment_result.risk_factors.high_loan_to_value,
                "risk_factors_count": assessment_result.risk_factors.risk_factors_count,
                "risk_level": assessment_result.risk_factors.risk_level.value
            },
            "reasoning": assessment_result.reasoning,
            "recommendations": assessment_result.recommendations,
            "assessed_at": assessment_result.assessed_at.isoformat(),
            "processing_time_seconds": assessment_result.processing_time_seconds
        }
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ Assessment completed for {request.credit_application.application_id} in {processing_time:.2f}s")
        
        return AssessmentResponse(
            success=True,
            assessment_result=result_dict,
            processing_time_seconds=processing_time,
            paisalo_validation={
                "is_valid": paisalo_validation["is_valid"],
                "risk_level": paisalo_validation["risk_level"].value,
                "validations": paisalo_validation["validations"],
                "rejection_reasons": paisalo_validation["rejection_reasons"],
                "warnings": paisalo_validation["warnings"],
                "emi_details": paisalo_validation["emi_details"]
            }
        )
        
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"❌ Assessment failed: {str(e)}")
        
        return AssessmentResponse(
            success=False,
            error_message=str(e),
            processing_time_seconds=processing_time
        )


# Paisalo rules validation endpoint
@app.post("/validate", response_model=ValidationResponse)
async def validate_paisalo_rules(application: CreditApplication):
    """
    Validate application against Paisalo business rules only.
    
    This endpoint performs only the business rules validation without
    full AI assessment, useful for quick pre-screening.
    """
    try:
        logger.info(f"🔍 Validating Paisalo rules for application {application.application_id}")
        
        # Perform Paisalo validation
        validation_results = PaisaloBusinessRules.perform_complete_validation(application)
        
        return ValidationResponse(
            is_valid=validation_results["is_valid"],
            risk_level=validation_results["risk_level"].value,
            validations=validation_results["validations"],
            rejection_reasons=validation_results["rejection_reasons"],
            warnings=validation_results["warnings"],
            emi_details=validation_results["emi_details"]
        )
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# EMI calculation request model
class EMIRequest(BaseModel):
    """EMI calculation request."""
    loan_amount: float = Field(..., description="Loan amount in INR")
    term_months: int = Field(..., description="Loan term in months (12, 24, 36, or 48)")


# EMI calculation endpoint
@app.post("/calculate-emi")
async def calculate_emi(request: EMIRequest):
    """
    Calculate EMI using Paisalo's SLM (Straight Line Method).
    
    Returns monthly EMI, total interest, and total amount to be paid.
    """
    try:
        logger.info(f"💰 Calculating EMI for amount ₹{request.loan_amount:,.2f}, term {request.term_months} months")
        
        # Validate inputs
        if request.term_months not in [12, 24, 36, 48]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid term. Allowed terms: 12, 24, 36, or 48 months"
            )
        
        if not (50000 <= request.loan_amount <= 100000):
            raise HTTPException(
                status_code=400,
                detail="Loan amount must be between ₹50,000 and ₹1,00,000"
            )
        
        # Calculate EMI
        monthly_emi, annual_roi = PaisaloBusinessRules.calculate_emi_slm(
            Decimal(str(request.loan_amount)), request.term_months
        )
        
        total_amount = monthly_emi * request.term_months
        total_interest = total_amount - Decimal(str(request.loan_amount))
        
        return {
            "loan_amount": request.loan_amount,
            "term_months": request.term_months,
            "monthly_emi": float(monthly_emi),
            "annual_roi": annual_roi,
            "total_interest": float(total_interest),
            "total_amount": float(total_amount),
            "calculation_method": "SLM (Straight Line Method)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ EMI calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Sample data endpoint
@app.get("/sample-request")
async def get_sample_request():
    """
    Get a sample credit application request for testing.
    
    Returns a properly formatted request that can be used with the /assess endpoint.
    """
    try:
        with open('sample_paisalo_request.json', 'r') as f:
            sample_data = json.load(f)
        return sample_data
    except Exception as e:
        logger.error(f"❌ Failed to load sample request: {str(e)}")
        raise HTTPException(status_code=500, detail="Sample request not available")


# Business rules info endpoint
@app.get("/business-rules")
async def get_business_rules():
    """
    Get information about Paisalo business rules and validation criteria.
    """
    return {
        "paisalo_business_rules": {
            "age_range": {
                "minimum": PaisaloBusinessRules.MIN_AGE,
                "maximum": PaisaloBusinessRules.MAX_AGE,
                "description": "Applicant age must be between 21-57 years"
            },
            "credit_score_range": {
                "minimum": PaisaloBusinessRules.MIN_CREDIT_SCORE,
                "maximum": PaisaloBusinessRules.MAX_CREDIT_SCORE,
                "description": "Credit score must be between 18-650"
            },
            "loan_amount_range": {
                "minimum": float(PaisaloBusinessRules.MIN_LOAN_AMOUNT),
                "maximum": float(PaisaloBusinessRules.MAX_LOAN_AMOUNT),
                "description": "Loan amount must be between ₹50,000-₹1,00,000"
            },
            "document_requirements": {
                "valid_combinations": [
                    "Voter ID + PAN",
                    "Driving License + PAN"
                ],
                "description": "Must provide one of the valid document combinations"
            },
            "income_expense_ratio": {
                "maximum_ratio": PaisaloBusinessRules.MAX_EXPENSE_RATIO,
                "description": "Total expenses must not exceed 50% of total income"
            },
            "roi_rates": {
                "12_months": f"{PaisaloBusinessRules.ROI_RATES[12]:.1%}",
                "24_months": f"{PaisaloBusinessRules.ROI_RATES[24]:.1%}",
                "36_months": f"{PaisaloBusinessRules.ROI_RATES[36]:.1%}",
                "48_months": f"{PaisaloBusinessRules.ROI_RATES[48]:.1%}",
                "description": "Interest rates by loan tenure using SLM method"
            },
            "pan_format": {
                "pattern": PaisaloBusinessRules.PAN_REGEX,
                "example": "ABCDE1234F",
                "description": "PAN must be in format: 5 letters + 4 digits + 1 letter"
            }
        }
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Paisalo Credit Assessment API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
