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
            'page_image',
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
    docling_preset_sqid: Optional[str] = None  # Allow selection of Docling preset
    ocr_preset_sqid: Optional[str] = None  # Allow selection of OCR preset
    metadata: Optional[dict] = {}


class DocumentUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    docling_preset_sqid: Optional[str] = None  # Allow updating Docling preset
    ocr_preset_sqid: Optional[str] = None  # Allow updating OCR preset
    metadata: Optional[dict] = None


class PageDetailSchema(ModelSchema):
    class Meta:
        model = Page
        fields = [
            'sqid',
            'page_number',
            'page_pdf',
            'page_image',
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


