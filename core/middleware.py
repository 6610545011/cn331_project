from datetime import date
from django.utils.deprecation import MiddlewareMixin
from django.db import IntegrityError

from stats.models import DailyActiveUser


class DailyActiveUserMiddleware(MiddlewareMixin):
    """Middleware to log a user's presence per day.

    For authenticated users, it will ensure a DailyActiveUser record exists
    for today's date. This is a lightweight way to approximate DAU.
    """
    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            today = date.today()
            try:
                DailyActiveUser.objects.get_or_create(user=user, date=today)
            except IntegrityError:
                # race condition guard for concurrent requests
                pass
