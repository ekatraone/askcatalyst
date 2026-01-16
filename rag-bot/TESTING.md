# Testing Phase 1 Critical Fixes

This guide helps you test all the security and reliability improvements from Phase 1.

## Prerequisites

1. **Environment Setup**
   ```bash
   cd rag-bot
   pip install -r requirements.txt
   ```

2. **Generate API Key**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Copy the output and add to your `.env` file:
   ```bash
   API_KEY=your_generated_key_here
   ```

3. **Verify Configuration**
   ```bash
   python verify_config.py
   ```

## Quick Test

### Option 1: Automated Test Suite

Run the comprehensive test script:

```bash
python test_phase1.py
```

This will test:
- ✅ Health check (no auth)
- ✅ API authentication (missing, invalid, valid keys)
- ✅ Input validation
- ✅ New endpoints (Issue #3)
- ✅ WhatsApp signature verification

### Option 2: Manual Testing with curl

**Test 1: Health Check (No Auth)**
```bash
curl http://localhost:5000/health
```
Expected: 200 OK with service status

**Test 2: Missing API Key**
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"hello"}'
```
Expected: 401 Unauthorized

**Test 3: Invalid API Key**
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid_key" \
  -d '{"user_id":"test","message":"hello"}'
```
Expected: 403 Forbidden

**Test 4: Valid API Key**
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"user_id":"test","message":"What is RAG?"}'
```
Expected: 200 OK (or 503 if services not configured)

**Test 5: Input Validation**
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"user_id":"test","message":""}'
```
Expected: 400 Bad Request

**Test 6: New Endpoints (Issue #3)**
```bash
# List files in vector store
curl http://localhost:5000/api/vector-store/files \
  -H "X-API-Key: YOUR_API_KEY_HERE"

# Get user profile
curl http://localhost:5000/api/user/test_user \
  -H "X-API-Key: YOUR_API_KEY_HERE"

# Delete file (requires file_id)
curl -X DELETE http://localhost:5000/api/vector-store/files/file-123 \
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

**Test 7: WhatsApp Webhook Verification**
```bash
curl "http://localhost:5000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=test_challenge"
```
Expected: Returns challenge if token matches

## Start the Development Server

```bash
# Method 1: Direct Python
python api.py

# Method 2: Flask CLI
export FLASK_APP=api.py
flask run --host=0.0.0.0 --port=5000

# Method 3: With specific configuration
PORT=5000 FLASK_DEBUG=False python api.py
```

## Testing Retry Logic

The retry decorators will automatically retry on transient failures. To test:

1. **Simulate network issues**: Temporarily disconnect network after starting a request
2. **Check logs**: Look for "Retrying in X.XXs..." messages
3. **Monitor behavior**: Should retry 3 times before failing

Example log output:
```
WARNING - process_user_message failed (attempt 1/3): Connection error. Retrying in 1.23s...
WARNING - process_user_message failed (attempt 2/3): Connection error. Retrying in 2.87s...
INFO - Request succeeded on attempt 3
```

## Testing UUID Generation

The ID collision fix uses UUID4. Verify in logs:

```bash
# Before (timestamp-based, collision risk):
id: test_user_1642342800.123

# After (UUID4, no collision risk):
id: test_user_a1b2c3d4-e5f6-4789-a012-b3c4d5e6f7a8
```

## Load Testing (Optional)

Test under concurrent load to verify no race conditions:

```bash
# Install hey (HTTP load generator)
# https://github.com/rakyll/hey

# Run 100 requests with 10 concurrent connections
hey -n 100 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"user_id":"load_test","message":"test"}' \
  http://localhost:5000/api/query
```

Expected results:
- No 401/403 errors (auth working)
- No ID collisions in database
- Successful retries on transient failures

## Azure Functions Testing

To test in Azure Functions environment:

```bash
# Install Azure Functions Core Tools
# https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local

# Start local Functions runtime
func start

# Test endpoints
curl http://localhost:7071/api/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"user_id":"test","message":"hello"}'
```

## Verification Checklist

After testing, verify:

- [ ] Health endpoint works without auth
- [ ] All `/api/*` endpoints require API key
- [ ] Invalid/missing API keys are rejected
- [ ] WhatsApp webhook still accepts webhooks (signature verification)
- [ ] Input validation prevents malformed requests
- [ ] New endpoints exist (GET /user/{id}, GET/DELETE /vector-store/files)
- [ ] Retry logic handles transient failures
- [ ] No ID collisions under load
- [ ] Services work in both Flask and Azure Functions

## Troubleshooting

**Problem**: All API requests return 401
- **Solution**: Check that `API_KEY` is set in `.env` file
- **Verify**: `echo $API_KEY` or check `.env` file

**Problem**: Tests timeout
- **Solution**: Increase timeout values, check service configuration
- **Verify**: Run `python verify_config.py` to check all services

**Problem**: Services not configured (503 errors)
- **Solution**: This is expected if Azure services aren't set up yet
- **Note**: Auth and validation still work, just can't process requests

**Problem**: Import errors
- **Solution**: Make sure all dependencies installed: `pip install -r requirements.txt`
- **Verify**: `python -c "import pydantic; print(pydantic.__version__)"`

## Next Steps

Once Phase 1 tests pass:

1. **Deploy to Azure Functions** for production testing
2. **Set up monitoring** with Application Insights
3. **Configure alerts** for auth failures, retry exhaustion
4. **Phase 2**: Implement reliability improvements (thread cleanup, rate limiting)

## Support

For issues or questions:
- Check logs: Look for ERROR/WARNING messages
- Review configuration: `python verify_config.py`
- Test services individually: Health check each service
