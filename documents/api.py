from typing import List
from ninja import Router, File, UploadedFile, Form, Query
from ninja.pagination import paginate
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from collections import defaultdict

from documents.models import Document, Page, Image, DoclingSettings, OcrSettings
from documents.schemas import (
    DocumentSchema, DocumentCreateSchema, DocumentUpdateSchema,
    PageSchema, PageUpdateSchema, ImageSchema,
    DoclingSettingsSchema, DoclingSettingsUpdateSchema,
    OcrSettingsSchema, OcrSettingsCreateSchema, OcrSettingsUpdateSchema,
    SearchResultSchema, SearchDocumentSchema, SearchPageSchema, DocumentListFilterSchema,
    PagesListFilterSchema, SearchFilterSchema, PageDetailsSchema
)
from documents.tasks import process_document
from bucket.models import Bucket

router = Router()

# Document endpoints
@router.get("/documents/", response=List[DocumentSchema])
@paginate
def list_documents(request, filters: DocumentListFilterSchema = Query(...)):
    """Get all documents, optionally filtered by bucket"""
    queryset = Document.objects.select_related('group').all()
    queryset = filters.filter(queryset)
    return queryset


@router.post("/documents/", response=DocumentSchema)
def create_document(request, payload: DocumentCreateSchema):
    """Create a new document"""
    bucket = get_object_or_404(Bucket, sqid=payload.group_sqid)
    
    # Get OCR settings if provided
    ocr_settings = None
    if payload.ocr_settings_sqid:
        ocr_settings = get_object_or_404(OcrSettings, sqid=payload.ocr_settings_sqid)
    
    document = Document.objects.create(
        title=payload.title,
        group=bucket,
        ocr_settings=ocr_settings,
        metadata=payload.metadata
    )
    return document

@router.post("/documents/upload/", response=DocumentSchema)
def upload_document(
    request,
    file: UploadedFile = File(...),
    title: str = Form(...),
    group_sqid: str = Form(...),
    ocr_settings_sqid: str = Form(None),
    metadata: str = Form('{}')
):
    """Upload a PDF document and start processing"""
    import json

    # Validate file type
    if not file.name.lower().endswith('.pdf'):
        return {"error": "Only PDF files are allowed"}, 400

    # Get bucket
    bucket = get_object_or_404(Bucket, sqid=group_sqid)

    # Get OCR settings if provided
    ocr_settings = None
    if ocr_settings_sqid:
        ocr_settings = get_object_or_404(OcrSettings, sqid=ocr_settings_sqid)

    # Parse metadata
    try:
        metadata_dict = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError:
        metadata_dict = {}

    # Create document
    document = Document.objects.create(
        title=title,
        group=bucket,
        original_pdf=file,
        ocr_settings=ocr_settings,
        metadata=metadata_dict
    )

    # Start background processing
    process_document.delay(document.id)

    return document


@router.get("/documents/{sqid}", response=DocumentSchema)
def get_document(request, sqid: str):
    """Get a specific document by sqid"""
    return get_object_or_404(Document.objects.select_related('group'), sqid=sqid)


@router.put("/documents/{sqid}", response=DocumentSchema)
def update_document(request, sqid: str, payload: DocumentUpdateSchema):
    """Update a document"""
    document = get_object_or_404(Document, sqid=sqid)

    for attr, value in payload.model_dump(exclude_unset=True).items():
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
    ).select_related('document', 'document__group')

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
    document_groups = defaultdict(list)
    document_max_scores = {}

    for page in queryset:
        doc_id = page.document.id
        document_groups[doc_id].append(page)

        # Track the maximum score for this document
        if doc_id not in document_max_scores:
            document_max_scores[doc_id] = page.combined_score
        else:
            document_max_scores[doc_id] = max(document_max_scores[doc_id], page.combined_score)

    # Create SearchDocumentSchema objects
    documents = []
    for doc_id, pages in document_groups.items():
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

# Docling Settings endpoints (Legacy - deprecated)
@router.get("/settings/docling/", response=DoclingSettingsSchema)
def get_docling_settings(request):
    """DEPRECATED: Get current Docling settings. Use /settings/ocr/ instead."""
    from django.http import HttpResponse
    response = HttpResponse()
    response['Deprecation'] = 'true'
    response['Sunset'] = 'Sat, 01 Jan 2027 00:00:00 GMT'
    response['Link'] = '</api/settings/ocr/>; rel="alternate"'
    
    settings = DoclingSettings.get_default_settings()
    return settings


@router.put("/settings/docling/", response=DoclingSettingsSchema)
def update_docling_settings(request, payload: DoclingSettingsUpdateSchema):
    """DEPRECATED: Update Docling settings. Use /settings/ocr/ instead."""
    from django.http import HttpResponse
    response = HttpResponse()
    response['Deprecation'] = 'true'
    response['Sunset'] = 'Sat, 01 Jan 2027 00:00:00 GMT'
    response['Link'] = '</api/settings/ocr/>; rel="alternate"'
    
    settings = DoclingSettings.get_default_settings()

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, attr, value)

    settings.save()
    return settings


# OCR Settings endpoints
@router.get("/settings/ocr/", response=List[OcrSettingsSchema])
def list_ocr_settings(request):
    """List all OCR settings"""
    return OcrSettings.objects.all()


@router.get("/settings/ocr/default/", response=OcrSettingsSchema)
def get_default_ocr_settings(request):
    """Get default OCR settings"""
    settings = OcrSettings.get_default_settings()
    return settings


@router.get("/settings/ocr/{sqid}", response=OcrSettingsSchema)
def get_ocr_settings(request, sqid: str):
    """Get specific OCR settings by sqid"""
    return get_object_or_404(OcrSettings, sqid=sqid)


@router.post("/settings/ocr/", response=OcrSettingsSchema)
def create_ocr_settings(request, payload: OcrSettingsCreateSchema):
    """Create new OCR settings"""
    settings = OcrSettings.objects.create(**payload.model_dump())
    return settings


@router.put("/settings/ocr/{sqid}", response=OcrSettingsSchema)
def update_ocr_settings(request, sqid: str, payload: OcrSettingsUpdateSchema):
    """Update OCR settings"""
    settings = get_object_or_404(OcrSettings, sqid=sqid)

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, attr, value)

    settings.save()
    return settings


@router.put("/settings/ocr/default/", response=OcrSettingsSchema)
def update_default_ocr_settings(request, payload: OcrSettingsUpdateSchema):
    """Update default OCR settings"""
    settings = OcrSettings.get_default_settings()

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, attr, value)

    settings.save()
    return settings


@router.delete("/settings/ocr/{sqid}")
def delete_ocr_settings(request, sqid: str):
    """Delete OCR settings (cannot delete default)"""
    from django.http import JsonResponse
    
    settings = get_object_or_404(OcrSettings, sqid=sqid)
    
    if settings.name == 'default':
        return JsonResponse(
            {"error": "Cannot delete default settings"},
            status=403  # Forbidden - business rule violation
        )
    
    settings.delete()
    return {"success": True}


# Image redirect view for authentication
@router.get("/images/{sqid}/view")
def view_image(request, sqid: str):
    """Redirect to S3 URL for image - allows for authentication layer"""
    from django.http import HttpResponseRedirect
    
    image = get_object_or_404(Image, sqid=sqid)
    
    # TODO: Add authentication check here if needed
    # if not request.user.is_authenticated:
    #     return {"error": "Authentication required"}, 401
    
    # Redirect to S3 URL
    return HttpResponseRedirect(image.image_file.url)


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
