#!/usr/bin/env python3
"""
Test Suite for Simple Credit Assessment

Comprehensive testing of Google ADK credit assessment system
with focus on agent behavior and business rules validation.
"""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from simple_credit_agent import (
    SimpleCreditAssessmentAgent,
    CreditApplication,
    ApplicantInfo,
    LoanRequest,
    AssessmentRequest,
    EmploymentStatus,
    LoanPurpose,
    RiskLevel,
    SimpleCreditRules
)


def test_business_rules():
    """Test core business rules validation."""
    print("=== Testing Business Rules ===")
    
    # Test age validation
    print("\n1. Age Validation:")
    test_cases = [
        (17, False, "Below minimum"),
        (18, True, "Minimum age"),
        (35, True, "Valid age"),
        (75, True, "Maximum age"),
        (76, False, "Above maximum")
    ]
    
    for age, expected, description in test_cases:
        valid, reason = SimpleCreditRules.validate_age(age)
        status = "✅ PASS" if valid == expected else "❌ FAIL"
        print(f"  {status} Age {age} ({description}): {reason}")
    
    # Test credit score validation
    print("\n2. Credit Score Validation:")
    test_cases = [
        (579, False, "Below minimum"),
        (580, True, "Minimum score"),
        (720, True, "Good score"),
        (850, True, "Excellent score")
    ]
    
    for score, expected, description in test_cases:
        valid, reason = SimpleCreditRules.validate_credit_score(score)
        status = "✅ PASS" if valid == expected else "❌ FAIL"
        print(f"  {status} Score {score} ({description}): {reason}")
    
    # Test income validation
    print("\n3. Income Validation:")
    test_cases = [
        (Decimal('29999'), Decimal('25000'), False, "Below minimum income"),
        (Decimal('30000'), Decimal('25000'), True, "Minimum income"),
        (Decimal('75000'), Decimal('25000'), True, "Good income"),
        (Decimal('50000'), Decimal('200000'), False, "Loan too high for income")
    ]
    
    for income, loan_amount, expected, description in test_cases:
        valid, reason = SimpleCreditRules.validate_income(income, loan_amount)
        status = "✅ PASS" if valid == expected else "❌ FAIL"
        print(f"  {status} Income ${income:,.2f}, Loan ${loan_amount:,.2f} ({description}): {reason}")


