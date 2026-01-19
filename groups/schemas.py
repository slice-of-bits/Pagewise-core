from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GroupSchema(BaseModel):
    sqid: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class GroupUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class GroupShareSchema(BaseModel):
    sqid: str
    group_sqid: str
    expire_date: datetime
    access_count: int
    is_expired: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @staticmethod
    def from_group_share(obj):
        return GroupShareSchema(
            sqid=obj.sqid,
            group_sqid=obj.group.sqid,
            expire_date=obj.expire_date,
            access_count=obj.access_count,
            is_expired=obj.is_expired,
            created_at=obj.created_at
        )


class GroupShareCreateSchema(BaseModel):
    group_sqid: str
    expire_date: datetime = Field(..., description="Expiration date for the share link")


class PublicGroupSchema(BaseModel):
    """Schema for publicly shared group data"""
    sqid: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

