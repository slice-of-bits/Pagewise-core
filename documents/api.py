from typing import List
from ninja import Router, File, UploadedFile, Form, Query
from ninja.pagination import paginate
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from collections import defaultdict

from documents.models import Document, Page, Image, ProcessingStatus
from documents.models import Document, Page, Image, ProcessingStatus
from docling_presets.models import DoclingPreset
from documents.schemas import (
    DocumentSchema, DocumentCreateSchema, DocumentUpdateSchema,
    PageSchema, PageUpdateSchema, ImageSchema,
    SearchResultSchema, SearchDocumentSchema, SearchPageSchema, DocumentListFilterSchema,
    PagesListFilterSchema, SearchFilterSchema, PageDetailsSchema
)
from documents.tasks import process_document, process_page
from ponds.models import Pond

router = Router()

# Document endpoints
@router.get("/documents/", response=List[DocumentSchema])
@paginate
def list_documents(request, filters: DocumentListFilterSchema = Query(...)):
    """Get all documents, optionally filtered by pond"""
    queryset = Document.objects.select_related('pond').all()
    queryset = filters.filter(queryset)
    return queryset


@router.post("/documents/", response=DocumentSchema)
def create_document(request, payload: DocumentCreateSchema):
    """Create a new document"""
    pond = get_object_or_404(Pond, sqid=payload.pond_sqid)
    
    # Get docling preset if specified
    docling_preset = None
    if payload.docling_preset_sqid:
        docling_preset = get_object_or_404(DoclingPreset, sqid=payload.docling_preset_sqid)
    
    # Get OCR preset if specified
    from ocr_presets.models import OcrPreset
    ocr_preset = None
    if payload.ocr_preset_sqid:
        ocr_preset = get_object_or_404(OcrPreset, sqid=payload.ocr_preset_sqid)

    document = Document.objects.create(
        title=payload.title,
        pond=pond,
        docling_preset=docling_preset,
        ocr_preset=ocr_preset,
        metadata=payload.metadata
    )
    return document

@router.post("/documents/upload/", response=DocumentSchema)
def upload_document(
    request,
    file: UploadedFile = File(...),
    title: str = Form(...),
    pond_sqid: str = Form(...),
    docling_preset_sqid: str = Form(None),
    ocr_preset_sqid: str = Form(None),
    metadata: str = Form('{}')
):
    """Upload a PDF document and start processing"""
    import json

    # Validate file type
    if not file.name.lower().endswith('.pdf'):
        return {"error": "Only PDF files are allowed"}, 400

    # Parse metadata
    try:
        metadata_dict = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError:
        metadata_dict = {}
    
    # Get docling preset if specified
    docling_preset = None
    if docling_preset_sqid:
        docling_preset = get_object_or_404(DoclingPreset, sqid=docling_preset_sqid)

    # Get OCR preset if specified
    from ocr_presets.models import OcrPreset
    ocr_preset = None
    if ocr_preset_sqid:
        ocr_preset = get_object_or_404(OcrPreset, sqid=ocr_preset_sqid)

    # Create document
    document = Document.objects.create(
        title=title,
        pond=get_object_or_404(Pond, sqid=pond_sqid),
        original_pdf=file,
        docling_preset=docling_preset,
        ocr_preset=ocr_preset,
        metadata=metadata_dict
    )

    # Start background processing
    process_document.delay(document.id)

    return document


@router.get("/documents/{sqid}", response=DocumentSchema)
def get_document(request, sqid: str):
    """Get a specific document by sqid"""
    return get_object_or_404(Document.objects.select_related('pond'), sqid=sqid)


@router.put("/documents/{sqid}", response=DocumentSchema)
def update_document(request, sqid: str, payload: DocumentUpdateSchema):
    """Update a document"""
    document = get_object_or_404(Document, sqid=sqid)
    
    # Handle presets separately
    data = payload.model_dump(exclude_unset=True)

    if 'docling_preset_sqid' in data:
        preset_sqid = data.pop('docling_preset_sqid')
        if preset_sqid:
            docling_preset = get_object_or_404(DoclingPreset, sqid=preset_sqid)
            document.docling_preset = docling_preset
        else:
            document.docling_preset = None

    if 'ocr_preset_sqid' in data:
        from ocr_presets.models import OcrPreset
        preset_sqid = data.pop('ocr_preset_sqid')
        if preset_sqid:
            ocr_preset = get_object_or_404(OcrPreset, sqid=preset_sqid)
            document.ocr_preset = ocr_preset
        else:
            document.ocr_preset = None

    for attr, value in data.items():
        setattr(document, attr, value)

    document.save()
    return document


@router.delete("/documents/{sqid}")
def delete_document(request, sqid: str):
    """Delete a document"""
    document = get_object_or_404(Document, sqid=sqid)
    document.delete()
    return {"success": True}


@router.get("/documents/{sqid}/progress")
def get_document_progress(request, sqid: str):
    """Get document processing progress"""
    document = get_object_or_404(Document, sqid=sqid)
    return {
        "processing_status": document.processing_status,
        "processed_pages": document.processed_pages,
        "total_pages": document.page_count,
        "progress_percentage": document.processing_progress
    }


# Page endpoints
@router.get("/pages/", response=List[PageSchema])
@paginate
def list_pages(request, filters: PagesListFilterSchema = Query(...)):
    """Get all pages, optionally filtered by document"""
    queryset = Page.objects.all()
    queryset = filters.filter(queryset)
    return queryset


