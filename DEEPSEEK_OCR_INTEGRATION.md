# DeepSeek-OCR Integration Summary

This document summarizes the changes made to integrate DeepSeek-OCR via Ollama as a replacement for Docling in the Pagewise-core project.

## Overview

The integration replaces the Docling OCR engine with DeepSeek-OCR, a more advanced OCR model hosted via Ollama. The new system provides:

1. Better OCR accuracy with grounding capabilities
2. Bounding box detection for all text elements
3. Automated image extraction with dimensions
4. Configurable OCR models per document
5. Debug visualizations with bounding boxes

## Changes Made

### 1. New Package: `deepseek_ocr/`

Created a modular package with separate concerns:

- **`client.py`**: Ollama API client for running DeepSeek-OCR
- **`parser.py`**: Parses OCR output to extract references and markdown
- **`extractor.py`**: Extracts images and creates bounding box visualizations
- **`processor.py`**: High-level orchestration of the OCR pipeline
- **`tests.py`**: Unit tests for the package
- **`README.md`**: Package documentation

### 2. Model Updates

#### Document Model
- Added `ocr_model` field to select which OCR model to use (default: 'deepseek-ocr')

#### Page Model
- Added `ocr_references` JSONField to store parsed OCR references with bounding boxes
- Added `bbox_visualization` FileField to store debug images showing detected regions
- Kept `docling_layout` for backward compatibility

#### Image Model
- Added `width` IntegerField to store image width
- Added `height` IntegerField to store image height

#### OCRSettings Model (replaces DoclingSettings)
- Added `ocr_backend` field to choose between 'deepseek-ocr' and 'docling'
- Added `default_model` field for DeepSeek-OCR model name
- Added `default_prompt` field for OCR prompt customization
- Kept legacy Docling fields for backward compatibility
- Created alias `DoclingSettings = OCRSettings` for backward compatibility

### 3. Task Updates (`documents/tasks.py`)

Rewrote the `process_page` task to:
1. Convert PDF page to high-resolution image
2. Call DeepSeek-OCR via Ollama
3. Parse OCR output for references and markdown
4. Extract images from detected regions
5. Save bounding box visualizations
6. Store all data in the database
7. Update document progress

Key features:
- Uses `OLLAMA_HOST` environment variable
- Supports per-document OCR model selection
- Maintains progress tracking
- Proper cleanup of temporary files

### 4. API and Schema Updates

#### DocumentCreateSchema
- Added `ocr_model` field (optional, default: 'deepseek-ocr')

#### Upload Endpoint
- Added `ocr_model` form parameter
- Passes model selection to document creation

#### OCRSettingsSchema (replaces DoclingSettingsSchema)
- Added fields for DeepSeek-OCR configuration
- Kept legacy Docling fields
- Created alias for backward compatibility

### 5. Admin Interface Updates

#### DocumentAdmin
- Added `ocr_model` field to form

#### PageAdmin
- Added `ocr_references` and `bbox_visualization` fields
- Organized into "DeepSeek OCR Data" section

#### ImageAdmin
- Added `width` and `height` fields to display

#### OCRSettingsAdmin
- Updated to show both DeepSeek-OCR and legacy Docling settings
- Organized into collapsible sections

### 6. Configuration Updates

#### pyproject.toml
- Added `ollama>=0.4.0` dependency

#### .env.example
- Added `OLLAMA_HOST` variable (default: http://localhost:11434)
- Reorganized configuration sections

### 7. Tests

#### documents/tests.py
- Updated imports to use `OCRSettings`
- Updated test assertions for new model fields

#### deepseek_ocr/tests.py
- Added unit tests for parser functions
- Added unit tests for client with mocked Ollama

### 8. Documentation

#### README.md
- Updated architecture diagram
- Added Ollama/DeepSeek-OCR information
- Updated setup instructions
- Updated API examples
- Updated configuration documentation

#### deepseek_ocr/README.md
- Comprehensive package documentation
- Usage examples for all modules
- Configuration instructions
- Testing instructions

### 9. Database Migration

Created migration `0004_add_deepseek_ocr_support.py` that:
- Adds new fields to existing models
- Renames DoclingSettings to OCRSettings
- Adds new OCR configuration fields
- Maintains backward compatibility

## Backward Compatibility

The integration maintains backward compatibility:

1. **Models**: `DoclingSettings` is now an alias for `OCRSettings`
2. **Imports**: Old imports continue to work
3. **Data**: Legacy `docling_layout` field is preserved
4. **Settings**: Legacy Docling configuration fields are kept

## Usage

### Upload a Document with OCR Model Selection

```bash
curl -X POST "http://localhost:8000/api/documents/upload/" \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "group_sqid=bucket_sqid_here" \
  -F "ocr_model=deepseek-ocr"
```

### Configure OCR Settings

Access Django admin at `/admin/` to configure:
- OCR backend (deepseek-ocr or docling)
- Default model name
- Default OCR prompt
- Legacy Docling settings

### Environment Configuration

Set in `.env` file:
```
OLLAMA_HOST=http://localhost:11434
```

## Testing

Run tests:
```bash
# All tests
python manage.py test

# DeepSeek-OCR package tests
python deepseek_ocr/tests.py

# Documents app tests
python manage.py test documents
```

## Deployment Considerations

1. **Ollama Server**: Ensure Ollama is installed and running with DeepSeek-OCR model
2. **Network**: Celery workers must have access to Ollama server
3. **Resources**: DeepSeek-OCR requires significant GPU memory (recommended: 8GB+ VRAM)
4. **Environment**: Set `OLLAMA_HOST` in environment for all workers
5. **Migration**: Run database migration before deployment

## Future Enhancements

Potential improvements:
1. Support for additional OCR models
2. Model fine-tuning capabilities
3. Batch processing optimization
4. Custom prompt templates per document type
5. Advanced bounding box filtering
6. OCR result caching
7. Multi-language OCR support
8. Custom post-processing pipelines

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   - Check `OLLAMA_HOST` environment variable
   - Verify Ollama server is running: `ollama list`
   - Check network connectivity

2. **Model Not Found**
   - Pull the model: `ollama pull deepseek-ocr`
   - Verify model name matches configuration

3. **OCR Processing Fails**
   - Check Celery worker logs
   - Verify image conversion from PDF works
   - Check temporary file permissions

4. **Images Not Extracted**
   - Verify bounding box coordinates are valid
   - Check output directory permissions
   - Review `ocr_references` JSON data

## Rollback

To rollback to Docling:

1. Update `OCRSettings.ocr_backend` to 'docling'
2. Optionally revert code to previous commit
3. Note: Already processed documents will keep DeepSeek-OCR data

## Support

For issues or questions:
1. Check logs in Celery worker
2. Review Django admin for OCRSettings
3. Test with deepseek_ocr package tests
4. Review Ollama server logs
