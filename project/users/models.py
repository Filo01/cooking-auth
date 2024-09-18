import uuid
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from enum import Enum
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    has_2fa = models.BooleanField(
        verbose_name="2FA enabled", default=False, blank=False, null=False
    )
    email = models.EmailField(_("email address"), blank=False, null=False, unique=True)

    def __str__(self):
        return self.username


class OTPState(Enum):
    """
    OTP States.

    - VALID: the OTP starts in the VALID state and can be used to authenticate
    - USED: the user has already submitted the valid OTP
    - TOO_MANY_ATTEMPTS: the user has submitted the wrong OTP too many times
    - EXPIRED: the user has not submitted the valid OTP in the required time
    - GONE: the OTP has reached its final state from the previous states
    """

    VALID = "VALID"
    USED = "USED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"
    EXPIRED = "EXPIRED"
    GONE = "GONE"

    def __eq__(self, other):
        return self.value == other


class OTPManager(models.Manager):
    OTP_EXPIRES_IN = timedelta(minutes=5)
    _otp_characters = "abcdefghijklmnprstuvwxyz0123456789"

    def create_otp(
        self,
        user,
    ):
        code = "".join(
            random.SystemRandom().choice(self._otp_characters) for _ in range(6)
        )
        expires_at = timezone.now() + OTPManager.OTP_EXPIRES_IN
        otp = self.model(
            user=user,
            code=code,
            expires_at=expires_at.astimezone(timezone.get_current_timezone()),
        )
        otp.save()
        return otp


class OTP(models.Model):
    STATES = [
        OTPState.VALID,
        OTPState.USED,
        OTPState.TOO_MANY_ATTEMPTS,
        OTPState.EXPIRED,
        OTPState.GONE,
    ]

    code = models.CharField(
        verbose_name="Code", blank=False, null=False, db_index=True, max_length=6
    )
    expires_at = models.DateTimeField(
        verbose_name="Expiration Time", blank=False, null=False
    )
    error_count = models.IntegerField(
        verbose_name="Error count", blank=False, null=False, default=0
    )
    state = models.CharField(
        verbose_name="OTP State",
        choices=[(s.value, s.name) for s in STATES],
        max_length=max([len(s.value) for s in STATES]),
    )
    user = models.OneToOneField(
        to=User,
        verbose_name="User",
        on_delete=models.deletion.CASCADE,
        related_name="otp",
        primary_key=True,
    )

    objects = OTPManager()

    def __str__(self):
        return self.code
