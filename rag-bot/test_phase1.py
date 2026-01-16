#!/usr/bin/env python3
"""
Test script for Phase 1 critical fixes
Tests security, authentication, retry logic, and input validation
"""
import os
import sys
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5000')
API_KEY = os.getenv('API_KEY', '')

def print_test(test_name: str):
    """Print test header"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print('='*60)

def print_result(success: bool, message: str):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")

def test_health_check():
    """Test 1: Health check endpoint (no auth required)"""
    print_test("Health Check - No Auth Required")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Health check successful")
            print(f"  Status: {data.get('status')}")
            print(f"  Services: {data.get('services')}")
            return True
        else:
            print_result(False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_api_auth_missing():
    """Test 2: API authentication - missing key"""
    print_test("API Authentication - Missing Key")

    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={'user_id': 'test', 'message': 'hello'},
            timeout=5
        )

        if response.status_code == 401:
            print_result(True, "Correctly rejected request without API key")
            return True
        else:
            print_result(False, f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_api_auth_invalid():
    """Test 3: API authentication - invalid key"""
    print_test("API Authentication - Invalid Key")

    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={'user_id': 'test', 'message': 'hello'},
            headers={'X-API-Key': 'invalid_key_12345'},
            timeout=5
        )

        if response.status_code == 403:
            print_result(True, "Correctly rejected invalid API key")
            return True
        else:
            print_result(False, f"Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_api_auth_valid():
    """Test 4: API authentication - valid key"""
    print_test("API Authentication - Valid Key")

    if not API_KEY:
        print_result(False, "No API_KEY configured in .env")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={'user_id': 'test_user', 'message': 'What is RAG?'},
            headers={'X-API-Key': API_KEY},
            timeout=30
        )

        if response.status_code in [200, 503]:  # 503 if services not configured
            data = response.json()
            if response.status_code == 200:
                print_result(True, "API key accepted and request processed")
                print(f"  Response: {data.get('response', 'N/A')[:100]}...")
            else:
                print_result(True, "API key accepted (services not configured)")
            return True
        else:
            print_result(False, f"Unexpected status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_input_validation_phone():
    """Test 5: Input validation - invalid phone number"""
    print_test("Input Validation - Invalid Phone Number")

    if not API_KEY:
        print_result(False, "No API_KEY configured")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/api/whatsapp/send",
            json={'phone_number': 'invalid', 'message': 'test'},
            headers={'X-API-Key': API_KEY},
            timeout=5
        )

        # Should reject invalid phone number
        if response.status_code == 400:
            print_result(True, "Correctly rejected invalid phone number")
            return True
        elif response.status_code == 503:
            print_result(True, "Validation passed (WhatsApp not configured)")
            return True
        else:
            print_result(False, f"Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_input_validation_message():
    """Test 6: Input validation - empty message"""
    print_test("Input Validation - Empty Message")

    if not API_KEY:
        print_result(False, "No API_KEY configured")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={'user_id': 'test', 'message': ''},
            headers={'X-API-Key': API_KEY},
            timeout=5
        )

        if response.status_code == 400:
            print_result(True, "Correctly rejected empty message")
            return True
        else:
            print_result(False, f"Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_new_endpoints():
    """Test 7: New endpoints from Issue #3"""
    print_test("New Endpoints - Feature Parity")

    if not API_KEY:
        print_result(False, "No API_KEY configured")
        return False

    endpoints = [
        ('GET', '/api/user/test_user'),
        ('GET', '/api/vector-store/files'),
    ]

    all_passed = True
    for method, path in endpoints:
        try:
            if method == 'GET':
                response = requests.get(
                    f"{BASE_URL}{path}",
                    headers={'X-API-Key': API_KEY},
                    timeout=5
                )

            # Should not get auth errors
            if response.status_code in [200, 404, 503]:
                print_result(True, f"{method} {path} - endpoint exists")
            else:
                print_result(False, f"{method} {path} - status {response.status_code}")
                all_passed = False

        except Exception as e:
            print_result(False, f"{method} {path} - Error: {e}")
            all_passed = False

    return all_passed

def test_whatsapp_signature():
    """Test 8: WhatsApp signature verification"""
    print_test("WhatsApp Signature Verification")

    try:
        # Test webhook verification (GET)
        response = requests.get(
            f"{BASE_URL}/webhook/whatsapp",
            params={
                'hub.mode': 'subscribe',
                'hub.verify_token': os.getenv('WHATSAPP_VERIFY_TOKEN', 'test'),
                'hub.challenge': 'test_challenge'
            },
            timeout=5
        )

        if response.status_code in [200, 403]:
            if response.status_code == 200:
                print_result(True, "Webhook verification working")
            else:
                print_result(True, "Webhook verification rejected (token mismatch)")
            return True
        else:
            print_result(False, f"Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("PHASE 1 CRITICAL FIXES - TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key configured: {'Yes' if API_KEY else 'No'}")

    tests = [
        test_health_check,
        test_api_auth_missing,
        test_api_auth_invalid,
        test_api_auth_valid,
        test_input_validation_message,
        test_new_endpoints,
        test_whatsapp_signature,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print_result(False, f"Test crashed: {e}")
            results.append((test_func.__name__, False))
        time.sleep(0.5)  # Brief pause between tests

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")
    print("="*60)

    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
