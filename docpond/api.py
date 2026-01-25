from ninja import NinjaAPI
from ponds.api import router as ponds_router
from documents.api import router as documents_router
from ocr_presets.api import router as ocr_presets_router
from docling_presets.api import router as docling_presets_router

api = NinjaAPI(title="DocPond API", version="1.0.0", description="Document management backend for scanned books")

api.add_router("/ponds", ponds_router, tags=["Ponds"])
api.add_router("/", documents_router, tags=["Documents"])
api.add_router("/", ocr_presets_router, tags=["OCR Presets"])
api.add_router("/", docling_presets_router, tags=["Docling Presets"])

@api.get("/health")
def health_check(request):
    return {"status": "ok", "message": "DocPond API is running"}
