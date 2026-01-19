import os
import logging
import tempfile
import time
import json
import base64

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.postgres.search import SearchVector
import fitz  # PyMuPDF
import ocrmypdf
import ollama

from documents.models import Document, Page, Image, ProcessingStatus, OcrSettings

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_document(self, document_id: int):
    """
    Main task to process an uploaded document
    1. Apply OCRmyPDF if enabled (optional)
    2. Extract page count
    3. Generate thumbnail
    4. Split PDF into individual pages
    5. Start processing tasks for each page
    """
    try:
        document = Document.objects.get(id=document_id)
        document.processing_status = ProcessingStatus.PROCESSING
        document.save()

        logger.info(f"Starting processing of document: {document.title}")

        # Get OCR settings for this document
        ocr_settings = document.get_ocr_settings()

        # Step 1: Apply OCRmyPDF if enabled (synchronous to ensure completion)
        if ocr_settings.use_ocrmypdf and not document.ocrmypdf_applied:
            logger.info(f"Applying OCRmyPDF to document: {document.title}")
            # Call OCRmyPDF synchronously to ensure it completes before continuing
            apply_ocrmypdf(document_id)
            # Reload document to get updated ocrmypdf_applied flag
            document.refresh_from_db()
        
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
def apply_ocrmypdf(document_id: int):
    """
    Apply OCRmyPDF to the document to add selectable text layer
    This runs on the complete PDF before splitting into pages
    """
    try:
        document = Document.objects.get(id=document_id)
        
        # Skip if already applied
        if document.ocrmypdf_applied:
            logger.info(f"OCRmyPDF already applied to document: {document.title}")
            return
        
        # Get OCR settings
        ocr_settings = document.get_ocr_settings()
        
        logger.info(f"Starting OCRmyPDF for document: {document.title}")

        # Download PDF to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_input:
            with default_storage.open(document.original_pdf.name, 'rb') as pdf_file:
                tmp_input.write(pdf_file.read())
            input_path = tmp_input.name

        # Create output temporary file
        output_fd, output_path = tempfile.mkstemp(suffix='.pdf')
        os.close(output_fd)

        try:
            # Run OCRmyPDF
            ocrmypdf_args = {
                'language': ocr_settings.ocrmypdf_language,
                'skip_text': True,  # Skip pages that already have text
                'optimize': 1 if ocr_settings.ocrmypdf_compression else 0,
                'output_type': 'pdf',
            }
            
            ocrmypdf.ocr(
                input_path,
                output_path,
                **ocrmypdf_args
            )

            # Upload the OCR'd PDF back to storage, replacing the original
            with open(output_path, 'rb') as ocr_pdf:
                document.original_pdf.save(
                    os.path.basename(document.original_pdf.name),
                    ContentFile(ocr_pdf.read()),
                    save=False
                )
            
            document.ocrmypdf_applied = True
            document.save()

            logger.info(f"OCRmyPDF completed for document: {document.title}")

        except Exception as e:
            logger.error(f"OCRmyPDF failed for document {document_id}: {str(e)}")
            # Don't fail the entire processing pipeline if OCRmyPDF fails
            # Just log the error and continue
        finally:
            # Clean up temporary files
            try:
                os.unlink(input_path)
            except (OSError, PermissionError):
                pass
            try:
                os.unlink(output_path)
            except (OSError, PermissionError):
                pass

    except Exception as e:
        logger.error(f"Error in apply_ocrmypdf for document {document_id}: {str(e)}")


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
    """Process a single page with PaddleOCR-VL via Ollama"""
    try:
        page = Page.objects.get(id=page_id)
        page.processing_status = ProcessingStatus.PROCESSING
        page.save()

        # Get OCR settings
        settings = page.document.get_ocr_settings()

        # Process the page - use temporary file for S3 storage compatibility
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            # Use default_storage to read the file (works for both S3 and local)
            with default_storage.open(page.page_pdf.name, 'rb') as pdf_file:
                content = pdf_file.read()
                if len(content) == 0:
                    raise ValueError(f"Page PDF file {page.page_pdf.name} is empty")
                if not content.startswith(b'%PDF'):
                    raise ValueError(f"Page PDF file {page.page_pdf.name} is not a valid PDF")
                tmp_file.write(content)
            pdf_path = tmp_file.name

        # Convert PDF page to image for PaddleOCR-VL
        image_path = None
        try:
            logger.info(f"Processing page {page.page_number} of document {page.document.title}")
            
            # Convert PDF to image and validate page count first
            pdf_doc = fitz.open(pdf_path)
            
            # Verify PDF has exactly one page before processing
            page_count = len(pdf_doc)
            if page_count != 1:
                logger.error(f"Page PDF should have exactly 1 page, found {page_count}")
                pdf_doc.close()
                page.processing_status = ProcessingStatus.FAILED
                page.save()
                return
            
            # Now that we've validated, process the page
            first_page = pdf_doc[0]
            mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
            pix = first_page.get_pixmap(matrix=mat)
            
            # Save to temporary image file
            image_fd, image_path = tempfile.mkstemp(suffix='.png')
            os.close(image_fd)
            pix.save(image_path)
            pdf_doc.close()
            
            # Call PaddleOCR-VL via Ollama
            try:
                client = ollama.Client(host=settings.ollama_base_url)
                
                # Read image as base64
                with open(image_path, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Call Ollama with PaddleOCR-VL model
                response = client.generate(
                    model=settings.paddleocr_model,
                    prompt='Convert this page to markdown format. Ignore page numbers and headers/footers. Handle multiple columns properly.',
                    images=[image_data],
                )
                
                # Extract markdown from response - validate response structure
                if not isinstance(response, dict) or 'response' not in response:
                    logger.error(f"Invalid response from Ollama for page {page.id}: {response}")
                    page.processing_status = ProcessingStatus.FAILED
                    page.save()
                    return
                
                page.ocr_markdown_raw = response['response']
                
                # Store any layout information if available
                page.paddleocr_layout = {
                    'model': settings.paddleocr_model,
                    'processed_at': str(time.time()),
                }
                
            except Exception as e:
                logger.error(f"PaddleOCR-VL conversion failed for page {page.id}: {e}")
                # Set page as failed but don't crash the task
                page.processing_status = ProcessingStatus.FAILED
                page.save()
                return
                
        finally:
            # Clean up temporary files
            try:
                os.unlink(pdf_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"Could not delete temporary file {pdf_path}: {e}")
                time.sleep(0.1)
                try:
                    os.unlink(pdf_path)
                except (OSError, PermissionError):
                    logger.error(f"Could not delete temporary file even after delay: {pdf_path}")
            
            if image_path:
                try:
                    os.unlink(image_path)
                except (OSError, PermissionError):
                    pass

        # Clean text - PaddleOCR-VL should handle this better than Docling
        if page.ocr_markdown_raw:
            page.text_markdown_clean = clean_markdown_text(page.ocr_markdown_raw)
        else:
            page.text_markdown_clean = ""

        # Extract images from the page if needed
        # Note: This would require additional logic to detect and extract images
        # For now, we'll skip this as PaddleOCR-VL focuses on text extraction
        
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

    except Exception as e:
        logger.error(f"Error processing page {page_id}: {str(e)}")
        page = Page.objects.get(id=page_id)
        page.processing_status = ProcessingStatus.FAILED
        page.save()


@shared_task
def extract_images_from_page(page_id: int, layout_data: dict):
    """Extract images from page layout data"""
    try:
        page = Page.objects.get(id=page_id)

        # Extract figures from layout data
        if 'figures' in layout_data:
            for idx, figure in enumerate(layout_data['figures']):
                if 'image' in figure:
                    # Save image
                    image_name = f"page_{page.page_number}_img_{idx + 1}.jpg"
                    image_obj = Image.objects.create(
                        page=page,
                        caption=figure.get('caption', ''),
                        metadata={'figure_data': figure}
                    )

                    # Note: In a real implementation, you'd extract the actual image data
                    # from the figure object and save it to the ImageField
                    logger.info(f"Image extracted from page {page}: {image_name}")

    except Exception as e:
        logger.error(f"Error extracting images from page {page_id}: {str(e)}")


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
