"""
Utility functions for the Credit Assessment Agent system.

This module contains common helper functions used across the application.
"""

import re
import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import hashlib
import uuid

from .data_models import (
    CreditApplication,
    BankTransaction,
    TransactionSummary,
    ConfidenceScore,
    RiskLevel
)

logger = logging.getLogger(__name__)


def calculate_confidence_score(
    credit_score: int,
    income: Decimal,
    transaction_summary: Optional[TransactionSummary] = None,
    employment_months: Optional[int] = None,
    data_completeness: float = 1.0
) -> ConfidenceScore:
    """
    Calculate confidence scores for different assessment components.
    
    Args:
        credit_score: Applicant's credit score
        income: Applicant's annual income
        transaction_summary: Bank transaction analysis
        employment_months: Employment duration in months
        data_completeness: Completeness of provided data (0-1)
        
    Returns:
        ConfidenceScore object with component scores
    """
    try:
        # Credit score confidence (based on score range and validity)
        credit_confidence = _calculate_credit_score_confidence(credit_score)
        
        # Income confidence (based on amount and employment duration)
        income_confidence = _calculate_income_confidence(income, employment_months)
        
        # Transaction confidence (based on transaction data quality)
        transaction_confidence = _calculate_transaction_confidence(transaction_summary)
        
        # Application confidence (based on data completeness)
        application_confidence = min(1.0, data_completeness * 0.9 + 0.1)
        
        # Overall confidence (weighted average)
        weights = {
            'credit': 0.3,
            'income': 0.25,
            'transaction': 0.25,
            'application': 0.2
        }
        
        overall_confidence = (
            credit_confidence * weights['credit'] +
            income_confidence * weights['income'] +
            transaction_confidence * weights['transaction'] +
            application_confidence * weights['application']
        )
        
        return ConfidenceScore(
            overall_confidence=overall_confidence,
            credit_score_confidence=credit_confidence,
            income_confidence=income_confidence,
            transaction_confidence=transaction_confidence,
            application_confidence=application_confidence,
            data_quality_score=data_completeness
        )
        
    except Exception as e:
        logger.error(f"Failed to calculate confidence scores: {str(e)}")
        # Return low confidence scores on error
        return ConfidenceScore(
            overall_confidence=0.3,
            credit_score_confidence=0.3,
            income_confidence=0.3,
            transaction_confidence=0.3,
            application_confidence=0.3,
            data_quality_score=0.3
        )


def _calculate_credit_score_confidence(credit_score: int) -> float:
    """Calculate confidence based on credit score."""
    if credit_score >= 750:
        return 0.95
    elif credit_score >= 700:
        return 0.85
    elif credit_score >= 650:
        return 0.70
    elif credit_score >= 600:
        return 0.55
    elif credit_score >= 550:
        return 0.40
    else:
        return 0.25


def _calculate_income_confidence(
    income: Decimal, 
    employment_months: Optional[int]
) -> float:
    """Calculate confidence based on income and employment duration."""
    base_confidence = 0.5
    
    # Income level factor
    if income >= Decimal('100000'):
        income_factor = 0.4
    elif income >= Decimal('75000'):
        income_factor = 0.3
    elif income >= Decimal('50000'):
        income_factor = 0.2
    elif income >= Decimal('30000'):
        income_factor = 0.1
    else:
        income_factor = 0.0
    
    # Employment duration factor
    if employment_months is None:
        employment_factor = 0.0
    elif employment_months >= 24:
        employment_factor = 0.1
    elif employment_months >= 12:
        employment_factor = 0.05
    else:
        employment_factor = 0.0
    
    return min(1.0, base_confidence + income_factor + employment_factor)


def _calculate_transaction_confidence(
    transaction_summary: Optional[TransactionSummary]
) -> float:
    """Calculate confidence based on transaction data quality."""
    if not transaction_summary:
        return 0.3  # Low confidence without transaction data
    
    base_confidence = 0.5
    
    # Transaction count factor
    if transaction_summary.total_transactions >= 100:
        count_factor = 0.2
    elif transaction_summary.total_transactions >= 50:
        count_factor = 0.15
    elif transaction_summary.total_transactions >= 20:
        count_factor = 0.1
    else:
        count_factor = 0.05
    
    # Analysis period factor
    if transaction_summary.analysis_period_months >= 6:
        period_factor = 0.2
    elif transaction_summary.analysis_period_months >= 3:
        period_factor = 0.15
    else:
        period_factor = 0.1
    
    # Income stability factor
    stability_factor = transaction_summary.income_stability_score * 0.1
    
    return min(1.0, base_confidence + count_factor + period_factor + stability_factor)


