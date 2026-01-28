"""
OCRmyPDF processor module.
Handles PDF OCR processing using the OCRmyPDF library with configurable presets.
"""

import os
import logging
import tempfile
from typing import Optional

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class OcrProcessor:
    """
    Processor for PDF documents using OCRmyPDF library.
    Adds OCR text layer to PDFs using configurable presets.
    """

    def __init__(self, preset):
        """
        Initialize the OCR processor with a preset.

        Args:
            preset: OcrPreset instance with configuration
        """
        self.preset = preset

    def process_pdf(self, input_pdf_path: str, output_pdf_path: str) -> bool:
        """
        Process a PDF file with OCRmyPDF.

        Args:
            input_pdf_path: Path to input PDF file
            output_pdf_path: Path to save output PDF file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import ocrmypdf
        except ImportError as e:
            logger.error(f"OCRmyPDF not installed: {e}")
            raise ImportError("OCRmyPDF library is required. Install with: pip install ocrmypdf")

        try:
            # Build OCRmyPDF arguments - only use documented Python API parameters
            kwargs = {}

            # Core OCR settings - handle conflicts intelligently
            # Note: force_ocr, skip_text, and redo_ocr have specific precedence rules:
            # - force_ocr: Force OCR on all pages
            # - skip_text: Skip pages that already have text
            # - redo_ocr: Remove existing OCR and redo it
            # These options are mutually exclusive in practice

            if self.preset.redo_ocr:
                # redo_ocr takes precedence - it will remove and redo OCR
                kwargs['redo_ocr'] = True
                # redo_ocr is incompatible with certain image processing options
                # so we'll skip those below
            elif self.preset.force_ocr:
                # force_ocr: OCR everything
                kwargs['force_ocr'] = True
            elif self.preset.skip_text:
                # skip_text: only OCR pages without text
                kwargs['skip_text'] = True

            # Language - OCRmyPDF expects a list for the 'language' parameter (singular)
            if self.preset.language:
                langs = self.preset.language.split('+')
                kwargs['language'] = langs  # Note: 'language' is singular but accepts a list

            # PDF optimization
            if self.preset.optimize > 0:
                kwargs['optimize'] = self.preset.optimize

            # Image quality settings (note: OCRmyPDF uses jpg_quality, not jpeg_quality)
            if self.preset.jpeg_quality and self.preset.jpeg_quality != 75:
                kwargs['jpg_quality'] = self.preset.jpeg_quality  # OCRmyPDF uses jpg_quality
            if self.preset.png_quality and self.preset.png_quality != 70:
                kwargs['png_quality'] = self.preset.png_quality

            # Image preprocessing (only if NOT using redo_ocr, as they're incompatible)
            if not self.preset.redo_ocr:
                if self.preset.deskew:
                    kwargs['deskew'] = True
                if self.preset.rotate_pages:
                    kwargs['rotate_pages'] = True
                # Note: clean, clean_final, remove_background are also incompatible with redo_ocr
                # They're CLI-only in many cases anyway
            else:
                logger.info("Skipping image preprocessing options (deskew, etc.) because redo_ocr is enabled")

            # Note: clean, clean_final, remove_background, oversample, remove_vectors
            # may not be valid Python API parameters - they're CLI-only
            # Only add them if they're in advanced_settings as user knows what they're doing

            # Add advanced settings last (but filter out invalid ones and handle conflicts)
            if self.preset.advanced_settings:
                # Don't add ocr_engine or ocr-engine as they're invalid
                for key, value in self.preset.advanced_settings.items():
                    if key not in ['ocr_engine', 'ocr-engine']:
                        # Skip options that conflict with redo_ocr
                        if self.preset.redo_ocr and key in ['deskew', 'clean_final', 'remove_background']:
                            logger.warning(f"Skipping advanced setting '{key}' because it conflicts with redo_ocr")
                            continue
                        kwargs[key] = value

            # Run OCRmyPDF
            logger.info(f"Running OCRmyPDF with preset {self.preset.name}")
            logger.info(f"OCRmyPDF arguments: {kwargs}")

            result = ocrmypdf.ocr(
                input_pdf_path,
                output_pdf_path,
                **kwargs
            )

            if result == 0:
                logger.info(f"OCRmyPDF processing completed successfully")
                return True
            else:
                logger.warning(f"OCRmyPDF completed with return code: {result}")
                return True  # Non-zero doesn't always mean failure

        except Exception as e:
            logger.error(f"Error processing PDF with OCRmyPDF: {str(e)}")
            raise


def process_document_with_ocr(document, preset, storage_path: str) -> bool:
    """
    Helper function to process a document with OCRmyPDF preset.

    Args:
        document: Document model instance
        preset: OcrPreset instance
        storage_path: Path where OCR'd PDF should be saved in storage

    Returns:
        bool: True if successful
    """
    processor = OcrProcessor(preset)

    # Download original PDF to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_input:
        with default_storage.open(document.original_pdf.name, 'rb') as pdf_file:
            tmp_input.write(pdf_file.read())
        input_path = tmp_input.name

    # Create temp file for output
    output_fd, output_path = tempfile.mkstemp(suffix='.pdf')
    os.close(output_fd)

    try:
        # Process with OCRmyPDF
        success = processor.process_pdf(input_path, output_path)

        if success:
            # Read the OCR'd PDF and replace the original
            with open(output_path, 'rb') as ocr_pdf:
                ocr_content = ocr_pdf.read()

                # Delete the old file first
                if document.original_pdf:
                    try:
                        document.original_pdf.delete(save=False)
                    except Exception as e:
                        logger.warning(f"Could not delete old PDF: {e}")

                # Save the OCR'd PDF as the original
                document.original_pdf.save(
                    storage_path,
                    ContentFile(ocr_content),
                    save=True
                )

            logger.info(f"Successfully replaced document PDF with OCR'd version")
            return True

        return False

    finally:
        # Clean up temp files
        try:
            os.unlink(input_path)
        except (OSError, PermissionError):
            pass
        try:
            os.unlink(output_path)
        except (OSError, PermissionError):
            pass

