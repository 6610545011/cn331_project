from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import Review, Bookmark, ReviewVote, ReviewReport

class AutoUserAdminMixin:
    exclude = ('user',)

    def save_model(self, request, obj, form, change):
        # Ensure a valid user PK is set before saving to avoid FK failures.
        if not getattr(obj, 'user_id', None):
            obj.user_id = request.user.pk
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
        except IntegrityError as exc:
            # Convert DB-level FK failures into a validation error shown in the admin form.
            raise ValidationError("Could not save: a related foreign-key value is invalid or missing.") from exc


@admin.register(Review)
class ReviewAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'course', 'section', 'professor', 'rating', 'created_at')
    raw_id_fields = ('course', 'section', 'professor')


@admin.register(Bookmark)
class BookmarkAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'section', 'review', 'created_at')
    raw_id_fields = ('course', 'section', 'review')


@admin.register(ReviewVote)
class ReviewVoteAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'review', 'user', 'vote_type', 'created_at')
    raw_id_fields = ('review',)


@admin.register(ReviewReport)
class ReviewReportAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'review', 'user', 'status', 'reported_at')
    raw_id_fields = ('review',)