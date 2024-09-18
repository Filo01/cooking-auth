from django.urls import reverse
from django.contrib.auth.hashers import check_password
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker
import factory
import pytest
from ..models import User
from .factories import UserFactory
from rest_framework_simplejwt.tokens import RefreshToken


fake = Faker()


@pytest.mark.django_db
class TestUserListTestCase(APITestCase):
    """
    Tests /users list operations.
    """

    def setUp(self):
        self.url = reverse("user-list")
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
        self.user2 = UserFactory()
        self.url = reverse("user-detail", kwargs={"pk": self.user.pk})
        self.url2 = reverse("user-detail", kwargs={"pk": self.user2.pk})
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
