from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404
from django.http import Http404

from ponds.models import Pond, PondShare
from ponds.schemas import (
    PondSchema, PondCreateSchema, PondUpdateSchema,
    PondShareSchema, PondShareCreateSchema, PublicPondSchema
)

router = Router()


# Pond endpoints
@router.get("/", response=List[PondSchema])
def list_ponds(request):
    """Get all ponds"""
    return Pond.objects.all()


@router.post("/", response=PondSchema)
def create_pond(request, payload: PondCreateSchema):
    """Create a new pond"""
    pond = Pond.objects.create(**payload.model_dump())
    return pond


@router.get("/{sqid}", response=PondSchema)
def get_pond(request, sqid: str):
    """Get a specific pond by sqid"""
    pond = get_object_or_404(Pond, sqid=sqid)
    return pond


@router.put("/{sqid}", response=PondSchema)
def update_pond(request, sqid: str, payload: PondUpdateSchema):
    """Update a pond"""
    pond = get_object_or_404(Pond, sqid=sqid)

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(pond, attr, value)

    pond.save()
    return pond


@router.delete("/{sqid}")
def delete_pond(request, sqid: str):
    """Delete a pond"""
    pond = get_object_or_404(Pond, sqid=sqid)
    pond.delete()
    return {"success": True}


# Pond Share endpoints
@router.get("/{sqid}/shares", response=List[PondShareSchema])
def list_pond_shares(request, sqid: str):
    """Get all share links for a pond"""
    pond = get_object_or_404(Pond, sqid=sqid)
    shares = pond.shares.all()
    return [PondShareSchema.from_pond_share(share) for share in shares]


@router.post("/shares", response=PondShareSchema)
def create_pond_share(request, payload: PondShareCreateSchema):
    """Create a new share link for a pond"""
    pond = get_object_or_404(Pond, sqid=payload.pond_sqid)

    share = PondShare.objects.create(
        pond=pond,
        expire_date=payload.expire_date
    )

    return PondShareSchema.from_pond_share(share)


@router.get("/shares/{share_sqid}", response=PondShareSchema)
def get_pond_share(request, share_sqid: str):
    """Get details about a specific share link"""
    share = get_object_or_404(PondShare, sqid=share_sqid)
    return PondShareSchema.from_pond_share(share)


@router.delete("/shares/{share_sqid}")
def delete_pond_share(request, share_sqid: str):
    """Delete a share link"""
    share = get_object_or_404(PondShare, sqid=share_sqid)
    share.delete()
    return {"success": True}


# Public share endpoint (no authentication needed)
@router.get("/public/{share_sqid}", response=PublicPondSchema, auth=None)
def get_public_pond(request, share_sqid: str):
    """Get a pond via public share link (increments access count)"""
    share = get_object_or_404(PondShare.objects.select_related('pond'), sqid=share_sqid)

    # Check if expired
    if share.is_expired:
        raise Http404("This share link has expired")

    # Increment access count
    share.increment_access()

    # Return pond data
    return share.pond

