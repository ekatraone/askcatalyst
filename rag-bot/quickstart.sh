#!/bin/bash
# Quick Start Script for Ask Catalyst RAG Bot Testing
# Helps set up and test Phase 1 critical fixes

set -e

echo "========================================"
echo "Ask Catalyst RAG Bot - Quick Start"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your Azure credentials!"
    echo ""
fi

# Check if API_KEY is set
if ! grep -q "^API_KEY=.\+" .env 2>/dev/null; then
    echo "🔑 Generating API Key..."
    API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo ""
    echo "Generated API Key: $API_KEY"
    echo ""

    # Add to .env if not exists
    if ! grep -q "^API_KEY=" .env 2>/dev/null; then
        echo "API_KEY=$API_KEY" >> .env
        echo "✅ Added API_KEY to .env"
    else
        sed -i "s/^API_KEY=.*/API_KEY=$API_KEY/" .env
        echo "✅ Updated API_KEY in .env"
    fi
    echo ""
else
    echo "✅ API_KEY already configured"
    echo ""
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."
if python -c "import flask" 2>/dev/null; then
    echo "✅ Flask installed"
else
    echo "⚠️  Flask not installed"
    echo "   Installing dependencies..."
    pip install -r requirements.txt
fi

if python -c "import pydantic" 2>/dev/null; then
    echo "✅ Pydantic installed"
else
    echo "⚠️  Pydantic not installed"
    echo "   Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""

# Verify configuration
echo "🔍 Verifying configuration..."
if python verify_config.py > /dev/null 2>&1; then
    echo "✅ Configuration verified"
else
    echo "⚠️  Some services not configured (this is OK for testing)"
    echo "   Run: python verify_config.py for details"
fi

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1️⃣  Test the implementation:"
echo "   python test_phase1.py"
echo ""
echo "2️⃣  Start the development server:"
echo "   python api.py"
echo ""
echo "3️⃣  Test with curl (in another terminal):"
echo "   curl http://localhost:5000/health"
echo ""
echo "4️⃣  Or read the testing guide:"
echo "   cat TESTING.md"
echo ""
echo "📄 View Phase 1 summary:"
echo "   cat PHASE1_SUMMARY.md"
echo ""
echo "🔑 Your API Key is in .env file"
echo "   Keep it secure and don't commit it!"
echo ""
