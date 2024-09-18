from rest_framework import viewsets, mixins
from rest_framework import status
from .models import User, OTP, OTPState
from .permissions import IsUserOrCreatingAccountOrReadOnly, IsNotAuthenticated
from .responses import LoginResponseOtp, LoginResponse
from .serializers import (
    CreateUserSerializer,
    UserSerializer,
    OTPSerializer,
    FirstStepLoginSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

OTP_MAX_ERRORS = 3


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Updates and retrieves user accounts
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsUserOrCreatingAccountOrReadOnly,)

    def get_serializer_class(self):
        is_creating_a_new_user = self.action == "create"
        if is_creating_a_new_user:
            return CreateUserSerializer
        return self.serializer_class


@api_view(http_method_names=["POST"])
@permission_classes([IsNotAuthenticated])
def jwt_login(request, **kwargs):
    serializer = FirstStepLoginSerializer(data=request.data)
    serializer.is_valid()
    validated_data = serializer.validated_data
    email: str = validated_data["email"]
    password: str = validated_data["password"]
    user: User = User.objects.filter(email=email).first()
    if not user or not user.check_password(password):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if user.has_2fa:
        otp = OTP.objects.filter(user=user).first()

        if not otp:
            OTP.objects.create_otp(user=user)
        elif otp.state != OTPState.VALID:
            otp.delete()
            OTP.objects.create_otp(user=user)

        return Response(
            LoginResponseOtp(
                body="Login via email OTP",
                _links=[
                    {
                        "href": f"/api/v1/login/{user.id}/otp/",
                        "method": "POST",
                        "body": {"otp": {"type": "str"}},
                    }
                ],
            )
        )

    return _generate_successful_login_jwt_response(user)


@api_view(http_method_names=["POST"])
@permission_classes([IsNotAuthenticated])
def jwt_login_via_otp(request, pk, **kwargs):
    user: User = User.objects.filter(id=pk).first()
    if not user or not user.has_2fa:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = OTPSerializer(data=request.data)
    serializer.is_valid()
    validated_data = serializer.validated_data

    otp_db: OTP | None = OTP.objects.filter(user=user).first()
    if not otp_db:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    # Handle OTP state-based responses
    if otp_db.state == OTPState.GONE:
        return Response(status=status.HTTP_410_GONE)

    if otp_db.state in (OTPState.EXPIRED, OTPState.TOO_MANY_ATTEMPTS):
        otp_db.state = OTPState.GONE.value
        otp_db.save(update_fields=["state"])
        return Response(status=status.HTTP_403_FORBIDDEN)

    if otp_db.error_count > OTP_MAX_ERRORS:
        otp_db.state = OTPState.TOO_MANY_ATTEMPTS.value
        otp_db.save(update_fields=["state"])
        return Response(status=status.HTTP_403_FORBIDDEN)

    if timezone.now() > otp_db.expires_at:
        otp_db.state = OTPState.EXPIRED.value
        otp_db.save()
        return Response(status=status.HTTP_403_FORBIDDEN)

    # Validate OTP code
    otp = validated_data.get("code")

    if not otp:
        # Increment error count and return 400 if OTP is missing from request
        otp_db.error_count += 1
        otp_db.save(update_fields=["error_count"])
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if otp != otp_db.code:
        # Increment error count and return 401 if OTP is incorrect
        otp_db.error_count += 1
        otp_db.save(update_fields=["error_count"])
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    # OTP matches
    return _generate_successful_login_jwt_response(user)


def _generate_successful_login_jwt_response(user: User) -> LoginResponse:
    """
    Generates a Response for the provided user
    """

    refresh: Token = RefreshToken.for_user(user)

    return Response(
        LoginResponse(
            {
                "message": "Login successful",
                "token": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
        )
    )