def validate_credit_score(credit_score: int) -> bool:
    """
    Validate if credit score is within acceptable range.
    
    Args:
        credit_score: Credit score to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 300 <= credit_score <= 850


def normalize_income(income: Decimal) -> Decimal:
    """
    Normalize income to annual amount.
    
    Args:
        income: Income amount (could be monthly, annual, etc.)
        
    Returns:
        Normalized annual income
    """
    try:
        # If income seems to be monthly (< 10k), convert to annual
        if income < Decimal('10000'):
            return income * 12
        
        # If income seems to be weekly (< 2k), convert to annual
        if income < Decimal('2000'):
            return income * 52
        
        # Otherwise assume it's already annual
        return income
        
    except Exception as e:
        logger.error(f"Failed to normalize income: {str(e)}")
        return income


def extract_financial_metrics(
    application: CreditApplication,
    transaction_summary: Optional[TransactionSummary] = None
) -> Dict[str, Any]:
    """
    Extract key financial metrics from application and transaction data.
    
    Args:
        application: Credit application data
        transaction_summary: Optional transaction summary
        
    Returns:
        Dictionary of financial metrics
    """
    try:
        metrics = {}
        
        # Basic application metrics
        annual_income = normalize_income(application.applicant_info.income)
        monthly_income = annual_income / 12
        
        # Calculate debt-to-income ratio
        total_debt = application.existing_debt or Decimal('0')
        monthly_payment = calculate_monthly_payment(
            application.loan_amount,
            application.requested_term_months,
            estimate_interest_rate(application.credit_score)
        )
        
        monthly_debt_payments = total_debt / 12 + monthly_payment  # Simplified
        debt_to_income_ratio = float(monthly_debt_payments / monthly_income)
        
        # Loan-to-income ratio
        loan_to_income_ratio = float(application.loan_amount / annual_income)
        
        metrics.update({
            'annual_income': float(annual_income),
            'monthly_income': float(monthly_income),
            'debt_to_income_ratio': debt_to_income_ratio,
            'loan_to_income_ratio': loan_to_income_ratio,
            'monthly_payment': float(monthly_payment),
            'credit_score_tier': get_credit_score_tier(application.credit_score),
            'loan_amount': float(application.loan_amount),
            'requested_term_months': application.requested_term_months
        })
        
        # Add transaction-based metrics if available
        if transaction_summary:
            metrics.update({
                'transaction_monthly_income': float(transaction_summary.average_monthly_income),
                'transaction_monthly_expenses': float(transaction_summary.average_monthly_expenses),
                'income_stability_score': transaction_summary.income_stability_score,
                'overdraft_incidents': transaction_summary.overdraft_incidents,
                'transaction_analysis_months': transaction_summary.analysis_period_months,
                'expense_to_income_ratio': float(
                    transaction_summary.average_monthly_expenses / 
                    max(transaction_summary.average_monthly_income, Decimal('1'))
                )
            })
            
            # Income consistency check
            income_difference = abs(
                float(monthly_income) - float(transaction_summary.average_monthly_income)
            )
            income_consistency = 1.0 - min(1.0, income_difference / float(monthly_income))
            metrics['income_consistency'] = income_consistency
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to extract financial metrics: {str(e)}")
        return {}


def calculate_monthly_payment(
    loan_amount: Decimal,
    term_months: int,
    annual_interest_rate: float
) -> Decimal:
    """
    Calculate monthly loan payment.
    
    Args:
        loan_amount: Principal loan amount
        term_months: Loan term in months
        annual_interest_rate: Annual interest rate (as decimal)
        
    Returns:
        Monthly payment amount
    """
    try:
        if annual_interest_rate == 0:
            return loan_amount / term_months
        
        monthly_rate = annual_interest_rate / 12
        payment = loan_amount * (
            monthly_rate * (1 + monthly_rate) ** term_months
        ) / ((1 + monthly_rate) ** term_months - 1)
        
        return payment
        
    except Exception as e:
        logger.error(f"Failed to calculate monthly payment: {str(e)}")
        return loan_amount / term_months  # Fallback to simple division


def estimate_interest_rate(credit_score: int) -> float:
    """
    Estimate interest rate based on credit score.
    
    Args:
        credit_score: Applicant's credit score
        
    Returns:
        Estimated annual interest rate (as decimal)
    """
    if credit_score >= 750:
        return 0.035  # 3.5%
    elif credit_score >= 700:
        return 0.055  # 5.5%
    elif credit_score >= 650:
        return 0.085  # 8.5%
    elif credit_score >= 600:
        return 0.125  # 12.5%
    elif credit_score >= 550:
        return 0.165  # 16.5%
    else:
        return 0.225  # 22.5%


def get_credit_score_tier(credit_score: int) -> str:
    """
    Get credit score tier description.
    
    Args:
        credit_score: Credit score
        
    Returns:
        Credit score tier string
    """
    if credit_score >= 750:
        return "excellent"
    elif credit_score >= 700:
        return "good"
    elif credit_score >= 650:
        return "fair"
    elif credit_score >= 600:
        return "poor"
    else:
        return "very_poor"


def generate_application_id() -> str:
    """Generate a unique application ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:8]
    return f"APP_{timestamp}_{random_suffix}"


