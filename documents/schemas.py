from typing import List, Optional
from typing import Annotated

from ninja import ModelSchema, FilterSchema, FilterLookup, Schema
from django.db.models import Q
from pydantic import Field

from documents.models import Document, Page, Image


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
            'docling_json',
            'docling_json_override',
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

class DocumentCreateSchema(DocumentSchema):
    class Meta:
        model = Document
        fields = [
            'title',
            'pond_sqid',
            'docling_preset',
            'ocr_preset',
            'metadata',
        ]


class DocumentUpdateSchema(ModelSchema):
    class Meta:
        model = Document
        fields = [
            'title',
            'docling_preset',
            'ocr_preset',
            'metadata',
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


class PageUpdateSchema(ModelSchema):

    class Meta:
        model = Page
        fields = [
            'ocr_markdown_raw',
            'text_markdown_clean',
            'metadata',
        ]

class ImageSchema(ModelSchema):
    class Meta:
        model = Image
        fields = [
            'sqid',
            'image_file',
            'caption',
            'metadata',
            'created_at',
            'updated_at',
        ]


class SearchDocumentSchema(ModelSchema):
    pages: PageDetailsSchema

    class Meta:
        model = Document
        fields = [
            'sqid',
            'title',
            'thumbnail',
        ]


class SearchResultSchema(Schema):
    documents: List[DocumentSchema]
    total_results: int

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


