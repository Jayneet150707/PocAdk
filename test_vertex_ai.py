#!/usr/bin/env python3
"""
Test Vertex AI authentication and basic functionality.
Run this script to verify your Google Cloud and Vertex AI setup.
"""

import os
import sys
from pathlib import Path

def test_environment_setup():
    """Test if environment variables are properly set."""
    print("🔧 Testing Environment Setup...")
    
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_APPLICATION_CREDENTIALS'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("💡 Make sure to create and configure your .env file")
        return False
    
    # Check if service account key file exists
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not Path(creds_path).exists():
        print(f"❌ Service account key file not found: {creds_path}")
        return False
    
    print(f"✅ Service account key file found: {creds_path}")
    return True


def test_google_cloud_libraries():
    """Test if Google Cloud libraries are installed."""
    print("\n📚 Testing Google Cloud Libraries...")
    
    try:
        import google.auth
        print("✅ google-auth installed")
    except ImportError:
        print("❌ google-auth not installed. Run: pip install google-auth")
        return False
    
    try:
        import google.cloud.aiplatform
        print("✅ google-cloud-aiplatform installed")
    except ImportError:
        print("❌ google-cloud-aiplatform not installed. Run: pip install google-cloud-aiplatform")
        return False
    
    try:
        import vertexai
        print("✅ vertexai installed")
    except ImportError:
        print("❌ vertexai not installed. Run: pip install google-cloud-aiplatform")
        return False
    
    return True


def test_vertex_ai_auth():
    """Test Vertex AI authentication."""
    print("\n🔐 Testing Vertex AI Authentication...")
    
    try:
        from google.auth import default
        from google.cloud import aiplatform
        
        # Get project from environment
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        
        # Test authentication
        credentials, project = default()
        print(f"✅ Authentication successful!")
        print(f"📋 Project: {project}")
        print(f"🌍 Location: {location}")
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        print(f"✅ Vertex AI initialized successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your service account key and permissions")
        return False


def test_model_access():
    """Test access to Vertex AI models."""
    print("\n🤖 Testing Model Access...")
    
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Get configuration
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        model_name = os.getenv('VERTEX_AI_MODEL', 'gemini-1.5-flash-001')
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Initialize model
        model = GenerativeModel(model_name)
        print(f"✅ Model '{model_name}' initialized successfully!")
        
        # Test simple prompt
        print("🧪 Testing model with simple prompt...")
        response = model.generate_content(
            "Hello! This is a test of the Vertex AI integration. "
            "Please respond with exactly: 'Vertex AI is working correctly!'"
        )
        
        print(f"✅ Model response received!")
        print(f"🤖 Response: {response.text}")
        
        # Verify response
        if "Vertex AI is working" in response.text:
            print("✅ Model is responding correctly!")
            return True
        else:
            print("⚠️ Model responded but content may be unexpected")
            return True
        
    except Exception as e:
        print(f"❌ Model access failed: {e}")
        print("💡 Check your model name, location, and API quotas")
        return False


def test_credit_assessment_integration():
    """Test integration with the credit assessment system."""
    print("\n🏦 Testing Credit Assessment Integration...")
    
    try:
        # Import our vertex AI client
        from credit_assessment_agent.shared_libraries.vertex_ai_client import VertexAIClient
        
        # Initialize client
        client = VertexAIClient()
        print("✅ VertexAIClient initialized successfully!")
        
        # Check if Vertex AI is available
        if client.vertex_ai_available:
            print("✅ Vertex AI is available and ready!")
            return True
        else:
            print("⚠️ Vertex AI not available, will use fallback assessment")
            return False
        
    except Exception as e:
        print(f"❌ Credit assessment integration failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Vertex AI Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Google Cloud Libraries", test_google_cloud_libraries),
        ("Vertex AI Authentication", test_vertex_ai_auth),
        ("Model Access", test_model_access),
        ("Credit Assessment Integration", test_credit_assessment_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Vertex AI is ready to use with your Credit Assessment POC!")
        print("\n🚀 Next steps:")
        print("   1. Start your server: uvicorn main:app --reload")
        print("   2. Test the API endpoints")
        print("   3. Look for 'Vertex AI client initialized successfully' in the logs")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix the issues above.")
        print("\n🔧 Common solutions:")
        print("   1. Make sure your .env file is properly configured")
        print("   2. Install missing dependencies: pip install google-cloud-aiplatform")
        print("   3. Check your Google Cloud project and service account setup")
        print("   4. Verify your service account has the required permissions")
        return 1


if __name__ == "__main__":
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📄 Loaded environment variables from .env file")
    except ImportError:
        print("💡 python-dotenv not installed. Environment variables should be set manually.")
    except Exception:
        print("💡 No .env file found or error loading it.")
    
    exit_code = main()
    sys.exit(exit_code)

