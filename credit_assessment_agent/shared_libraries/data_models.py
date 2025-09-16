"""
Data models for the Credit Assessment Agent system.

This module defines Pydantic models for all data structures used throughout
the credit assessment process.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class EmploymentStatus(str, Enum):
    """Employment status enumeration."""
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"
    STUDENT = "student"


class LoanPurpose(str, Enum):
    """Loan purpose enumeration."""
    HOME_PURCHASE = "home_purchase"
    HOME_IMPROVEMENT = "home_improvement"
    DEBT_CONSOLIDATION = "debt_consolidation"
    AUTO_LOAN = "auto_loan"
    BUSINESS = "business"
    EDUCATION = "education"
    PERSONAL = "personal"
    OTHER = "other"


class TransactionType(str, Enum):
    """Bank transaction type enumeration."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    FEE = "fee"
    INTEREST = "interest"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ApplicantInfo(BaseModel):
    """Applicant personal information."""
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=18, le=100)
    income: Decimal = Field(..., ge=0)
    employment_status: EmploymentStatus
    employment_duration_months: Optional[int] = Field(None, ge=0)
    address: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    @validator('income')
    def validate_income(cls, v: Decimal) -> Decimal:
        """Validate income is reasonable."""
        if v > Decimal('10000000'):  # 10M limit
            raise ValueError('Income exceeds reasonable limit')
        return v


class CreditApplication(BaseModel):
    """Complete credit application data."""
    application_id: str = Field(..., min_length=1)
    applicant_info: ApplicantInfo
    credit_score: int = Field(..., ge=300, le=850)
    loan_amount: Decimal = Field(..., ge=1000)
    loan_purpose: LoanPurpose
    requested_term_months: int = Field(..., ge=6, le=360)
    down_payment: Optional[Decimal] = Field(None, ge=0)
    existing_debt: Optional[Decimal] = Field(None, ge=0)
    assets: Optional[Decimal] = Field(None, ge=0)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('loan_amount')
    def validate_loan_amount(cls, v: Decimal) -> Decimal:
        """Validate loan amount is reasonable."""
        if v > Decimal('5000000'):  # 5M limit
            raise ValueError('Loan amount exceeds limit')
        return v


class BankTransaction(BaseModel):
    """Individual bank transaction."""
    transaction_id: str
    date: date
    description: str = Field(..., max_length=200)
    amount: Decimal
    transaction_type: TransactionType
    balance: Optional[Decimal] = None
    category: Optional[str] = Field(None, max_length=50)
    
    @validator('amount')
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount is not zero."""
        if v == 0:
            raise ValueError('Transaction amount cannot be zero')
        return v


class TransactionSummary(BaseModel):
    """Summary of bank transactions analysis."""
    total_transactions: int = Field(..., ge=0)
    total_credits: Decimal = Field(..., ge=0)
    total_debits: Decimal = Field(..., ge=0)
    average_monthly_income: Decimal = Field(..., ge=0)
    average_monthly_expenses: Decimal = Field(..., ge=0)
    income_stability_score: float = Field(..., ge=0.0, le=1.0)
    expense_patterns: Dict[str, Decimal] = Field(default_factory=dict)
    overdraft_incidents: int = Field(..., ge=0)
    large_transactions_count: int = Field(..., ge=0)
    analysis_period_months: int = Field(..., ge=1)


class ConfidenceScore(BaseModel):
    """Confidence score breakdown."""
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    credit_score_confidence: float = Field(..., ge=0.0, le=1.0)
    income_confidence: float = Field(..., ge=0.0, le=1.0)
    transaction_confidence: float = Field(..., ge=0.0, le=1.0)
    application_confidence: float = Field(..., ge=0.0, le=1.0)
    data_quality_score: float = Field(..., ge=0.0, le=1.0)


class RiskFactors(BaseModel):
    """Identified risk factors."""
    high_debt_to_income: bool = False
    insufficient_income: bool = False
    poor_credit_history: bool = False
    irregular_income: bool = False
    excessive_expenses: bool = False
    frequent_overdrafts: bool = False
    short_employment_history: bool = False
    high_loan_to_value: bool = False
    risk_factors_count: int = Field(..., ge=0)
    risk_level: RiskLevel


class CreditAssessmentResult(BaseModel):
    """Complete credit assessment result."""
    application_id: str
    assessment_id: str = Field(..., min_length=1)
    approved: bool
    risk_level: RiskLevel
    recommended_loan_amount: Optional[Decimal] = None
    recommended_interest_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_scores: ConfidenceScore
    risk_factors: RiskFactors
    transaction_summary: Optional[TransactionSummary] = None
    reasoning: str = Field(..., min_length=10)
    recommendations: List[str] = Field(default_factory=list)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: Optional[float] = Field(None, ge=0.0)
    
    @validator('recommended_interest_rate')
    def validate_interest_rate(cls, v: Optional[float]) -> Optional[float]:
        """Validate interest rate is reasonable."""
        if v is not None and v > 0.5:  # 50% max
            raise ValueError('Interest rate exceeds reasonable limit')
        return v


class AgentResponse(BaseModel):
    """Base response from any agent."""
    agent_name: str
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AssessmentRequest(BaseModel):
    """Request for credit assessment."""
    credit_application: CreditApplication
    bank_statement_data: Optional[List[BankTransaction]] = None
    additional_documents: Optional[List[str]] = None
    priority: str = Field(default="normal", pattern=r'^(low|normal|high|urgent)$')
    callback_url: Optional[str] = None
