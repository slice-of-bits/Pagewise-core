import os
import logging
import tempfile

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from images.models import Image

logger = logging.getLogger(__name__)


@shared_task
def extract_images_from_page(page_id: int, extracted_images: list, output_dir: str):
    """Extract images from OCR result and save them to the database
    
    This task is called after OCR processing to extract and save images.
    It also generates alt text using ollama with qwen-2vl model.
    
    Args:
        page_id: The ID of the page to extract images from
        extracted_images: List of extracted image info from OCR result
        output_dir: Directory where extracted images are temporarily stored
        
    Returns:
        List of image sqids in the order they were extracted
    """
    from documents.models import Page
    
    logger.info(f"Extracting {len(extracted_images)} images for page {page_id}")
    image_sqids = []
    
    try:
        page = Page.objects.get(id=page_id)
        
        for img_info in extracted_images:
            img_path = img_info['path']
            logger.info(f"Processing image at path: {img_path}")

            if os.path.exists(img_path):
                try:
                    with open(img_path, 'rb') as img_file:
                        file_content = img_file.read()

                        # Validate file content
                        if len(file_content) == 0:
                            logger.error(f"Image file at {img_path} is empty, skipping")
                            continue

                        # Create image object without saving to DB yet
                        image_obj = Image(
                            page=page,
                            metadata={'index': img_info['index']}
                        )

                        # Save the image file - Django will automatically populate width and height
                        image_obj.image_file.save(
                            f"image_{img_info['index']}.png",
                            ContentFile(file_content),
                            save=True  # This saves the image_obj to DB with auto-populated dimensions
                        )

                        # Verify the file was actually saved
                        if not image_obj.image_file:
                            logger.error(f"Failed to save image file for index {img_info['index']}, deleting image object")
                            image_obj.delete()
                            continue

                        # Add the sqid to the list
                        image_sqids.append(image_obj.sqid)

                        logger.info(f"Saved extracted image {img_info['index']} from page {page} with sqid {image_obj.sqid} (dimensions: {image_obj.width}x{image_obj.height}, file: {image_obj.image_file.name})")
                        
                        # Generate alt text asynchronously
                        generate_image_alt_text.delay(image_obj.id)

                except Exception as img_error:
                    logger.error(f"Error saving image at index {img_info['index']}: {str(img_error)}")
                    # Clean up if image object was created
                    try:
                        if 'image_obj' in locals() and image_obj.pk:
                            image_obj.delete()
                    except:
                        pass
            else:
                logger.warning(f"Image file not found at path: {img_path}")

    except Exception as e:
        logger.error(f"Error extracting images from page {page_id}: {str(e)}")

    logger.info(f"Returning {len(image_sqids)} image sqids: {image_sqids}")
    return image_sqids


@shared_task
def generate_image_alt_text(image_id: int):
    """Generate alt text for an image using ollama with qwen-2vl model
    
    Args:
        image_id: The ID of the image to generate alt text for
    """
    logger.info(f"Generating alt text for image {image_id}")
    
    try:
        image = Image.objects.get(id=image_id)
        
        # Get OLLAMA_HOST from environment
        ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
        
        # Get model name from environment or use default
        model_name = os.environ.get('IMAGE_ALT_TEXT_MODEL', 'qwen2-vl')
        
        # Download the image to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            with default_storage.open(image.image_file.name, 'rb') as img_file:
                tmp_file.write(img_file.read())
            img_path = tmp_file.name
        
        try:
            # Use ollama to generate alt text with vision model
            import ollama
            
            # Read the image and encode it to base64
            with open(img_path, 'rb') as img_file:
                import base64
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Create ollama client with custom host
            client = ollama.Client(host=ollama_host)
            
            # Generate alt text using vision model
            response = client.chat(
                model=model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': 'Describe this image concisely in 5-10 words suitable for a filename. Focus on the main subject.',
                        'images': [img_base64]
                    }
                ]
            )
            
            # Extract alt text from response
            alt_text = response['message']['content'].strip()
            
            # Update image with alt text
            image.alt_text = alt_text
            image.save()
            
            logger.info(f"Generated alt text for image {image_id}: {alt_text}")
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(img_path)
            except (OSError, PermissionError):
                pass
                
    except Image.DoesNotExist:
        logger.error(f"Image with ID {image_id} not found")
    except Exception as e:
        logger.error(f"Error generating alt text for image {image_id}: {str(e)}")
