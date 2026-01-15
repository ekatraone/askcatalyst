# Ask Catalyst RAG Bot

An Azure-powered RAG (Retrieval-Augmented Generation) bot using Azure OpenAI Assistants API, native vector store, and Cosmos DB.

## Features

- **Azure OpenAI Assistants API**: Leverages GPT-4o with built-in RAG capabilities
- **Native Vector Store**: Azure OpenAI's managed vector store for document retrieval
- **Cosmos DB Integration**: User profiles, conversation history, and analytics
- **Dual Deployment**: Flask API for development, Azure Functions for production
- **Citation Tracking**: Automatic source attribution in responses
- **Conversation Context**: Thread-based conversations with memory
- **Document Management**: Upload, list, and delete documents via API
- **Analytics**: Track usage, performance, and user interactions

## Architecture

```
User Query → API/Azure Function → Assistant Manager → Azure OpenAI Assistants API
                                         ↓
                                  Vector Store Manager → Azure OpenAI Vector Store
                                         ↓
                                  Database Manager → Cosmos DB
                                         ↓
                                  Response with Citations
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp local.settings.json.example local.settings.json

# Edit local.settings.json with your Azure credentials
```

## Quick Start

### Local Development (Flask)

```bash
# Set up environment
cp ../.env.example ../.env
# Edit .env with your credentials

# Run the Flask API
python api.py
```

The API will start on `http://localhost:5000`

### Azure Functions (Production)

```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Deploy to Azure
func azure functionapp publish <your-function-app-name>
```

## Configuration

### Environment Variables

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-05-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_ASSISTANT_ID=  # Auto-generated
AZURE_OPENAI_VECTOR_STORE_ID=  # Auto-generated

# Cosmos DB Configuration
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DB_KEY=your-key
COSMOS_DB_DATABASE=askcatalyst
```

**Note**: `ASSISTANT_ID` and `VECTOR_STORE_ID` are auto-generated on first run. Check logs and add them to your config.

## Modules

### assistant_manager.py
Manages Azure OpenAI Assistants API operations:
- Creates and manages conversation threads
- Processes messages with RAG capabilities
- Extracts citations from responses
- Tracks processing time and metadata

**Global Instance**: `assistant_manager`

### vector_store_manager.py
Handles document operations:
- Uploads files to Azure OpenAI Vector Store
- Validates file formats and sizes (max 512MB)
- Supports: PDF, TXT, MD, JSON, DOCX, HTML, CSV, XLSX
- Auto-loads documents from `documents/` directory
- Manages vector store lifecycle

**Global Instance**: `vector_store_manager`

### database.py
Cosmos DB wrapper:
- User profile management
- Conversation logging with citations
- Analytics and metrics tracking
- GDPR-compliant data deletion

**Global Instance**: `db`

### api.py
Flask REST API for local development:
- All endpoint implementations
- Service health monitoring
- Easy testing and debugging

### function_app.py
Azure Functions implementation:
- Production serverless deployment
- Same endpoints as Flask API
- Automatic scaling
- Built-in monitoring

## API Endpoints

### Query
**POST** `/api/query`
```json
{
  "user_id": "user123",
  "message": "What is RAG?",
  "thread_id": "thread_abc"  // optional
}
```

**Response**:
```json
{
  "success": true,
  "response": "RAG stands for...",
  "thread_id": "thread_abc",
  "citations": [
    {
      "file_id": "file-123",
      "quote": "relevant passage"
    }
  ],
  "processing_time": 2.3
}
```

### Upload Documents
**POST** `/api/upload`
```json
{
  "file_paths": ["/path/to/doc1.pdf", "/path/to/doc2.txt"]
}
```

### Get Vector Store Info
**GET** `/api/vector-store/info`

### List Files
**GET** `/api/vector-store/files`

### Delete File
**DELETE** `/api/vector-store/files/<file_id>`

### Get Conversation History
**GET** `/api/history/<user_id>?limit=10`

### Get Analytics
**GET** `/api/analytics?date=2024-01-15`

### Get User Profile
**GET** `/api/user/<user_id>`

### Health Check
**GET** `/health`

## Document Management

### Auto-Loading Documents

Place documents in the `documents/` directory:

```
documents/
├── company_policies.pdf
├── product_docs.md
├── faq.txt
└── guides/
    └── user_guide.pdf
