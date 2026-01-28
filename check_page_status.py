#!/usr/bin/env python
"""
Check status of retried pages
"""

import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docpond.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

def check_pages():
    """Check status of pages that were retried"""
    from documents.models import Page, Image, ProcessingStatus

    print("\n=== Checking Retried Pages Status ===\n")

    # Pages that were retried
    retried_page_ids = [445, 446, 448, 449, 450, 451, 452, 455, 456, 457]

    completed = 0
    failed = 0
    processing = 0
    pending = 0

    print("Page Status:")
    print("-" * 80)

    for page_id in retried_page_ids:
        try:
            page = Page.objects.get(id=page_id)
            images_count = Image.objects.filter(page=page).count()

            status_icon = {
                ProcessingStatus.COMPLETED: "✅",
                ProcessingStatus.FAILED: "❌",
                ProcessingStatus.PROCESSING: "⏳",
                ProcessingStatus.PENDING: "⏸️",
            }.get(page.processing_status, "❓")

            print(f"{status_icon} Page {page_id} (page {page.page_number}): "
                  f"{page.processing_status} - {images_count} images")

            if page.processing_status == ProcessingStatus.COMPLETED:
                completed += 1
            elif page.processing_status == ProcessingStatus.FAILED:
                failed += 1
            elif page.processing_status == ProcessingStatus.PROCESSING:
                processing += 1
            elif page.processing_status == ProcessingStatus.PENDING:
                pending += 1

        except Page.DoesNotExist:
            print(f"❓ Page {page_id}: NOT FOUND")

    print("-" * 80)
    print(f"\nSummary:")
    print(f"  ✅ Completed: {completed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⏳ Processing: {processing}")
    print(f"  ⏸️  Pending: {pending}")

    if completed > 0:
        print(f"\n🎉 {completed} pages successfully processed!")

        # Show image details for completed pages
        print(f"\nImage Details:")
        for page_id in retried_page_ids:
            try:
                page = Page.objects.get(id=page_id)
                if page.processing_status == ProcessingStatus.COMPLETED:
                    images = Image.objects.filter(page=page)
                    if images.exists():
                        print(f"  Page {page_id}: {images.count()} images")
                        for img in images:
                            print(f"    - Image {img.sqid}: {img.caption or '(no caption)'}")
            except:
                pass

    if processing > 0:
        print(f"\n⏳ {processing} pages still processing - check again in a moment")

    if failed > 0:
        print(f"\n⚠️  {failed} pages failed - check Celery logs for errors")

    return completed, failed, processing, pending


if __name__ == '__main__':
    try:
        check_pages()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

