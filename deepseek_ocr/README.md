# DeepSeek OCR Package

This package provides integration with DeepSeek OCR models via Ollama for document processing.

## Overview

The DeepSeek OCR package processes document images and extracts:
- Markdown-formatted text
- Bounding boxes for text regions
- Extracted images from the document
- Structured references with type annotations

## Modules

### `client.py`
Ollama client for running DeepSeek OCR models.

```python
from deepseek_ocr.client import run_ollama_ocr

result = run_ollama_ocr(
    image_path='path/to/image.png',
    prompt='<|grounding|>Convert the document to markdown.',
    model='deepseek-ocr',
    host='http://localhost:11434'
)
```

### `parser.py`
Parses OCR output to extract references and generate markdown.

```python
from deepseek_ocr.parser import parse_ocr_output

references, markdown = parse_ocr_output(ocr_text)
```

### `extractor.py`
Extracts images from bounding boxes and creates visualizations.

```python
from deepseek_ocr.extractor import extract_images_from_bounding_boxes, visualize_bounding_boxes

# Extract images
extracted = extract_images_from_bounding_boxes(
    image_path='path/to/image.png',
    references=references,
    output_dir='output'
)

# Visualize bounding boxes
visualize_bounding_boxes(
    image_path='path/to/image.png',
    references=references,
    output_path='output/visualization.png'
)
```

### `processor.py`
High-level processing pipeline that combines all functionality.

```python
from deepseek_ocr.processor import process_image_with_ollama

result = process_image_with_ollama(
    image_path='path/to/image.png',
    output_dir='output',
    prompt='<|grounding|>Convert the document to markdown.',
    model='deepseek-ocr',
    host='http://localhost:11434'
)

# Result contains:
# - references: List of extracted references with bounding boxes
# - markdown: Generated markdown text
# - raw_output: Raw OCR output
# - extracted_images: List of extracted image info
```

### `utils.py`
Utility functions for working with image URLs and sqids.

```python
from deepseek_ocr.utils import (
    regenerate_markdown_with_sqids,
    create_sqid_image_url_generator,
    create_placeholder_image_url_generator
)

# Generate markdown with placeholder URLs, then replace with sqids
image_url_gen = create_placeholder_image_url_generator()
references, markdown = parse_ocr_output(ocr_text, image_url_gen)

# After saving images to database and getting their sqids
sqids = ['abc123', 'def456', 'ghi789']
final_markdown = regenerate_markdown_with_sqids(markdown, sqids)
```

## Working with Image URLs and SQID

The package supports custom image URL generation through the `image_url_generator` parameter. This is particularly useful when integrating with database models that use unique identifiers (sqids).

### Approach 1: Placeholder URLs (Recommended)

Use placeholders during parsing, then replace with sqids after saving images:

```python
from deepseek_ocr import (
    process_image_with_ollama,
    create_placeholder_image_url_generator
)

# Parse with placeholders
result = process_image_with_ollama(
    image_path='image.png',
    output_dir='output',
    image_url_generator=create_placeholder_image_url_generator()
)

# Save images to database and collect sqids
image_sqids = []
for img_info in result['extracted_images']:
    image_obj = Image.objects.create(...)
    image_sqids.append(image_obj.sqid)

# Replace placeholders with sqids
from deepseek_ocr import regenerate_markdown_with_sqids
final_markdown = regenerate_markdown_with_sqids(result['markdown'], image_sqids)
```

### Approach 2: Pre-determined SQIDs

If you already have the sqids before parsing:

```python
from deepseek_ocr import parse_ocr_output, create_sqid_image_url_generator

# Create URL generator with known sqids
sqids = ['abc123', 'def456']
url_generator = create_sqid_image_url_generator(sqids)

# Parse with sqids directly
references, markdown = parse_ocr_output(ocr_text, url_generator)
```

### Benefits of SQID Integration

- **Unique References**: Each image gets a unique identifier that can be used to link back to the source
- **Easy Lookup**: Frontend can easily fetch image metadata using the sqid from the markdown
- **Consistent**: Works seamlessly with the rest of the application's sqid-based architecture

## Configuration

The package uses the following environment variables:

- `OLLAMA_HOST`: URL of the Ollama server (default: `http://localhost:11434`)

## Reference Types

The parser recognizes the following reference types:

- `text`: Regular text content
- `image`: Image regions
- `sub_title`: Section subtitles
- `title`: Document titles

## Bounding Box Format

Bounding boxes are represented as `[x1, y1, x2, y2]` where:
- `(x1, y1)` is the top-left corner
- `(x2, y2)` is the bottom-right corner

The package automatically detects whether coordinates are normalized (0-1000 range) or in pixels.

## Testing

Run tests with:

```bash
python -m pytest deepseek_ocr/tests.py
```

or

```bash
python deepseek_ocr/tests.py
```
