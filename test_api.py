#!/usr/bin/env python3
"""
Simple test script to verify the Credit Assessment API endpoints.
"""

import asyncio
import json
from datetime import datetime

import httpx


async def test_health_endpoint():
    """Test the health check endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/v1/health")
            print(f"Health Check: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


async def test_assess_endpoint():
    """Test the credit assessment endpoint."""
    # Sample credit application data
    test_application = {
        "application_id": "TEST_001",
        "applicant_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "annual_income": 75000,
        "employment_status": "employed",
        "employer": "Tech Corp",
        "requested_amount": 25000,
        "loan_purpose": "home_improvement",
        "credit_score": 720,
        "existing_debt": 15000,
        "assets": 50000,
        "application_date": datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/assess",
                json=test_application,
                timeout=30.0
            )
            print(f"Assessment: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Assessment Result: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"Assessment test failed: {e}")
            return False


async def test_upload_endpoint():
    """Test the file upload endpoint (should return 501 without multipart)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:8000/api/v1/upload-bank-statement")
            print(f"Upload Test: {response.status_code}")
            if response.status_code == 501:
                print("Upload endpoint correctly returns 501 (multipart not available)")
                return True
            else:
                print(f"Unexpected response: {response.text}")
                return False
        except Exception as e:
            print(f"Upload test failed: {e}")
            return False


async def main():
    """Run all API tests."""
    print("Testing Credit Assessment API...")
    print("=" * 50)
    
    # Test health endpoint
    health_ok = await test_health_endpoint()
    print()
    
    # Test assessment endpoint
    assess_ok = await test_assess_endpoint()
    print()
    
    # Test upload endpoint
    upload_ok = await test_upload_endpoint()
    print()
    
    # Summary
    print("=" * 50)
    print("Test Results:")
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Assessment: {'✅ PASS' if assess_ok else '❌ FAIL'}")
    print(f"Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    
    if all([health_ok, assess_ok, upload_ok]):
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

