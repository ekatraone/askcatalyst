#!/usr/bin/env python3
"""
Configuration Verification Script
Tests all environment variables and service connections
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_var(name, required=True):
    """Check if environment variable is set"""
    value = os.getenv(name)
    if value:
        # Show first 10 and last 4 characters for security
        if len(value) > 20:
            masked = f"{value[:10]}...{value[-4:]}"
        else:
            masked = f"{value[:4]}...{value[-2:]}"
        print(f"✓ {name}: {masked}")
        return True
    else:
        if required:
            print(f"✗ {name}: NOT SET (required)")
            return False
        else:
            print(f"○ {name}: not set (optional)")
            return True

def main():
    """Verify all configuration"""
    print("=" * 60)
    print("Ask Catalyst RAG Bot - Configuration Verification")
    print("=" * 60)
    print()

    all_ok = True

    # Azure OpenAI
    print("📘 Azure OpenAI Configuration")
    print("-" * 60)
    all_ok &= check_env_var("AZURE_OPENAI_API_KEY")
    all_ok &= check_env_var("AZURE_OPENAI_ENDPOINT")
    all_ok &= check_env_var("AZURE_OPENAI_API_VERSION")
    all_ok &= check_env_var("AZURE_OPENAI_DEPLOYMENT_NAME")
    all_ok &= check_env_var("AZURE_OPENAI_ASSISTANT_ID")
    all_ok &= check_env_var("AZURE_OPENAI_VECTOR_STORE_ID")
    print()

    # Cosmos DB
    print("🗄️  Cosmos DB Configuration")
    print("-" * 60)
    all_ok &= check_env_var("COSMOS_DB_ENDPOINT")
    all_ok &= check_env_var("COSMOS_DB_KEY")
    all_ok &= check_env_var("COSMOS_DB_DATABASE")
    print()

    # WhatsApp
    print("💬 WhatsApp Cloud API Configuration")
    print("-" * 60)
    all_ok &= check_env_var("WHATSAPP_ACCESS_TOKEN")
    all_ok &= check_env_var("WHATSAPP_PHONE_NUMBER_ID")
    all_ok &= check_env_var("WHATSAPP_VERIFY_TOKEN")
    all_ok &= check_env_var("WHATSAPP_API_VERSION")
    check_env_var("WHATSAPP_APP_SECRET", required=False)
    check_env_var("WHATSAPP_BUSINESS_ACCOUNT_ID", required=False)
    print()

    # Test service connections
    print("🔌 Testing Service Connections")
    print("-" * 60)

    try:
        from assistant_manager import assistant_manager
        if assistant_manager.is_enabled():
            print("✓ Azure OpenAI Assistant: Connected")
        else:
            print("✗ Azure OpenAI Assistant: Not configured")
            all_ok = False
    except Exception as e:
        print(f"✗ Azure OpenAI Assistant: Error - {e}")
        all_ok = False

    try:
        from vector_store_manager import vector_store_manager
        if vector_store_manager.is_enabled():
            print("✓ Azure OpenAI Vector Store: Connected")
        else:
            print("✗ Azure OpenAI Vector Store: Not configured")
            all_ok = False
    except Exception as e:
        print(f"✗ Azure OpenAI Vector Store: Error - {e}")
        all_ok = False

    try:
        from database import db
        if db.is_enabled():
            print("✓ Cosmos DB: Connected")
        else:
            print("✗ Cosmos DB: Not configured")
            all_ok = False
    except Exception as e:
        print(f"✗ Cosmos DB: Error - {e}")
        all_ok = False

    try:
        from whatsapp_handler import whatsapp_handler
        if whatsapp_handler.is_enabled():
            print("✓ WhatsApp Cloud API: Configured")
        else:
            print("✗ WhatsApp Cloud API: Not configured")
            all_ok = False
    except Exception as e:
        print(f"✗ WhatsApp Cloud API: Error - {e}")
        all_ok = False

    print()
    print("=" * 60)
    if all_ok:
        print("✅ All configuration checks passed!")
        print()
        print("Next steps:")
        print("1. Start the Flask API: python api.py")
        print("2. Test health endpoint: curl http://localhost:5000/health")
        print("3. Configure WhatsApp webhook (see WHATSAPP_SETUP.md)")
        print("4. Deploy to Azure Functions when ready")
        return 0
    else:
        print("❌ Configuration issues found!")
        print()
        print("Please check:")
        print("1. Verify .env file exists in project root")
        print("2. Check all required variables are set")
        print("3. Review CONFIGURATION.md for details")
        print("4. Restart application after fixing")
        return 1

if __name__ == "__main__":
    sys.exit(main())
