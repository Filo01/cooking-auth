from django.contrib.auth.hashers import check_password
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker
import factory
import pytest
from ..models import User, OTPState
from .factories import UserFactory, OTPFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from uuid import uuid4
from datetime import timedelta

fake = Faker()


@pytest.mark.django_db
class TestUserListTestCase(APITestCase):
    """
    Tests /users list operations.
    """

    def setUp(self):
        self.url = "/api/v1/users/"
        self.user_data = factory.build(dict, FACTORY_CLASS=UserFactory)

    def test_get_request(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.user_data)
        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(pk=response.data.get("id"))
        assert user.username == self.user_data.get("username")
        assert check_password(self.user_data.get("password"), user.password)
        assert not user.has_2fa

    def test_post_request_with_has_2fa_succeeds(self):
        self.client.logout()
        user_data_2fa = factory.build(dict, FACTORY_CLASS=UserFactory)
        user_data_2fa["has_2fa"] = True
        response = self.client.post(self.url, user_data_2fa)
        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(pk=response.data.get("id"))
        assert user.username == user_data_2fa.get("username")
        assert check_password(user_data_2fa.get("password"), user.password)
        assert user.has_2fa


class TestUserDetailTestCase(APITestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        self.user = UserFactory()
        self.user2 = UserFactory(username="test")
        self.url = f"/api/v1/users/{self.user.pk}/"
        self.url2 = f"/api/v1/users/{self.user2.pk}/"
        self.refresh = RefreshToken.for_user(self.user)
        self.refresh2 = RefreshToken.for_user(self.user2)
        self.auth_header = {"Authorization": f"Bearer {self.refresh.access_token}"}
        self.auth_header2 = {"Authorization": f"Bearer {self.refresh2.access_token}"}
        # self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.refresh.access_token}")

    def test_get_request_returns_a_given_user(self):
        response = self.client.get(self.url, headers=self.auth_header)
        assert response.status_code == status.HTTP_200_OK

    def test_get_request_does_not_return_a_given_user(self):
        response = self.client.get(self.url2, headers=self.auth_header)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_put_request_updates_a_user(self):
        new_first_name = fake.first_name()
        payload = {"first_name": new_first_name}
        response = self.client.put(self.url, payload, headers=self.auth_header)
        assert response.status_code == status.HTTP_200_OK

        user = User.objects.get(pk=self.user.id)
        assert user.first_name == new_first_name

    def test_put_request_updates_a_user_2fa(self):
        payload = {"has_2fa": True}
        response = self.client.put(self.url, payload, headers=self.auth_header)
        assert response.status_code == status.HTTP_200_OK

        user = User.objects.get(pk=self.user.id)
        assert user.has_2fa

    def test_get_request_gets_a_user(self):
        response = self.client.get(self.url, headers=self.auth_header)
        assert response.status_code == status.HTTP_200_OK

        user = User.objects.get(pk=self.user.id)
        assert user.has_2fa == response.data.get("has_2fa")
        assert user.username == response.data.get("username")


class TestJWTLoginTestCase(APITestCase):
    def setUp(self):
        self.password = "securepassword123"
        self.user = UserFactory(password=make_password(self.password))
        self.url = "/api/v1/login/"

    def test_login_with_correct_credentials(self):
        """Test logging in with correct email and password."""
        data = {"email": self.user.email, "password": self.password}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("token", response.data)

    def test_login_with_incorrect_password(self):
        """Test logging in with incorrect password."""
        data = {"email": self.user.email, "password": "wrongpass"}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_2fa_enabled(self):
        """Test login where 2FA is enabled, expecting an OTP step."""
        self.user.has_2fa = True
        self.user.save()

        data = {"email": self.user.email, "password": "securepassword123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Login via email OTP", response.data["body"])
        self.assertIn(
            f"{self.url}{self.user.id}/otp/", response.data["_links"][0]["href"]
        )

    def test_login_with_2fa_enabled_otp_already_created(self):
        """Test login where 2FA is enabled and an otp was already created, expecting an OTP step."""
        self.user.has_2fa = True
        self.user.save()
        OTPFactory(user=self.user)

        data = {"email": self.user.email, "password": "securepassword123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Login via email OTP", response.data["body"])
        self.assertIn(
            f"{self.url}{self.user.id}/otp/", response.data["_links"][0]["href"]
        )

    def test_login_with_2fa_enabled_otp_already_created_invalid(self):
        """Test login where 2FA is enabled and an otp was already created, but in an invalid state, expecting an OTP step."""
        self.user.has_2fa = True
        self.user.save()
        otp = OTPFactory(user=self.user)
        otp.state = OTPState.EXPIRED.value
        otp.save()

        data = {"email": self.user.email, "password": "securepassword123"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Login via email OTP", response.data["body"])
        self.assertIn(
            f"{self.url}{self.user.id}/otp/", response.data["_links"][0]["href"]
        )


class JWTStepTwoLoginTest(APITestCase):
    def setUp(self):
        self.otp = OTPFactory()
        self.otp.user.has_2fa = True
        self.otp.user.save()
        self.user = self.otp.user
        self.url = f"/api/v1/login/{self.user.id}/otp"

    def test_login_with_correct_otp(self):
        """Test login with correct OTP."""
        data = {"code": self.otp.code}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("token", response.data)

    def test_login_with_incorrect_otp(self):
        """Test login with incorrect OTP."""
        data = {"code": "654321"}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_incorrect_user(self):
        """Test login with incorrect OTP."""
        data = {"code": self.otp.code}
        url = f"/api/v1/login/{uuid4()}/otp"

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_user_no_2fa(self):
        """Test login with User without has_2fa."""
        self.user.has_2fa = False
        self.user.save()
        data = {"code": self.otp.code}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_user_no_otp(self):
        """Test login with no OTP."""
        user = UserFactory(username="test1")
        user.has_2fa = True
        user.save()
        data = {"code": self.otp.code}
        url = f"/api/v1/login/{user.id}/otp"

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_expired_otp(self):
        """Test login when OTP is expired."""
        self.otp.state = OTPState.EXPIRED.value
        self.otp.save()

        data = {"code": self.otp.code}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.otp.refresh_from_db()
        self.assertEqual(self.otp.state, OTPState.GONE)

    def test_login_with_expired_otp_time(self):
        """Test login when OTP is expired first request."""
        self.otp.expires_at = self.otp.expires_at - timedelta(minutes=10)
        self.otp.save()

        data = {"code": self.otp.code}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.otp.refresh_from_db()
        self.assertEqual(self.otp.state, OTPState.EXPIRED)

    def test_login_with_too_many_attempts(self):
        """Test login after exceeding OTP attempts."""
        self.otp.error_count = 4  # Over the max allowed attempts
        self.otp.save()

        data = {"code": self.otp.code}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.otp.refresh_from_db()
        self.assertEqual(self.otp.state, OTPState.TOO_MANY_ATTEMPTS)

    def test_login_with_otp_gone(self):
        """Test login with OTP gone."""
        self.otp.state = OTPState.GONE.value
        self.otp.save()

        data = {"code": self.otp.code}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.otp.refresh_from_db()
        self.assertEqual(self.otp.state, OTPState.GONE)

    def test_login_with_missing_otp(self):
        """Test login when OTP is missing."""
        data = {}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.otp.refresh_from_db()
        self.assertEqual(self.otp.error_count, 1)
