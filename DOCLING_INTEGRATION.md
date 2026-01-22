# Docling Integration Guide

This document explains how to use Docling for document processing in Pagewise-core.

## Overview

Docling is a powerful document processing library that supports:
- Advanced PDF understanding with page layout analysis
- Multiple OCR engines (EasyOCR, Tesseract, RapidOCR, macOS Vision)
- Vision-Language Models (VLM) for end-to-end document processing
- Table structure extraction
- Code and formula recognition
- Picture description generation
- Multi-language support

## Quick Start

### 1. Install Docling

Docling is already added to `pyproject.toml` as a dependency:

```bash
pip install docling
```

Note: Docling has a large set of dependencies including ML models. The first run will download models automatically (cached for future use).

### 2. Create a Docling Preset

Use the API or Django admin to create a preset:

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/docling-presets/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "standard-english",
    "is_default": true,
    "pipeline_type": "standard",
    "ocr_engine": "easyocr",
    "force_ocr": true,
    "ocr_languages": ["en"],
    "enable_table_structure": true,
    "table_former_mode": "accurate"
  }'
```

**Via Django Admin:**
1. Navigate to `/admin/documents/doclingpreset/`
2. Click "Add Docling Preset"
3. Configure settings and save

### 3. Process Documents with Docling

**Upload with Preset:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload/" \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "group_sqid=<group_sqid>" \
  -F "docling_preset_sqid=<preset_sqid>"
```

The system will automatically:
1. Split the PDF into pages
2. Process each page with Docling using the specified preset
3. Save Docling JSON to `page.docling_json`
4. Generate markdown and save to `page.text_markdown_clean`
5. Extract images and create Image objects

## Docling Presets Configuration

### Pipeline Types

#### Standard PDF Pipeline
Best for most PDF documents. Provides full control over OCR, layout analysis, and enrichments.

```json
{
  "pipeline_type": "standard",
  "ocr_engine": "easyocr",
  "force_ocr": true,
  "enable_table_structure": true,
  "enable_code_enrichment": false,
  "enable_formula_enrichment": false
}
```

#### VLM Pipeline
Uses vision-language models for end-to-end processing. Best for complex layouts and when you want AI-powered understanding.

```json
{
  "pipeline_type": "vlm",
  "vlm_model": "ibm-granite/granite-docling-258M",
  "enable_picture_description": true
}
```

### OCR Engines

| Engine | Best For | Languages | Performance |
|--------|----------|-----------|-------------|
| `auto` | Auto-detection | Varies | Automatic |
| `easyocr` | Multi-language | 80+ | Moderate |
| `tesseract` | Speed | 100+ | Fast |
| `rapidocr` | Lightweight | Limited | Fast |
| `ocrmac` | macOS only | System | Very Fast |

### Language Support

Use ISO 639-1 language codes. Examples:
- `["en"]` - English
- `["en", "es"]` - English and Spanish
- `["fr", "de", "it"]` - French, German, Italian

See `documents/language_codes.py` for full list of 40+ supported languages.

### Table Structure Extraction

```json
{
  "enable_table_structure": true,
  "table_former_mode": "accurate"  // or "fast"
}
```

- `accurate`: Higher quality, slower processing
- `fast`: Faster processing, may miss complex table structures

### Picture Description

Enable AI-powered image descriptions:

```json
{
  "enable_picture_description": true,
  "picture_description_prompt": "Describe this image in detail."
}
```

### Code and Formula Enrichment

```json
{
  "enable_code_enrichment": true,      // Specialized processing for code blocks
  "enable_formula_enrichment": true    // LaTeX formula recognition
}
```

### Layout Filters

Control which elements to include in the output:

```json
{
  "filter_orphan_clusters": true,   // Filter page numbers, headers, footers
  "filter_empty_clusters": true      // Remove empty regions
}
```

## API Endpoints

### Preset Management

- `GET /api/docling-presets/` - List all presets
- `POST /api/docling-presets/` - Create preset
- `GET /api/docling-presets/{sqid}` - Get preset details
- `PUT /api/docling-presets/{sqid}` - Update preset
- `DELETE /api/docling-presets/{sqid}` - Delete preset
- `POST /api/docling-presets/{sqid}/set-default` - Set as default
- `GET /api/docling-presets/default/get` - Get default preset

### Document Processing

Documents can be processed with either:
1. **Docling**: Set `docling_preset_sqid` when uploading
2. **DeepSeek OCR** (legacy): Leave `docling_preset_sqid` empty and set `ocr_model`

## Data Storage

### Docling JSON

Each processed page stores:
- `page.docling_json`: Original Docling JSON output (full structure)
- `page.docling_json_override`: Manual corrections (optional)
- `page.text_markdown_clean`: Generated markdown (from JSON)

### Override Workflow

