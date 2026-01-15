# Configuration Guide

This document explains the environment configuration for the Ask Catalyst RAG Bot.

## ⚠️ Security Notice

**IMPORTANT**: Never commit `.env` or `local.settings.json` files to git. These files contain sensitive credentials and are automatically excluded via `.gitignore`.

## Configuration Files

### 1. `.env` (Project Root)
Used by Flask API for local development.

Location: `/home/user/askcatalyst/.env`

### 2. `local.settings.json` (rag-bot directory)
Used by Azure Functions for local development.

Location: `/home/user/askcatalyst/rag-bot/local.settings.json`

### 3. Azure Function App Settings
Production environment variables configured in Azure Portal.

## Environment Variables Reference

### Azure OpenAI Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | `2RXu0uaa...` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint | `https://your-resource.cognitiveservices.azure.com` |
| `AZURE_OPENAI_API_VERSION` | API version to use | `2025-01-01-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Model deployment name | `gpt-4.1-nano` |
| `AZURE_OPENAI_ASSISTANT_ID` | Pre-created assistant ID | `asst_xxxxx` |
| `AZURE_OPENAI_VECTOR_STORE_ID` | Pre-created vector store ID | `vs_xxxxx` |

### Cosmos DB Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `COSMOS_DB_ENDPOINT` | Cosmos DB account endpoint | `https://your-account.documents.azure.com:443/` |
| `COSMOS_DB_KEY` | Cosmos DB primary or secondary key | `YZxMLiCs...` |
| `COSMOS_DB_DATABASE` | Database name | `whatsapp_bot` |

### WhatsApp Cloud API Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business API token | `EAAPnCmC...` |
| `WHATSAPP_PHONE_NUMBER_ID` | Business phone number ID | `281336435065790` |
| `WHATSAPP_VERIFY_TOKEN` | Custom webhook verification token | `verify_token_123` |
| `WHATSAPP_API_VERSION` | WhatsApp API version | `v21.0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Flask API port | `5000` |
| `FLASK_DEBUG` | Enable Flask debug mode | `False` |
| `WHATSAPP_APP_SECRET` | App secret for signature validation | (optional) |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Business account ID | (optional) |

## Configuration Status

✅ **Configured Services:**
- Azure OpenAI (GPT-4.1-nano)
- Azure OpenAI Assistant (ID: asst_9AQWvtmGqMHv8se0rwI8xV6s)
- Azure OpenAI Vector Store (ID: vs_K7VIvFf9PSavsAXlDXuHw6Ec)
- Cosmos DB (whatsapp_bot database)
- WhatsApp Cloud API (Phone ID: 281336435065790)

## Quick Start

### Local Development (Flask)

```bash
# Ensure .env is configured
cd /home/user/askcatalyst

# Install dependencies
pip install -r rag-bot/requirements.txt

# Run Flask API
cd rag-bot
python api.py
```

The API will be available at `http://localhost:5000`

### Local Development (Azure Functions)

```bash
# Ensure local.settings.json is configured
cd /home/user/askcatalyst/rag-bot

# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Run locally
func start
```

The Functions will be available at `http://localhost:7071`

## Verifying Configuration

### Check Service Status

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "assistant": true,
    "vector_store": true,
    "database": true,
    "whatsapp": true
  }
}
```

If any service shows `false`, check the corresponding environment variables.

### Test WhatsApp Webhook

```bash
# Verify webhook
curl "http://localhost:5000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=verify_token_123&hub.challenge=test123"

# Should return: test123
```

### Test Azure OpenAI Assistant

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello, can you help me?"
  }'
```

## Troubleshooting

### "Service not configured" errors

**Problem**: Health check shows service as disabled

**Solutions**:
1. Verify environment variable names are correct (no typos)
2. Check `.env` or `local.settings.json` syntax
3. Restart the application after changing config
4. Check logs for specific error messages

### WhatsApp messages not working

**Problem**: Webhook not receiving messages

**Solutions**:
1. Verify `WHATSAPP_ACCESS_TOKEN` is valid (not expired)
2. Check `WHATSAPP_PHONE_NUMBER_ID` matches your business number
3. Ensure `WHATSAPP_VERIFY_TOKEN` matches what's configured in Meta
4. Test with ngrok for local development

### Azure OpenAI errors

**Problem**: "Assistant service not configured" or API errors

**Solutions**:
1. Verify `AZURE_OPENAI_API_KEY` is valid
2. Check `AZURE_OPENAI_ENDPOINT` URL is correct
3. Ensure `AZURE_OPENAI_ASSISTANT_ID` exists in your Azure account
4. Verify API version compatibility

### Cosmos DB connection issues

**Problem**: Database operations failing

**Solutions**:
1. Verify `COSMOS_DB_ENDPOINT` includes port `:443/`
2. Check `COSMOS_DB_KEY` is valid (not regenerated)
3. Ensure `COSMOS_DB_DATABASE` exists in your account
4. Check Azure firewall settings allow your IP

## Security Best Practices

1. **Never commit secrets**
   - `.env` and `local.settings.json` are in `.gitignore`
   - Use example files (`.env.example`) for templates

2. **Rotate credentials regularly**
   - Regenerate API keys periodically
   - Update access tokens before expiration

3. **Use Azure Key Vault** (Production)
   - Store secrets in Azure Key Vault
   - Use Managed Identity for access
   - Update Function App to reference Key Vault

4. **Limit access**
   - Use least-privilege principles
   - Enable IP restrictions in production
   - Monitor access logs

5. **Enable webhook signature verification**
   - Set `WHATSAPP_APP_SECRET` for signature validation
   - Reject unsigned webhook requests

## Production Deployment

When deploying to Azure Functions, set environment variables in Azure Portal:

1. Go to Function App → Configuration → Application settings
2. Add each environment variable
3. Click "Save" and restart the Function App

Alternatively, use Azure CLI:

```bash
az functionapp config appsettings set \
  --name func-whatsapp-rag-bot \
  --resource-group your-resource-group \
  --settings \
  AZURE_OPENAI_API_KEY="your-key" \
  AZURE_OPENAI_ENDPOINT="your-endpoint" \
  # ... other settings
```

## Support

For configuration issues:
1. Check logs: `tail -f /path/to/app.log`
2. Review Azure Application Insights
3. Verify all required variables are set
4. Test each service independently

## References

- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Cosmos DB Documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Azure Functions Configuration](https://learn.microsoft.com/en-us/azure/azure-functions/functions-app-settings)
