# accounts/utils/datetime.py
from django.utils import timezone

DATETIME_FMT = "%d/%m/%Y %H:%M:%S"  # 25/08/2025 23:09:36


def fmt_local(dt):
    if not dt:
        return None
    return timezone.localtime(dt).strftime(DATETIME_FMT)
