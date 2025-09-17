"""
Main Credit Assessment Agent

This is the orchestrating agent that coordinates between sub-agents to provide
comprehensive credit application assessments.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .shared_libraries.data_models import (
    CreditApplication,
    BankTransaction,
    CreditAssessmentResult,
    TransactionSummary,
    ConfidenceScore,
    RiskFactors,
    RiskLevel,
    AgentResponse
)
from .shared_libraries.vertex_ai_client import VertexAIClient
from .shared_libraries.pdf_processor import PDFProcessor
from .shared_libraries.paisalo_rules import PaisaloBusinessRules
from .shared_libraries.utils import (
    extract_financial_metrics,
    calculate_confidence_score,
    calculate_risk_score,
    generate_assessment_id
)
from .sub_agents.transaction_analyzer.agent import TransactionAnalyzerAgent

logger = logging.getLogger(__name__)


class CreditAssessmentAgent:
    """
    Main orchestrating agent for credit assessment.
    
    This agent coordinates between specialized sub-agents to provide
    comprehensive credit application assessments using AI-powered analysis.
    """
    
    def __init__(
        self,
        vertex_ai_client: Optional[VertexAIClient] = None,
        pdf_processor: Optional[PDFProcessor] = None
    ):
        """
        Initialize the Credit Assessment Agent.
        
        Args:
            vertex_ai_client: Vertex AI client for intelligent analysis
            pdf_processor: PDF processor for bank statement analysis
        """
        self.agent_name = "CreditAssessmentAgent"
        self.vertex_ai_client = vertex_ai_client
        self.pdf_processor = pdf_processor or PDFProcessor()
        
        # Initialize sub-agents
        self.transaction_analyzer = TransactionAnalyzerAgent(
            vertex_ai_client=vertex_ai_client,
            pdf_processor=self.pdf_processor
        )
        
        logger.info(f"Initialized {self.agent_name} with sub-agents")
    
    async def assess_credit_application(
        self,
        application: CreditApplication,
        bank_transactions: Optional[List[BankTransaction]] = None,
        priority: str = "normal"
    ) -> CreditAssessmentResult:
        """
        Perform comprehensive credit assessment.
        
        Args:
            application: Credit application data
            bank_transactions: Optional bank transaction data
            priority: Assessment priority level
            
        Returns:
            Complete credit assessment result
        """
        start_time = datetime.utcnow()
        assessment_id = generate_assessment_id(application.application_id)
        
        try:
            logger.info(f"Starting Paisalo credit assessment {assessment_id} for application {application.application_id}")
            
            # Step 1: Paisalo Business Rules Validation (Primary Check)
            paisalo_validation = PaisaloBusinessRules.perform_complete_validation(application)
            
            # If Paisalo rules fail, return immediate rejection
            if not paisalo_validation['is_valid']:
                logger.info(f"Application {application.application_id} rejected by Paisalo business rules")
                return self._create_paisalo_rejection_assessment(
                    application=application,
                    assessment_id=assessment_id,
                    validation_results=paisalo_validation,
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            # Step 2: Extract financial metrics
            financial_metrics = extract_financial_metrics(application)
            
            # Step 3: Analyze bank transactions if provided
            transaction_summary = None
            transaction_analysis = None
            
            if bank_transactions:
                transaction_response = await self.transaction_analyzer.analyze_transaction_list(
                    transactions=bank_transactions,
                    analysis_context={"application_id": application.application_id}
                )
                
                if transaction_response.success and transaction_response.data:
                    transaction_summary = TransactionSummary(**transaction_response.data["transaction_summary"])
                    transaction_analysis = transaction_response.data
            
            # Step 4: Calculate confidence scores
            confidence_scores = calculate_confidence_score(
                credit_score=application.credit_score,
                income=application.applicant_info.income,
                transaction_summary=transaction_summary,
                employment_months=application.applicant_info.employment_duration_months,
                data_completeness=self._calculate_data_completeness(application, bank_transactions)
            )
            
            # Step 5: Calculate risk assessment
            debt_to_income_ratio = financial_metrics.get('debt_to_income_ratio', 0.0)
            income_stability = transaction_summary.income_stability_score if transaction_summary else 1.0
            overdraft_count = transaction_summary.overdraft_incidents if transaction_summary else 0
            
            risk_score, risk_level = calculate_risk_score(
                credit_score=application.credit_score,
                debt_to_income_ratio=debt_to_income_ratio,
                income_stability=income_stability,
                overdraft_count=overdraft_count
            )
            
            # Step 6: Identify risk factors
            risk_factors = self._identify_risk_factors(
                application, financial_metrics, transaction_summary
            )
            
            # Step 7: AI-powered assessment if available
            ai_assessment = None
            if self.vertex_ai_client:
                try:
                    ai_assessment = await self.vertex_ai_client.assess_credit_application(
                        application=application,
                        transaction_summary=transaction_summary,
                        additional_context={
                            "financial_metrics": financial_metrics,
                            "risk_score": risk_score
                        }
                    )
                except Exception as e:
                    logger.warning(f"AI assessment failed, using fallback: {str(e)}")
            
            # Step 8: Make final decision
            if ai_assessment:
                # Use AI assessment as primary decision
                final_result = ai_assessment
                final_result.transaction_summary = transaction_summary
            else:
                # Fallback to Paisalo rule-based assessment
                final_result = self._update_fallback_assessment_with_paisalo_rules(
                    application=application,
                    assessment_id=assessment_id,
                    confidence_scores=confidence_scores,
                    risk_factors=risk_factors,
                    risk_level=risk_level,
                    financial_metrics=financial_metrics,
                    transaction_summary=transaction_summary
                )
            
            # Step 9: Add processing metadata and Paisalo branding
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            final_result.processing_time_seconds = processing_time
            
            logger.info(f"Completed credit assessment {assessment_id} in {processing_time:.2f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"Credit assessment {assessment_id} failed: {str(e)}")
            # Return conservative assessment on error
            return self._create_error_assessment(
                application.application_id,
                assessment_id,
                str(e),
                (datetime.utcnow() - start_time).total_seconds()
            )
    
    async def analyze_bank_statement(
        self,
        pdf_path: Path,
        applicant_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a bank statement PDF.
        
        Args:
            pdf_path: Path to the bank statement PDF
            applicant_id: ID of the applicant
            
        Returns:
            Bank statement analysis results
        """
        try:
            logger.info(f"Analyzing bank statement for applicant {applicant_id}")
            
            # Use transaction analyzer sub-agent
            analysis_response = await self.transaction_analyzer.analyze_bank_statement_pdf(
                pdf_path=pdf_path,
                account_holder=applicant_id
            )
            
            if analysis_response.success:
                return analysis_response.data
            else:
                raise Exception(analysis_response.message)
                
        except Exception as e:
            logger.error(f"Bank statement analysis failed: {str(e)}")
            raise
    
    def _calculate_data_completeness(
        self,
        application: CreditApplication,
        bank_transactions: Optional[List[BankTransaction]]
    ) -> float:
        """Calculate data completeness score (0-1)."""
        completeness_factors = []
        
        # Application data completeness
        app_fields = [
            application.applicant_info.employment_duration_months,
            application.applicant_info.address,
            application.applicant_info.phone,
            application.applicant_info.email,
            application.down_payment,
            application.existing_debt,
            application.assets
        ]
        
        app_completeness = sum(1 for field in app_fields if field is not None) / len(app_fields)
        completeness_factors.append(app_completeness)
        
        # Bank transaction data completeness
        if bank_transactions:
            # High completeness if we have transaction data
            tx_completeness = min(1.0, len(bank_transactions) / 50)  # 50+ transactions = full score
            completeness_factors.append(tx_completeness)
        else:
            # Lower completeness without transaction data
            completeness_factors.append(0.3)
        
        return sum(completeness_factors) / len(completeness_factors)
    
    def _identify_risk_factors(
        self,
        application: CreditApplication,
        financial_metrics: Dict[str, Any],
        transaction_summary: Optional[TransactionSummary]
    ) -> RiskFactors:
        """Identify risk factors from application and transaction data."""
        
        # Initialize risk factors
        risk_factors = {
            "high_debt_to_income": False,
            "insufficient_income": False,
            "poor_credit_history": False,
            "irregular_income": False,
            "excessive_expenses": False,
            "frequent_overdrafts": False,
            "short_employment_history": False,
            "high_loan_to_value": False
        }
        
        # Check debt-to-income ratio
        dti_ratio = financial_metrics.get('debt_to_income_ratio', 0.0)
        if dti_ratio > 0.36:
            risk_factors["high_debt_to_income"] = True
        
        # Check income sufficiency
        monthly_income = financial_metrics.get('monthly_income', 0.0)
        monthly_payment = financial_metrics.get('monthly_payment', 0.0)
        if monthly_payment > monthly_income * 0.28:  # 28% rule
            risk_factors["insufficient_income"] = True
        
        # Check credit history
        if application.credit_score < 650:
            risk_factors["poor_credit_history"] = True
        
        # Check employment history
        if application.applicant_info.employment_duration_months and application.applicant_info.employment_duration_months < 12:
            risk_factors["short_employment_history"] = True
        
        # Check loan-to-value ratio (simplified)
        loan_to_income = financial_metrics.get('loan_to_income_ratio', 0.0)
        if loan_to_income > 5.0:  # Loan > 5x annual income
            risk_factors["high_loan_to_value"] = True
        
        # Transaction-based risk factors
        if transaction_summary:
            if transaction_summary.income_stability_score < 0.6:
                risk_factors["irregular_income"] = True
            
            if transaction_summary.overdraft_incidents > 3:
                risk_factors["frequent_overdrafts"] = True
            
            expense_ratio = float(
                transaction_summary.average_monthly_expenses / 
                max(transaction_summary.average_monthly_income, transaction_summary.average_monthly_expenses)
            )
            if expense_ratio > 0.8:
                risk_factors["excessive_expenses"] = True
        
        # Count risk factors and determine level
        risk_count = sum(risk_factors.values())
        
        if risk_count == 0:
            risk_level = RiskLevel.LOW
        elif risk_count <= 2:
            risk_level = RiskLevel.MEDIUM
        elif risk_count <= 4:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.VERY_HIGH
        
        return RiskFactors(
            **risk_factors,
            risk_factors_count=risk_count,
            risk_level=risk_level
        )
    
    def _create_fallback_assessment(
        self,
        application: CreditApplication,
        assessment_id: str,
        confidence_scores: ConfidenceScore,
        risk_factors: RiskFactors,
        risk_level: RiskLevel,
        financial_metrics: Dict[str, Any],
        transaction_summary: Optional[TransactionSummary]
    ) -> CreditAssessmentResult:
        """Create fallback assessment when AI is unavailable."""
        
        # Simple rule-based approval logic
        approved = (
            application.credit_score >= 650 and
            financial_metrics.get('debt_to_income_ratio', 1.0) <= 0.36 and
            risk_factors.risk_factors_count <= 2
        )
        
        # Calculate recommended loan amount
        recommended_amount = None
        if approved:
            max_affordable = financial_metrics.get('monthly_income', 0) * 0.28 * application.requested_term_months
            recommended_amount = min(float(application.loan_amount), max_affordable)
        
        # Generate reasoning
        reasoning = self._generate_fallback_reasoning(
            application, approved, risk_factors, financial_metrics
        )
        
        # Generate recommendations
        recommendations = self._generate_fallback_recommendations(
            approved, risk_factors, financial_metrics
        )
        
        return CreditAssessmentResult(
            application_id=application.application_id,
            assessment_id=assessment_id,
            approved=approved,
            risk_level=risk_level,
            recommended_loan_amount=recommended_amount,
            recommended_interest_rate=self._estimate_interest_rate(application.credit_score),
            confidence_scores=confidence_scores,
            risk_factors=risk_factors,
            transaction_summary=transaction_summary,
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def _generate_fallback_reasoning(
        self,
        application: CreditApplication,
        approved: bool,
        risk_factors: RiskFactors,
        financial_metrics: Dict[str, Any]
    ) -> str:
        """Generate reasoning for fallback assessment."""
        
        decision = "APPROVED" if approved else "DECLINED"
        credit_tier = financial_metrics.get('credit_score_tier', 'unknown')
        dti_ratio = financial_metrics.get('debt_to_income_ratio', 0.0)
        
        reasoning = f"""
Credit Assessment Decision: {decision}

Key Factors:
- Credit Score: {application.credit_score} ({credit_tier.title()})
- Debt-to-Income Ratio: {dti_ratio:.1%}
- Risk Factors Identified: {risk_factors.risk_factors_count}
- Overall Risk Level: {risk_factors.risk_level.value.title()}

"""
        
        if approved:
            reasoning += """
Approval Rationale:
- Credit score meets minimum requirements (≥650)
- Debt-to-income ratio is within acceptable limits (≤36%)
- Limited risk factors identified
- Financial profile indicates ability to repay
"""
        else:
            reasoning += """
Decline Rationale:
- Credit assessment indicates elevated risk
- One or more key criteria not met
- Risk factors may impact repayment ability
"""
        
        return reasoning.strip()
    
    def _generate_fallback_recommendations(
        self,
        approved: bool,
        risk_factors: RiskFactors,
        financial_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for fallback assessment."""
        recommendations = []
        
        if not approved:
            if risk_factors.poor_credit_history:
                recommendations.append("Work on improving credit score through timely payments")
            
            if risk_factors.high_debt_to_income:
                recommendations.append("Reduce existing debt to improve debt-to-income ratio")
            
            if risk_factors.insufficient_income:
                recommendations.append("Consider a smaller loan amount or longer repayment term")
            
            if risk_factors.short_employment_history:
                recommendations.append("Establish longer employment history before reapplying")
        
        else:
            recommendations.append("Maintain current financial habits to ensure successful repayment")
            recommendations.append("Consider setting up automatic payments to avoid missed payments")
        
        return recommendations
    
    def _estimate_interest_rate(self, credit_score: int) -> float:
        """Estimate interest rate based on credit score."""
        if credit_score >= 750:
            return 0.045  # 4.5%
        elif credit_score >= 700:
            return 0.065  # 6.5%
        elif credit_score >= 650:
            return 0.095  # 9.5%
        elif credit_score >= 600:
            return 0.135  # 13.5%
        else:
            return 0.185  # 18.5%
    
    def _create_error_assessment(
        self,
        application_id: str,
        assessment_id: str,
        error_message: str,
        processing_time: float
    ) -> CreditAssessmentResult:
        """Create conservative assessment when processing fails."""
        
        return CreditAssessmentResult(
            application_id=application_id,
            assessment_id=assessment_id,
            approved=False,
            risk_level=RiskLevel.HIGH,
            confidence_scores=ConfidenceScore(
                overall_confidence=0.1,
                credit_score_confidence=0.1,
                income_confidence=0.1,
                transaction_confidence=0.1,
                application_confidence=0.1,
                data_quality_score=0.1
            ),
            risk_factors=RiskFactors(
                risk_factors_count=1,
                risk_level=RiskLevel.HIGH
            ),
            reasoning=f"Assessment could not be completed due to technical error: {error_message}",
            recommendations=[
                "Please resubmit your application",
                "Contact support if the issue persists"
            ],
            processing_time_seconds=processing_time
        )
    
    def _create_paisalo_rejection_assessment(
        self,
        application: CreditApplication,
        assessment_id: str,
        validation_results: Dict[str, any],
        processing_time: float
    ) -> CreditAssessmentResult:
        """Create assessment result for Paisalo business rules rejection."""
        
        # Generate detailed reasoning with Paisalo branding
        reasoning = PaisaloBusinessRules.generate_paisalo_assessment_summary(
            application, validation_results
        )
        
        # Create recommendations based on failed validations
        recommendations = []
        for validation_name, validation_data in validation_results['validations'].items():
            if not validation_data['valid']:
                if validation_name == 'age':
                    recommendations.append(f"Applicant must be between {PaisaloBusinessRules.MIN_AGE}-{PaisaloBusinessRules.MAX_AGE} years old")
                elif validation_name == 'credit_score':
                    recommendations.append(f"Credit score must be between {PaisaloBusinessRules.MIN_CREDIT_SCORE}-{PaisaloBusinessRules.MAX_CREDIT_SCORE}")
                elif validation_name == 'loan_amount':
                    recommendations.append(f"Loan amount must be between ₹{PaisaloBusinessRules.MIN_LOAN_AMOUNT:,.2f}-₹{PaisaloBusinessRules.MAX_LOAN_AMOUNT:,.2f}")
                elif validation_name == 'documents':
                    recommendations.append("Provide valid document combination: (Voter ID + PAN) OR (Driving License + PAN)")
                elif validation_name == 'income_expense_ratio':
                    recommendations.append("Reduce expenses to below 50% of total income")
        
        if not recommendations:
            recommendations.append("Please review application details and resubmit")
        
        # Create basic risk factors for rejection
        risk_factors = RiskFactors(
            risk_factors_count=len(validation_results['rejection_reasons']),
            risk_level=RiskLevel.VERY_HIGH,
            insufficient_income=any('income' in reason.lower() for reason in validation_results['rejection_reasons']),
            poor_credit_history=any('credit' in reason.lower() for reason in validation_results['rejection_reasons'])
        )
        
        # Create low confidence scores for rejection
        confidence_scores = ConfidenceScore(
            overall_confidence=0.1,
            credit_score_confidence=0.2,
            income_confidence=0.2,
            transaction_confidence=0.1,
            application_confidence=0.1,
            data_quality_score=0.3
        )
        
        return CreditAssessmentResult(
            application_id=application.application_id,
            assessment_id=assessment_id,
            approved=False,
            risk_level=validation_results['risk_level'],
            recommended_loan_amount=None,
            recommended_interest_rate=None,
            confidence_scores=confidence_scores,
            risk_factors=risk_factors,
            reasoning=reasoning,
            recommendations=recommendations,
            processing_time_seconds=processing_time
        )
    
    def _update_fallback_assessment_with_paisalo_rules(
        self,
        application: CreditApplication,
        assessment_id: str,
        confidence_scores: ConfidenceScore,
        risk_factors: RiskFactors,
        risk_level: RiskLevel,
        financial_metrics: Dict[str, Any],
        transaction_summary: Optional[TransactionSummary]
    ) -> CreditAssessmentResult:
        """Create fallback assessment with Paisalo business rules integration."""
        
        # Get Paisalo validation results
        paisalo_validation = PaisaloBusinessRules.perform_complete_validation(application)
        
        # Use Paisalo rules for approval decision
        approved = paisalo_validation['is_valid']
        
        # Calculate recommended loan amount using Paisalo rules
        recommended_amount = None
        recommended_interest_rate = None
        
        if approved and paisalo_validation['emi_details']:
            recommended_amount = float(application.loan_amount)  # Full amount if approved
            recommended_interest_rate = paisalo_validation['emi_details']['annual_roi']
        
        # Generate Paisalo-specific reasoning
        reasoning_parts = [
            "=== PAISALO CREDIT ASSESSMENT ===",
            f"Application processed using Paisalo business rules and policies.",
            "",
            PaisaloBusinessRules.generate_paisalo_assessment_summary(application, paisalo_validation)
        ]
        
        if not approved:
            reasoning_parts.extend([
                "",
                "Additional Analysis:",
                f"Standard credit score: {application.credit_score}",
                f"Debt-to-income ratio: {financial_metrics.get('debt_to_income_ratio', 0.0):.1%}",
                f"Risk factors identified: {risk_factors.risk_factors_count}"
            ])
        
        reasoning = "\n".join(reasoning_parts)
        
        # Generate Paisalo-specific recommendations
        recommendations = []
        if approved:
            if paisalo_validation['emi_details']:
                emi = paisalo_validation['emi_details']
                recommendations.extend([
                    f"Monthly EMI: ₹{emi['monthly_emi']:,.2f} using SLM method",
                    f"Total interest: ₹{emi['total_interest']:,.2f}",
                    "Set up automatic EMI payments to avoid defaults",
                    "Maintain stable income throughout loan tenure"
                ])
        else:
            # Add specific recommendations based on failed validations
            for reason in paisalo_validation['rejection_reasons']:
                if 'age' in reason.lower():
                    recommendations.append("Applicant must be between 21-57 years old")
                elif 'credit score' in reason.lower():
                    recommendations.append("Improve credit score to 18-650 range")
                elif 'loan amount' in reason.lower():
                    recommendations.append("Apply for loan amount between ₹50,000-₹1,00,000")
                elif 'document' in reason.lower():
                    recommendations.append("Provide valid documents: (Voter ID + PAN) OR (DL + PAN)")
                elif 'expense' in reason.lower():
                    recommendations.append("Reduce monthly expenses to below 50% of income")
        
        if not recommendations:
            recommendations.append("Contact Paisalo customer service for assistance")
        
        return CreditAssessmentResult(
            application_id=application.application_id,
            assessment_id=assessment_id,
            approved=approved,
            risk_level=paisalo_validation['risk_level'],
            recommended_loan_amount=recommended_amount,
            recommended_interest_rate=recommended_interest_rate,
            confidence_scores=confidence_scores,
            risk_factors=risk_factors,
            transaction_summary=transaction_summary,
            reasoning=reasoning,
            recommendations=recommendations
        )
