"""
Simplified Credit Assessment Data Models

Clean, streamlined data models for demonstrating Google ADK
credit assessment capabilities without complex business rules.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class EmploymentStatus(str, Enum):
    """Employment status options."""
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"


class LoanPurpose(str, Enum):
    """Loan purpose categories."""
    PERSONAL = "personal"
    HOME = "home"
    AUTO = "auto"
    BUSINESS = "business"
    EDUCATION = "education"
    MEDICAL = "medical"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ApplicantInfo(BaseModel):
    """Basic applicant information."""
    name: str = Field(..., description="Full name of the applicant")
    age: int = Field(..., ge=18, le=80, description="Age in years")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    
    # Financial information
    annual_income: Decimal = Field(..., ge=0, description="Annual income in USD")
    monthly_expenses: Decimal = Field(..., ge=0, description="Monthly expenses in USD")
    employment_status: EmploymentStatus = Field(..., description="Current employment status")
    employment_duration_months: int = Field(..., ge=0, description="Months in current job")
    
    # Credit information
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (300-850)")
    existing_debt: Decimal = Field(default=Decimal('0'), ge=0, description="Total existing debt")
    
    @validator('monthly_expenses')
    def validate_expenses(cls, v, values):
        """Ensure monthly expenses are reasonable compared to income."""
        if 'annual_income' in values:
            monthly_income = values['annual_income'] / 12
            if v > monthly_income * Decimal('1.2'):  # Allow 20% buffer
                raise ValueError("Monthly expenses cannot exceed 120% of monthly income")
        return v


class LoanRequest(BaseModel):
    """Loan request details."""
    amount: Decimal = Field(..., ge=1000, le=500000, description="Requested loan amount")
    purpose: LoanPurpose = Field(..., description="Purpose of the loan")
    term_months: int = Field(..., ge=6, le=360, description="Loan term in months")
    
    @validator('term_months')
    def validate_term(cls, v, values):
        """Validate loan term based on amount."""
        if 'amount' in values:
            amount = values['amount']
            # Larger loans can have longer terms
            max_term = min(360, int(amount / 1000) * 6 + 60)  # Dynamic max term
            if v > max_term:
                raise ValueError(f"Maximum term for ${amount:,.2f} is {max_term} months")
        return v


class CreditApplication(BaseModel):
    """Complete credit application."""
    application_id: str = Field(..., description="Unique application identifier")
    applicant: ApplicantInfo = Field(..., description="Applicant information")
    loan_request: LoanRequest = Field(..., description="Loan request details")
    submitted_at: datetime = Field(default_factory=datetime.utcnow, description="Submission timestamp")


class ConfidenceScores(BaseModel):
    """Confidence metrics for assessment."""
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall assessment confidence")
    income_confidence: float = Field(..., ge=0, le=1, description="Income verification confidence")
    credit_confidence: float = Field(..., ge=0, le=1, description="Credit history confidence")
    employment_confidence: float = Field(..., ge=0, le=1, description="Employment stability confidence")


class RiskFactors(BaseModel):
    """Risk assessment factors."""
    high_debt_to_income: bool = Field(default=False, description="Debt-to-income ratio too high")
    low_credit_score: bool = Field(default=False, description="Credit score below threshold")
    insufficient_income: bool = Field(default=False, description="Income too low for loan amount")
    short_employment: bool = Field(default=False, description="Employment history too short")
    high_expenses: bool = Field(default=False, description="Monthly expenses too high")
    
    @property
    def risk_count(self) -> int:
        """Count of active risk factors."""
        return sum([
            self.high_debt_to_income,
            self.low_credit_score,
            self.insufficient_income,
            self.short_employment,
            self.high_expenses
        ])
    
    @property
    def risk_level(self) -> RiskLevel:
        """Determine risk level based on factor count."""
        count = self.risk_count
        if count == 0:
            return RiskLevel.LOW
        elif count <= 2:
            return RiskLevel.MEDIUM
        elif count <= 3:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH


class AssessmentResult(BaseModel):
    """Credit assessment result."""
    application_id: str = Field(..., description="Application identifier")
    assessment_id: str = Field(..., description="Unique assessment identifier")
    
    # Decision
    approved: bool = Field(..., description="Approval decision")
    risk_level: RiskLevel = Field(..., description="Assessed risk level")
    
    # Recommendations
    recommended_amount: Optional[Decimal] = Field(None, description="Recommended loan amount")
    recommended_rate: Optional[float] = Field(None, description="Recommended interest rate")
    recommended_term: Optional[int] = Field(None, description="Recommended term in months")
    
    # Analysis
    confidence_scores: ConfidenceScores = Field(..., description="Confidence metrics")
    risk_factors: RiskFactors = Field(..., description="Identified risk factors")
    
    # Reasoning
    reasoning: str = Field(..., description="Detailed reasoning for decision")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for applicant")
    
    # Metadata
    assessed_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment timestamp")
    processing_time_seconds: float = Field(..., description="Processing time")


class AssessmentRequest(BaseModel):
    """API request for credit assessment."""
    application: CreditApplication = Field(..., description="Credit application to assess")
    priority: str = Field(default="normal", description="Processing priority")


class AssessmentResponse(BaseModel):
    """API response for credit assessment."""
    success: bool = Field(..., description="Request success status")
    result: Optional[AssessmentResult] = Field(None, description="Assessment result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Total processing time")


class HealthStatus(BaseModel):
    """System health status."""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")
    components: Dict[str, str] = Field(default_factory=dict, description="Component statuses")
    version: str = Field(default="1.0.0", description="System version")


# Sample data for testing
SAMPLE_APPLICANT = ApplicantInfo(
    name="John Smith",
    age=32,
    email="john.smith@example.com",
    phone="+1-555-0123",
    annual_income=Decimal('75000'),
    monthly_expenses=Decimal('3500'),
    employment_status=EmploymentStatus.EMPLOYED,
    employment_duration_months=36,
    credit_score=720,
    existing_debt=Decimal('15000')
)

SAMPLE_LOAN_REQUEST = LoanRequest(
    amount=Decimal('25000'),
    purpose=LoanPurpose.PERSONAL,
    term_months=60
)

SAMPLE_APPLICATION = CreditApplication(
    application_id="SIMPLE_001",
    applicant=SAMPLE_APPLICANT,
    loan_request=SAMPLE_LOAN_REQUEST
)

