from typing import List
from ninja import Router
from ninja.pagination import paginate
from django.shortcuts import get_object_or_404

from docling_presets.models import DoclingPreset
from docling_presets.schemas import (
    DoclingPresetSchema,
    DoclingPresetCreateSchema,
    DoclingPresetUpdateSchema
)

router = Router()


@router.get("/docling-presets/", response=List[DoclingPresetSchema])
@paginate
def list_docling_presets(request):
    """List all Docling presets"""
    return DoclingPreset.objects.all()


@router.post("/docling-presets/", response=DoclingPresetSchema)
def create_docling_preset(request, payload: DoclingPresetCreateSchema):
    """Create a new Docling preset"""
    preset = DoclingPreset.objects.create(**payload.model_dump())
    return preset


@router.get("/docling-presets/{sqid}", response=DoclingPresetSchema)
def get_docling_preset(request, sqid: str):
    """Get a specific Docling preset"""
    return get_object_or_404(DoclingPreset, sqid=sqid)


@router.put("/docling-presets/{sqid}", response=DoclingPresetSchema)
def update_docling_preset(request, sqid: str, payload: DoclingPresetUpdateSchema):
    """Update a Docling preset"""
    preset = get_object_or_404(DoclingPreset, sqid=sqid)

    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(preset, attr, value)

    preset.save()
    return preset


@router.delete("/docling-presets/{sqid}")
def delete_docling_preset(request, sqid: str):
    """Delete a Docling preset"""
    preset = get_object_or_404(DoclingPreset, sqid=sqid)
    preset.delete()
    return {"success": True}


@router.post("/docling-presets/{sqid}/set-default", response=DoclingPresetSchema)
def set_default_docling_preset(request, sqid: str):
    """Set a preset as the default"""
    preset = get_object_or_404(DoclingPreset, sqid=sqid)
    preset.is_default = True
    preset.save()  # The save method will handle removing default from other presets
    return preset


@router.get("/docling-presets/default/get", response=DoclingPresetSchema)
def get_default_docling_preset(request):
    """Get the default Docling preset"""
    preset = DoclingPreset.get_default_preset()
    return preset

