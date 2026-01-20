from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404

from images.models import Image


def image_redirect_view(request, image_sqid, filename=None):
    """Redirect to the image file URL by SQID
    
    Args:
        image_sqid: The SQID of the image
        filename: Optional filename (for SEO-friendly URLs)
    """
    image = get_object_or_404(Image, sqid=image_sqid)

    # Check if image has a file attached
    if not image.image_file:
        raise Http404(f"Image {image_sqid} exists but has no file attached")

    return redirect(image.image_file.url)
