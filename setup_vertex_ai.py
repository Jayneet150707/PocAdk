#!/usr/bin/env python3
"""
Interactive setup script for Google Cloud and Vertex AI integration.
This script helps you configure your environment step by step.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description=""):
    """Run a shell command and return the result."""
    print(f"🔄 {description}")
    print(f"   Running: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"✅ Success!")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False, e.stderr.strip() if e.stderr else str(e)


def check_gcloud_installed():
    """Check if Google Cloud CLI is installed."""
    print("🔍 Checking Google Cloud CLI installation...")
    
    success, output = run_command("gcloud --version", "Checking gcloud version")
    
    if not success:
        print("\n❌ Google Cloud CLI is not installed!")
        print("📥 Please install it from: https://cloud.google.com/sdk/docs/install")
        print("\nAfter installation, run this script again.")
        return False
    
    print("✅ Google Cloud CLI is installed!")
    return True


def login_to_gcloud():
    """Login to Google Cloud."""
    print("\n🔐 Google Cloud Authentication...")
    
    # Check if already logged in
    success, output = run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'", "Checking current authentication")
    
    if success and output.strip():
        print(f"✅ Already logged in as: {output.strip()}")
        return True
    
    print("🔑 Please login to Google Cloud...")
    success, _ = run_command("gcloud auth login", "Logging in to Google Cloud")
    
    return success


def get_or_create_project():
    """Get existing project or help create a new one."""
    print("\n📋 Google Cloud Project Setup...")
    
    # List existing projects
    success, output = run_command("gcloud projects list --format='value(projectId,name)'", "Listing existing projects")
    
    if success and output.strip():
        print("📂 Your existing projects:")
        for line in output.strip().split('\n'):
            if line.strip():
                project_id, name = line.split('\t', 1) if '\t' in line else (line, '')
                print(f"   • {project_id} ({name})")
    
    print("\n🤔 Choose an option:")
    print("1. Use an existing project")
    print("2. Create a new project")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        project_id = input("Enter your project ID: ").strip()
        if not project_id:
            print("❌ Project ID cannot be empty!")
            return None
    elif choice == "2":
        project_id = input("Enter a new project ID (must be globally unique): ").strip()
        if not project_id:
            print("❌ Project ID cannot be empty!")
            return None
        
        project_name = input(f"Enter project name (or press Enter to use '{project_id}'): ").strip()
        if not project_name:
            project_name = project_id
        
        print(f"🏗️ Creating project '{project_id}'...")
        success, _ = run_command(
            f'gcloud projects create {project_id} --name="{project_name}"',
            f"Creating project {project_id}"
        )
        
        if not success:
            print("❌ Failed to create project!")
            return None
    else:
        print("❌ Invalid choice!")
        return None
    
    # Set the project
    success, _ = run_command(f"gcloud config set project {project_id}", f"Setting project to {project_id}")
    
    if success:
        print(f"✅ Project set to: {project_id}")
        return project_id
    else:
        print("❌ Failed to set project!")
        return None


def enable_apis(project_id):
    """Enable required APIs."""
    print(f"\n🔌 Enabling required APIs for project {project_id}...")
    
    apis = [
        "aiplatform.googleapis.com",
        "compute.googleapis.com", 
        "storage.googleapis.com"
    ]
    
    for api in apis:
        success, _ = run_command(f"gcloud services enable {api}", f"Enabling {api}")
        if not success:
            print(f"❌ Failed to enable {api}")
            return False
    
    print("✅ All required APIs enabled!")
    return True


def create_service_account(project_id):
    """Create service account and download key."""
    print(f"\n👤 Creating service account for project {project_id}...")
    
    sa_name = "credit-assessment-sa"
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
    
    # Create service account
    success, _ = run_command(
        f'gcloud iam service-accounts create {sa_name} '
        f'--description="Service account for Credit Assessment Agent" '
        f'--display-name="Credit Assessment SA"',
        "Creating service account"
    )
    
    if not success:
        print("⚠️ Service account might already exist, continuing...")
    
    # Grant roles
    roles = [
        "roles/aiplatform.user",
        "roles/storage.objectViewer"
    ]
    
    for role in roles:
        success, _ = run_command(
            f"gcloud projects add-iam-policy-binding {project_id} "
            f"--member='serviceAccount:{sa_email}' "
            f"--role='{role}'",
            f"Granting {role}"
        )
        
        if not success:
            print(f"❌ Failed to grant {role}")
            return False, None
    
    # Create and download key
    key_file = "./service-account-key.json"
    success, _ = run_command(
        f"gcloud iam service-accounts keys create {key_file} "
        f"--iam-account={sa_email}",
        "Creating and downloading service account key"
    )
    
    if success:
        print(f"✅ Service account key saved to: {key_file}")
        return True, key_file
    else:
        print("❌ Failed to create service account key!")
        return False, None


def create_env_file(project_id, key_file):
    """Create .env file with configuration."""
    print("\n📄 Creating .env configuration file...")
    
    env_content = f"""# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT={project_id}
