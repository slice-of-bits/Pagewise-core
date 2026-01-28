from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from ponds.models import Pond, PondShare


class PondModelTests(TestCase):
    def test_create_pond(self):
        """Test creating a pond"""
        pond = Pond.objects.create(
            name="Test Pond",
            description="Test Description"
        )
        self.assertEqual(pond.name, "Test Pond")
        self.assertEqual(pond.description, "Test Description")
        self.assertIsNotNone(pond.sqid)

    def test_pond_str(self):
        """Test pond string representation"""
        pond = Pond.objects.create(name="Test Pond")
        self.assertEqual(str(pond), "Test Pond")


class PondShareModelTests(TestCase):
    def setUp(self):
        self.pond = Pond.objects.create(name="Test Pond")

    def test_create_pond_share(self):
        """Test creating a pond share"""
        expire_date = timezone.now() + timedelta(days=7)
        share = PondShare.objects.create(
            pond=self.pond,
            expire_date=expire_date
        )
        self.assertEqual(share.pond, self.pond)
        self.assertEqual(share.access_count, 0)
        self.assertIsNotNone(share.sqid)
        self.assertGreaterEqual(len(share.sqid), 12)  # Min length should be 12

    def test_is_expired(self):
        """Test expired check"""
        # Not expired
        future_date = timezone.now() + timedelta(days=1)
        share = PondShare.objects.create(
            pond=self.pond,
            expire_date=future_date
        )
        self.assertFalse(share.is_expired)

        # Expired
        past_date = timezone.now() - timedelta(days=1)
        expired_share = PondShare.objects.create(
            pond=self.pond,
            expire_date=past_date
        )
        self.assertTrue(expired_share.is_expired)

    def test_increment_access(self):
        """Test incrementing access count"""
        expire_date = timezone.now() + timedelta(days=7)
        share = PondShare.objects.create(
            pond=self.pond,
            expire_date=expire_date
        )

        initial_count = share.access_count
        share.increment_access()
        self.assertEqual(share.access_count, initial_count + 1)

        share.increment_access()
        self.assertEqual(share.access_count, initial_count + 2)
