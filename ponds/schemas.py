from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PondSchema(BaseModel):
    sqid: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PondCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class PondUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class PondShareSchema(BaseModel):
    sqid: str
    pond_sqid: str
    expire_date: datetime
    access_count: int
    is_expired: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @staticmethod
    def from_pond_share(obj):
        return PondShareSchema(
            sqid=obj.sqid,
            pond_sqid=obj.pond.sqid,
            expire_date=obj.expire_date,
            access_count=obj.access_count,
            is_expired=obj.is_expired,
            created_at=obj.created_at
        )


class PondShareCreateSchema(BaseModel):
    pond_sqid: str
    expire_date: datetime = Field(..., description="Expiration date for the share link")


class PublicPondSchema(BaseModel):
    """Schema for publicly shared pond data"""
    sqid: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

