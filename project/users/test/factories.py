import factory
from datetime import datetime, timedelta


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.User"
        django_get_or_create = ("username",)

    id = factory.Faker("uuid4")
    username = factory.Sequence(lambda n: f"testuser{n}")
    password = factory.Faker(
        "password",
        length=10,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True,
    )
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    has_2fa = False


class OTPFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.OTP"

    code = factory.Faker("pystr", min_chars=6, max_chars=6)
    state = "VALID"
    expires_at = datetime.now() + timedelta(minutes=5)
    error_count = 0
    user = factory.SubFactory(UserFactory)
