import random

from django.conf import settings


def calculate_delay(retry_count):
    return settings.BASE_DELAY * (2**retry_count) + random.uniform(0, 1)
