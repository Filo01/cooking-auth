from django.test import TestCase
import pytest
from .factories import UserFactory, OTPFactory
from ..models import User, OTP


@pytest.mark.django_db
class TestUserModel(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_user_str(self):
        user = User.objects.filter(id=self.user.id).get()
        assert str(user) == self.user.username


class TestOtpModel(TestCase):
    def setUp(self):
        self.otp = OTPFactory()

    def test_otp_str(self):
        otp = OTP.objects.filter(user=self.otp.user).get()
        assert str(otp) == self.otp.code
