"""
Simple Credit Assessment API

Streamlined FastAPI application demonstrating Google ADK
credit assessment capabilities with clean, simple endpoints.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import our simple credit assessment components
from simple_credit_agent import (
    SimpleCreditAssessmentAgent,
    CreditApplication,
    ApplicantInfo,
    LoanRequest,
    AssessmentRequest,
    AssessmentResponse,
    HealthStatus,
    EmploymentStatus,
    LoanPurpose,
    SimpleCreditRules
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Simple Credit Assessment API",
    description="Streamlined credit assessment service using Google ADK",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
credit_agent: Optional[SimpleCreditAssessmentAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the application components."""
    global credit_agent
    
    logger.info("🚀 Starting Simple Credit Assessment API...")
    
    try:
        # Initialize credit assessment agent
        credit_agent = SimpleCreditAssessmentAgent()
        logger.info("✅ Simple Credit Assessment Agent initialized")
        
        # Test business rules
        test_validation = SimpleCreditRules.validate_age(25)
        if test_validation[0]:
            logger.info("✅ Business rules loaded successfully")
        
        logger.info("🎉 Simple Credit Assessment API started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    components = {
        "credit_agent": "available" if credit_agent else "unavailable",
        "business_rules": "available",
        "sub_agents": "available" if credit_agent else "unavailable"
    }
    
    return HealthStatus(
        status="healthy" if credit_agent else "degraded",
        components=components
    )


@app.post("/assess", response_model=AssessmentResponse)
async def assess_credit_application(request: AssessmentRequest):
    """
    Assess a credit application using Google ADK agents.
    
    This endpoint demonstrates:
    - Google ADK agent orchestration
    - Sub-agent coordination
    - Risk assessment and decision making
    - Transparent reasoning and recommendations
    """
    start_time = datetime.utcnow()
    
    try:
        if not credit_agent:
            raise HTTPException(status_code=500, detail="Credit assessment agent not available")
        
        logger.info(f"📋 Processing assessment for application {request.application.application_id}")
        
        # Perform assessment using Google ADK agent
        result = await credit_agent.assess_credit_application(request)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ Assessment completed: {'APPROVED' if result.approved else 'REJECTED'} "
                   f"in {processing_time:.3f}s")
        
        return AssessmentResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"❌ Assessment failed: {str(e)}")
        
        return AssessmentResponse(
            success=False,
            error=str(e),
            processing_time=processing_time
        )


@app.get("/sample")
async def get_sample_application():
    """Get a sample credit application for testing."""
    from simple_credit_agent.models import SAMPLE_APPLICATION
    
    return {
        "sample_application": {
            "application_id": SAMPLE_APPLICATION.application_id,
            "applicant": {
                "name": SAMPLE_APPLICATION.applicant.name,
                "age": SAMPLE_APPLICATION.applicant.age,
                "email": SAMPLE_APPLICATION.applicant.email,
                "phone": SAMPLE_APPLICATION.applicant.phone,
                "annual_income": float(SAMPLE_APPLICATION.applicant.annual_income),
                "monthly_expenses": float(SAMPLE_APPLICATION.applicant.monthly_expenses),
                "employment_status": SAMPLE_APPLICATION.applicant.employment_status.value,
                "employment_duration_months": SAMPLE_APPLICATION.applicant.employment_duration_months,
                "credit_score": SAMPLE_APPLICATION.applicant.credit_score,
                "existing_debt": float(SAMPLE_APPLICATION.applicant.existing_debt)
            },
            "loan_request": {
                "amount": float(SAMPLE_APPLICATION.loan_request.amount),
                "purpose": SAMPLE_APPLICATION.loan_request.purpose.value,
                "term_months": SAMPLE_APPLICATION.loan_request.term_months
            }
        }
    }


@app.get("/rules")
async def get_business_rules():
    """Get information about credit assessment business rules."""
    return {
        "business_rules": {
            "age_requirements": {
                "minimum": SimpleCreditRules.MIN_AGE,
                "maximum": SimpleCreditRules.MAX_AGE,
                "description": f"Applicant must be between {SimpleCreditRules.MIN_AGE}-{SimpleCreditRules.MAX_AGE} years old"
            },
            "credit_score": {
                "minimum": SimpleCreditRules.MIN_CREDIT_SCORE,
                "description": f"Minimum credit score of {SimpleCreditRules.MIN_CREDIT_SCORE} required"
            },
            "income_requirements": {
                "minimum": float(SimpleCreditRules.MIN_ANNUAL_INCOME),
                "description": f"Minimum annual income of ${SimpleCreditRules.MIN_ANNUAL_INCOME:,.2f} required"
            },
            "debt_to_income": {
                "maximum_ratio": SimpleCreditRules.MAX_DEBT_TO_INCOME_RATIO,
                "description": f"Debt-to-income ratio must not exceed {SimpleCreditRules.MAX_DEBT_TO_INCOME_RATIO:.1%}"
            },
            "employment": {
                "minimum_months": SimpleCreditRules.MIN_EMPLOYMENT_MONTHS,
                "description": f"Minimum {SimpleCreditRules.MIN_EMPLOYMENT_MONTHS} months employment history required"
            },
            "expense_ratio": {
                "maximum_ratio": SimpleCreditRules.MAX_EXPENSE_TO_INCOME_RATIO,
                "description": f"Monthly expenses must not exceed {SimpleCreditRules.MAX_EXPENSE_TO_INCOME_RATIO:.1%} of income"
            }
        },
        "loan_limits": {
            "by_credit_score": {str(k): float(v) for k, v in SimpleCreditRules.LOAN_LIMITS.items()},
            "description": "Maximum loan amounts based on credit score tiers"
        }
    }


@app.get("/agent-status")
async def get_agent_status():
    """Get detailed agent status and capabilities."""
    if not credit_agent:
        raise HTTPException(status_code=503, detail="Credit agent not available")
    
    return credit_agent.get_agent_status()


@app.post("/scenarios")
async def analyze_scenarios(application: CreditApplication):
    """
    Analyze alternative loan scenarios for an application.
    
    This demonstrates advanced Google ADK capabilities for
    scenario analysis and recommendation generation.
    """
    if not credit_agent:
        raise HTTPException(status_code=503, detail="Credit agent not available")
    
    try:
        logger.info(f"🔍 Analyzing scenarios for application {application.application_id}")
        
        scenarios = credit_agent.analyze_scenarios(application)
        
        return {
            "application_id": application.application_id,
            "scenarios": scenarios,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Scenario analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_processing_metrics():
    """Get agent processing metrics and performance data."""
    if not credit_agent:
        raise HTTPException(status_code=503, detail="Credit agent not available")
    
    return credit_agent.get_processing_metrics()


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
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
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Simple Credit Assessment API server...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8001,  # Different port from the complex version
        reload=True,
        log_level="info"
    )

