from typing import List
from ninja import Router
from django.shortcuts import get_object_or_404

from ocr_presets.models import OcrPreset
from ocr_presets.schemas import (
    OcrPresetSchema,
    OcrPresetCreateSchema,
    OcrPresetUpdateSchema
)

router = Router()


@router.get("/ocr-presets/", response=List[OcrPresetSchema])
def list_ocr_presets(request):
    """Get all OCR presets"""
    return OcrPreset.objects.all()


@router.post("/ocr-presets/", response=OcrPresetSchema)
def create_ocr_preset(request, payload: OcrPresetCreateSchema):
    """Create a new OCR preset"""
    preset = OcrPreset.objects.create(**payload.dict())
    return preset


@router.get("/ocr-presets/{sqid}", response=OcrPresetSchema)
def get_ocr_preset(request, sqid: str):
    """Get a specific OCR preset by sqid"""
    return get_object_or_404(OcrPreset, sqid=sqid)


@router.put("/ocr-presets/{sqid}", response=OcrPresetSchema)
def update_ocr_preset(request, sqid: str, payload: OcrPresetUpdateSchema):
    """Update an OCR preset"""
    preset = get_object_or_404(OcrPreset, sqid=sqid)

    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(preset, attr, value)

    preset.save()
    return preset


@router.delete("/ocr-presets/{sqid}")
def delete_ocr_preset(request, sqid: str):
    """Delete an OCR preset"""
    preset = get_object_or_404(OcrPreset, sqid=sqid)
    preset.delete()
    return {"success": True}


@router.get("/ocr-presets/default/get", response=OcrPresetSchema)
def get_default_preset(request):
    """Get the default OCR preset"""
    return OcrPreset.get_default_preset()

