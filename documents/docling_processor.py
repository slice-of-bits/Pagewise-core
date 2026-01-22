"""
Docling document processor module.
Handles PDF processing using the Docling library with configurable presets.
"""

import os
import logging
import tempfile
from typing import Dict, Any, List, Optional

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class DoclingProcessor:
    """
    Processor for PDF documents using Docling library.
    Converts PDFs to structured JSON and Markdown using configurable presets.
    """

    def __init__(self, preset):
        """
        Initialize the Docling processor with a preset.
        
        Args:
            preset: DoclingPreset instance with configuration
        """
        self.preset = preset
        self.converter = None
        
    def _create_converter(self):
        """Create and configure DocumentConverter based on preset settings"""
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                VlmPipelineOptions,
                OcrAutoOptions,
                EasyOcrOptions,
                TesseractCliOcrOptions,
                RapidOcrOptions,
                OcrMacOptions,
                TableStructureOptions,
                TableFormerMode as DoclingTableFormerMode,
                LayoutOptions,
                PictureDescriptionVlmOptions,
            )
            from docling.pipeline.vlm_pipeline import VlmPipeline
            from docling.datamodel import vlm_model_specs
            
        except ImportError as e:
            logger.error(f"Docling not installed: {e}")
            raise ImportError("Docling library is required. Install with: pip install docling")
        
        # Choose pipeline based on preset
        if self.preset.pipeline_type == 'vlm':
            return self._create_vlm_pipeline()
        else:
            return self._create_standard_pipeline()
    
    def _create_standard_pipeline(self):
        """Create standard PDF pipeline with OCR"""
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            OcrAutoOptions,
            EasyOcrOptions,
            TesseractCliOcrOptions,
            RapidOcrOptions,
            OcrMacOptions,
            TableStructureOptions,
            TableFormerMode as DoclingTableFormerMode,
            LayoutOptions,
            PictureDescriptionVlmOptions,
        )
        
        # Configure OCR options
        ocr_options = self._get_ocr_options()
        
        # Configure table structure options
        table_options = TableStructureOptions()
        if self.preset.table_former_mode == 'fast':
            table_options.mode = DoclingTableFormerMode.FAST
        else:
            table_options.mode = DoclingTableFormerMode.ACCURATE
        
        # Configure layout options (for filtering)
        layout_options = LayoutOptions()
        layout_options.create_orphan_clusters = not self.preset.filter_orphan_clusters
        layout_options.keep_empty_clusters = not self.preset.filter_empty_clusters
        
        # Configure picture description if enabled
        picture_description_options = None
        if self.preset.enable_picture_description:
            picture_description_options = PictureDescriptionVlmOptions(
                prompt=self.preset.picture_description_prompt,
            )
        
        # Create pipeline options
        pipeline_options = PdfPipelineOptions(
            do_ocr=True,
            do_table_structure=self.preset.enable_table_structure,
            do_code_enrichment=self.preset.enable_code_enrichment,
            do_formula_enrichment=self.preset.enable_formula_enrichment,
            do_picture_description=self.preset.enable_picture_description,
            ocr_options=ocr_options,
            table_structure_options=table_options,
            layout_options=layout_options,
            generate_picture_images=True,  # Always generate for Image model
        )
        
        if picture_description_options:
            pipeline_options.picture_description_options = picture_description_options
        
        # Create converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        return converter
    
    def _create_vlm_pipeline(self):
        """Create VLM pipeline for end-to-end vision-language processing"""
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import VlmPipelineOptions
        from docling.pipeline.vlm_pipeline import VlmPipeline
        from docling.datamodel import vlm_model_specs
        
        # Select VLM model
        vlm_options = vlm_model_specs.GRANITEDOCLING_TRANSFORMERS  # Default
        
        # TODO: Allow custom VLM model selection based on preset.vlm_model
        # This would require parsing the model repo_id and creating InlineVlmOptions
        
        pipeline_options = VlmPipelineOptions(
            vlm_options=vlm_options,
            generate_picture_images=True,
        )
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                )
            }
        )
        
        return converter
    
    def _get_ocr_options(self):
        """Get OCR options based on preset configuration"""
        from docling.datamodel.pipeline_options import (
            OcrAutoOptions,
            EasyOcrOptions,
            TesseractCliOcrOptions,
            RapidOcrOptions,
            OcrMacOptions,
        )
        
        ocr_engine = self.preset.ocr_engine
        languages = self.preset.ocr_languages if self.preset.ocr_languages else ['en']
        force_ocr = self.preset.force_ocr
        
        if ocr_engine == 'easyocr':
            return EasyOcrOptions(
                lang=languages,
                force_full_page_ocr=force_ocr,
            )
        elif ocr_engine == 'tesseract':
            # Convert ISO 639-1 to Tesseract codes if needed
            from documents.language_codes import get_tesseract_lang
            tesseract_langs = [get_tesseract_lang(lang) for lang in languages]
            return TesseractCliOcrOptions(
                lang=tesseract_langs,
                force_full_page_ocr=force_ocr,
            )
        elif ocr_engine == 'rapidocr':
            return RapidOcrOptions(
                lang=languages,
                force_full_page_ocr=force_ocr,
            )
        elif ocr_engine == 'ocrmac':
            return OcrMacOptions(
                lang=languages,
                force_full_page_ocr=force_ocr,
            )
        else:  # auto
            return OcrAutoOptions(
                force_full_page_ocr=force_ocr,
            )
    
    def process_page(self, page, output_dir: str) -> Dict[str, Any]:
        """
        Process a single page with Docling.
        
        Args:
            page: Page model instance
            output_dir: Directory to save extracted images
            
        Returns:
            Dictionary with processing results:
            {
                'docling_json': dict - The docling JSON structure
                'markdown': str - Generated markdown
                'images': list - List of extracted image info
            }
        """
        try:
            # Lazy initialize converter
            if self.converter is None:
                self.converter = self._create_converter()
            
            # Get page PDF file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                with default_storage.open(page.page_pdf.name, 'rb') as pdf_file:
                    content = pdf_file.read()
                    if len(content) == 0:
                        raise ValueError(f"Page PDF file {page.page_pdf.name} is empty")
                    tmp_pdf.write(content)
                pdf_path = tmp_pdf.name
            
            try:
                # Convert document
                logger.info(f"Processing page {page.page_number} with Docling preset {self.preset.name}")
                result = self.converter.convert(pdf_path)
                
                # Extract docling JSON
                docling_json = result.document.export_to_dict()
                
                # Generate markdown from docling
                markdown = result.document.export_to_markdown()
                
                # Extract images
                images = []
                if result.document.pictures:
                    for idx, picture in enumerate(result.document.pictures):
                        # Save picture
                        if hasattr(picture, 'image') and picture.image:
                            image_filename = f"image_{idx}.png"
                            image_path = os.path.join(output_dir, image_filename)
                            
                            # Save image to output directory
                            picture.image.save(image_path)
                            
                            images.append({
                                'index': idx,
                                'path': image_path,
                                'caption': picture.caption if hasattr(picture, 'caption') else '',
                            })
                
                return {
                    'docling_json': docling_json,
                    'markdown': markdown,
                    'images': images,
                }
                
            finally:
                # Clean up temporary PDF
                try:
                    os.unlink(pdf_path)
                except (OSError, PermissionError):
                    pass
                    
        except Exception as e:
            logger.error(f"Error processing page {page.page_number} with Docling: {str(e)}")
            raise


def process_page_with_docling(page, preset, output_dir: str) -> Dict[str, Any]:
    """
    Helper function to process a page with a specific Docling preset.
    
    Args:
        page: Page model instance
        preset: DoclingPreset instance
        output_dir: Directory to save extracted images
        
    Returns:
        Dictionary with processing results
    """
    processor = DoclingProcessor(preset)
    return processor.process_page(page, output_dir)