def generate_assessment_id(application_id: str) -> str:
    """Generate a unique assessment ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    hash_suffix = hashlib.md5(application_id.encode()).hexdigest()[:8]
    return f"ASSESS_{timestamp}_{hash_suffix}"


def sanitize_text(text: str, max_length: int = 200) -> str:
    """
    Sanitize and truncate text input.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())
    
    # Truncate if necessary
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized


def format_currency(amount: Decimal) -> str:
    """Format decimal amount as currency string."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format float as percentage string."""
    return f"{value:.1%}"


def calculate_risk_score(
    credit_score: int,
    debt_to_income_ratio: float,
    income_stability: float = 1.0,
    overdraft_count: int = 0
) -> Tuple[float, RiskLevel]:
    """
    Calculate overall risk score and level.
    
    Args:
        credit_score: Credit score
        debt_to_income_ratio: Debt-to-income ratio
        income_stability: Income stability score (0-1)
        overdraft_count: Number of overdraft incidents
        
    Returns:
        Tuple of (risk_score, risk_level)
    """
    try:
        # Credit score component (0-1, lower is better)
        if credit_score >= 750:
            credit_risk = 0.1
        elif credit_score >= 700:
            credit_risk = 0.2
        elif credit_score >= 650:
            credit_risk = 0.4
        elif credit_score >= 600:
            credit_risk = 0.6
        else:
            credit_risk = 0.8
        
        # Debt-to-income component (0-1, lower is better)
        if debt_to_income_ratio <= 0.2:
            dti_risk = 0.1
        elif debt_to_income_ratio <= 0.36:
            dti_risk = 0.3
        elif debt_to_income_ratio <= 0.5:
            dti_risk = 0.6
        else:
            dti_risk = 0.9
        
        # Income stability component (0-1, lower is better)
        stability_risk = 1.0 - income_stability
        
        # Overdraft component (0-1, lower is better)
        overdraft_risk = min(1.0, overdraft_count * 0.1)
        
        # Weighted risk score
        risk_score = (
            credit_risk * 0.4 +
            dti_risk * 0.3 +
            stability_risk * 0.2 +
            overdraft_risk * 0.1
        )
        
        # Determine risk level
        if risk_score <= 0.25:
            risk_level = RiskLevel.LOW
        elif risk_score <= 0.5:
            risk_level = RiskLevel.MEDIUM
        elif risk_score <= 0.75:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        return risk_score, risk_level
        
    except Exception as e:
        logger.error(f"Failed to calculate risk score: {str(e)}")
        return 0.8, RiskLevel.HIGH  # Conservative fallback


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15


def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging/display.
    
    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to leave visible at the end
        
    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]
