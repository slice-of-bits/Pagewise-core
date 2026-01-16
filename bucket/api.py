from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404
from django.http import Http404

from bucket.models import Bucket
from bucket.schemas import BucketSchema, BucketCreateSchema, BucketUpdateSchema

router = Router()


@router.get("/", response=List[BucketSchema])
def list_buckets(request):
    """Get all buckets"""
    return Bucket.objects.all()


@router.post("/", response=BucketSchema)
def create_bucket(request, payload: BucketCreateSchema):
    """Create a new bucket"""
    bucket = Bucket.objects.create(**payload.dict())
    return bucket


@router.get("/{sqid}", response=BucketSchema)
def get_bucket(request, sqid: str):
    """Get a specific bucket by sqid"""
    return get_object_or_404(Bucket, sqid=sqid)


@router.put("/{sqid}", response=BucketSchema)
def update_bucket(request, sqid: str, payload: BucketUpdateSchema):
    """Update a bucket"""
    bucket = get_object_or_404(Bucket, sqid=sqid)

    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(bucket, attr, value)

    bucket.save()
    return bucket


@router.delete("/{sqid}")
def delete_bucket(request, sqid: str):
    """Delete a bucket"""
    bucket = get_object_or_404(Bucket, sqid=sqid)
    bucket.delete()
    return {"success": True}
