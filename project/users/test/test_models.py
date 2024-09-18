from django.test import TestCase
import pytest
from .factories import UserFactory
from ..models import User


@pytest.mark.django_db
class TestUserModel(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_user_str(self):
        user = User.objects.filter(id=self.user.id).get()
        assert str(user) == self.user.username
