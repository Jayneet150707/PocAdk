#!/usr/bin/env python3
"""
Test script for Paisalo business rules validation.

This script tests various scenarios to ensure Paisalo business rules
are working correctly.
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from credit_assessment_agent.shared_libraries.data_models import (
    CreditApplication, ApplicantInfo, DocumentType, EmploymentStatus, LoanPurpose
)
from credit_assessment_agent.shared_libraries.paisalo_rules import PaisaloBusinessRules


def test_age_validation():
    """Test age validation rules."""
    print("=== Testing Age Validation ===")
    
    test_cases = [
        (20, False, "Below minimum age"),
        (21, True, "Minimum age"),
        (35, True, "Valid age"),
        (57, True, "Maximum age"),
        (58, False, "Above maximum age")
    ]
    
    for age, expected_valid, description in test_cases:
        is_valid, reason = PaisaloBusinessRules.validate_age(age)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"  {status} Age {age} ({description}): {reason}")
    
    print()


def test_credit_score_validation():
    """Test credit score validation rules."""
    print("=== Testing Credit Score Validation ===")
    
    test_cases = [
        (17, False, "Below minimum"),
        (18, True, "Minimum score"),
        (300, True, "Valid score"),
        (650, True, "Maximum score"),
        (651, False, "Above maximum")
    ]
    
    for score, expected_valid, description in test_cases:
        is_valid, reason = PaisaloBusinessRules.validate_credit_score(score)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"  {status} Score {score} ({description}): {reason}")
    
    print()


def test_loan_amount_validation():
    """Test loan amount validation rules."""
    print("=== Testing Loan Amount Validation ===")
    
    test_cases = [
        (Decimal('49999'), False, "Below minimum"),
        (Decimal('50000'), True, "Minimum amount"),
        (Decimal('75000'), True, "Valid amount"),
        (Decimal('100000'), True, "Maximum amount"),
        (Decimal('100001'), False, "Above maximum")
    ]
    
    for amount, expected_valid, description in test_cases:
        is_valid, reason = PaisaloBusinessRules.validate_loan_amount(amount)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"  {status} Amount ₹{amount:,.2f} ({description}): {reason}")
    
    print()


def test_pan_validation():
    """Test PAN number validation."""
    print("=== Testing PAN Validation ===")
    
    test_cases = [
        ("ABCDE1234F", True, "Valid PAN"),
        ("abcde1234f", True, "Valid PAN (lowercase)"),
        ("ABCDE1234", False, "Missing last letter"),
        ("ABCD1234F", False, "Too few letters"),
        ("ABCDEF1234F", False, "Too many letters"),
        ("12345ABCDF", False, "Wrong format"),
        (None, False, "No PAN provided")
    ]
    
    for pan, expected_valid, description in test_cases:
        is_valid, reason = PaisaloBusinessRules.validate_pan_number(pan)
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"  {status} PAN {pan} ({description}): {reason}")
    
    print()


def test_emi_calculation():
    """Test EMI calculation using SLM method."""
    print("=== Testing EMI Calculation (SLM) ===")
    
    test_cases = [
        (Decimal('50000'), 12, 0.07),  # 12 months, 7%
        (Decimal('75000'), 24, 0.09),  # 24 months, 9%
        (Decimal('100000'), 36, 0.12), # 36 months, 12%
        (Decimal('80000'), 48, 0.18),  # 48 months, 18%
    ]
    
    for amount, term, expected_roi in test_cases:
        try:
            monthly_emi, annual_roi = PaisaloBusinessRules.calculate_emi_slm(amount, term)
            
            # Calculate expected EMI manually
            years = Decimal(term) / 12
            total_interest = amount * Decimal(str(expected_roi)) * years
            total_amount = amount + total_interest
            expected_emi = total_amount / term
            
            emi_match = abs(monthly_emi - expected_emi) < Decimal('0.01')
            roi_match = abs(annual_roi - expected_roi) < 0.001
            
            status = "✅ PASS" if emi_match and roi_match else "❌ FAIL"
            print(f"  {status} Amount: ₹{amount:,.2f}, Term: {term}m")
            print(f"    EMI: ₹{monthly_emi:,.2f} (Expected: ₹{expected_emi:,.2f})")
            print(f"    ROI: {annual_roi:.1%} (Expected: {expected_roi:.1%})")
            print(f"    Total Interest: ₹{(monthly_emi * term - amount):,.2f}")
            
        except Exception as e:
            print(f"  ❌ FAIL Amount: ₹{amount:,.2f}, Term: {term}m - Error: {e}")
        
        print()


def test_document_validation():
    """Test document validation rules."""
    print("=== Testing Document Validation ===")
    
    # Create test applications with different document combinations
    test_cases = [
        {
            "description": "Valid: Voter ID + PAN",
            "pan_number": "ABCDE1234F",
            "has_voter_id": True,
            "has_driving_license": False,
            "documents_provided": [DocumentType.VOTER_ID, DocumentType.PAN],
            "expected_valid": True
        },
        {
            "description": "Valid: Driving License + PAN",
            "pan_number": "ABCDE1234F",
            "has_voter_id": False,
            "has_driving_license": True,
            "documents_provided": [DocumentType.DRIVING_LICENSE, DocumentType.PAN],
            "expected_valid": True
        },
        {
            "description": "Invalid: Only PAN",
            "pan_number": "ABCDE1234F",
            "has_voter_id": False,
            "has_driving_license": False,
            "documents_provided": [DocumentType.PAN],
            "expected_valid": False
        },
        {
            "description": "Invalid: No PAN",
            "pan_number": None,
            "has_voter_id": True,
            "has_driving_license": False,
            "documents_provided": [DocumentType.VOTER_ID],
            "expected_valid": False
        },
        {
            "description": "Invalid: Invalid PAN format",
            "pan_number": "INVALID123",
            "has_voter_id": True,
            "has_driving_license": False,
            "documents_provided": [DocumentType.VOTER_ID, DocumentType.PAN],
            "expected_valid": False,
            "skip_pydantic": True  # Skip this test due to Pydantic validation
        }
    ]
    
    for test_case in test_cases:
        # Skip tests that would fail Pydantic validation
        if test_case.get("skip_pydantic", False):
            print(f"  ⏭️ SKIP {test_case['description']}: Pydantic validation prevents this test")
            continue
            
        try:
            # Create test application
            applicant = ApplicantInfo(
                name="Test User",
                age=30,
                income=Decimal('50000'),
                employment_status=EmploymentStatus.EMPLOYED,
                pan_number=test_case["pan_number"],
                has_voter_id=test_case["has_voter_id"],
                has_driving_license=test_case["has_driving_license"],
                documents_provided=test_case["documents_provided"]
            )
            
            application = CreditApplication(
                application_id="TEST_001",
                applicant_info=applicant,
                credit_score=400,
                loan_amount=Decimal('75000'),
                loan_purpose=LoanPurpose.PERSONAL,
                requested_term_months=24
            )
            
            is_valid, reason = PaisaloBusinessRules.validate_documents(application)
            expected_valid = test_case["expected_valid"]
            status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
            print(f"  {status} {test_case['description']}: {reason}")
            
        except Exception as e:
            # Handle Pydantic validation errors
            if "Invalid PAN format" in str(e):
                expected_valid = test_case["expected_valid"]
                status = "✅ PASS" if not expected_valid else "❌ FAIL"
                print(f"  {status} {test_case['description']}: Pydantic validation caught invalid PAN")
            else:
                print(f"  ❌ FAIL {test_case['description']}: Unexpected error: {e}")
    
    print()


def test_income_expense_validation():
    """Test income vs expense ratio validation."""
    print("=== Testing Income vs Expense Validation ===")
    
    test_cases = [
        {
            "description": "Valid: 40% expense ratio",
            "personal_income": Decimal('50000'),
            "family_income": Decimal('30000'),
            "personal_expenses": Decimal('20000'),
            "family_expenses": Decimal('12000'),  # Total: 32k/80k = 40%
            "expected_valid": True
        },
        {
            "description": "Valid: Exactly 50% expense ratio",
            "personal_income": Decimal('40000'),
            "family_income": Decimal('20000'),
            "personal_expenses": Decimal('20000'),
            "family_expenses": Decimal('10000'),  # Total: 30k/60k = 50%
            "expected_valid": True
        },
        {
            "description": "Invalid: 60% expense ratio",
            "personal_income": Decimal('30000'),
            "family_income": Decimal('20000'),
            "personal_expenses": Decimal('20000'),
            "family_expenses": Decimal('10000'),  # Total: 30k/50k = 60%
            "expected_valid": False
        },
        {
            "description": "Invalid: Zero income",
            "personal_income": Decimal('0'),
            "family_income": None,
            "personal_expenses": Decimal('10000'),
            "family_expenses": None,
            "expected_valid": False
        }
    ]
    
    for test_case in test_cases:
        # Create test application
        applicant = ApplicantInfo(
            name="Test User",
            age=30,
            income=test_case["personal_income"],
            family_income=test_case["family_income"],
            personal_expenses=test_case["personal_expenses"],
            family_expenses=test_case["family_expenses"],
            employment_status=EmploymentStatus.EMPLOYED,
            pan_number="ABCDE1234F",
            has_voter_id=True,
            documents_provided=[DocumentType.VOTER_ID, DocumentType.PAN]
        )
        
        application = CreditApplication(
            application_id="TEST_001",
            applicant_info=applicant,
            credit_score=400,
            loan_amount=Decimal('75000'),
            loan_purpose=LoanPurpose.PERSONAL,
            requested_term_months=24
        )
        
        is_valid, reason = PaisaloBusinessRules.validate_income_expense_ratio(application)
        expected_valid = test_case["expected_valid"]
        status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
        print(f"  {status} {test_case['description']}: {reason}")
    
    print()


def test_complete_validation():
    """Test complete validation with sample application."""
    print("=== Testing Complete Validation ===")
    
    # Load sample application
    with open('sample_paisalo_request.json', 'r') as f:
        sample_data = json.load(f)
    
    # Convert to application object
    app_data = sample_data['credit_application']
    applicant_data = app_data['applicant_info']
    
    applicant = ApplicantInfo(
        name=applicant_data['name'],
        age=applicant_data['age'],
        income=Decimal(str(applicant_data['income'])),
        family_income=Decimal(str(applicant_data['family_income'])),
        personal_expenses=Decimal(str(applicant_data['personal_expenses'])),
        family_expenses=Decimal(str(applicant_data['family_expenses'])),
        employment_status=EmploymentStatus(applicant_data['employment_status']),
        employment_duration_months=applicant_data['employment_duration_months'],
        phone=applicant_data['phone'],
        email=applicant_data['email'],
        address=applicant_data['address'],
        pan_number=applicant_data['pan_number'],
        has_voter_id=applicant_data['has_voter_id'],
        has_driving_license=applicant_data['has_driving_license'],
        documents_provided=[DocumentType(doc) for doc in applicant_data['documents_provided']]
    )
    
    application = CreditApplication(
        application_id=app_data['application_id'],
        applicant_info=applicant,
        credit_score=app_data['credit_score'],
        loan_amount=Decimal(str(app_data['loan_amount'])),
        loan_purpose=LoanPurpose(app_data['loan_purpose']),
        requested_term_months=app_data['requested_term_months']
    )
    
    # Perform complete validation
    results = PaisaloBusinessRules.perform_complete_validation(application)
    
    print(f"Application ID: {application.application_id}")
    print(f"Overall Valid: {'✅ YES' if results['is_valid'] else '❌ NO'}")
    print(f"Risk Level: {results['risk_level'].value.upper()}")
    print()
    
    print("Individual Validations:")
    for validation_name, validation_data in results['validations'].items():
        status = "✅ PASS" if validation_data['valid'] else "❌ FAIL"
        print(f"  {status} {validation_name.replace('_', ' ').title()}: {validation_data['reason']}")
    
    if results['emi_details']:
        print("\nEMI Details:")
        emi = results['emi_details']
        print(f"  Monthly EMI: ₹{emi['monthly_emi']:,.2f}")
        print(f"  Annual ROI: {emi['annual_roi']:.1%}")
        print(f"  Total Interest: ₹{emi['total_interest']:,.2f}")
        print(f"  Total Amount: ₹{emi['total_amount']:,.2f}")
        print(f"  Method: {emi['calculation_method']}")
    
    if results['rejection_reasons']:
        print("\nRejection Reasons:")
        for reason in results['rejection_reasons']:
            print(f"  • {reason}")
    
    if results['warnings']:
        print("\nWarnings:")
        for warning in results['warnings']:
            print(f"  ⚠️ {warning}")
    
    print()
    
    # Generate assessment summary
    summary = PaisaloBusinessRules.generate_paisalo_assessment_summary(application, results)
    print("Assessment Summary:")
    print(summary)


def main():
    """Run all tests."""
    print("🏦 PAISALO BUSINESS RULES VALIDATION TESTS")
    print("=" * 50)
    print()
    
    try:
        test_age_validation()
        test_credit_score_validation()
        test_loan_amount_validation()
        test_pan_validation()
        test_emi_calculation()
        test_document_validation()
        test_income_expense_validation()
        test_complete_validation()
        
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
