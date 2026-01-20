"""
DeepSeek OCR package for document processing using Ollama.
"""

from .client import run_ollama_ocr
from .parser import parse_bounding_box, parse_ocr_output
from .extractor import extract_images_from_bounding_boxes, visualize_bounding_boxes
from .processor import process_image_with_ollama
from .utils import (
    regenerate_markdown_with_sqids,
    create_sqid_image_url_generator,
    create_placeholder_image_url_generator
)

__all__ = [
    'run_ollama_ocr',
    'parse_bounding_box',
    'parse_ocr_output',
    'extract_images_from_bounding_boxes',
    'visualize_bounding_boxes',
    'process_image_with_ollama',
    'regenerate_markdown_with_sqids',
    'create_sqid_image_url_generator',
    'create_placeholder_image_url_generator',
]
