from ninja import NinjaAPI
from bucket.api import router as bucket_router
from documents.api import router as documents_router

api = NinjaAPI(title="Pagewise API", version="1.0.0", description="Document management backend for scanned books")

api.add_router("/buckets", bucket_router, tags=["Buckets"])
api.add_router("/", documents_router, tags=["Documents"])

@api.get("/health")
def health_check(request):
    return {"status": "ok", "message": "Pagewise API is running"}
