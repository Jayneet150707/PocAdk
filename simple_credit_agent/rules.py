"""
Simple Credit Assessment Business Rules

Streamlined business rules for demonstrating Google ADK
decision-making capabilities without complex validations.
"""

from decimal import Decimal
from typing import Tuple, Dict, Any
from .models import ApplicantInfo, LoanRequest, RiskFactors, RiskLevel


class SimpleCreditRules:
    """Simple credit assessment business rules."""
    
    # Basic thresholds
    MIN_AGE = 18
    MAX_AGE = 75
    MIN_CREDIT_SCORE = 580
    MIN_ANNUAL_INCOME = Decimal('30000')
    MAX_DEBT_TO_INCOME_RATIO = 0.40
    MIN_EMPLOYMENT_MONTHS = 6
    MAX_EXPENSE_TO_INCOME_RATIO = 0.60
    
    # Loan limits by credit score
    LOAN_LIMITS = {
        850: Decimal('500000'),  # Excellent
        800: Decimal('300000'),  # Very Good
        740: Decimal('200000'),  # Good
        670: Decimal('100000'),  # Fair
        580: Decimal('50000'),   # Poor
        300: Decimal('0')        # Very Poor
    }
    
    # Interest rates by credit score and risk level
    INTEREST_RATES = {
        RiskLevel.LOW: {
            'excellent': 0.045,  # 4.5%
            'very_good': 0.055,  # 5.5%
            'good': 0.065,       # 6.5%
            'fair': 0.085,       # 8.5%
        },
        RiskLevel.MEDIUM: {
            'excellent': 0.065,  # 6.5%
            'very_good': 0.075,  # 7.5%
            'good': 0.095,       # 9.5%
            'fair': 0.125,       # 12.5%
        },
        RiskLevel.HIGH: {
            'excellent': 0.095,  # 9.5%
            'very_good': 0.115,  # 11.5%
            'good': 0.145,       # 14.5%
            'fair': 0.185,       # 18.5%
        }
    }
    
    @classmethod
    def validate_age(cls, age: int) -> Tuple[bool, str]:
        """Validate applicant age."""
        if age < cls.MIN_AGE:
            return False, f"Applicant must be at least {cls.MIN_AGE} years old"
        if age > cls.MAX_AGE:
            return False, f"Applicant cannot be older than {cls.MAX_AGE} years"
        return True, "Age requirement met"
    
    @classmethod
    def validate_credit_score(cls, credit_score: int) -> Tuple[bool, str]:
        """Validate credit score."""
        if credit_score < cls.MIN_CREDIT_SCORE:
            return False, f"Credit score {credit_score} is below minimum requirement of {cls.MIN_CREDIT_SCORE}"
        return True, f"Credit score {credit_score} meets requirements"
    
    @classmethod
    def validate_income(cls, annual_income: Decimal, loan_amount: Decimal) -> Tuple[bool, str]:
        """Validate income requirements."""
        if annual_income < cls.MIN_ANNUAL_INCOME:
            return False, f"Annual income ${annual_income:,.2f} is below minimum of ${cls.MIN_ANNUAL_INCOME:,.2f}"
        
        # Income should be at least 3x the annual loan payment
        max_annual_payment = annual_income * Decimal('0.33')  # 33% of income
        estimated_annual_payment = loan_amount * Decimal('0.15')  # Rough estimate
        
        if estimated_annual_payment > max_annual_payment:
            return False, f"Loan amount too high relative to income. Maximum recommended: ${max_annual_payment / Decimal('0.15'):,.2f}"
        
        return True, "Income requirements met"
    
    @classmethod
    def calculate_debt_to_income_ratio(cls, applicant: ApplicantInfo, loan_amount: Decimal) -> float:
        """Calculate debt-to-income ratio including new loan."""
        monthly_income = applicant.annual_income / 12
        estimated_monthly_payment = loan_amount * Decimal('0.02')  # Rough 2% monthly payment
        total_monthly_debt = (applicant.existing_debt * Decimal('0.03')) + estimated_monthly_payment  # 3% of existing debt
        
        return float(total_monthly_debt / monthly_income)
    
    @classmethod
    def assess_risk_factors(cls, applicant: ApplicantInfo, loan_request: LoanRequest) -> RiskFactors:
        """Assess risk factors for the application."""
        risk_factors = RiskFactors()
        
        # High debt-to-income ratio
        dti_ratio = cls.calculate_debt_to_income_ratio(applicant, loan_request.amount)
        risk_factors.high_debt_to_income = dti_ratio > cls.MAX_DEBT_TO_INCOME_RATIO
        
        # Low credit score
        risk_factors.low_credit_score = applicant.credit_score < 650
        
        # Insufficient income
        monthly_income = applicant.annual_income / 12
        estimated_payment = loan_request.amount * Decimal('0.02')
        risk_factors.insufficient_income = estimated_payment > (monthly_income * Decimal('0.25'))
        
        # Short employment history
        risk_factors.short_employment = applicant.employment_duration_months < cls.MIN_EMPLOYMENT_MONTHS
        
        # High expenses
        monthly_income = applicant.annual_income / 12
        expense_ratio = applicant.monthly_expenses / monthly_income
        risk_factors.high_expenses = expense_ratio > cls.MAX_EXPENSE_TO_INCOME_RATIO
        
        return risk_factors
    
    @classmethod
    def get_credit_tier(cls, credit_score: int) -> str:
        """Get credit tier based on score."""
        if credit_score >= 800:
            return 'excellent'
        elif credit_score >= 740:
            return 'very_good'
        elif credit_score >= 670:
            return 'good'
        elif credit_score >= 580:
            return 'fair'
        else:
            return 'poor'
    
    @classmethod
    def get_max_loan_amount(cls, credit_score: int) -> Decimal:
        """Get maximum loan amount based on credit score."""
        for min_score, max_amount in sorted(cls.LOAN_LIMITS.items(), reverse=True):
            if credit_score >= min_score:
                return max_amount
        return Decimal('0')
    
    @classmethod
    def get_interest_rate(cls, credit_score: int, risk_level: RiskLevel) -> float:
        """Get recommended interest rate."""
        credit_tier = cls.get_credit_tier(credit_score)
        
        if risk_level in cls.INTEREST_RATES and credit_tier in cls.INTEREST_RATES[risk_level]:
            return cls.INTEREST_RATES[risk_level][credit_tier]
        
        # Fallback rates for high risk or poor credit
        if risk_level == RiskLevel.VERY_HIGH or credit_tier == 'poor':
            return 0.25  # 25% for very high risk
        
        return 0.15  # 15% default rate
    
    @classmethod
    def calculate_recommended_amount(cls, applicant: ApplicantInfo, requested_amount: Decimal) -> Decimal:
        """Calculate recommended loan amount."""
        max_by_credit = cls.get_max_loan_amount(applicant.credit_score)
        
        # Calculate based on income (max 3x annual income)
        max_by_income = applicant.annual_income * 3
        
        # Calculate based on debt-to-income ratio
        monthly_income = applicant.annual_income / 12
        available_monthly_payment = (monthly_income * Decimal('0.25')) - (applicant.existing_debt * Decimal('0.03'))
        max_by_dti = available_monthly_payment * 50  # Assuming 50-month average term
        
        # Take the minimum of all constraints
        recommended = min(requested_amount, max_by_credit, max_by_income, max_by_dti)
        
        # Ensure it's at least $1000 or $0
        if recommended < Decimal('1000'):
            return Decimal('0')
        
        return recommended
    
    @classmethod
    def should_approve(cls, applicant: ApplicantInfo, loan_request: LoanRequest, risk_factors: RiskFactors) -> Tuple[bool, str]:
        """Determine if application should be approved."""
        # Check basic eligibility
        age_valid, age_reason = cls.validate_age(applicant.age)
        if not age_valid:
            return False, age_reason
        
        credit_valid, credit_reason = cls.validate_credit_score(applicant.credit_score)
        if not credit_valid:
            return False, credit_reason
        
        income_valid, income_reason = cls.validate_income(applicant.annual_income, loan_request.amount)
        if not income_valid:
            return False, income_reason
        
        # Check risk level
        if risk_factors.risk_level == RiskLevel.VERY_HIGH:
            return False, f"Too many risk factors ({risk_factors.risk_count}). Application rejected."
        
        # Check if requested amount is within limits
        max_amount = cls.get_max_loan_amount(applicant.credit_score)
        if loan_request.amount > max_amount:
            return False, f"Requested amount ${loan_request.amount:,.2f} exceeds maximum of ${max_amount:,.2f} for credit score {applicant.credit_score}"
        
        return True, "Application meets all approval criteria"
    
    @classmethod
    def generate_recommendations(cls, applicant: ApplicantInfo, loan_request: LoanRequest, 
                               risk_factors: RiskFactors, approved: bool) -> list[str]:
        """Generate recommendations for the applicant."""
        recommendations = []
        
        if approved:
            recommendations.append("Congratulations! Your loan application has been approved.")
            
            if risk_factors.risk_count > 0:
                recommendations.append("Consider the following to improve your financial profile:")
                
                if risk_factors.high_debt_to_income:
                    recommendations.append("• Work on reducing existing debt to improve debt-to-income ratio")
                
                if risk_factors.low_credit_score:
                    recommendations.append("• Focus on improving credit score through timely payments")
                
                if risk_factors.high_expenses:
                    recommendations.append("• Review and optimize monthly expenses")
            
            recommendations.append("• Set up automatic payments to ensure timely loan repayment")
            recommendations.append("• Consider making extra payments to reduce total interest")
            
        else:
            recommendations.append("Your application was not approved at this time.")
            recommendations.append("Consider the following improvements:")
            
            if risk_factors.low_credit_score:
                recommendations.append("• Improve credit score by paying bills on time and reducing credit utilization")
            
            if risk_factors.insufficient_income:
                recommendations.append("• Increase income or consider a smaller loan amount")
            
            if risk_factors.high_debt_to_income:
                recommendations.append("• Pay down existing debt before applying for new credit")
            
            if risk_factors.short_employment:
                recommendations.append("• Build employment history (minimum 6 months recommended)")
            
            if risk_factors.high_expenses:
                recommendations.append("• Reduce monthly expenses to improve financial stability")
            
            recommendations.append("• Reapply after addressing these factors")
        
        return recommendations

