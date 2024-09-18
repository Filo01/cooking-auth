from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "has_2fa")
        read_only_fields = ("username",)


class CreateUserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "has_2fa",
        )
        extra_kwargs = {"password": {"write_only": True}}


class OTPSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6, required=True)


class FirstStepLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


class TokenResponseSerializer(serializers.Field):
    access = serializers.CharField(required=True)
    refresh = serializers.CharField(required=True)


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    token = serializers.DictField(child=TokenResponseSerializer())


class OTPLink(serializers.Field):
    rel = serializers.CharField(required=True)
    href = serializers.CharField(required=True)
    method = serializers.CharField(required=True)
    body = serializers.DictField(child=serializers.DictField())


class OTPResponseSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    token = serializers.CharField()
    _links = serializers.ListField(child=OTPLink())