def test_risk_assessment():
    """Test risk assessment functionality."""
    print("\n=== Testing Risk Assessment ===")
    
    # Create test applicants with different risk profiles
    test_cases = [
        {
            "name": "Low Risk Applicant",
            "applicant": ApplicantInfo(
                name="John Low-Risk",
                age=35,
                email="john@example.com",
                phone="+1-555-0001",
                annual_income=Decimal('80000'),
                monthly_expenses=Decimal('3000'),
                employment_status=EmploymentStatus.EMPLOYED,
                employment_duration_months=36,
                credit_score=750,
                existing_debt=Decimal('5000')
            ),
            "loan": LoanRequest(
                amount=Decimal('25000'),
                purpose=LoanPurpose.PERSONAL,
                term_months=60
            ),
            "expected_risk": RiskLevel.LOW
        },
        {
            "name": "High Risk Applicant",
            "applicant": ApplicantInfo(
                name="Jane High-Risk",
                age=22,
                email="jane@example.com",
                phone="+1-555-0002",
                annual_income=Decimal('35000'),
                monthly_expenses=Decimal('2800'),
                employment_status=EmploymentStatus.EMPLOYED,
                employment_duration_months=3,
                credit_score=590,
                existing_debt=Decimal('15000')
            ),
            "loan": LoanRequest(
                amount=Decimal('40000'),
                purpose=LoanPurpose.AUTO,
                term_months=72
            ),
            "expected_risk": RiskLevel.HIGH
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        
        # Assess risk factors
        risk_factors = SimpleCreditRules.assess_risk_factors(
            test_case['applicant'], 
            test_case['loan']
        )
        
        print(f"  Risk Level: {risk_factors.risk_level.value.upper()}")
        print(f"  Risk Factors: {risk_factors.risk_count}/5")
        
        # Check individual factors
        factors = [
            ("High Debt-to-Income", risk_factors.high_debt_to_income),
            ("Low Credit Score", risk_factors.low_credit_score),
            ("Insufficient Income", risk_factors.insufficient_income),
            ("Short Employment", risk_factors.short_employment),
            ("High Expenses", risk_factors.high_expenses)
        ]
        
        for factor_name, is_present in factors:
            status = "❌" if is_present else "✅"
            print(f"    {status} {factor_name}")
        
        # Check if risk level matches expectation
        expected_match = risk_factors.risk_level == test_case['expected_risk']
        match_status = "✅ EXPECTED" if expected_match else "⚠️ UNEXPECTED"
        print(f"  {match_status} Risk Level Assessment")


async def test_agent_workflow():
    """Test complete agent workflow."""
    print("\n=== Testing Agent Workflow ===")
    
    # Initialize agent
    agent = SimpleCreditAssessmentAgent()
    print("✅ Agent initialized successfully")
    
    # Create test application
    applicant = ApplicantInfo(
        name="Test Applicant",
        age=30,
        email="test@example.com",
        phone="+1-555-0123",
        annual_income=Decimal('65000'),
        monthly_expenses=Decimal('3200'),
        employment_status=EmploymentStatus.EMPLOYED,
        employment_duration_months=24,
        credit_score=680,
        existing_debt=Decimal('8000')
    )
    
    loan_request = LoanRequest(
        amount=Decimal('30000'),
        purpose=LoanPurpose.HOME,
        term_months=60
    )
    
    application = CreditApplication(
        application_id="TEST_WORKFLOW_001",
        applicant=applicant,
        loan_request=loan_request
    )
    
    request = AssessmentRequest(application=application)
    
    print(f"📋 Processing application: {application.application_id}")
    print(f"   Applicant: {applicant.name}")
    print(f"   Amount: ${loan_request.amount:,.2f}")
    print(f"   Credit Score: {applicant.credit_score}")
    
    try:
        # Perform assessment
        result = await agent.assess_credit_application(request)
        
        print(f"\n✅ Assessment completed:")
        print(f"   Decision: {'APPROVED' if result.approved else 'REJECTED'}")
        print(f"   Risk Level: {result.risk_level.value.upper()}")
        print(f"   Overall Confidence: {result.confidence_scores.overall_confidence:.2%}")
        print(f"   Processing Time: {result.processing_time_seconds:.3f}s")
        
        if result.approved:
            print(f"   Recommended Amount: ${result.recommended_amount:,.2f}")
            print(f"   Recommended Rate: {result.recommended_rate:.2%}")
            print(f"   Recommended Term: {result.recommended_term} months")
        
        print(f"\n📝 Risk Factors ({result.risk_factors.risk_count}/5):")
        factors = [
            ("High Debt-to-Income", result.risk_factors.high_debt_to_income),
            ("Low Credit Score", result.risk_factors.low_credit_score),
            ("Insufficient Income", result.risk_factors.insufficient_income),
            ("Short Employment", result.risk_factors.short_employment),
            ("High Expenses", result.risk_factors.high_expenses)
        ]
        
        for factor_name, is_present in factors:
            status = "❌" if is_present else "✅"
            print(f"   {status} {factor_name}")
        
        print(f"\n💡 Recommendations ({len(result.recommendations)}):")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"   {i}. {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Assessment failed: {str(e)}")
        return False


def test_loan_limits():
    """Test loan limit calculations."""
    print("\n=== Testing Loan Limits ===")
    
    credit_scores = [580, 650, 700, 750, 800, 850]
    
    for score in credit_scores:
        max_amount = SimpleCreditRules.get_max_loan_amount(score)
        credit_tier = SimpleCreditRules.get_credit_tier(score)
        interest_rate = SimpleCreditRules.get_interest_rate(score, RiskLevel.LOW)
        
        print(f"Credit Score {score}:")
        print(f"  Tier: {credit_tier.title()}")
        print(f"  Max Loan: ${max_amount:,.2f}")
        print(f"  Base Rate: {interest_rate:.2%}")


def test_recommendations():
    """Test recommendation generation."""
    print("\n=== Testing Recommendations ===")
    
    # Test approved scenario
    print("\n1. Approved Application:")
    approved_applicant = ApplicantInfo(
        name="Approved Applicant",
        age=35,
        email="approved@example.com",
        phone="+1-555-0001",
        annual_income=Decimal('75000'),
        monthly_expenses=Decimal('3000'),
        employment_status=EmploymentStatus.EMPLOYED,
        employment_duration_months=36,
        credit_score=720,
        existing_debt=Decimal('5000')
    )
    
    approved_loan = LoanRequest(
        amount=Decimal('25000'),
        purpose=LoanPurpose.PERSONAL,
        term_months=60
    )
    
    approved_risk = SimpleCreditRules.assess_risk_factors(approved_applicant, approved_loan)
    approved_recs = SimpleCreditRules.generate_recommendations(
        approved_applicant, approved_loan, approved_risk, True
    )
    
    for i, rec in enumerate(approved_recs, 1):
        print(f"  {i}. {rec}")
    
    # Test rejected scenario
    print("\n2. Rejected Application:")
    rejected_applicant = ApplicantInfo(
        name="Rejected Applicant",
        age=25,
        email="rejected@example.com",
        phone="+1-555-0002",
        annual_income=Decimal('35000'),
        monthly_expenses=Decimal('2800'),
        employment_status=EmploymentStatus.EMPLOYED,
        employment_duration_months=3,
        credit_score=570,
        existing_debt=Decimal('20000')
    )
    
    rejected_loan = LoanRequest(
        amount=Decimal('50000'),
        purpose=LoanPurpose.AUTO,
        term_months=72
    )
    
    rejected_risk = SimpleCreditRules.assess_risk_factors(rejected_applicant, rejected_loan)
    rejected_recs = SimpleCreditRules.generate_recommendations(
        rejected_applicant, rejected_loan, rejected_risk, False
    )
    
    for i, rec in enumerate(rejected_recs, 1):
        print(f"  {i}. {rec}")


async def main():
    """Run all tests."""
    print("🧪 SIMPLE CREDIT ASSESSMENT TESTS")
    print("=" * 50)
    
    try:
        # Run synchronous tests
        test_business_rules()
        test_risk_assessment()
        test_loan_limits()
        test_recommendations()
        
        # Run asynchronous tests
        workflow_success = await test_agent_workflow()
        
        print("\n" + "=" * 50)
        if workflow_success:
            print("🎉 All tests completed successfully!")
            print("\n💡 To test the API:")
            print("   python simple_main.py")
            print("   Visit: http://localhost:8001/docs")
        else:
            print("❌ Some tests failed. Check the output above.")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