1. Page is processed → `docling_json` is saved
2. User reviews and makes corrections → saves to `docling_json_override`
3. Future: Regenerate markdown from override instead of original

### Image Extraction

Images are automatically extracted and saved as `Image` model instances:
- Integrated with existing image storage
- Includes dimensions (width/height)
- Optional captions (if picture description is enabled)

## Example Presets

### Simple English Document
```json
{
  "name": "simple-english",
  "pipeline_type": "standard",
  "ocr_engine": "tesseract",
  "force_ocr": false,
  "ocr_languages": ["en"],
  "enable_table_structure": true,
  "table_former_mode": "fast"
}
```

### Technical Document with Code
```json
{
  "name": "technical-with-code",
  "pipeline_type": "standard",
  "ocr_engine": "easyocr",
  "force_ocr": true,
  "ocr_languages": ["en"],
  "enable_table_structure": true,
  "table_former_mode": "accurate",
  "enable_code_enrichment": true,
  "enable_formula_enrichment": true
}
```

### Multi-Language Document
```json
{
  "name": "multilingual-european",
  "pipeline_type": "standard",
  "ocr_engine": "easyocr",
  "force_ocr": true,
  "ocr_languages": ["en", "fr", "de", "es", "it"],
  "enable_table_structure": true
}
```

### VLM Mode for Complex Layouts
```json
{
  "name": "vlm-complex-docs",
  "pipeline_type": "vlm",
  "vlm_model": "ibm-granite/granite-docling-258M",
  "enable_picture_description": true,
  "picture_description_prompt": "Provide a detailed technical description."
}
```

## Troubleshooting

### Import Error: "No module named 'docling'"
```bash
pip install docling
```

### Models Not Downloading
Docling downloads models on first use. Ensure internet connectivity or pre-fetch:
```bash
docling-tools models download
```

### OCR Not Working
- Verify OCR engine is installed (e.g., `tesseract` for Tesseract)
- Check language data files are available
- Try `ocr_engine: "auto"` for automatic selection

### Processing Takes Too Long
- Use `table_former_mode: "fast"` for tables
- Disable enrichments you don't need
- Consider smaller OCR language list
- Use VLM pipeline for complex documents (can be faster)

### Images Not Extracted
- Ensure `generate_picture_images: true` in pipeline options (handled automatically)
- Check file permissions for image storage
- Verify PDF contains extractable images

## Performance Considerations

### Processing Time

Typical processing time per page:
- Simple PDF with text: 2-5 seconds
- Scanned document with OCR: 10-20 seconds
- Tables + formulas + code: 20-30 seconds
- VLM pipeline: 5-15 seconds (with GPU)

### Resource Usage

- **CPU**: 4 threads by default (configurable via `OMP_NUM_THREADS`)
- **Memory**: 2-4 GB per worker process
- **Storage**: Models cached in `~/.cache/docling/models/` (~2-5 GB)
- **GPU**: Optional for VLM and EasyOCR (significantly faster)

### Optimization Tips

1. **Use Fast Mode**: Set `table_former_mode: "fast"` for simple tables
2. **Limit Languages**: Fewer languages = faster OCR
3. **Disable Unused Features**: Turn off code/formula enrichment if not needed
4. **Batch Processing**: Process multiple pages in parallel (Celery workers)
5. **GPU Acceleration**: Use GPU for OCR and VLM pipelines

## Migration from DeepSeek OCR

### Backward Compatibility

The system supports both processing methods:
- **New documents**: Use Docling presets
- **Existing documents**: Continue using DeepSeek OCR

No migration needed for existing documents.

### Comparison

| Feature | DeepSeek OCR | Docling |
|---------|--------------|---------|
| Layout Analysis | Basic | Advanced |
| Table Extraction | Manual | Automated |
| Code Recognition | No | Yes |
| Formula Recognition | No | Yes (LaTeX) |
| Multi-language | Via prompt | Native support |
| Image Description | Via grounding | Via VLM |
| Speed | Fast | Moderate |
| Dependencies | Ollama | Python only |

### When to Use Which

**Use Docling when:**
- Processing technical documents with tables, code, formulas
- Need structured JSON output
- Want advanced layout understanding
- Processing multi-language documents
- Need image descriptions

**Use DeepSeek OCR when:**
- Need fastest processing
- Working with simple text documents
- Already have Ollama infrastructure
- Custom prompts for specific extraction

## Support

For issues or questions:
1. Check logs: Celery worker logs show detailed processing info
2. Django admin: View processing status and debug data
3. API: Use `/api/documents/{sqid}/progress` to monitor processing

## References

- [Docling Documentation](https://docling-project.github.io/docling/)
- [Docling GitHub](https://github.com/docling-project/docling)
- [Docling Technical Report](https://arxiv.org/abs/2408.09869)
