"""
Vertex AI client for credit assessment agent.

This module provides integration with Google Cloud Vertex AI for intelligent
credit assessment using large language models.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import os

from google.cloud import aiplatform
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

from .data_models import (
    CreditApplication, 
    BankTransaction, 
    TransactionSummary,
    CreditAssessmentResult,
    ConfidenceScore,
    RiskFactors,
    RiskLevel
)

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Client for interacting with Google Cloud Vertex AI."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-pro"
    ):
        """
        Initialize Vertex AI client.
        
        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location
            model_name: Model name to use for predictions
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model_name = model_name
        
        if not self.project_id:
            raise ValueError("Google Cloud project ID must be provided")
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Vertex AI client."""
        try:
            # Initialize Vertex AI
            aiplatform.init(
                project=self.project_id,
                location=self.location
            )
            
            # Test authentication
            credentials, _ = default()
            logger.info(f"Initialized Vertex AI client for project: {self.project_id}")
            
        except DefaultCredentialsError as e:
            logger.error(f"Failed to authenticate with Google Cloud: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {str(e)}")
            raise
    
    async def assess_credit_application(
        self,
        application: CreditApplication,
        transaction_summary: Optional[TransactionSummary] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> CreditAssessmentResult:
        """
        Assess a credit application using Vertex AI.
        
        Args:
            application: Credit application data
            transaction_summary: Bank transaction analysis
            additional_context: Additional context for assessment
            
        Returns:
            Complete credit assessment result
        """
        try:
            start_time = datetime.utcnow()
            
            # Prepare assessment prompt
            prompt = self._build_assessment_prompt(
                application, transaction_summary, additional_context
            )
            
            # Get AI assessment
            ai_response = await self._generate_assessment(prompt)
            
            # Parse and validate response
            assessment_result = self._parse_assessment_response(
                ai_response, application.application_id
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            assessment_result.processing_time_seconds = processing_time
            
            logger.info(f"Completed credit assessment for {application.application_id}")
            return assessment_result
            
        except Exception as e:
            logger.error(f"Failed to assess credit application: {str(e)}")
            raise
    
    def _build_assessment_prompt(
        self,
        application: CreditApplication,
        transaction_summary: Optional[TransactionSummary],
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build the assessment prompt for the AI model."""
        
        prompt = f"""
You are an expert credit analyst tasked with evaluating a loan application. 
Analyze the provided information and provide a comprehensive assessment.

## APPLICATION DETAILS
- Applicant: {application.applicant_info.name}, Age: {application.applicant_info.age}
- Income: ${application.applicant_info.income:,.2f} annually
- Employment: {application.applicant_info.employment_status.value}
- Employment Duration: {application.applicant_info.employment_duration_months or 'Not specified'} months
- Credit Score: {application.credit_score}
- Requested Loan: ${application.loan_amount:,.2f}
- Loan Purpose: {application.loan_purpose.value}
- Loan Term: {application.requested_term_months} months
- Down Payment: ${application.down_payment or 0:,.2f}
- Existing Debt: ${application.existing_debt or 0:,.2f}
- Assets: ${application.assets or 0:,.2f}

"""
        
        if transaction_summary:
            prompt += f"""
## BANK TRANSACTION ANALYSIS
- Analysis Period: {transaction_summary.analysis_period_months} months
- Total Transactions: {transaction_summary.total_transactions}
- Average Monthly Income: ${transaction_summary.average_monthly_income:,.2f}
- Average Monthly Expenses: ${transaction_summary.average_monthly_expenses:,.2f}
- Income Stability Score: {transaction_summary.income_stability_score:.2f} (0-1 scale)
- Overdraft Incidents: {transaction_summary.overdraft_incidents}
- Large Transactions: {transaction_summary.large_transactions_count}

### Expense Breakdown:
"""
            for category, amount in transaction_summary.expense_patterns.items():
                prompt += f"- {category.title()}: ${amount:,.2f}\n"
        
        if additional_context:
            prompt += f"\n## ADDITIONAL CONTEXT\n{json.dumps(additional_context, indent=2)}\n"
        
        prompt += """

## ASSESSMENT REQUIREMENTS

Provide your assessment in the following JSON format:

{
  "approved": boolean,
  "risk_level": "low|medium|high|very_high",
  "recommended_loan_amount": number or null,
  "recommended_interest_rate": number (0-1) or null,
  "confidence_scores": {
    "overall_confidence": number (0-1),
    "credit_score_confidence": number (0-1),
    "income_confidence": number (0-1),
    "transaction_confidence": number (0-1),
    "application_confidence": number (0-1),
    "data_quality_score": number (0-1)
  },
  "risk_factors": {
    "high_debt_to_income": boolean,
    "insufficient_income": boolean,
    "poor_credit_history": boolean,
    "irregular_income": boolean,
    "excessive_expenses": boolean,
    "frequent_overdrafts": boolean,
    "short_employment_history": boolean,
    "high_loan_to_value": boolean,
    "risk_factors_count": number,
    "risk_level": "low|medium|high|very_high"
  },
  "reasoning": "Detailed explanation of the assessment decision",
  "recommendations": ["List of recommendations for the applicant"]
}

## ASSESSMENT CRITERIA

1. **Credit Score Analysis**: Evaluate creditworthiness based on credit score
   - Excellent (750+): Very low risk
   - Good (700-749): Low risk  
   - Fair (650-699): Medium risk
   - Poor (600-649): High risk
   - Very Poor (<600): Very high risk

2. **Income Assessment**: Analyze income stability and sufficiency
   - Debt-to-income ratio should be < 36%
   - Income should be 3x monthly payment
   - Employment history should be stable

3. **Transaction Analysis**: Review spending patterns and financial behavior
   - Income stability score > 0.7 is preferred
   - Minimal overdrafts indicate good financial management
   - Reasonable expense patterns

4. **Risk Factors**: Identify and weight risk factors appropriately

5. **Confidence Scoring**: Provide confidence levels for each assessment component

Provide a thorough, professional assessment that considers all available data.
"""
        
        return prompt
    
    async def _generate_assessment(self, prompt: str) -> str:
        """Generate assessment using Vertex AI model."""
        try:
            # Use Vertex AI Generative AI
            try:
                from vertexai.generative_models import GenerativeModel
            except ImportError:
                raise ImportError("vertexai package not installed. Install with: pip install google-cloud-aiplatform")
            
            model = GenerativeModel(self.model_name)
            
            # Generate response
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.1,  # Low temperature for consistent results
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Failed to generate AI assessment: {str(e)}")
            raise
    
    def _parse_assessment_response(
        self, 
        ai_response: str, 
        application_id: str
    ) -> CreditAssessmentResult:
        """Parse AI response into CreditAssessmentResult."""
        try:
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_str = ai_response[json_start:json_end]
            assessment_data = json.loads(json_str)
            
            # Create confidence scores
            confidence_data = assessment_data.get('confidence_scores', {})
            confidence_scores = ConfidenceScore(
                overall_confidence=confidence_data.get('overall_confidence', 0.5),
                credit_score_confidence=confidence_data.get('credit_score_confidence', 0.5),
                income_confidence=confidence_data.get('income_confidence', 0.5),
                transaction_confidence=confidence_data.get('transaction_confidence', 0.5),
                application_confidence=confidence_data.get('application_confidence', 0.5),
                data_quality_score=confidence_data.get('data_quality_score', 0.5)
            )
            
            # Create risk factors
            risk_data = assessment_data.get('risk_factors', {})
            risk_factors = RiskFactors(
                high_debt_to_income=risk_data.get('high_debt_to_income', False),
                insufficient_income=risk_data.get('insufficient_income', False),
                poor_credit_history=risk_data.get('poor_credit_history', False),
                irregular_income=risk_data.get('irregular_income', False),
                excessive_expenses=risk_data.get('excessive_expenses', False),
                frequent_overdrafts=risk_data.get('frequent_overdrafts', False),
                short_employment_history=risk_data.get('short_employment_history', False),
                high_loan_to_value=risk_data.get('high_loan_to_value', False),
                risk_factors_count=risk_data.get('risk_factors_count', 0),
                risk_level=RiskLevel(risk_data.get('risk_level', 'medium'))
            )
            
            # Create assessment result
            result = CreditAssessmentResult(
                application_id=application_id,
                assessment_id=f"assess_{application_id}_{int(datetime.utcnow().timestamp())}",
                approved=assessment_data.get('approved', False),
                risk_level=RiskLevel(assessment_data.get('risk_level', 'medium')),
                recommended_loan_amount=assessment_data.get('recommended_loan_amount'),
                recommended_interest_rate=assessment_data.get('recommended_interest_rate'),
                confidence_scores=confidence_scores,
                risk_factors=risk_factors,
                reasoning=assessment_data.get('reasoning', 'Assessment completed'),
                recommendations=assessment_data.get('recommendations', [])
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {str(e)}")
            # Return default assessment on parse failure
            return self._create_default_assessment(application_id, "Failed to parse AI response")
        except Exception as e:
            logger.error(f"Failed to parse assessment response: {str(e)}")
            return self._create_default_assessment(application_id, f"Error: {str(e)}")
    
    def _create_default_assessment(
        self, 
        application_id: str, 
        error_message: str
    ) -> CreditAssessmentResult:
        """Create a default assessment when AI processing fails."""
        return CreditAssessmentResult(
            application_id=application_id,
            assessment_id=f"assess_{application_id}_default_{int(datetime.utcnow().timestamp())}",
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
            reasoning=f"Assessment failed due to technical error: {error_message}",
            recommendations=["Please resubmit application", "Contact support if issue persists"]
        )
    
    async def analyze_transaction_patterns(
        self, 
        transactions: List[BankTransaction]
    ) -> Dict[str, Any]:
        """
        Analyze transaction patterns using AI.
        
        Args:
            transactions: List of bank transactions
            
        Returns:
            Analysis results with insights and patterns
        """
        try:
            if not transactions:
                return {"insights": [], "patterns": {}, "risk_indicators": []}
            
            # Prepare transaction data for analysis
            transaction_data = []
            for tx in transactions[:100]:  # Limit to recent 100 transactions
                transaction_data.append({
                    "date": tx.date.isoformat(),
                    "description": tx.description,
                    "amount": float(tx.amount),
                    "type": tx.transaction_type.value,
                    "balance": float(tx.balance) if tx.balance else None
                })
            
            prompt = f"""
Analyze the following bank transactions and provide insights about spending patterns, 
financial behavior, and potential risk indicators.

TRANSACTIONS:
{json.dumps(transaction_data, indent=2)}

Provide analysis in JSON format:
{{
  "insights": ["List of key insights about financial behavior"],
  "patterns": {{
    "spending_trends": "Description of spending trends",
    "income_patterns": "Description of income patterns",
    "unusual_activity": "Any unusual or concerning activity"
  }},
  "risk_indicators": ["List of potential risk factors identified"],
  "financial_health_score": number (0-1),
  "recommendations": ["Recommendations for financial improvement"]
}}
"""
            
            response = await self._generate_assessment(prompt)
            
            # Parse response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > 0:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            return {"insights": [], "patterns": {}, "risk_indicators": []}
            
        except Exception as e:
            logger.error(f"Failed to analyze transaction patterns: {str(e)}")
            return {"insights": [], "patterns": {}, "risk_indicators": [], "error": str(e)}
    
    async def generate_assessment_explanation(
        self,
        assessment_result: CreditAssessmentResult,
        application: CreditApplication
    ) -> str:
        """
        Generate a detailed explanation of the assessment decision.
        
        Args:
            assessment_result: The assessment result to explain
            application: Original application data
            
        Returns:
            Detailed explanation text
        """
        try:
            prompt = f"""
Generate a clear, professional explanation for the following credit assessment decision:

APPLICATION:
- Applicant: {application.applicant_info.name}
- Credit Score: {application.credit_score}
- Income: ${application.applicant_info.income:,.2f}
- Requested Loan: ${application.loan_amount:,.2f}

ASSESSMENT RESULT:
- Decision: {'APPROVED' if assessment_result.approved else 'DECLINED'}
- Risk Level: {assessment_result.risk_level.value.upper()}
- Overall Confidence: {assessment_result.confidence_scores.overall_confidence:.1%}
- Risk Factors Count: {assessment_result.risk_factors.risk_factors_count}

REASONING: {assessment_result.reasoning}

Provide a clear, empathetic explanation that:
1. Explains the decision in simple terms
2. Highlights key factors that influenced the decision
3. Provides constructive feedback
4. Suggests next steps or improvements if declined

Keep the explanation professional but accessible to non-experts.
"""
            
            explanation = await self._generate_assessment(prompt)
            return explanation.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate assessment explanation: {str(e)}")
            return assessment_result.reasoning
