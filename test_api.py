#!/usr/bin/env python3
"""
API Test Script for Paisalo Credit Assessment

This script tests the FastAPI endpoints to ensure they work correctly.
"""

import asyncio
import json
import sys
from pathlib import Path

# Test the API without actually starting the server
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from fastapi.testclient import TestClient

def test_api_endpoints():
    """Test all API endpoints."""
    print("🧪 Testing Paisalo Credit Assessment API")
    print("=" * 50)
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Health check
    print("\n1. Testing Health Check...")
    try:
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed: {data['status']}")
            print(f"   📊 Paisalo rules loaded: {data['paisalo_rules_loaded']}")
            print(f"   🤖 Vertex AI available: {data['vertex_ai_available']}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Business rules info
    print("\n2. Testing Business Rules Info...")
    try:
        response = client.get("/business-rules")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Business rules info retrieved")
            print(f"   📋 Age range: {data['paisalo_business_rules']['age_range']['minimum']}-{data['paisalo_business_rules']['age_range']['maximum']}")
            print(f"   💰 Loan range: ₹{data['paisalo_business_rules']['loan_amount_range']['minimum']:,.0f}-₹{data['paisalo_business_rules']['loan_amount_range']['maximum']:,.0f}")
        else:
            print(f"   ❌ Business rules failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Business rules error: {e}")
    
    # Test 3: Sample request
    print("\n3. Testing Sample Request...")
    try:
        response = client.get("/sample-request")
        if response.status_code == 200:
            sample_data = response.json()
            print("   ✅ Sample request retrieved")
            print(f"   👤 Applicant: {sample_data['credit_application']['applicant_info']['name']}")
            print(f"   💰 Loan amount: ₹{sample_data['credit_application']['loan_amount']:,.0f}")
        else:
            print(f"   ❌ Sample request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Sample request error: {e}")
    
    # Test 4: EMI calculation
    print("\n4. Testing EMI Calculation...")
    try:
        emi_request = {
            "loan_amount": 75000,
            "term_months": 24
        }
        response = client.post("/calculate-emi", json=emi_request)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ EMI calculation successful")
            print(f"   💰 Monthly EMI: ₹{data['monthly_emi']:,.2f}")
            print(f"   📊 ROI: {data['annual_roi']:.1%}")
            print(f"   💸 Total interest: ₹{data['total_interest']:,.2f}")
        else:
            print(f"   ❌ EMI calculation failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ EMI calculation error: {e}")
    
    # Test 5: Rules validation
    print("\n5. Testing Rules Validation...")
    try:
        # Load sample data
        with open('sample_paisalo_request.json', 'r') as f:
            sample_data = json.load(f)
        
        validation_request = sample_data['credit_application']
        response = client.post("/validate", json=validation_request)
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Rules validation successful")
            print(f"   📋 Valid: {'✅ YES' if data['is_valid'] else '❌ NO'}")
            print(f"   📊 Risk level: {data['risk_level'].upper()}")
            
            if data['emi_details']:
                emi = data['emi_details']
                print(f"   💰 Monthly EMI: ₹{float(emi['monthly_emi']):,.2f}")
            
            # Show validation results
            print("   📝 Validation Results:")
            for validation_name, validation_data in data['validations'].items():
                status = "✅" if validation_data['valid'] else "❌"
                print(f"      {status} {validation_name.replace('_', ' ').title()}")
                
        else:
            print(f"   ❌ Rules validation failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Rules validation error: {e}")
    
    # Test 6: Full assessment (this might fail without Vertex AI)
    print("\n6. Testing Full Assessment...")
    try:
        # Load sample data
        with open('sample_paisalo_request.json', 'r') as f:
            sample_data = json.load(f)
        
        response = client.post("/assess", json=sample_data)
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Full assessment successful")
            print(f"   📋 Success: {'✅ YES' if data['success'] else '❌ NO'}")
            
            if data['success'] and data['assessment_result']:
                result = data['assessment_result']
                print(f"   📊 Approved: {'✅ YES' if result['approved'] else '❌ NO'}")
                print(f"   📈 Risk level: {result['risk_level'].upper()}")
                print(f"   💰 Recommended amount: ₹{result['recommended_loan_amount']:,.2f}" if result['recommended_loan_amount'] else "   💰 No amount recommended")
                print(f"   🎯 Overall confidence: {result['confidence_scores']['overall_confidence']:.1%}")
            
            if data['paisalo_validation']:
                pv = data['paisalo_validation']
                print(f"   🏦 Paisalo validation: {'✅ PASS' if pv['is_valid'] else '❌ FAIL'}")
                
        else:
            print(f"   ❌ Full assessment failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Full assessment error: {e}")
    
    print("\n🎉 API testing completed!")
    print("\n💡 To start the server manually, run: python main.py")
    print("📚 API documentation available at: http://localhost:8000/docs")


if __name__ == "__main__":
    test_api_endpoints()
