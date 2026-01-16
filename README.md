# Pagewise Core - Document Management Backend

A comprehensive document management backend for scanned books with page-level search capabilities. Built with Django, designed to handle PDF documents with 100+ pages, extract text using Docling, and provide advanced search functionality at the page level.

## Features

- **Document Management**: Upload and manage PDF documents organized in buckets
- **Page-Level Processing**: Each page is stored as a separate model for granular search
- **Background Processing**: Celery-powered asynchronous document processing
- **OCR & Text Extraction**: Uses Docling for advanced document understanding
- **Thumbnail Generation**: Automatic thumbnail generation from first page
- **Progress Tracking**: Real-time processing progress monitoring
- **Configurable Processing**: User-configurable Docling settings
- **Image Extraction**: Extract and store images from document pages
- **Advanced Search**: Full-text search with bucket and document filtering
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
                       ┌──────────────────┐
                       │     Docling      │
                       │ (Text Extraction)│
                       └──────────────────┘
```

## File Organization

Documents are organized in a structured file system:
```
media/
├── {bucket_name}/
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

### Installation

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd pagewise-core
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Set up the database:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Start the development server:**
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

#### Buckets

- `GET /api/buckets/` - List all buckets
- `POST /api/buckets/` - Create a new bucket
- `GET /api/buckets/{sqid}` - Get bucket details
- `PUT /api/buckets/{sqid}` - Update bucket
- `DELETE /api/buckets/{sqid}` - Delete bucket

#### Documents

- `GET /api/documents/` - List documents (with optional bucket filtering)
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
    "bucket_sqid": "optional_bucket_filter",
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
  -F "group_sqid=bucket_sqid_here" \
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

### Bucket
Groups for organizing documents.

### Document
Main document model with processing status tracking.

### Page
Individual pages with OCR text and layout data.

### Image
Images extracted from document pages.

### DoclingSettings
Configurable settings for document processing.

## Background Processing

The system uses Celery for background processing with the following workflow:

1. **Document Upload** → `process_document` task
2. **PDF Analysis** → Extract page count
3. **Thumbnail Generation** → First page as JPEG
4. **Page Splitting** → Individual PDF pages
5. **Page Processing** → OCR and layout analysis per page
6. **Progress Updates** → Real-time status tracking

### Starting Celery Workers

```bash
# Development
celery -A pagewise worker --loglevel=info

# Production
celery -A pagewise worker --loglevel=info --concurrency=4
```

## Configuration

### Environment Variables

- `DEBUG`: Debug mode (default: True)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (default: redis://localhost:6379/0)

### Docling Settings

Configurable through the admin interface or API:

- **OCR Engine**: tesseract, easyocr, doctr
- **Language**: Document language for OCR
- **Layout Detection**: Tables, figures, headers/footers
- **Output Format**: markdown, text, json
- **Confidence Threshold**: OCR confidence level

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
