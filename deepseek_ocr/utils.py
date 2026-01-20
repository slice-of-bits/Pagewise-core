"""
Utility functions for DeepSeek OCR.
"""
from typing import List


def regenerate_markdown_with_sqids(markdown: str, image_sqids: List[str]) -> str:
    """
    Replace placeholder image URLs in markdown with sqid-based URLs.

    This function is useful when you need to regenerate markdown after
    images have been saved to the database and you have their sqids.

    Args:
        markdown: The markdown text with placeholder image URLs
        image_sqids: List of image sqids in the order they appear in the markdown

    Returns:
        Markdown with sqid-based image URLs
    """
    result = markdown
    for idx, sqid in enumerate(image_sqids):
        placeholder = f"__IMAGE_PLACEHOLDER_{idx}__"
        result = result.replace(placeholder, sqid)
    return result


def create_sqid_image_url_generator(sqids: List[str]):
    """
    Create an image URL generator function that uses a list of sqids.

    This is useful when you already have the sqids and want to use them
    during the initial parsing.

    Args:
        sqids: List of image sqids

    Returns:
        A function that can be passed to parse_ocr_output as image_url_generator
    """
    def generator(image_index: int, ref_data: dict) -> str:
        if image_index < len(sqids):
            return sqids[image_index]
        return f"__MISSING_SQID_{image_index}__"

    return generator


def create_placeholder_image_url_generator():
    """
    Create an image URL generator that produces placeholders.

    These placeholders can be replaced later with actual sqids using
    regenerate_markdown_with_sqids().

    Returns:
        A function that can be passed to parse_ocr_output as image_url_generator
    """
    def generator(image_index: int, ref_data: dict) -> str:
        return f"__IMAGE_PLACEHOLDER_{image_index}__"

    return generator

