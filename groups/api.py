from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404
from django.http import Http404

from groups.models import Group, GroupShare
from groups.schemas import (
    GroupSchema, GroupCreateSchema, GroupUpdateSchema,
    GroupShareSchema, GroupShareCreateSchema, PublicGroupSchema
)

router = Router()


# Group endpoints
@router.get("/", response=List[GroupSchema])
def list_groups(request):
    """Get all groups"""
    return Group.objects.all()


@router.post("/", response=GroupSchema)
def create_group(request, payload: GroupCreateSchema):
    """Create a new group"""
    group = Group.objects.create(**payload.model_dump())
    return group


@router.get("/{sqid}", response=GroupSchema)
def get_group(request, sqid: str):
    """Get a specific group by sqid"""
    group = get_object_or_404(Group, sqid=sqid)
    return group


@router.put("/{sqid}", response=GroupSchema)
def update_group(request, sqid: str, payload: GroupUpdateSchema):
    """Update a group"""
    group = get_object_or_404(Group, sqid=sqid)

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, attr, value)

    group.save()
    return group


@router.delete("/{sqid}")
def delete_group(request, sqid: str):
    """Delete a group"""
    group = get_object_or_404(Group, sqid=sqid)
    group.delete()
    return {"success": True}


# Group Share endpoints
@router.get("/{sqid}/shares", response=List[GroupShareSchema])
def list_group_shares(request, sqid: str):
    """Get all share links for a group"""
    group = get_object_or_404(Group, sqid=sqid)
    shares = group.shares.all()
    return [GroupShareSchema.from_group_share(share) for share in shares]


@router.post("/shares", response=GroupShareSchema)
def create_group_share(request, payload: GroupShareCreateSchema):
    """Create a new share link for a group"""
    group = get_object_or_404(Group, sqid=payload.group_sqid)

    share = GroupShare.objects.create(
        group=group,
        expire_date=payload.expire_date
    )

    return GroupShareSchema.from_group_share(share)


@router.get("/shares/{share_sqid}", response=GroupShareSchema)
def get_group_share(request, share_sqid: str):
    """Get details about a specific share link"""
    share = get_object_or_404(GroupShare, sqid=share_sqid)
    return GroupShareSchema.from_group_share(share)


@router.delete("/shares/{share_sqid}")
def delete_group_share(request, share_sqid: str):
    """Delete a share link"""
    share = get_object_or_404(GroupShare, sqid=share_sqid)
    share.delete()
    return {"success": True}


# Public share endpoint (no authentication needed)
@router.get("/public/{share_sqid}", response=PublicGroupSchema, auth=None)
def get_public_group(request, share_sqid: str):
    """Get a group via public share link (increments access count)"""
    share = get_object_or_404(GroupShare.objects.select_related('group'), sqid=share_sqid)

    # Check if expired
    if share.is_expired:
        raise Http404("This share link has expired")

    # Increment access count
    share.increment_access()

    # Return group data
    return share.group