@router.get("/pages/{sqid}", response=PageDetailsSchema)
def get_page(request, sqid: str):
    """Get a specific page by sqid"""
    return get_object_or_404(Page, sqid=sqid)


@router.put("/pages/{sqid}", response=PageSchema)
def update_page(request, sqid: str, payload: PageUpdateSchema):
    """Update a page"""
    page = get_object_or_404(Page, sqid=sqid)

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(page, attr, value)

    # Update search vector if text was changed
    if 'text_markdown_clean' in payload.model_dump(exclude_unset=True):
        pass  # Search vector update not needed for fuzzy search

    page.save()
    return page


@router.get("/pages/{sqid}/images/", response=List[ImageSchema])
def get_page_images(request, sqid: str):
    """Get all images from a specific page"""
    page = get_object_or_404(Page, sqid=sqid)
    return page.images.all()


@router.post("/pages/{sqid}/reprocess")
def reprocess_page(request, sqid: str):
    """
    Reprocess a page with specified OCR model.
    Clears old OCR data and starts reprocessing.
    Useful for development, testing, and production updates.
    """
    page = get_object_or_404(Page, sqid=sqid)
    
    # Clear old OCR data
    page.ocr_markdown_raw = ''
    page.text_markdown_clean = ''
    page.ocr_references = None
    page.bbox_visualization = None
    page.processing_status = ProcessingStatus.PENDING
    page.save()
    
    # Delete old extracted images
    page.images.all().delete()
    
    # Start reprocessing task
    task = process_page.delay(page.id)
    
    return {
        "success": True,
        "task_id": task.id,
        "page_sqid": page.sqid,
    }


# Image endpoints
@router.get("/images/{sqid}", response=ImageSchema)
def get_image(request, sqid: str):
    """Get a specific image by sqid"""
    return get_object_or_404(Image, sqid=sqid)


# Search endpoint
@router.get("/search/", response=SearchResultSchema)
def search_pages(request, filters: SearchFilterSchema = Query(...)):
    """Search pages using PostgreSQL text matching and similarity"""

    # Start with base queryset of completed pages
    queryset = Page.objects.filter(
        processing_status='completed',
        text_markdown_clean__isnull=False
    ).exclude(
        text_markdown_clean__exact=''
    ).select_related('document', 'document__pond')

    # Apply additional filters (document_title, bucket_name) using FilterSchema
    queryset = filters.filter(queryset)

    # If we have a search query, add text matching and scoring
    if filters.q:
        # Use basic icontains search with trigram similarity for scoring
        queryset = queryset.filter(
            text_markdown_clean__icontains=filters.q
        ).annotate(
            # Use trigram similarity for scoring
            similarity=TrigramSimilarity('text_markdown_clean', filters.q),
            combined_score=TrigramSimilarity('text_markdown_clean', filters.q)
        ).filter(
            # Filter by minimum similarity score
            combined_score__gte=filters.min_score
        ).order_by('-combined_score', '-created_at')
    else:
        # No search query, just return by creation date
        queryset = queryset.annotate(
            combined_score=Value(1.0)
        ).order_by('-created_at')

    # Group pages by document and calculate max scores
    document_ponds = defaultdict(list)
    document_max_scores = {}

    for page in queryset:
        doc_id = page.document.id
        document_ponds[doc_id].append(page)

        # Track the maximum score for this document
        if doc_id not in document_max_scores:
            document_max_scores[doc_id] = page.combined_score
        else:
            document_max_scores[doc_id] = max(document_max_scores[doc_id], page.combined_score)

    # Create SearchDocumentSchema objects
    documents = []
    for doc_id, pages in document_ponds.items():
        document = pages[0].document

        # Create SearchPageSchema objects for this document
        pages_data = []
        for page in pages:
            # Create snippet around search term if we have a query
            snippet = create_snippet(page.text_markdown_clean, filters.q or "") if filters.q else page.text_markdown_clean[:300] + "..."

            page_data = SearchPageSchema.from_orm(page)
            page_data.snippet = snippet
            page_data.relevance_score = float(page.combined_score)
            pages_data.append(page_data)

        # Sort pages within document by score
        pages_data.sort(key=lambda p: p.relevance_score, reverse=True)

        # Create document schema
        doc_schema = SearchDocumentSchema(
            sqid=document.sqid,
            title=document.title,
            thumbnail=document.thumbnail.url if document.thumbnail else None,
            pages=pages_data,
            max_relevance_score=float(document_max_scores[doc_id])
        )
        documents.append(doc_schema)

    # Sort documents by their maximum relevance score
    documents.sort(key=lambda d: d.max_relevance_score, reverse=True)

    # Return search results
    return SearchResultSchema(
        documents=documents,
        total_results=queryset.count()
    )

def create_snippet(text: str, query: str, max_length: int = 300) -> str:
    """Create a text snippet around the search query"""
    query_lower = query.lower()
    text_lower = text.lower()

    # Find the query in the text
    index = text_lower.find(query_lower)
    if index == -1:
        # Query not found, return beginning of text
        return text[:max_length] + "..." if len(text) > max_length else text

    # Calculate snippet boundaries
    start = max(0, index - max_length // 2)
    end = min(len(text), start + max_length)

    # Adjust start if we're at the end
    if end - start < max_length:
        start = max(0, end - max_length)

    snippet = text[start:end]

    # Add ellipsis if we cut the text
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet

