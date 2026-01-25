from ninja import Schema
from typing import Optional


class OcrPresetSchema(Schema):
    sqid: str
    name: str
    is_default: bool
    force_ocr: bool
    skip_text: bool
    redo_ocr: bool
    ocr_backend: str
    language: str
    optimize: int
    jpeg_quality: int
    png_quality: int
    deskew: bool
    do_clean: bool
    do_clean_final: bool
    remove_background: bool
    oversample: int
    rotate_pages: bool
    remove_vectors: bool
    advanced_settings: dict


class OcrPresetCreateSchema(Schema):
    name: str
    is_default: bool = False
    force_ocr: bool = False
    skip_text: bool = True
    redo_ocr: bool = False
    ocr_backend: str = 'tesseract'
    language: str = 'eng'
    optimize: int = 1
    jpeg_quality: int = 75
    png_quality: int = 70
    deskew: bool = False
    do_clean: bool = False
    do_clean_final: bool = False
    remove_background: bool = False
    oversample: int = 0
    rotate_pages: bool = False
    remove_vectors: bool = False
    advanced_settings: dict = {}


class OcrPresetUpdateSchema(Schema):
    name: Optional[str] = None
    is_default: Optional[bool] = None
    force_ocr: Optional[bool] = None
    skip_text: Optional[bool] = None
    redo_ocr: Optional[bool] = None
    ocr_backend: Optional[str] = None
    language: Optional[str] = None
    optimize: Optional[int] = None
    jpeg_quality: Optional[int] = None
    png_quality: Optional[int] = None
    deskew: Optional[bool] = None
    do_clean: Optional[bool] = None
    do_clean_final: Optional[bool] = None
    remove_background: Optional[bool] = None
    oversample: Optional[int] = None
    rotate_pages: Optional[bool] = None
    remove_vectors: Optional[bool] = None
    advanced_settings: Optional[dict] = None

