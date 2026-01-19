from typing import List, Optional
from typing import Annotated

from ninja import ModelSchema, FilterSchema, FilterLookup
from pydantic import BaseModel, Field
from datetime import datetime
from django.db.models import Q

from documents.models import Document, Page, OcrSettings


class DocumentListFilterSchema(FilterSchema):
    processing_status: Optional[str] = None


class PagesListFilterSchema(FilterSchema):
    document_id: Optional[str] = None


class BucketSchema(BaseModel):
    sqid: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BucketCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class BucketUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


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
    group_sqid: str
    ocr_settings_sqid: Optional[str] = Field(None, description="OCR settings to use for this document. If not provided, uses global default.")
    metadata: Optional[dict] = {}


class DocumentUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
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


class DoclingSettingsSchema(BaseModel):
    sqid: str
    name: str
    ocr_engine: str
    detect_tables: bool
    detect_figures: bool
    ignore_headers_footers: bool
    language: str
    confidence_threshold: float
    settings_json: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoclingSettingsUpdateSchema(BaseModel):
    ocr_engine: Optional[str] = Field(None, pattern="^(tesseract|easyocr|doctr)$")
    detect_tables: Optional[bool] = None
    detect_figures: Optional[bool] = None
    ignore_headers_footers: Optional[bool] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    settings_json: Optional[dict] = None


class OcrSettingsSchema(BaseModel):
    sqid: str
    name: str
    ollama_base_url: str
    paddleocr_model: str
    use_ocrmypdf: bool
    ocrmypdf_language: str
    ocrmypdf_compression: bool
    language: str
    settings_json: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OcrSettingsCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    ollama_base_url: str = Field(default='http://localhost:11434', max_length=255)
    paddleocr_model: str = Field(default='paddleocr-vl', max_length=100)
    use_ocrmypdf: bool = Field(default=False)
    ocrmypdf_language: str = Field(default='eng', max_length=10)
    ocrmypdf_compression: bool = Field(default=True)
    language: str = Field(default='en', min_length=2, max_length=10)
    settings_json: Optional[dict] = {}


class OcrSettingsUpdateSchema(BaseModel):
    ollama_base_url: Optional[str] = Field(None, max_length=255)
    paddleocr_model: Optional[str] = Field(None, max_length=100)
    use_ocrmypdf: Optional[bool] = None
    ocrmypdf_language: Optional[str] = Field(None, max_length=10)
    ocrmypdf_compression: Optional[bool] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    settings_json: Optional[dict] = None


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
    bucket_name: Annotated[Optional[str], FilterLookup("document__group__name__icontains")] = None

    def custom_expression(self) -> Q:
        """Custom filtering logic for the search schema"""
        q = Q()

        # Handle document title filtering
        if self.document_title:
            q &= Q(document__title__icontains=self.document_title)

        # Handle bucket name filtering
        if self.bucket_name:
            q &= Q(document__group__name__icontains=self.bucket_name)

        # Note: q (search query) and min_score are handled in the API function
        return q


