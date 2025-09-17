"""
AI Prompts for Simple Credit Assessment

Prompts for Google ADK agents when using AI capabilities.
These demonstrate how to structure prompts for credit assessment tasks.
"""

from typing import Dict, Any
from .models import ApplicantInfo, LoanRequest


class CreditAssessmentPrompts:
    """Prompts for credit assessment AI interactions."""
    
    SYSTEM_PROMPT = """
You are a professional credit assessment AI agent specializing in loan application analysis.

Your role is to:
1. Analyze credit applications objectively and fairly
2. Identify risk factors and opportunities
3. Provide clear, actionable recommendations
4. Explain your reasoning transparently
5. Follow regulatory compliance guidelines

Always be:
- Fair and unbiased in your assessments
- Transparent about your reasoning
- Focused on financial factors only
- Compliant with fair lending practices
- Professional and helpful in your recommendations

You have access to applicant financial information, credit scores, and loan request details.
Base your analysis on quantitative factors and established credit assessment principles.
"""
    
    @staticmethod
    def create_risk_assessment_prompt(applicant: ApplicantInfo, loan_request: LoanRequest) -> str:
        """Create prompt for AI-powered risk assessment."""
        return f"""
Analyze the following credit application for risk factors:

APPLICANT PROFILE:
- Name: {applicant.name}
- Age: {applicant.age}
- Annual Income: ${applicant.annual_income:,.2f}
- Monthly Expenses: ${applicant.monthly_expenses:,.2f}
- Employment: {applicant.employment_status.value} ({applicant.employment_duration_months} months)
- Credit Score: {applicant.credit_score}
- Existing Debt: ${applicant.existing_debt:,.2f}

LOAN REQUEST:
- Amount: ${loan_request.amount:,.2f}
- Purpose: {loan_request.purpose.value}
- Term: {loan_request.term_months} months

Please analyze:
1. Key risk factors present in this application
2. Debt-to-income ratio implications
3. Credit score adequacy for the requested amount
4. Employment stability assessment
5. Overall risk level (Low/Medium/High/Very High)

Provide specific, quantitative analysis where possible.
"""
    
    @staticmethod
    def create_decision_prompt(applicant: ApplicantInfo, loan_request: LoanRequest, 
                             risk_analysis: str) -> str:
        """Create prompt for AI-powered decision making."""
        return f"""
Based on the following credit application and risk analysis, make a loan decision:

APPLICANT: {applicant.name}
REQUESTED AMOUNT: ${loan_request.amount:,.2f}
REQUESTED TERM: {loan_request.term_months} months

RISK ANALYSIS:
{risk_analysis}

Please provide:
1. DECISION: Approve or Reject (with clear reasoning)
2. If approved:
   - Recommended loan amount (may be different from requested)
   - Recommended interest rate
   - Recommended term
   - Key conditions or requirements
3. If rejected:
   - Primary reasons for rejection
   - What the applicant could improve
   - Potential for future approval

4. RECOMMENDATIONS: Specific advice for the applicant

Be decisive but fair. Focus on financial factors and risk mitigation.
Explain your reasoning clearly and provide actionable guidance.
"""
    
    @staticmethod
    def create_explanation_prompt(decision_result: Dict[str, Any]) -> str:
        """Create prompt for generating customer-friendly explanations."""
        approved = decision_result.get('approved', False)
        risk_level = decision_result.get('risk_level', 'unknown')
        
        return f"""
Create a clear, customer-friendly explanation for this credit decision:

DECISION: {'APPROVED' if approved else 'REJECTED'}
RISK LEVEL: {risk_level}

The explanation should:
1. Be written in plain English (avoid jargon)
2. Explain the key factors that influenced the decision
3. Provide specific, actionable next steps
4. Be encouraging and constructive (even for rejections)
5. Include relevant financial education tips

Keep the tone professional but friendly and supportive.
Focus on helping the customer understand and improve their financial situation.
"""
    
    @staticmethod
    def create_scenario_analysis_prompt(applicant: ApplicantInfo, loan_request: LoanRequest) -> str:
        """Create prompt for analyzing alternative loan scenarios."""
        return f"""
Analyze alternative loan scenarios for this applicant:

CURRENT REQUEST:
- Amount: ${loan_request.amount:,.2f}
- Term: {loan_request.term_months} months
- Purpose: {loan_request.purpose.value}

APPLICANT PROFILE:
- Income: ${applicant.annual_income:,.2f}
- Credit Score: {applicant.credit_score}
- Existing Debt: ${applicant.existing_debt:,.2f}

Please analyze these alternative scenarios:
1. Reduced loan amount (75% of requested)
2. Extended repayment term (+12 months)
3. Different loan purpose category
4. Co-signer option benefits

For each scenario, evaluate:
- Approval likelihood
- Risk level changes
- Monthly payment impact
- Total cost implications
- Pros and cons for the applicant

Recommend the best alternative if the original request isn't optimal.
"""
    
    COMPLIANCE_GUIDELINES = """
FAIR LENDING COMPLIANCE GUIDELINES:

1. PROHIBITED FACTORS:
   - Race, color, religion, national origin
   - Sex, marital status, age (except minimum age requirements)
   - Receipt of public assistance
   - Exercise of consumer rights

2. PERMITTED FACTORS:
   - Credit history and score
   - Income and employment history
   - Debt-to-income ratio
   - Collateral and down payment
   - Loan purpose and amount

3. DOCUMENTATION REQUIREMENTS:
   - All decisions must be based on documented criteria
   - Adverse action notices required for rejections
   - Consistent application of underwriting standards

4. BEST PRACTICES:
   - Use objective, quantifiable criteria
   - Apply standards consistently
   - Provide clear reasoning for decisions
   - Offer alternatives when possible
   - Maintain detailed records
"""

