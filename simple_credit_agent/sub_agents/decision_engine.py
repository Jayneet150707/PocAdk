"""
Decision Engine Sub-Agent

Specialized Google ADK sub-agent for final credit decisions.
Demonstrates agent orchestration and transparent decision-making.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal

from ..models import ApplicantInfo, LoanRequest, RiskFactors, RiskLevel, AssessmentResult
from ..rules import SimpleCreditRules

logger = logging.getLogger(__name__)


class DecisionEngineAgent:
    """
    Google ADK sub-agent specialized in final credit decisions.
    
    This agent demonstrates:
    - Final decision authority
    - Integration of multiple data sources
    - Transparent reasoning
    - Recommendation generation
    """
    
    def __init__(self):
        """Initialize the decision engine agent."""
        self.agent_id = "decision_engine"
        self.version = "1.0.0"
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def make_credit_decision(self, applicant: ApplicantInfo, loan_request: LoanRequest, 
                           risk_assessment: Dict[str, Any], application_id: str) -> AssessmentResult:
        """
        Make final credit decision based on risk assessment and business rules.
        
        Args:
            applicant: Applicant information
            loan_request: Loan request details
            risk_assessment: Results from risk assessment agent
            application_id: Unique application identifier
            
        Returns:
            Complete assessment result with decision and recommendations
        """
        start_time = datetime.utcnow()
        
        logger.info(f"Making credit decision for application {application_id}")
        
        try:
            # Extract risk assessment data
            risk_factors: RiskFactors = risk_assessment['risk_factors']
            confidence_scores = risk_assessment['confidence_scores']
            
            # Make approval decision
            approved, approval_reason = self._make_approval_decision(applicant, loan_request, risk_factors)
            
            # Calculate recommendations
            recommended_amount = self._calculate_recommended_amount(applicant, loan_request, approved)
            recommended_rate = self._calculate_recommended_rate(applicant.credit_score, risk_factors.risk_level)
            recommended_term = self._calculate_recommended_term(loan_request, risk_factors.risk_level)
            
            # Generate reasoning
            reasoning = self._generate_decision_reasoning(
                applicant, loan_request, risk_factors, approved, approval_reason,
                recommended_amount, recommended_rate, recommended_term
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(applicant, loan_request, risk_factors, approved)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create assessment result
            result = AssessmentResult(
                application_id=application_id,
                assessment_id=f"ASSESS_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{application_id[-6:]}",
                approved=approved,
                risk_level=risk_factors.risk_level,
                recommended_amount=recommended_amount if approved else None,
                recommended_rate=recommended_rate if approved else None,
                recommended_term=recommended_term if approved else None,
                confidence_scores=confidence_scores,
                risk_factors=risk_factors,
                reasoning=reasoning,
                recommendations=recommendations,
                processing_time_seconds=processing_time
            )
            
            logger.info(f"Decision completed: {'APPROVED' if approved else 'REJECTED'} "
                       f"(Risk: {risk_factors.risk_level.value}, "
                       f"Confidence: {confidence_scores.overall_confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Decision making failed: {str(e)}")
            raise
    
    def _make_approval_decision(self, applicant: ApplicantInfo, loan_request: LoanRequest, 
                              risk_factors: RiskFactors) -> tuple[bool, str]:
        """Make the core approval/rejection decision."""
        return SimpleCreditRules.should_approve(applicant, loan_request, risk_factors)
    
    def _calculate_recommended_amount(self, applicant: ApplicantInfo, loan_request: LoanRequest, 
                                    approved: bool) -> Decimal:
        """Calculate recommended loan amount."""
        if not approved:
            return Decimal('0')
        
        return SimpleCreditRules.calculate_recommended_amount(applicant, loan_request.amount)
    
    def _calculate_recommended_rate(self, credit_score: int, risk_level: RiskLevel) -> float:
        """Calculate recommended interest rate."""
        return SimpleCreditRules.get_interest_rate(credit_score, risk_level)
    
    def _calculate_recommended_term(self, loan_request: LoanRequest, risk_level: RiskLevel) -> int:
        """Calculate recommended loan term."""
        requested_term = loan_request.term_months
        
        # Adjust term based on risk level
        if risk_level == RiskLevel.LOW:
            # Low risk can have requested term
            return requested_term
        elif risk_level == RiskLevel.MEDIUM:
            # Medium risk gets slightly shorter term
            return min(requested_term, 60)  # Max 5 years
        elif risk_level == RiskLevel.HIGH:
            # High risk gets shorter term
            return min(requested_term, 36)  # Max 3 years
        else:
            # Very high risk gets very short term (if approved at all)
            return min(requested_term, 24)  # Max 2 years
    
    def _generate_decision_reasoning(self, applicant: ApplicantInfo, loan_request: LoanRequest,
                                   risk_factors: RiskFactors, approved: bool, approval_reason: str,
                                   recommended_amount: Decimal, recommended_rate: float, 
                                   recommended_term: int) -> str:
        """Generate detailed reasoning for the decision."""
        reasoning_parts = [
            "=== CREDIT DECISION ANALYSIS ===",
            f"Application ID: {loan_request}",
            f"Applicant: {applicant.name}",
            f"Decision: {'APPROVED' if approved else 'REJECTED'}",
            "",
            "DECISION FACTORS:"
        ]
        
        # Basic eligibility
        age_valid, _ = SimpleCreditRules.validate_age(applicant.age)
        credit_valid, _ = SimpleCreditRules.validate_credit_score(applicant.credit_score)
        income_valid, _ = SimpleCreditRules.validate_income(applicant.annual_income, loan_request.amount)
        
        reasoning_parts.extend([
            f"• Age Eligibility: {'✅ PASS' if age_valid else '❌ FAIL'} ({applicant.age} years)",
            f"• Credit Score: {'✅ PASS' if credit_valid else '❌ FAIL'} ({applicant.credit_score})",
            f"• Income Level: {'✅ PASS' if income_valid else '❌ FAIL'} (${applicant.annual_income:,.2f})",
            f"• Risk Level: {risk_factors.risk_level.value.upper()} ({risk_factors.risk_count} factors)",
            ""
        ])
        
        # Risk factor details
        if risk_factors.risk_count > 0:
            reasoning_parts.append("IDENTIFIED RISK FACTORS:")
            if risk_factors.high_debt_to_income:
                reasoning_parts.append("• High debt-to-income ratio")
            if risk_factors.low_credit_score:
                reasoning_parts.append("• Credit score below optimal range")
            if risk_factors.insufficient_income:
                reasoning_parts.append("• Income may be insufficient for loan amount")
            if risk_factors.short_employment:
                reasoning_parts.append("• Short employment history")
            if risk_factors.high_expenses:
                reasoning_parts.append("• High monthly expenses relative to income")
            reasoning_parts.append("")
        
        # Decision rationale
        reasoning_parts.extend([
            "DECISION RATIONALE:",
            f"• {approval_reason}",
            ""
        ])
        
        # Recommendations if approved
        if approved:
            reasoning_parts.extend([
                "LOAN TERMS:",
                f"• Recommended Amount: ${recommended_amount:,.2f}",
                f"• Recommended Rate: {recommended_rate:.2%} APR",
                f"• Recommended Term: {recommended_term} months",
                f"• Estimated Monthly Payment: ${self._calculate_monthly_payment(recommended_amount, recommended_rate, recommended_term):,.2f}",
                ""
            ])
            
            # Payment analysis
            monthly_income = applicant.annual_income / 12
            monthly_payment = self._calculate_monthly_payment(recommended_amount, recommended_rate, recommended_term)
            payment_ratio = monthly_payment / monthly_income
            
            reasoning_parts.extend([
                "AFFORDABILITY ANALYSIS:",
                f"• Monthly Income: ${monthly_income:,.2f}",
                f"• Estimated Payment: ${monthly_payment:,.2f}",
                f"• Payment-to-Income Ratio: {payment_ratio:.1%}",
                f"• Remaining Income: ${monthly_income - monthly_payment - applicant.monthly_expenses:,.2f}",
                ""
            ])
        
        reasoning_parts.append("=== END DECISION ANALYSIS ===")
        
        return "\n".join(reasoning_parts)
    
    def _calculate_monthly_payment(self, amount: Decimal, annual_rate: float, term_months: int) -> Decimal:
        """Calculate estimated monthly payment."""
        if annual_rate == 0:
            return amount / term_months
        
        monthly_rate = Decimal(str(annual_rate)) / 12
        num_payments = Decimal(str(term_months))
        
        # Standard loan payment formula
        payment = amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                 ((1 + monthly_rate) ** num_payments - 1)
        
        return payment.quantize(Decimal('0.01'))
    
    def _generate_recommendations(self, applicant: ApplicantInfo, loan_request: LoanRequest,
                                risk_factors: RiskFactors, approved: bool) -> List[str]:
        """Generate recommendations using business rules."""
        return SimpleCreditRules.generate_recommendations(applicant, loan_request, risk_factors, approved)
    
    def evaluate_alternative_scenarios(self, applicant: ApplicantInfo, loan_request: LoanRequest,
                                     risk_factors: RiskFactors) -> Dict[str, Any]:
        """
        Evaluate alternative loan scenarios for better decision making.
        
        This demonstrates advanced ADK capabilities for scenario analysis.
        """
        scenarios = {}
        
        # Scenario 1: Reduced loan amount
        if loan_request.amount > Decimal('10000'):
            reduced_amount = loan_request.amount * Decimal('0.75')  # 75% of requested
            reduced_request = LoanRequest(
                amount=reduced_amount,
                purpose=loan_request.purpose,
                term_months=loan_request.term_months
            )
            reduced_risk = SimpleCreditRules.assess_risk_factors(applicant, reduced_request)
            approved, reason = SimpleCreditRules.should_approve(applicant, reduced_request, reduced_risk)
            
            scenarios['reduced_amount'] = {
                'amount': reduced_amount,
                'risk_level': reduced_risk.risk_level.value,
                'approved': approved,
                'reason': reason
            }
        
        # Scenario 2: Extended term
        if loan_request.term_months < 72:
            extended_term = min(72, loan_request.term_months + 24)
            extended_request = LoanRequest(
                amount=loan_request.amount,
                purpose=loan_request.purpose,
                term_months=extended_term
            )
            extended_risk = SimpleCreditRules.assess_risk_factors(applicant, extended_request)
            approved, reason = SimpleCreditRules.should_approve(applicant, extended_request, extended_risk)
            
            scenarios['extended_term'] = {
                'term_months': extended_term,
                'risk_level': extended_risk.risk_level.value,
                'approved': approved,
                'reason': reason
            }
        
        return scenarios
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            'agent_id': self.agent_id,
            'agent_type': 'decision_engine',
            'version': self.version,
            'capabilities': [
                'final_credit_decisions',
                'loan_term_recommendations',
                'interest_rate_calculation',
                'scenario_analysis',
                'recommendation_generation'
            ],
            'description': 'Final decision-making agent for credit applications'
        }

