from typing import TypedDict


class OTPLink(TypedDict):
    rel: str
    href: str
    method: str
    body: dict


class LoginResponse(TypedDict):
    message: str
    token: dict


class LoginResponseOtp(LoginResponse):
    _links: list[OTPLink] | None