```

Documents are automatically uploaded on initialization.

### Manual Upload via API

```bash
curl -X POST http://localhost:5000/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": ["/absolute/path/to/document.pdf"]
  }'
```

### Supported Formats

- PDF (`.pdf`)
- Text (`.txt`)
- Markdown (`.md`)
- JSON (`.json`)
- Word (`.docx`, `.doc`)
- HTML (`.html`, `.htm`)
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)

**Max file size**: 512 MB

## Usage Examples

### Python Client

```python
import requests

# Query the bot
response = requests.post('http://localhost:5000/api/query', json={
    'user_id': 'user123',
    'message': 'What are your return policies?'
})

data = response.json()
print(data['response'])
print(f"Citations: {data['citations']}")
```

### cURL

```bash
# Query
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user123","message":"What is RAG?"}'

# Upload document
curl -X POST http://localhost:5000/api/upload \
  -H "Content-Type: application/json" \
  -d '{"file_paths":["/path/to/doc.pdf"]}'

# Get history
curl http://localhost:5000/api/history/user123?limit=5
```

## Testing

```bash
# Test the Flask API
python api.py

# In another terminal, test an endpoint
curl http://localhost:5000/health
```

## Deployment

### Azure Setup

1. **Create Azure OpenAI resource**
   - Deploy GPT-4o model
   - Note API key and endpoint

2. **Create Cosmos DB account**
   - Use SQL API
   - Note endpoint and key

3. **Create Azure Function App**
   - Runtime: Python 3.10+
   - Plan: Consumption or Premium

4. **Configure Function App settings**
   ```bash
   az functionapp config appsettings set \
     --name <app-name> \
     --resource-group <rg-name> \
     --settings \
     AZURE_OPENAI_API_KEY=<key> \
     AZURE_OPENAI_ENDPOINT=<endpoint> \
     # ... other settings
   ```

5. **Deploy**
   ```bash
   func azure functionapp publish <app-name>
   ```

## Monitoring

- **Azure Application Insights**: Automatic telemetry
- **Cosmos DB Metrics**: Query performance and RU usage
- **Custom Analytics**: Via `/api/analytics` endpoint

## Troubleshooting

### Assistant/Vector Store not initializing
- Check Azure OpenAI credentials
- Verify API version compatibility
- Check logs for auto-generated IDs

### Documents not loading
- Verify file paths are absolute
- Check file formats and sizes
- Review logs for validation errors

### Cosmos DB connection failed
- Verify endpoint and key
- Check firewall settings
- Ensure database name is correct

### API timeout
- Increase `functionTimeout` in host.json
- Consider Azure Functions Premium plan
- Optimize document size and count

## Performance Tips

1. **Use thread_id**: Maintain conversation context efficiently
2. **Batch uploads**: Upload multiple documents at once
3. **Monitor RU usage**: Optimize Cosmos DB provisioned throughput
4. **Cache responses**: Implement caching for common queries
5. **Limit history**: Use reasonable limits for conversation history

## Security

- Store credentials in Azure Key Vault (production)
- Use Managed Identity for Azure resources
- Enable CORS restrictions
- Implement rate limiting
- Audit Cosmos DB access logs

## Cost Optimization

- Use Azure Functions Consumption plan for low traffic
- Set Cosmos DB autoscale for variable workloads
- Monitor Azure OpenAI token usage
- Archive old conversations to blob storage
- Set vector store expiration policy

## Contributing

See CONTRIBUTING.md for guidelines.

## License

See LICENSE file.

## Resources

- [Azure OpenAI Assistants API](https://learn.microsoft.com/en-us/azure/ai-services/openai/assistants-reference)
- [Azure Functions Python Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Cosmos DB Documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/)
- [RAG Best Practices](https://www.anthropic.com/index/retrieval-augmented-generation)
