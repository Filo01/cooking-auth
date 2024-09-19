import os
from .common import Common


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Test(Common):
    DEBUG = True

    # Testing
    INSTALLED_APPS = Common.INSTALLED_APPS

    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

    REST_FRAMEWORK = {**Common.REST_FRAMEWORK}
    del REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]
    del REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
