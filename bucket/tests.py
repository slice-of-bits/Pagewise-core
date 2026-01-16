from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from bucket.models import Bucket


class BucketModelTest(TestCase):
    def setUp(self):
        self.bucket = Bucket.objects.create(
            name="Test Bucket",
            description="A test bucket"
        )

    def test_bucket_creation(self):
        """Test bucket is created with correct attributes"""
        self.assertEqual(self.bucket.name, "Test Bucket")
        self.assertEqual(self.bucket.description, "A test bucket")
        self.assertTrue(self.bucket.sqid)
        self.assertTrue(self.bucket.created_at)
        self.assertTrue(self.bucket.updated_at)

    def test_bucket_str(self):
        """Test bucket string representation"""
        self.assertEqual(str(self.bucket), "Test Bucket")

    def test_bucket_update(self):
        """Test bucket can be updated"""
        self.bucket.name = "Updated Bucket"
        self.bucket.save()
        self.assertEqual(self.bucket.name, "Updated Bucket")
