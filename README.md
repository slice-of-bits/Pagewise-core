# DocPond Core - Document Management Backend

A comprehensive document management backend for scanned books with page-level search capabilities. Built with Django, designed to handle PDF documents with 100+ pages, extract text using Docling, and provide advanced search functionality at the page level.

## Features

- **Document Management**: Upload and manage PDF documents organized in ponds
- **Page-Level Processing**: Each page is stored as a separate model for granular search
- **Background Processing**: Celery-powered asynchronous document processing
- **OCR & Text Extraction**: Uses DeepSeek-OCR via Ollama for advanced document understanding
- **Bounding Box Detection**: Extracts and visualizes text regions and images
- **Image Extraction**: Extract embedded images with dimensions from document pages
- **Thumbnail Generation**: Automatic thumbnail generation from first page
- **Progress Tracking**: Real-time processing progress monitoring
- **Configurable Processing**: User-configurable OCR settings
- **Advanced Search**: Full-text search with pond and document filtering
- **REST API**: Django Ninja-powered API for all operations

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Frontend     │───▶│   Django API     │───▶│   PostgreSQL    │
│                 │    │  (Django Ninja)  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Celery Tasks   │───▶│     Redis       │
                       │  (Background)    │    │  (Message Broker)│
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  DeepSeek-OCR    │───▶│     Ollama      │
                       │ (via deepseek_ocr│    │  (Model Hosting)│
                       │     package)     │    │                 │
                       └──────────────────┘    └─────────────────┘
```

## File Organization

Documents are organized in a structured file system:
```
media/
├── {pond_name}/
│   ├── {document_title}/
│   │   ├── {document_title}.pdf          # Original PDF
│   │   ├── {document_title}-cover.jpg    # Thumbnail
│   │   ├── pages/
│   │   │   ├── 1.pdf                     # Individual pages
│   │   │   ├── 2.pdf
│   │   │   └── ...
│   │   └── images/
│   │       ├── 1_image_1.jpg             # Extracted images
│   │       └── ...
│   └── ...
└── ...
```

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL (for production) or SQLite (for development)
- Redis (for Celery)
- Ollama with DeepSeek-OCR model

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd docpond-core
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Install and configure Ollama:**
   ```bash
   # Install Ollama (see https://ollama.ai)
   # Pull DeepSeek-OCR model
   ollama pull deepseek-ocr
   ```

4. **Set up the database:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

### Using Docker (Recommended for Development)

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

## API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication
Currently uses Django's built-in session authentication. Token authentication can be added as needed.

### Endpoints

#### Ponds

- `GET /api/ponds/` - List all ponds
- `POST /api/ponds/` - Create a new pond
- `GET /api/ponds/{sqid}` - Get pond details
- `PUT /api/ponds/{sqid}` - Update pond
- `DELETE /api/ponds/{sqid}` - Delete pond

#### Documents

- `GET /api/documents/` - List documents (with optional pond filtering)
- `POST /api/documents/` - Create document metadata
- `POST /api/documents/upload/` - Upload PDF and start processing
- `GET /api/documents/{sqid}` - Get document details
- `PUT /api/documents/{sqid}` - Update document
- `DELETE /api/documents/{sqid}` - Delete document
- `GET /api/documents/{sqid}/progress` - Get processing progress

#### Pages

- `GET /api/pages/` - List pages (with optional document filtering)
- `GET /api/pages/{sqid}` - Get page details
- `PUT /api/pages/{sqid}` - Update page content
- `GET /api/pages/{sqid}/images/` - Get page images

#### Search

- `POST /api/search/` - Full-text search across pages
  ```json
  {
    "q": "search query",
    "pond_sqid": "optional_pond_filter",
    "document_sqid": "optional_document_filter",
    "limit": 20,
    "offset": 0
  }
  ```

#### Settings

- `GET /api/settings/` - Get current Docling settings
- `PUT /api/settings/` - Update Docling settings

### Example Usage

#### Upload a Document
```bash
curl -X POST "http://localhost:8000/api/documents/upload/" \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "pond_sqid=pond_sqid_here" \
  -F "ocr_model=deepseek-ocr" \
  -F "metadata={\"author\": \"John Doe\"}"
```

#### Search Pages
```bash
curl -X POST "http://localhost:8000/api/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "machine learning",
    "limit": 10
  }'
```

## Models

### Pond
Ponds for organizing documents.

### Document
Main document model with processing status tracking.

### Page
Individual pages with OCR text and layout data.

### Image
Images extracted from document pages.

### OCRSettings
Configurable settings for OCR processing (DeepSeek-OCR or legacy Docling).

## Background Processing

The system uses Celery for background processing with the following workflow:

1. **Document Upload** → `process_document` task
2. **PDF Analysis** → Extract page count
3. **Thumbnail Generation** → First page as JPEG
4. **Page Splitting** → Individual PDF pages
5. **Page Processing** → Convert to image, run DeepSeek-OCR via Ollama
6. **Data Extraction** → Parse references, extract images, generate markdown
7. **Progress Updates** → Real-time status tracking

### Starting Celery Workers

```bash
# Development
celery -A docpond worker --loglevel=info

# Production
celery -A docpond worker --loglevel=info --concurrency=4
```

## Configuration

### Environment Variables

- `DEBUG`: Debug mode (default: True)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379/0)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `AWS_ACCESS_KEY_ID`: S3/MinIO access key
- `AWS_SECRET_ACCESS_KEY`: S3/MinIO secret key
- `AWS_STORAGE_BUCKET_NAME`: S3/MinIO bucket name
- `AWS_S3_ENDPOINT_URL`: S3/MinIO endpoint URL

### OCR Settings

Configurable through the admin interface or API:

- **OCR Backend**: deepseek-ocr (recommended), docling (legacy)
- **Default Model**: Model name for DeepSeek-OCR (default: deepseek-ocr)
- **Default Prompt**: OCR prompt template
- **Language**: Document language for OCR
- **Layout Detection**: Tables, figures, headers/footers (legacy Docling)
- **Confidence Threshold**: OCR confidence level (legacy Docling)

## Testing

Run the test suite:

```bash
# All tests
python manage.py test

# Specific app
python manage.py test bucket
python manage.py test documents

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Development

### Code Style

- Follow PEP 8
- Use type hints where possible
- Document functions and classes
- Write tests for new features

### Adding New Features

1. Create/update models in `models.py`
2. Create migrations: `python manage.py makemigrations`
3. Update serializers in `schemas.py`
4. Add API endpoints in `api.py`
5. Write tests in `tests.py`
6. Update admin interface in `admin.py`

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for Celery
- [ ] Configure static files serving
- [ ] Set up media files storage (S3 recommended)
- [ ] Configure Celery workers and monitoring
- [ ] Set up reverse proxy (nginx)
- [ ] Configure SSL/TLS
- [ ] Set up monitoring and logging

### Docker Production

Use the provided `docker-compose.yml` as a starting point and customize for your production environment.

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed in the correct Python environment
2. **Celery not working**: Check Redis connection and worker processes
3. **File upload errors**: Verify media directory permissions
4. **OCR failures**: Check Docling installation and language packages

### Logs

- Django logs: Check console output or configure logging
- Celery logs: Use `--loglevel=info` or higher
- Database logs: Check PostgreSQL logs for query issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Roadmap

- [ ] Token-based authentication
- [ ] Elasticsearch integration for advanced search
- [ ] Document versioning
- [ ] Batch document processing
- [ ] REST API client SDKs
- [ ] Web interface
- [ ] Cloud storage integration
- [ ] Performance optimizations
- [ ] Multi-language support
