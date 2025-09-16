#!/usr/bin/env python3
"""
Basic functionality test for Credit Assessment Agent POC.

This script tests the core functionality without requiring Vertex AI credentials.
"""

import json
import asyncio
from decimal import Decimal
from datetime import datetime, date
from pathlib import Path

from credit_assessment_agent.shared_libraries.data_models import (
    CreditApplication,
    ApplicantInfo,
    BankTransaction,
    TransactionType,
    EmploymentStatus,
    LoanPurpose
)
from credit_assessment_agent.shared_libraries.utils import (
    extract_financial_metrics,
    calculate_confidence_score,
    calculate_risk_score,
    validate_credit_score
)
from credit_assessment_agent.shared_libraries.pdf_processor import PDFProcessor
from credit_assessment_agent.agent import CreditAssessmentAgent


def test_data_models():
    """Test data model validation."""
    print("🧪 Testing data models...")
    
    # Test ApplicantInfo
    applicant = ApplicantInfo(
        name="John Doe",
        age=35,
        income=Decimal('75000'),
        employment_status=EmploymentStatus.EMPLOYED,
        employment_duration_months=24,
        address="123 Main St",
        phone="+1-555-123-4567",
        email="john.doe@email.com"
    )
    
    # Test CreditApplication
    application = CreditApplication(
        application_id="TEST_001",
        applicant_info=applicant,
        credit_score=720,
        loan_amount=Decimal('25000'),
        loan_purpose=LoanPurpose.HOME_IMPROVEMENT,
        requested_term_months=60,
        down_payment=Decimal('5000'),
        existing_debt=Decimal('15000'),
        assets=Decimal('50000')
    )
    
    print(f"✅ Created application for {application.applicant_info.name}")
    print(f"   Credit Score: {application.credit_score}")
    print(f"   Loan Amount: ${application.loan_amount:,}")
    
    return application


def test_financial_metrics(application):
    """Test financial metrics calculation."""
    print("\n💰 Testing financial metrics...")
    
    metrics = extract_financial_metrics(application)
    
    print(f"✅ Financial metrics calculated:")
    print(f"   Annual Income: ${metrics.get('annual_income', 0):,.2f}")
    print(f"   Monthly Income: ${metrics.get('monthly_income', 0):,.2f}")
    print(f"   Debt-to-Income Ratio: {metrics.get('debt_to_income_ratio', 0):.1%}")
    print(f"   Credit Score Tier: {metrics.get('credit_score_tier', 'unknown').title()}")
    
    return metrics


def test_confidence_scoring(application):
    """Test confidence score calculation."""
    print("\n📊 Testing confidence scoring...")
    
    confidence = calculate_confidence_score(
        credit_score=application.credit_score,
        income=application.applicant_info.income,
        employment_months=application.applicant_info.employment_duration_months,
        data_completeness=0.9
    )
    
    print(f"✅ Confidence scores calculated:")
    print(f"   Overall Confidence: {confidence.overall_confidence:.1%}")
    print(f"   Credit Score Confidence: {confidence.credit_score_confidence:.1%}")
    print(f"   Income Confidence: {confidence.income_confidence:.1%}")
    
    return confidence


def test_risk_assessment(application, metrics):
    """Test risk assessment calculation."""
    print("\n⚠️  Testing risk assessment...")
    
    risk_score, risk_level = calculate_risk_score(
        credit_score=application.credit_score,
        debt_to_income_ratio=metrics.get('debt_to_income_ratio', 0),
        income_stability=0.8,
        overdraft_count=1
    )
    
    print(f"✅ Risk assessment completed:")
    print(f"   Risk Score: {risk_score:.2f}")
    print(f"   Risk Level: {risk_level.value.title()}")
    
    return risk_score, risk_level


