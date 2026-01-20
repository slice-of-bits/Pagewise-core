"""
Image extraction and visualization utilities for DeepSeek OCR.
"""
from pathlib import Path
from typing import List, Dict
from PIL import Image, ImageDraw


def extract_images_from_bounding_boxes(
    image_path: str,
    references: List[Dict],
    output_dir: str = "output"
) -> List[Dict]:
    """
    Extract image regions based on bounding boxes and save them.
    
    Args:
        image_path: Path to the original image
        references: List of reference dictionaries with bounding boxes
        output_dir: Directory to save extracted images
        
    Returns:
        List of extracted image info (path, width, height)
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Open the original image
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # Detect coordinate system: check if bounding boxes are normalized (0-1000 range)
    # or if they use pixel coordinates
    max_coord = 0
    for ref in references:
        bbox = ref['bounding_box']
        max_coord = max(max_coord, max(bbox))
    
    # If max coordinate is <= 1000 but image is larger, assume normalized coordinates
    use_normalized = max_coord <= 1000 and (img_width > 1000 or img_height > 1000)
    
    if use_normalized:
        scale_x = img_width / 1000.0
        scale_y = img_height / 1000.0
    else:
        scale_x = scale_y = 1.0
    
    # Extract images for each reference with type 'image'
    image_count = 0
    extracted_images = []
    for ref in references:
        if ref['type'] == 'image':
            bbox = ref['bounding_box']
            
            # Scale coordinates if needed
            if use_normalized:
                scaled_bbox = [
                    int(bbox[0] * scale_x),
                    int(bbox[1] * scale_y),
                    int(bbox[2] * scale_x),
                    int(bbox[3] * scale_y)
                ]
                bbox = scaled_bbox
            
            # bbox format: [x1, y1, x2, y2]
            cropped = img.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
            
            output_file = output_path / f"image_{image_count}.png"
            cropped.save(output_file)
            
            extracted_images.append({
                'path': str(output_file),
                'width': cropped.size[0],
                'height': cropped.size[1],
                'index': image_count
            })
            image_count += 1
    
    return extracted_images


def visualize_bounding_boxes(
    image_path: str,
    references: List[Dict],
    output_path: str = "output/bbox_visualization.png"
) -> None:
    """
    Draw all bounding boxes on the image for visualization/debugging.
    
    Args:
        image_path: Path to the original image
        references: List of reference dictionaries with bounding boxes
        output_path: Path to save visualization image
    """
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # Create a copy to draw on
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # Detect coordinate system
    max_coord = max(max(ref['bounding_box']) for ref in references) if references else 0
    use_normalized = max_coord <= 1000 and (img_width > 1000 or img_height > 1000)
    
    if use_normalized:
        scale_x = img_width / 1000.0
        scale_y = img_height / 1000.0
    else:
        scale_x = scale_y = 1.0
    
    # Color map for different types
    colors = {
        'image': 'red',
        'text': 'blue',
        'sub_title': 'green',
        'title': 'purple'
    }
    
    # Draw each bounding box
    for i, ref in enumerate(references):
        bbox = ref['bounding_box']
        ref_type = ref['type']
        
        # Scale if needed
        if use_normalized:
            scaled_bbox = [
                int(bbox[0] * scale_x),
                int(bbox[1] * scale_y),
                int(bbox[2] * scale_x),
                int(bbox[3] * scale_y)
            ]
        else:
            scaled_bbox = bbox
        
        color = colors.get(ref_type, 'yellow')
        
        # Draw rectangle
        draw.rectangle(scaled_bbox, outline=color, width=3)
        
        # Draw label
        label = f"{i+1}: {ref_type}"
        draw.text((scaled_bbox[0], scaled_bbox[1] - 15), label, fill=color)
    
    # Save visualization
    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)
    img_copy.save(output_file)
