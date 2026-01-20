"""
Main processor for DeepSeek OCR.
"""
import json
from pathlib import Path
from typing import Dict, List

from .client import run_ollama_ocr
from .parser import parse_ocr_output
from .extractor import extract_images_from_bounding_boxes, visualize_bounding_boxes


def process_image_with_ollama(
    image_path: str,
    output_dir: str = "output",
    prompt: str = "<|grounding|>Convert the document to markdown.",
    model: str = "deepseek-ocr",
    host: str = None
) -> Dict:
    """
    Complete pipeline: run OCR, parse output, extract images, save data.
    
    Args:
        image_path: Path to the image to process
        output_dir: Directory for output files
        prompt: Prompt to send to the model
        model: The model name to use (default: deepseek-ocr)
        host: Ollama host URL (if None, uses OLLAMA_HOST env var or default)
        
    Returns:
        Dictionary with references, markdown, and raw output
    """
    # Step 1: Run Ollama OCR
    ocr_output = run_ollama_ocr(image_path, prompt, model, host)
    
    # Save raw OCR output
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    raw_output_path = output_path / "raw_ocr_output.txt"
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(ocr_output)
    
    # Step 2: Parse the output
    references, markdown = parse_ocr_output(ocr_output)
    
    # Step 3: Extract images based on bounding boxes
    extracted_images = extract_images_from_bounding_boxes(image_path, references, output_dir)
    
    # Step 4: Save references to JSON
    references_path = output_path / "references.json"
    with open(references_path, 'w', encoding='utf-8') as f:
        json.dump(references, f, indent=2, ensure_ascii=False)
    
    # Step 5: Visualize bounding boxes
    bbox_viz_path = output_path / "bbox_visualization.png"
    if references:
        visualize_bounding_boxes(image_path, references, str(bbox_viz_path))
    
    # Step 6: Save markdown
    markdown_path = output_path / "output.md"
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    return {
        'references': references,
        'markdown': markdown,
        'raw_output': ocr_output,
        'extracted_images': extracted_images
    }
