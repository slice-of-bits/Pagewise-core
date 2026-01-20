"""
Parser for DeepSeek OCR output.
"""
import re
from typing import List, Dict, Tuple


def parse_bounding_box(bbox_str: str) -> List[int]:
    """
    Parse bounding box string like '[[53, 123, 477, 435]]' to list [53, 123, 477, 435].
    
    Args:
        bbox_str: String representation of bounding box
        
    Returns:
        List of 4 integers [x1, y1, x2, y2]
    """
    # Extract numbers from the string
    numbers = re.findall(r'\d+', bbox_str)
    return [int(n) for n in numbers]


def parse_ocr_output(ocr_text: str) -> Tuple[List[Dict], str]:
    """
    Parse the OCR output to extract references with bounding boxes and generate markdown.
    
    Args:
        ocr_text: The raw OCR output from the model
        
    Returns:
        Tuple of (references list, markdown text)
    """
    references = []
    markdown_parts = []
    
    # Pattern to match: <|ref|>type<|/ref|><|det|>[[x1, y1, x2, y2]]<|/det|>
    # Followed by optional text content
    # Using lazy matching to capture content until the next <|ref|> tag or end
    pattern = r'<\|ref\|>(\w+)<\|/ref\|><\|det\|>(\[\[.*?\]\])<\|/det\|>(.*?)(?=<\|ref\|>|$)'

    matches = re.finditer(pattern, ocr_text, re.DOTALL)
    
    for match in matches:
        ref_type = match.group(1)
        bbox_str = match.group(2)
        content = match.group(3).strip()
        
        bbox = parse_bounding_box(bbox_str)
        
        # Store reference data
        ref_data = {
            'type': ref_type,
            'bounding_box': bbox,
            'content': content
        }
        references.append(ref_data)
        
        # Generate markdown based on type
        if ref_type == 'image':
            markdown_parts.append(f"![Image](output/image_{len([r for r in references if r['type'] == 'image']) - 1}.png)\n")
        elif ref_type == 'sub_title':
            # check if the content start with ## then do nothing, else add proper markdown heading
            if not content.startswith('#'):
                markdown_parts.append(f"## {content}\n")
            else:
                markdown_parts.append(f"{content}\n")
        elif ref_type == 'text':
            # check if the content start with a number then text. then add a dot after the number for the markdown list
            if re.match(r'^\d+\s', content):
                content = re.sub(r'^(\d+)\s', r'\1. ', content)

            markdown_parts.append(f"{content}\n")
        else:
            markdown_parts.append(f"{content}\n")
    
    markdown_text = '\n'.join(markdown_parts)
    
    return references, markdown_text
