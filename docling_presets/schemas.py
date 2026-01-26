from typing import List, Optional
from ninja import Schema, ModelSchema
from datetime import datetime

from docling_presets.models import DoclingPreset


class DoclingPresetSchema(Schema):
    class Meta:
        model = DoclingPreset
        fields = [
            'sqid',
            'name',
            'is_default',
            'pipeline_type',
            'ocr_engine',
            'force_ocr',
            'ocr_languages',
            'vlm_model',
            'enable_picture_description',
            'picture_description_prompt',
            'enable_table_structure',
            'table_former_mode',
            'enable_code_enrichment',
            'enable_formula_enrichment',
            'filter_orphan_clusters',
            'filter_empty_clusters',
            'advanced_settings',
            'created_at',
            'updated_at',
        ]


class DoclingPresetCreateSchema(ModelSchema):
    class Meta:
        model = DoclingPreset
        fields = [
            'name',
            'is_default',
            'pipeline_type',
            'ocr_engine',
            'force_ocr',
            'ocr_languages',
            'vlm_model',
            'enable_picture_description',
            'picture_description_prompt',
            'enable_table_structure',
            'table_former_mode',
            'enable_code_enrichment',
            'enable_formula_enrichment',
            'filter_orphan_clusters',
            'filter_empty_clusters',
            'advanced_settings',
        ]



class DoclingPresetUpdateSchema(ModelSchema):
    class Meta:
        model = DoclingPreset
        fields = [
            'name',
            'is_default',
            'pipeline_type',
            'ocr_engine',
            'force_ocr',
            'ocr_languages',
            'vlm_model',
            'enable_picture_description',
            'picture_description_prompt',
            'enable_table_structure',
            'table_former_mode',
            'enable_code_enrichment',
            'enable_formula_enrichment',
            'filter_orphan_clusters',
            'filter_empty_clusters',
            'advanced_settings',
        ]