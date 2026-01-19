from ninja import NinjaAPI
from groups.api import router as groups_router
from documents.api import router as documents_router

api = NinjaAPI(title="Pagewise API", version="1.0.0", description="Document management backend for scanned books")

api.add_router("/groups", groups_router, tags=["Groups"])
api.add_router("/", documents_router, tags=["Documents"])

@api.get("/health")
def health_check(request):
    return {"status": "ok", "message": "Pagewise API is running"}
