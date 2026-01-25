from typing import List, Optional
from ninja import Schema
from pydantic import BaseModel, Field
from datetime import datetime


class DoclingPresetSchema(BaseModel):
    """Schema for Docling preset output"""
    sqid: str
    name: str
    is_default: bool
    pipeline_type: str
    ocr_engine: str
    force_ocr: bool
    ocr_languages: List[str]
    vlm_model: str
    enable_picture_description: bool
    picture_description_prompt: str
    enable_table_structure: bool
    table_former_mode: str
    enable_code_enrichment: bool
    enable_formula_enrichment: bool
    filter_orphan_clusters: bool
    filter_empty_clusters: bool
    advanced_settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoclingPresetCreateSchema(BaseModel):
    """Schema for creating a new Docling preset"""
    name: str = Field(..., min_length=1, max_length=100)
    is_default: Optional[bool] = False
    pipeline_type: Optional[str] = 'standard'
    ocr_engine: Optional[str] = 'auto'
    force_ocr: Optional[bool] = False
    ocr_languages: Optional[List[str]] = ['en']
    vlm_model: Optional[str] = ''
    enable_picture_description: Optional[bool] = False
    picture_description_prompt: Optional[str] = 'Describe this image in a few sentences.'
    enable_table_structure: Optional[bool] = True
    table_former_mode: Optional[str] = 'accurate'
    enable_code_enrichment: Optional[bool] = False
    enable_formula_enrichment: Optional[bool] = False
    filter_orphan_clusters: Optional[bool] = False
    filter_empty_clusters: Optional[bool] = True
    advanced_settings: Optional[dict] = {}


class DoclingPresetUpdateSchema(BaseModel):
    """Schema for updating a Docling preset"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_default: Optional[bool] = None
    pipeline_type: Optional[str] = None
    ocr_engine: Optional[str] = None
    force_ocr: Optional[bool] = None
    ocr_languages: Optional[List[str]] = None
    vlm_model: Optional[str] = None
    enable_picture_description: Optional[bool] = None
    picture_description_prompt: Optional[str] = None
    enable_table_structure: Optional[bool] = None
    table_former_mode: Optional[str] = None
    enable_code_enrichment: Optional[bool] = None
    enable_formula_enrichment: Optional[bool] = None
    filter_orphan_clusters: Optional[bool] = None
    filter_empty_clusters: Optional[bool] = None
    advanced_settings: Optional[dict] = None

