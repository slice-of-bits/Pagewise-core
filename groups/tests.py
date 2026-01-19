from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from groups.models import Group, GroupShare


class GroupModelTests(TestCase):
    def test_create_group(self):
        """Test creating a group"""
        group = Group.objects.create(
            name="Test Group",
            description="Test Description"
        )
        self.assertEqual(group.name, "Test Group")
        self.assertEqual(group.description, "Test Description")
        self.assertIsNotNone(group.sqid)

    def test_group_str(self):
        """Test group string representation"""
        group = Group.objects.create(name="Test Group")
        self.assertEqual(str(group), "Test Group")


class GroupShareModelTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Test Group")

    def test_create_group_share(self):
        """Test creating a group share"""
        expire_date = timezone.now() + timedelta(days=7)
        share = GroupShare.objects.create(
            group=self.group,
            expire_date=expire_date
        )
        self.assertEqual(share.group, self.group)
        self.assertEqual(share.access_count, 0)
        self.assertIsNotNone(share.sqid)
        self.assertGreaterEqual(len(share.sqid), 12)  # Min length should be 12

    def test_is_expired(self):
        """Test expired check"""
        # Not expired
        future_date = timezone.now() + timedelta(days=1)
        share = GroupShare.objects.create(
            group=self.group,
            expire_date=future_date
        )
        self.assertFalse(share.is_expired)

        # Expired
        past_date = timezone.now() - timedelta(days=1)
        expired_share = GroupShare.objects.create(
            group=self.group,
            expire_date=past_date
        )
        self.assertTrue(expired_share.is_expired)

    def test_increment_access(self):
        """Test incrementing access count"""
        expire_date = timezone.now() + timedelta(days=7)
        share = GroupShare.objects.create(
            group=self.group,
            expire_date=expire_date
        )

        initial_count = share.access_count
        share.increment_access()
        self.assertEqual(share.access_count, initial_count + 1)

        share.increment_access()
        self.assertEqual(share.access_count, initial_count + 2)