GOOGLE_APPLICATION_CREDENTIALS={key_file}

# Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-flash-001

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Optional: Model parameters
VERTEX_AI_TEMPERATURE=0.7
VERTEX_AI_MAX_TOKENS=1000
VERTEX_AI_TOP_P=0.8
VERTEX_AI_TOP_K=40
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def install_dependencies():
    """Install required Python dependencies."""
    print("\n📦 Installing required Python dependencies...")
    
    dependencies = [
        "google-cloud-aiplatform",
        "google-auth",
        "google-auth-oauthlib",
        "PyPDF2",
        "python-multipart",
        "python-dotenv"
    ]
    
    for dep in dependencies:
        success, _ = run_command(f"pip install {dep}", f"Installing {dep}")
        if not success:
            print(f"⚠️ Failed to install {dep}, you may need to install it manually")
    
    print("✅ Dependencies installation completed!")


def main():
    """Main setup process."""
    print("🚀 Google Cloud & Vertex AI Setup for Credit Assessment POC")
    print("=" * 70)
    print("This script will help you set up Google Cloud and Vertex AI integration.")
    print("Make sure you have a Google account and are ready to enable billing.")
    print()
    
    # Check prerequisites
    if not check_gcloud_installed():
        return 1
    
    # Login to Google Cloud
    if not login_to_gcloud():
        print("❌ Failed to login to Google Cloud!")
        return 1
    
    # Get or create project
    project_id = get_or_create_project()
    if not project_id:
        print("❌ Failed to set up project!")
        return 1
    
    # Enable APIs
    if not enable_apis(project_id):
        print("❌ Failed to enable required APIs!")
        return 1
    
    # Create service account
    sa_success, key_file = create_service_account(project_id)
    if not sa_success:
        print("❌ Failed to create service account!")
        return 1
    
    # Create .env file
    if not create_env_file(project_id, key_file):
        print("❌ Failed to create .env file!")
        return 1
    
    # Install dependencies
    install_dependencies()
    
    # Final instructions
    print("\n" + "=" * 70)
    print("🎉 Setup completed successfully!")
    print("=" * 70)
    print("\n📋 Next steps:")
    print("1. Test your setup: python test_vertex_ai.py")
    print("2. Start the server: uvicorn main:app --reload")
    print("3. Test the API endpoints")
    print("\n💡 Important notes:")
    print("• Make sure billing is enabled in your Google Cloud project")
    print("• Vertex AI usage will incur costs after free tier limits")
    print("• Keep your service-account-key.json file secure and private")
    print("\n🔗 Useful links:")
    print("• Google Cloud Console: https://console.cloud.google.com")
    print("• Vertex AI Pricing: https://cloud.google.com/vertex-ai/pricing")
    print("• Free Tier Info: https://cloud.google.com/free")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