def create_sample_transactions():
    """Create sample bank transactions for testing."""
    print("\n🏦 Creating sample transactions...")
    
    transactions = [
        BankTransaction(
            transaction_id="tx_001",
            date=date(2024, 8, 1),
            description="SALARY DEPOSIT",
            amount=Decimal('6250.00'),
            transaction_type=TransactionType.CREDIT,
            balance=Decimal('8500.00')
        ),
        BankTransaction(
            transaction_id="tx_002",
            date=date(2024, 8, 2),
            description="GROCERY STORE",
            amount=Decimal('125.50'),
            transaction_type=TransactionType.DEBIT,
            balance=Decimal('8374.50')
        ),
        BankTransaction(
            transaction_id="tx_003",
            date=date(2024, 8, 3),
            description="ELECTRIC UTILITY",
            amount=Decimal('89.25'),
            transaction_type=TransactionType.DEBIT,
            balance=Decimal('8285.25')
        ),
        BankTransaction(
            transaction_id="tx_004",
            date=date(2024, 8, 15),
            description="SALARY DEPOSIT",
            amount=Decimal('6250.00'),
            transaction_type=TransactionType.CREDIT,
            balance=Decimal('14535.25')
        ),
        BankTransaction(
            transaction_id="tx_005",
            date=date(2024, 8, 16),
            description="RENT PAYMENT",
            amount=Decimal('1200.00'),
            transaction_type=TransactionType.DEBIT,
            balance=Decimal('13335.25')
        )
    ]
    
    print(f"✅ Created {len(transactions)} sample transactions")
    return transactions


async def test_credit_assessment(application, transactions):
    """Test the main credit assessment functionality."""
    print("\n🎯 Testing credit assessment (without Vertex AI)...")
    
    try:
        # Initialize agent without Vertex AI
        agent = CreditAssessmentAgent(vertex_ai_client=None)
        
        # Perform assessment
        result = await agent.assess_credit_application(
            application=application,
            bank_transactions=transactions,
            priority="normal"
        )
        
        print(f"✅ Credit assessment completed:")
        print(f"   Application ID: {result.application_id}")
        print(f"   Assessment ID: {result.assessment_id}")
        print(f"   Decision: {'APPROVED' if result.approved else 'DECLINED'}")
        print(f"   Risk Level: {result.risk_level.value.title()}")
        print(f"   Overall Confidence: {result.confidence_scores.overall_confidence:.1%}")
        print(f"   Processing Time: {result.processing_time_seconds:.2f}s")
        
        if result.recommended_loan_amount:
            print(f"   Recommended Amount: ${result.recommended_loan_amount:,.2f}")
        
        print(f"\n📝 Reasoning: {result.reasoning[:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Credit assessment failed: {str(e)}")
        return None


def test_sample_data_loading():
    """Test loading sample data from JSON file."""
    print("\n📄 Testing sample data loading...")
    
    try:
        sample_file = Path("sample_data/credit_applications.json")
        if sample_file.exists():
            with open(sample_file, 'r') as f:
                sample_data = json.load(f)
            
            print(f"✅ Loaded {len(sample_data)} sample applications")
            
            # Test parsing first application
            first_app_data = sample_data[0]
            print(f"   First application: {first_app_data['applicant_info']['name']}")
            print(f"   Credit Score: {first_app_data['credit_score']}")
            
            return sample_data
        else:
            print("⚠️  Sample data file not found")
            return None
            
    except Exception as e:
        print(f"❌ Failed to load sample data: {str(e)}")
        return None


async def main():
    """Run all tests."""
    print("🚀 Starting Credit Assessment Agent POC Tests\n")
    
    # Test 1: Data Models
    application = test_data_models()
    
    # Test 2: Financial Metrics
    metrics = test_financial_metrics(application)
    
    # Test 3: Confidence Scoring
    confidence = test_confidence_scoring(application)
    
    # Test 4: Risk Assessment
    risk_score, risk_level = test_risk_assessment(application, metrics)
    
    # Test 5: Sample Transactions
    transactions = create_sample_transactions()
    
    # Test 6: Credit Assessment
    result = await test_credit_assessment(application, transactions)
    
    # Test 7: Sample Data Loading
    sample_data = test_sample_data_loading()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    tests_passed = 0
    total_tests = 7
    
    if application: tests_passed += 1
    if metrics: tests_passed += 1
    if confidence: tests_passed += 1
    if risk_score is not None: tests_passed += 1
    if transactions: tests_passed += 1
    if result: tests_passed += 1
    if sample_data: tests_passed += 1
    
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The Credit Assessment Agent POC is working correctly.")
        print("\n🚀 Next steps:")
        print("   1. Configure Google Cloud credentials in .env file")
        print("   2. Run: uvicorn main:app --reload")
        print("   3. Visit: http://localhost:8000/docs")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
