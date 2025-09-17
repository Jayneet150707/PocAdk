"""
Paisalo-specific business rules for credit assessment.

This module implements all the business logic specific to Paisalo's
credit assessment requirements and policies.
"""

import re
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from .data_models import CreditApplication, DocumentType, RiskLevel
import logging

logger = logging.getLogger(__name__)


class PaisaloBusinessRules:
    """Paisalo-specific business rules implementation."""
    
    # Paisalo ROI rates by tenure (SLM method)
    ROI_RATES = {
        12: 0.07,   # 7% for 12 months
        24: 0.09,   # 9% for 24 months
        36: 0.12,   # 12% for 36 months
        48: 0.18,   # 18% for 48 months
    }
    
    # Age limits
    MIN_AGE = 21
    MAX_AGE = 57
    
    # Credit score limits
    MIN_CREDIT_SCORE = 18
    MAX_CREDIT_SCORE = 650
    
    # Loan amount limits
    MIN_LOAN_AMOUNT = Decimal('50000')
    MAX_LOAN_AMOUNT = Decimal('100000')
    
    # Expense to income ratio limit
    MAX_EXPENSE_RATIO = 0.50  # 50%
    
    # PAN validation regex
    PAN_REGEX = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    
    @classmethod
    def validate_age(cls, age: int) -> Tuple[bool, str]:
        """
        Validate applicant age according to Paisalo rules.
        
        Args:
            age: Applicant's age
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if cls.MIN_AGE <= age <= cls.MAX_AGE:
            return True, f"Age {age} is within acceptable range ({cls.MIN_AGE}-{cls.MAX_AGE})"
        else:
            return False, f"Age {age} is outside acceptable range ({cls.MIN_AGE}-{cls.MAX_AGE}). Application rejected."
    
    @classmethod
    def validate_credit_score(cls, credit_score: int) -> Tuple[bool, str]:
        """
        Validate credit score according to Paisalo rules.
        
        Args:
            credit_score: Applicant's credit score
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if cls.MIN_CREDIT_SCORE <= credit_score <= cls.MAX_CREDIT_SCORE:
            return True, f"Credit score {credit_score} is within acceptable range ({cls.MIN_CREDIT_SCORE}-{cls.MAX_CREDIT_SCORE})"
        else:
            return False, f"Credit score {credit_score} is outside acceptable range ({cls.MIN_CREDIT_SCORE}-{cls.MAX_CREDIT_SCORE}). Application rejected."
    
    @classmethod
    def validate_loan_amount(cls, loan_amount: Decimal) -> Tuple[bool, str]:
        """
        Validate loan amount according to Paisalo rules.
        
        Args:
            loan_amount: Requested loan amount
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if cls.MIN_LOAN_AMOUNT <= loan_amount <= cls.MAX_LOAN_AMOUNT:
            return True, f"Loan amount ₹{loan_amount:,.2f} is within acceptable range (₹{cls.MIN_LOAN_AMOUNT:,.2f}-₹{cls.MAX_LOAN_AMOUNT:,.2f})"
        else:
            return False, f"Loan amount ₹{loan_amount:,.2f} is outside acceptable range (₹{cls.MIN_LOAN_AMOUNT:,.2f}-₹{cls.MAX_LOAN_AMOUNT:,.2f}). Application rejected."
    
    @classmethod
    def validate_pan_number(cls, pan_number: Optional[str]) -> Tuple[bool, str]:
        """
        Validate PAN number format using regex.
        
        Args:
            pan_number: PAN card number
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if not pan_number:
            return False, "PAN number is required for loan application"
        
        if re.match(cls.PAN_REGEX, pan_number.upper()):
            return True, f"PAN number {pan_number} is valid"
        else:
            return False, f"PAN number {pan_number} is invalid. Expected format: ABCDE1234F"
    
    @classmethod
    def validate_documents(cls, application: CreditApplication) -> Tuple[bool, str]:
        """
        Validate document requirements according to Paisalo rules.
        Required: (Voter ID + PAN) OR (PAN + Driving License)
        
        Args:
            application: Credit application data
            
        Returns:
            Tuple of (is_valid, reason)
        """
        applicant = application.applicant_info
        documents = set(applicant.documents_provided)
        
        # Check if PAN is provided and valid
        pan_valid, pan_reason = cls.validate_pan_number(applicant.pan_number)
        if not pan_valid:
            return False, pan_reason
        
        # Check valid document combinations
        has_voter_and_pan = (
            DocumentType.VOTER_ID in documents and 
            DocumentType.PAN in documents and
            applicant.has_voter_id
        )
        
        has_dl_and_pan = (
            DocumentType.DRIVING_LICENSE in documents and 
            DocumentType.PAN in documents and
            applicant.has_driving_license
        )
        
        if has_voter_and_pan:
            return True, "Valid document combination: Voter ID + PAN"
        elif has_dl_and_pan:
            return True, "Valid document combination: Driving License + PAN"
        else:
            return False, "Invalid document combination. Required: (Voter ID + PAN) OR (Driving License + PAN)"
    
    @classmethod
    def validate_income_expense_ratio(cls, application: CreditApplication) -> Tuple[bool, str]:
        """
        Validate that expenses don't exceed 50% of income.
        
        Args:
            application: Credit application data
            
        Returns:
            Tuple of (is_valid, reason)
        """
        applicant = application.applicant_info
        
        # Calculate total income
        total_income = applicant.income
        if applicant.family_income:
            total_income += applicant.family_income
        
        # Calculate total expenses
        total_expenses = Decimal('0')
        if applicant.personal_expenses:
            total_expenses += applicant.personal_expenses
        if applicant.family_expenses:
            total_expenses += applicant.family_expenses
        
        if total_income <= 0:
            return False, "Total income must be greater than zero"
        
        expense_ratio = float(total_expenses / total_income)
        
        if expense_ratio <= cls.MAX_EXPENSE_RATIO:
            return True, f"Expense ratio {expense_ratio:.1%} is within acceptable limit ({cls.MAX_EXPENSE_RATIO:.0%})"
        else:
            return False, f"Expense ratio {expense_ratio:.1%} exceeds maximum limit ({cls.MAX_EXPENSE_RATIO:.0%}). Application rejected."
    
    @classmethod
    def calculate_emi_slm(cls, loan_amount: Decimal, term_months: int) -> Tuple[Decimal, float]:
        """
        Calculate EMI using SLM (Straight Line Method) with Paisalo's ROI rates.
        
        Args:
            loan_amount: Principal loan amount
            term_months: Loan term in months
            
        Returns:
            Tuple of (monthly_emi, annual_roi)
        """
        if term_months not in cls.ROI_RATES:
            raise ValueError(f"Invalid term. Allowed terms: {list(cls.ROI_RATES.keys())}")
        
        annual_roi = cls.ROI_RATES[term_months]
        
        # SLM calculation: EMI = (Principal + (Principal * ROI * Years)) / Total Months
        years = Decimal(term_months) / 12
        total_interest = loan_amount * Decimal(str(annual_roi)) * years
        total_amount = loan_amount + total_interest
        monthly_emi = total_amount / term_months
        
        return monthly_emi, annual_roi
    
    @classmethod
    def perform_complete_validation(cls, application: CreditApplication) -> Dict[str, any]:
        """
        Perform complete Paisalo business rules validation.
        
        Args:
            application: Credit application data
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'rejection_reasons': [],
            'warnings': [],
            'validations': {},
            'emi_details': None,
            'risk_level': RiskLevel.LOW
        }
        
        # Age validation
        age_valid, age_reason = cls.validate_age(application.applicant_info.age)
        results['validations']['age'] = {'valid': age_valid, 'reason': age_reason}
        if not age_valid:
            results['is_valid'] = False
            results['rejection_reasons'].append(age_reason)
        
        # Credit score validation
        score_valid, score_reason = cls.validate_credit_score(application.credit_score)
        results['validations']['credit_score'] = {'valid': score_valid, 'reason': score_reason}
        if not score_valid:
            results['is_valid'] = False
            results['rejection_reasons'].append(score_reason)
        
        # Loan amount validation
        amount_valid, amount_reason = cls.validate_loan_amount(application.loan_amount)
        results['validations']['loan_amount'] = {'valid': amount_valid, 'reason': amount_reason}
        if not amount_valid:
            results['is_valid'] = False
            results['rejection_reasons'].append(amount_reason)
        
        # Document validation
        doc_valid, doc_reason = cls.validate_documents(application)
        results['validations']['documents'] = {'valid': doc_valid, 'reason': doc_reason}
        if not doc_valid:
            results['is_valid'] = False
            results['rejection_reasons'].append(doc_reason)
        
        # Income/Expense ratio validation
        ratio_valid, ratio_reason = cls.validate_income_expense_ratio(application)
        results['validations']['income_expense_ratio'] = {'valid': ratio_valid, 'reason': ratio_reason}
        if not ratio_valid:
            results['is_valid'] = False
            results['rejection_reasons'].append(ratio_reason)
        
        # Calculate EMI if basic validations pass
        if results['is_valid']:
            try:
                monthly_emi, annual_roi = cls.calculate_emi_slm(
                    application.loan_amount, 
                    application.requested_term_months
                )
                results['emi_details'] = {
                    'monthly_emi': monthly_emi,
                    'annual_roi': annual_roi,
                    'total_interest': monthly_emi * application.requested_term_months - application.loan_amount,
                    'total_amount': monthly_emi * application.requested_term_months,
                    'calculation_method': 'SLM (Straight Line Method)'
                }
            except Exception as e:
                logger.error(f"EMI calculation failed: {e}")
                results['warnings'].append(f"EMI calculation failed: {e}")
        
        # Determine risk level based on various factors
        risk_factors = 0
        
        # Age-based risk
        if application.applicant_info.age < 25 or application.applicant_info.age > 50:
            risk_factors += 1
        
        # Credit score-based risk
        if application.credit_score < 100:
            risk_factors += 2
        elif application.credit_score < 300:
            risk_factors += 1
        
        # Income-based risk
        if application.applicant_info.income < Decimal('30000'):
            risk_factors += 1
        
        # Determine risk level
        if risk_factors == 0:
            results['risk_level'] = RiskLevel.LOW
        elif risk_factors <= 2:
            results['risk_level'] = RiskLevel.MEDIUM
        elif risk_factors <= 3:
            results['risk_level'] = RiskLevel.HIGH
        else:
            results['risk_level'] = RiskLevel.VERY_HIGH
        
        return results
    
    @classmethod
    def generate_paisalo_assessment_summary(cls, application: CreditApplication, validation_results: Dict) -> str:
        """
        Generate a comprehensive assessment summary for Paisalo.
        
        Args:
            application: Credit application data
            validation_results: Results from complete validation
            
        Returns:
            Formatted assessment summary string
        """
        summary_lines = [
            "=== PAISALO CREDIT ASSESSMENT SUMMARY ===",
            f"Application ID: {application.application_id}",
            f"Applicant: {application.applicant_info.name}",
            f"Loan Amount: ₹{application.loan_amount:,.2f}",
            f"Term: {application.requested_term_months} months",
            "",
            "VALIDATION RESULTS:"
        ]
        
        for validation_name, validation_data in validation_results['validations'].items():
            status = "✅ PASS" if validation_data['valid'] else "❌ FAIL"
            summary_lines.append(f"  {status} {validation_name.replace('_', ' ').title()}: {validation_data['reason']}")
        
        summary_lines.append("")
        
        if validation_results['is_valid']:
            summary_lines.append("DECISION: ✅ APPROVED")
            summary_lines.append(f"Risk Level: {validation_results['risk_level'].value.upper()}")
            
            if validation_results['emi_details']:
                emi = validation_results['emi_details']
                summary_lines.extend([
                    "",
                    "EMI DETAILS (SLM Method):",
                    f"  Monthly EMI: ₹{emi['monthly_emi']:,.2f}",
                    f"  Annual ROI: {emi['annual_roi']:.1%}",
                    f"  Total Interest: ₹{emi['total_interest']:,.2f}",
                    f"  Total Amount: ₹{emi['total_amount']:,.2f}"
                ])
        else:
            summary_lines.append("DECISION: ❌ REJECTED")
            summary_lines.append("")
            summary_lines.append("REJECTION REASONS:")
            for reason in validation_results['rejection_reasons']:
                summary_lines.append(f"  • {reason}")
        
        if validation_results['warnings']:
            summary_lines.append("")
            summary_lines.append("WARNINGS:")
            for warning in validation_results['warnings']:
                summary_lines.append(f"  ⚠️ {warning}")
        
        summary_lines.append("")
        summary_lines.append("=== END ASSESSMENT ===")
        
        return "\n".join(summary_lines)

