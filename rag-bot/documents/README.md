# Documents Directory

Place your knowledge base documents in this directory. They will be automatically loaded into the vector store on initialization.

## Supported Formats

- PDF (`.pdf`)
- Text files (`.txt`)
- Markdown (`.md`)
- JSON (`.json`)
- Microsoft Word (`.docx`, `.doc`)
- HTML (`.html`, `.htm`)
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)

## File Size Limit

Maximum file size: 512 MB per file

## Example Structure

```
documents/
├── company_policies.pdf
├── product_documentation.md
├── faq.txt
├── knowledge_base/
│   ├── article1.md
│   ├── article2.md
│   └── guides/
│       └── user_guide.pdf
└── README.md
```

## How It Works

1. Place files in this directory
2. Start the application
3. Files are automatically uploaded to Azure OpenAI Vector Store
4. The RAG bot can now answer questions based on these documents

## Manual Upload

You can also upload documents via the API:

```bash
curl -X POST http://localhost:5000/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": ["/path/to/document.pdf"]
  }'
```
