"""
Risk Assessment Sub-Agent

Specialized Google ADK sub-agent for credit risk assessment.
Demonstrates focused agent responsibilities and decision-making.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Tuple
from decimal import Decimal

from ..models import ApplicantInfo, LoanRequest, RiskFactors, RiskLevel, ConfidenceScores
from ..rules import SimpleCreditRules

logger = logging.getLogger(__name__)


class RiskAssessmentAgent:
    """
    Google ADK sub-agent specialized in credit risk assessment.
    
    This agent demonstrates:
    - Focused responsibility (risk assessment only)
    - Data-driven decision making
    - Confidence scoring
    - Clear reasoning and transparency
    """
    
    def __init__(self):
        """Initialize the risk assessment agent."""
        self.agent_id = "risk_assessor"
        self.version = "1.0.0"
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def assess_credit_risk(self, applicant: ApplicantInfo, loan_request: LoanRequest) -> Dict[str, Any]:
        """
        Perform comprehensive credit risk assessment.
        
        Args:
            applicant: Applicant information
            loan_request: Loan request details
            
        Returns:
            Dict containing risk assessment results
        """
        start_time = datetime.utcnow()
        
        logger.info(f"Starting risk assessment for application {applicant.name}")
        
        try:
            # Assess individual risk factors
            risk_factors = self._assess_risk_factors(applicant, loan_request)
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(applicant, loan_request, risk_factors)
            
            # Generate detailed reasoning
            reasoning = self._generate_risk_reasoning(applicant, loan_request, risk_factors)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'risk_factors': risk_factors,
                'risk_level': risk_factors.risk_level,
                'confidence_scores': confidence_scores,
                'reasoning': reasoning,
                'processing_time_seconds': processing_time,
                'assessed_by': self.agent_id,
                'assessed_at': datetime.utcnow()
            }
            
            logger.info(f"Risk assessment completed: {risk_factors.risk_level.value} risk, "
                       f"{risk_factors.risk_count} factors, {confidence_scores.overall_confidence:.2f} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            raise
    
    def _assess_risk_factors(self, applicant: ApplicantInfo, loan_request: LoanRequest) -> RiskFactors:
        """Assess individual risk factors using business rules."""
        return SimpleCreditRules.assess_risk_factors(applicant, loan_request)
    
    def _calculate_confidence_scores(self, applicant: ApplicantInfo, loan_request: LoanRequest, 
                                   risk_factors: RiskFactors) -> ConfidenceScores:
        """
        Calculate confidence scores for different aspects of the assessment.
        
        Higher confidence = more reliable data and clearer decision factors.
        """
        # Income confidence based on employment status and duration
        income_confidence = self._assess_income_confidence(applicant)
        
        # Credit confidence based on credit score and existing debt
        credit_confidence = self._assess_credit_confidence(applicant)
        
        # Employment confidence based on status and duration
        employment_confidence = self._assess_employment_confidence(applicant)
        
        # Overall confidence is weighted average
        overall_confidence = (
            income_confidence * 0.4 +
            credit_confidence * 0.4 +
            employment_confidence * 0.2
        )
        
        # Reduce confidence if many risk factors present
        risk_penalty = min(0.2, risk_factors.risk_count * 0.05)
        overall_confidence = max(0.1, overall_confidence - risk_penalty)
        
        return ConfidenceScores(
            overall_confidence=overall_confidence,
            income_confidence=income_confidence,
            credit_confidence=credit_confidence,
            employment_confidence=employment_confidence
        )
    
    def _assess_income_confidence(self, applicant: ApplicantInfo) -> float:
        """Assess confidence in income information."""
        confidence = 0.5  # Base confidence
        
        # Higher income = more confidence (up to a point)
        if applicant.annual_income >= Decimal('100000'):
            confidence += 0.3
        elif applicant.annual_income >= Decimal('60000'):
            confidence += 0.2
        elif applicant.annual_income >= Decimal('40000'):
            confidence += 0.1
        
        # Employment status affects confidence
        if applicant.employment_status.value == 'employed':
            confidence += 0.2
        elif applicant.employment_status.value == 'self_employed':
            confidence += 0.1  # Self-employed income can be variable
        
        # Reasonable expense ratio increases confidence
        monthly_income = applicant.annual_income / 12
        expense_ratio = applicant.monthly_expenses / monthly_income
        if expense_ratio <= 0.5:
            confidence += 0.1
        elif expense_ratio >= 0.8:
            confidence -= 0.2
        
        return min(1.0, max(0.1, confidence))
    
    def _assess_credit_confidence(self, applicant: ApplicantInfo) -> float:
        """Assess confidence in credit information."""
        confidence = 0.3  # Base confidence
        
        # Credit score affects confidence
        if applicant.credit_score >= 750:
            confidence += 0.4
        elif applicant.credit_score >= 650:
            confidence += 0.3
        elif applicant.credit_score >= 580:
            confidence += 0.2
        else:
            confidence += 0.1
        
        # Existing debt level affects confidence
        debt_to_income = applicant.existing_debt / applicant.annual_income
        if debt_to_income <= 0.2:
            confidence += 0.2
        elif debt_to_income <= 0.4:
            confidence += 0.1
        else:
            confidence -= 0.1
        
        return min(1.0, max(0.1, confidence))
    
    def _assess_employment_confidence(self, applicant: ApplicantInfo) -> float:
        """Assess confidence in employment information."""
        confidence = 0.3  # Base confidence
        
        # Employment duration affects confidence
        if applicant.employment_duration_months >= 24:
            confidence += 0.4
        elif applicant.employment_duration_months >= 12:
            confidence += 0.3
        elif applicant.employment_duration_months >= 6:
            confidence += 0.2
        else:
            confidence += 0.1
        
        # Employment status affects confidence
        if applicant.employment_status.value == 'employed':
            confidence += 0.3
        elif applicant.employment_status.value == 'self_employed':
            confidence += 0.2
        elif applicant.employment_status.value == 'retired':
            confidence += 0.1
        
        return min(1.0, max(0.1, confidence))
    
    def _generate_risk_reasoning(self, applicant: ApplicantInfo, loan_request: LoanRequest, 
                               risk_factors: RiskFactors) -> str:
        """Generate detailed reasoning for the risk assessment."""
        reasoning_parts = [
            "=== RISK ASSESSMENT ANALYSIS ===",
            f"Applicant: {applicant.name}",
            f"Requested Amount: ${loan_request.amount:,.2f}",
            f"Credit Score: {applicant.credit_score}",
            f"Annual Income: ${applicant.annual_income:,.2f}",
            "",
            "RISK FACTOR ANALYSIS:"
        ]
        
        # Analyze each risk factor
        if risk_factors.high_debt_to_income:
            dti_ratio = SimpleCreditRules.calculate_debt_to_income_ratio(applicant, loan_request.amount)
            reasoning_parts.append(f"❌ HIGH DEBT-TO-INCOME: {dti_ratio:.1%} (max: {SimpleCreditRules.MAX_DEBT_TO_INCOME_RATIO:.1%})")
        else:
            dti_ratio = SimpleCreditRules.calculate_debt_to_income_ratio(applicant, loan_request.amount)
            reasoning_parts.append(f"✅ DEBT-TO-INCOME: {dti_ratio:.1%} (within acceptable range)")
        
        if risk_factors.low_credit_score:
            reasoning_parts.append(f"❌ LOW CREDIT SCORE: {applicant.credit_score} (recommended: 650+)")
        else:
            reasoning_parts.append(f"✅ CREDIT SCORE: {applicant.credit_score} (acceptable)")
        
        if risk_factors.insufficient_income:
            monthly_income = applicant.annual_income / 12
            estimated_payment = loan_request.amount * Decimal('0.02')
            payment_ratio = estimated_payment / monthly_income
            reasoning_parts.append(f"❌ INSUFFICIENT INCOME: Payment would be {payment_ratio:.1%} of monthly income")
        else:
            reasoning_parts.append(f"✅ SUFFICIENT INCOME: Income supports requested loan amount")
        
        if risk_factors.short_employment:
            reasoning_parts.append(f"❌ SHORT EMPLOYMENT: {applicant.employment_duration_months} months (min: {SimpleCreditRules.MIN_EMPLOYMENT_MONTHS})")
        else:
            reasoning_parts.append(f"✅ EMPLOYMENT HISTORY: {applicant.employment_duration_months} months (stable)")
        
        if risk_factors.high_expenses:
            monthly_income = applicant.annual_income / 12
            expense_ratio = applicant.monthly_expenses / monthly_income
            reasoning_parts.append(f"❌ HIGH EXPENSES: {expense_ratio:.1%} of income (max: {SimpleCreditRules.MAX_EXPENSE_TO_INCOME_RATIO:.1%})")
        else:
            monthly_income = applicant.annual_income / 12
            expense_ratio = applicant.monthly_expenses / monthly_income
            reasoning_parts.append(f"✅ REASONABLE EXPENSES: {expense_ratio:.1%} of income")
        
        # Summary
        reasoning_parts.extend([
            "",
            f"RISK SUMMARY:",
            f"• Risk Factors: {risk_factors.risk_count}/5",
            f"• Risk Level: {risk_factors.risk_level.value.upper()}",
            f"• Credit Tier: {SimpleCreditRules.get_credit_tier(applicant.credit_score).title()}",
            "",
            "=== END RISK ASSESSMENT ==="
        ])
        
        return "\n".join(reasoning_parts)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            'agent_id': self.agent_id,
            'agent_type': 'risk_assessor',
            'version': self.version,
            'capabilities': [
                'credit_risk_assessment',
                'risk_factor_analysis',
                'confidence_scoring',
                'debt_to_income_calculation'
            ],
            'description': 'Specialized agent for credit risk assessment and analysis'
        }

