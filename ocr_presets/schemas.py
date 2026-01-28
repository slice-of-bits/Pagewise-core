from ninja import Schema, ModelSchema
from typing import Optional

from ocr_presets.models import OcrPreset


class OcrPresetSchema(ModelSchema):
     class Meta:
        model = OcrPreset
        fields = [
            'sqid',
            'name',
            'is_default',
            'force_ocr',
            'skip_text',
            'redo_ocr',
            'ocr_backend',
            'language',
            'optimize',
            'jpeg_quality',
            'png_quality',
            'deskew',
            'do_clean',
            'do_clean_final',
            'remove_background',
            'oversample',
            'rotate_pages',
            'remove_vectors',
            'advanced_settings',
        ]


class OcrPresetCreateSchema(ModelSchema):
    class Meta:
        model = OcrPreset
        fields = [
            'name',
            'is_default',
            'force_ocr',
            'skip_text',
            'redo_ocr',
            'ocr_backend',
            'language',
            'optimize',
            'jpeg_quality',
            'png_quality',
            'deskew',
            'do_clean',
            'do_clean_final',
            'remove_background',
            'oversample',
            'rotate_pages',
            'remove_vectors',
            'advanced_settings',
        ]

class OcrPresetUpdateSchema(Schema):
    class Meta:
        model = OcrPreset
        fields = [
            'name',
            'is_default',
            'force_ocr',
            'skip_text',
            'redo_ocr',
            'ocr_backend',
            'language',
            'optimize',
            'jpeg_quality',
            'png_quality',
            'deskew',
            'do_clean',
            'do_clean_final',
            'remove_background',
            'oversample',
            'rotate_pages',
            'remove_vectors',
            'advanced_settings',
        ]

