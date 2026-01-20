import os
import logging
import tempfile
import time
import json

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.postgres.search import SearchVector
import fitz  # PyMuPDF
from PIL import Image as PILImage

from documents.models import Document, Page, ProcessingStatus, DeepSeekOCRSettings
from deepseek_ocr import process_image_with_ollama, create_placeholder_image_url_generator

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_document(self, document_id: int):
    """
    Main task to process an uploaded document
    1. Extract page count
    2. Generate thumbnail
    3. Split PDF into individual pages
    4. Start processing tasks for each page
    """
    try:
        document = Document.objects.get(id=document_id)
        document.processing_status = ProcessingStatus.PROCESSING
        document.save()

        logger.info(f"Starting processing of document: {document.title}")

        # Generate thumbnail from first page of PDF
        # For S3 storage, we need to handle file access differently

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            # Use default_storage to read the file (works for both S3 and local)
            with default_storage.open(document.original_pdf.name, 'rb') as pdf_file:
                tmp_file.write(pdf_file.read())
            pdf_path = tmp_file.name

        pdf_doc = None
        try:
            pdf_doc = fitz.open(pdf_path)
            document.page_count = len(pdf_doc)
            document.save()
            pdf_doc.close()
            pdf_doc = None
        except Exception as e:
            if pdf_doc is not None:
                pdf_doc.close()
            raise
        finally:
            # Clean up temporary file
            try:
                os.unlink(pdf_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not delete temporary file {pdf_path}: {e}")
                # Try brief delay and retry
                time.sleep(0.1)
                try:
                    os.unlink(pdf_path)
                except (OSError, PermissionError):
                    logger.error(f"Could not delete temporary file even after delay: {pdf_path}")

        # Generate thumbnail from first page
        generate_thumbnail.delay(document_id)

        # Split PDF into individual pages
        split_pdf_pages.delay(document_id)

        logger.info(f"Document processing initiated for {document.title} with {document.page_count} pages")

    except Document.DoesNotExist:
        logger.error(f"Document with ID {document_id} not found")
        self.retry(countdown=60, max_retries=3)
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        document = Document.objects.get(id=document_id)
        document.processing_status = ProcessingStatus.FAILED
        document.save()
        raise


@shared_task
def generate_thumbnail(document_id: int):
    """Generate thumbnail from first page of PDF"""
    try:
        document = Document.objects.get(id=document_id)

        # Use temporary file for PDF processing with S3 storage

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            # Use default_storage to read the file (works for both S3 and local)
            with default_storage.open(document.original_pdf.name, 'rb') as pdf_file:
                tmp_file.write(pdf_file.read())
            pdf_path = tmp_file.name

        pdf_doc = None
        try:
            pdf_doc = fitz.open(pdf_path)
            first_page = pdf_doc[0]

            # Render page to image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = first_page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("jpg")

            # Save thumbnail using Django FileField.save() - it handles all path logic
            content_file = ContentFile(img_data, name="cover.jpg")
            document.thumbnail.save("cover.jpg", content_file, save=True)

            pdf_doc.close()
            pdf_doc = None
        except Exception as e:
            if pdf_doc is not None:
                pdf_doc.close()
            raise
        finally:
            # Clean up temporary file
            try:
                os.unlink(pdf_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not delete temporary file {pdf_path}: {e}")
                # Try brief delay and retry
                time.sleep(0.1)
                try:
                    os.unlink(pdf_path)
                except (OSError, PermissionError):
                    logger.error(f"Could not delete temporary file even after delay: {pdf_path}")

        logger.info(f"Thumbnail generated for document: {document.title}")

    except Exception as e:
        logger.error(f"Error generating thumbnail for document {document_id}: {str(e)}")


@shared_task
def split_pdf_pages(document_id: int):
    """Split PDF into individual page files"""
    try:
        document = Document.objects.get(id=document_id)

        # Use temporary file for PDF processing with S3 storage

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            # Use default_storage to read the file (works for both S3 and local)
            with default_storage.open(document.original_pdf.name, 'rb') as pdf_file:
                tmp_file.write(pdf_file.read())
            pdf_path = tmp_file.name

        pdf_doc = None
        try:
            pdf_doc = fitz.open(pdf_path)

            for page_num in range(len(pdf_doc)):
                # Create new PDF with single page
                page_pdf = fitz.open()
                page_pdf.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)

                # Create Page object first (this will generate the proper path)
                page, created = Page.objects.get_or_create(
                    document=document,
                    page_number=page_num + 1,
                    defaults={
                        'processing_status': ProcessingStatus.PENDING
                    }
                )

                # Create a separate temporary file for each page
                page_tmp_fd, page_tmp_path = tempfile.mkstemp(suffix='.pdf')
                try:
                    # Close the file descriptor first
                    os.close(page_tmp_fd)

                    # Save PDF to temporary file
                    page_pdf.save(page_tmp_path)
                    page_pdf.close()

                    # Validate the PDF file before saving
                    file_size = os.path.getsize(page_tmp_path)
                    if file_size == 0:
                        logger.error(f"Generated PDF for page {page_num + 1} is empty")
                        continue

                    # Verify it's a valid PDF by checking content
                    with open(page_tmp_path, 'rb') as test_file:
                        content = test_file.read()
                        if not content.startswith(b'%PDF'):
                            logger.error(f"Generated file for page {page_num + 1} is not a valid PDF")
                            continue

                    logger.info(f"Successfully created page PDF {page_num + 1}: {file_size} bytes")

                    # Read the saved PDF file and save to Django storage
                    with open(page_tmp_path, 'rb') as saved_pdf:
                        page.page_pdf.save(
                            f"{page_num + 1}.pdf",
                            ContentFile(saved_pdf.read()),
                            save=True
                        )

                finally:
                    # Clean up page temporary file
                    try:
                        os.unlink(page_tmp_path)
                    except (OSError, PermissionError):
                        # If we can't delete immediately, that's okay
                        pass

                # Start processing this page
                process_page.delay(page.id)

            # Explicitly close the main PDF document BEFORE cleanup
            if pdf_doc is not None:
                pdf_doc.close()
                pdf_doc = None

        except Exception as e:
            # Make sure PDF is closed on error too
            if pdf_doc is not None:
                pdf_doc.close()
            raise
        finally:
            # Clean up main temporary file - PDF should be closed by now
            try:
                os.unlink(pdf_path)
            except (OSError, PermissionError) as e:
                # If we can't delete immediately, log it but don't fail
                logger.warning(f"Could not delete temporary file {pdf_path}: {e}")
                # Try to schedule cleanup for later
                import time
                time.sleep(0.1)  # Brief delay
                try:
                    os.unlink(pdf_path)
                    logger.info(f"Successfully deleted temporary file after delay: {pdf_path}")
                except (OSError, PermissionError):
                    logger.error(f"Could not delete temporary file even after delay: {pdf_path}")

        logger.info(f"PDF split completed for document: {document.title}")

    except Exception as e:
        logger.error(f"Error splitting PDF for document {document_id}: {str(e)}")


@shared_task
def process_page(page_id: int):
    """Process a single page with DeepSeek-OCR"""
    try:
        page = Page.objects.get(id=page_id)
        page.processing_status = ProcessingStatus.PROCESSING
        page.save()

        # Get OCR settings
        settings = DeepSeekOCRSettings.get_default_settings()
        
        # Get the OCR model from the document
        ocr_model = page.document.ocr_model or settings.default_model
        
        # Get OLLAMA_HOST from environment
        ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')

        # Convert PDF page to image for OCR processing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            with default_storage.open(page.page_pdf.name, 'rb') as pdf_file:
                content = pdf_file.read()
                if len(content) == 0:
                    raise ValueError(f"Page PDF file {page.page_pdf.name} is empty")
                if not content.startswith(b'%PDF'):
                    raise ValueError(f"Page PDF file {page.page_pdf.name} is not a valid PDF")
                tmp_pdf.write(content)
            pdf_path = tmp_pdf.name

        image_path = None
        output_dir = None
        try:
            # Convert PDF to image
            pdf_doc = fitz.open(pdf_path)
            first_page = pdf_doc[0]
            
            # Render page to image at high resolution
            mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR quality
            pix = first_page.get_pixmap(matrix=mat)
            
            # Save as temporary image
            image_fd, image_path = tempfile.mkstemp(suffix='.png')
            os.close(image_fd)
            pix.save(image_path)
            pdf_doc.close()
            
            # Create temporary output directory for OCR results
            output_dir = tempfile.mkdtemp()
            
            # Process image with DeepSeek-OCR
            # Use placeholder URLs - we'll replace them with sqids after saving images
            logger.info(f"Processing page {page.page_number} of document {page.document.title} with model {ocr_model}")
            result = process_image_with_ollama(
                image_path=image_path,
                output_dir=output_dir,
                prompt=settings.default_prompt,
                model=ocr_model,
                host=ollama_host,
                image_url_generator=create_placeholder_image_url_generator()
            )
            
            # Store OCR results
            page.ocr_markdown_raw = result['raw_output']
            page.ocr_references = result['references']
            
            # Save bbox visualization image
            bbox_viz_path = os.path.join(output_dir, 'bbox_visualization.png')
            if os.path.exists(bbox_viz_path):
                with open(bbox_viz_path, 'rb') as viz_file:
                    page.bbox_visualization.save(
                        f"page_{page.page_number}_bbox.png",
                        ContentFile(viz_file.read()),
                        save=False
                    )
            
            # Extract and save images in a separate task
            markdown_with_sqids = result['markdown']
            logger.info(f"Initial markdown: {markdown_with_sqids[:200]}...")
            logger.info(f"Extracted images count: {len(result['extracted_images']) if result['extracted_images'] else 0}")

            if result['extracted_images']:
                # Import the image extraction task
                from images.tasks import extract_images_from_page
                
                # Call the image extraction task synchronously to get the sqids
                image_sqids = extract_images_from_page(page.id, result['extracted_images'], output_dir)
                logger.info(f"Image SQIDs collected: {image_sqids}")

                # Replace placeholder URLs with actual sqid-based URLs
                # Now using the new URL format: /sqid/filename.ext
                from images.models import Image
                for idx, sqid in enumerate(image_sqids):
                    placeholder = f"__IMAGE_PLACEHOLDER_{idx}__"
                    
                    # Get the image object to get the full URL path
                    try:
                        image_obj = Image.objects.get(sqid=sqid)
                        url_path = image_obj.url_path  # This will be /sqid/filename.ext
                        logger.info(f"Replacing '{placeholder}' with '{url_path}'")
                        markdown_with_sqids = markdown_with_sqids.replace(placeholder, url_path)
                    except Image.DoesNotExist:
                        logger.error(f"Image with sqid {sqid} not found")

                # Remove any remaining orphaned placeholders (where extraction failed)
                import re
                orphaned_placeholders = re.findall(r'__IMAGE_PLACEHOLDER_\d+__', markdown_with_sqids)
                if orphaned_placeholders:
                    logger.warning(f"Found {len(orphaned_placeholders)} orphaned placeholders for page {page.page_number}: {orphaned_placeholders}")
                    for orphan in orphaned_placeholders:
                        logger.warning(f"Removing orphaned placeholder: {orphan}")
                        # Remove the entire markdown image syntax
                        markdown_with_sqids = re.sub(r'!\[Image\]\(' + re.escape(orphan) + r'\)\n?', '', markdown_with_sqids)
            else:
                logger.warning(f"No extracted images found for page {page.page_number}")

            logger.info(f"Final markdown: {markdown_with_sqids[:200]}...")

            # Store the final markdown with sqids
            page.text_markdown_clean = markdown_with_sqids

            # Update search vector
            try:
                page.search_vector = SearchVector('text_markdown_clean')
            except Exception as e:
                logger.warning(f"Could not update search vector for page {page.id}: {e}")

            page.processing_status = ProcessingStatus.COMPLETED
            page.save()
            
            # Update document progress
            update_document_progress(page.document.id)
            
            logger.info(f"Page processing completed: {page}")

        finally:
            # Clean up temporary files
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.unlink(pdf_path)
                except (OSError, PermissionError):
                    pass
            
            if image_path and os.path.exists(image_path):
                try:
                    os.unlink(image_path)
                except (OSError, PermissionError):
                    pass
            
            # Clean up output directory
            if output_dir and os.path.exists(output_dir):
                try:
                    import shutil
                    shutil.rmtree(output_dir)
                except (OSError, PermissionError):
                    pass

    except Exception as e:
        logger.error(f"Error processing page {page_id}: {str(e)}")
        page = Page.objects.get(id=page_id)
        page.processing_status = ProcessingStatus.FAILED
        page.save()


def clean_markdown_text(raw_text: str) -> str:
    """Clean markdown text by removing headers, footers, and page numbers"""
    lines = raw_text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Skip lines that look like page numbers
        if line.strip().isdigit() and len(line.strip()) <= 3:
            continue

        # Skip very short lines at start/end that might be headers/footers
        if len(line.strip()) < 10 and (not cleaned_lines or len(cleaned_lines) < 3):
            continue

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def update_document_progress(document_id: int):
    """Update document processing progress"""
    try:
        document = Document.objects.get(id=document_id)
        completed_pages = document.pages.filter(processing_status=ProcessingStatus.COMPLETED).count()
        document.processed_pages = completed_pages

        if completed_pages == document.page_count:
            document.processing_status = ProcessingStatus.COMPLETED
        elif document.pages.filter(processing_status=ProcessingStatus.FAILED).exists():
            # Check if all pages are either completed or failed
            total_processed = document.pages.filter(
                processing_status__in=[ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
            ).count()
            if total_processed == document.page_count:
                document.processing_status = ProcessingStatus.FAILED

        document.save()
        logger.info(f"Document progress updated: {document.title} - {completed_pages}/{document.page_count}")

    except Exception as e:
        logger.error(f"Error updating document progress for {document_id}: {str(e)}")
