from typing import List, Optional
from typing import Annotated

from ninja import ModelSchema, FilterSchema, FilterLookup
from pydantic import BaseModel, Field
from datetime import datetime
from django.db.models import Q

from documents.models import Document, Page


class DocumentListFilterSchema(FilterSchema):
    processing_status: Optional[str] = None


class PagesListFilterSchema(FilterSchema):
    document_id: Optional[str] = None



class PageSchema(ModelSchema):
    class Meta:
        model = Page
        fields = [
            'sqid',
            'page_number',
        ]

class PageDetailsSchema(ModelSchema):
    class Meta:
        model = Page
        fields = [
            'sqid',
            'page_number',
            'page_pdf',
            'ocr_markdown_raw',
            'text_markdown_clean',
            'processing_status',
            'metadata',
            'created_at',
            'updated_at',
        ]

class DocumentSchema(ModelSchema):
    processing_progress: float
    pages: List[PageSchema]

    class Meta:
        model = Document
        fields = [
            'sqid',
            'title',
            'thumbnail',
            'page_count',
            'original_pdf',
            'metadata',
            'created_at',
            'updated_at',
        ]

class DocumentCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    pond_sqid: str
    ocr_model: Optional[str] = 'deepseek-ocr'  # Allow selection of OCR model
    docling_preset_sqid: Optional[str] = None  # Allow selection of Docling preset
    metadata: Optional[dict] = {}


class DocumentUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    docling_preset_sqid: Optional[str] = None  # Allow updating Docling preset
    metadata: Optional[dict] = None


class PageDetailSchema(ModelSchema):
    class Meta:
        model = Page
        fields = [
            'sqid',
            'page_number',
            'page_pdf',
            'ocr_markdown_raw',
            'text_markdown_clean',
            'processing_status',
            'metadata',
            'created_at',
            'updated_at',
        ]


class SearchPageSchema(ModelSchema):
    snippet: Optional[str] = None
    relevance_score: Optional[float] = None

    class Meta:
        model = Page
        fields = [
            'sqid',
            'page_number',
            'text_markdown_clean',
            'processing_status',
            'created_at',
        ]


class PageUpdateSchema(BaseModel):
    ocr_markdown_raw: Optional[str] = None
    text_markdown_clean: Optional[str] = None
    metadata: Optional[dict] = None


class ImageSchema(BaseModel):
    sqid: str
    image_file: str
    caption: Optional[str] = None
    metadata: dict
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_image_file(obj):
        return obj.image_file.url if obj.image_file else None

    class Config:
        from_attributes = True


class DeepSeekOCRSettingsSchema(BaseModel):
    sqid: str
    name: str
    default_model: str
    default_prompt: str
    settings_json: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeepSeekOCRSettingsUpdateSchema(BaseModel):
    default_model: Optional[str] = None
    default_prompt: Optional[str] = None
    settings_json: Optional[dict] = None


class DoclingPresetSchema(BaseModel):
    """Schema for Docling preset output"""
    sqid: str
    name: str
    is_default: bool
    pipeline_type: str
    ocr_engine: str
    force_ocr: bool
    ocr_languages: List[str]
    vlm_model: str
    enable_picture_description: bool
    picture_description_prompt: str
    enable_table_structure: bool
    table_former_mode: str
    enable_code_enrichment: bool
    enable_formula_enrichment: bool
    filter_orphan_clusters: bool
    filter_empty_clusters: bool
    advanced_settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoclingPresetCreateSchema(BaseModel):
    """Schema for creating a new Docling preset"""
    name: str = Field(..., min_length=1, max_length=100)
    is_default: Optional[bool] = False
    pipeline_type: Optional[str] = 'standard'
    ocr_engine: Optional[str] = 'auto'
    force_ocr: Optional[bool] = False
    ocr_languages: Optional[List[str]] = ['en']
    vlm_model: Optional[str] = ''
    enable_picture_description: Optional[bool] = False
    picture_description_prompt: Optional[str] = 'Describe this image in a few sentences.'
    enable_table_structure: Optional[bool] = True
    table_former_mode: Optional[str] = 'accurate'
    enable_code_enrichment: Optional[bool] = False
    enable_formula_enrichment: Optional[bool] = False
    filter_orphan_clusters: Optional[bool] = False
    filter_empty_clusters: Optional[bool] = True
    advanced_settings: Optional[dict] = {}


class DoclingPresetUpdateSchema(BaseModel):
    """Schema for updating a Docling preset"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_default: Optional[bool] = None
    pipeline_type: Optional[str] = None
    ocr_engine: Optional[str] = None
    force_ocr: Optional[bool] = None
    ocr_languages: Optional[List[str]] = None
    vlm_model: Optional[str] = None
    enable_picture_description: Optional[bool] = None
    picture_description_prompt: Optional[str] = None
    enable_table_structure: Optional[bool] = None
    table_former_mode: Optional[str] = None
    enable_code_enrichment: Optional[bool] = None
    enable_formula_enrichment: Optional[bool] = None
    filter_orphan_clusters: Optional[bool] = None
    filter_empty_clusters: Optional[bool] = None
    advanced_settings: Optional[dict] = None


class SearchDocumentSchema(BaseModel):
    sqid: str
    title: str
    thumbnail: Optional[str] = None
    pages: List[SearchPageSchema]
    max_relevance_score: float

    class Config:
        from_attributes = True


class SearchResultSchema(BaseModel):
    documents: List[SearchDocumentSchema]
    total_results: int

    class Config:
        from_attributes = True

class SearchFilterSchema(FilterSchema):
    q: Optional[str] = None  # Handle search manually in the API function
    min_score: Optional[float] = Field(default=0.001, ge=0.0, le=1.0)
    document_title: Annotated[Optional[str], FilterLookup("document__title__icontains")] = None
    pond_name: Annotated[Optional[str], FilterLookup("document__pond__name__icontains")] = None

    def custom_expression(self) -> Q:
        """Custom filtering logic for the search schema"""
        q = Q()

        # Handle document title filtering
        if self.document_title:
            q &= Q(document__title__icontains=self.document_title)

        # Handle pond name filtering
        if self.pond_name:
            q &= Q(document__pond__name__icontains=self.pond_name)

        # Note: q (search query) and min_score are handled in the API function
        return q


