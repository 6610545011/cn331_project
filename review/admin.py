from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import Review, Bookmark, ReviewUpvote, Report, Tag

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

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Review)
class ReviewAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', '__str__', 'course', 'prof', 'rating', 'date_created')
    filter_horizontal = ('tags',) # Improves the UI for ManyToManyFields
    raw_id_fields = ('course', 'prof')


@admin.register(Bookmark)
class BookmarkAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'review')
    raw_id_fields = ('course', 'review')


@admin.register(ReviewUpvote)
class ReviewVoteAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'review', 'user', 'vote_type')
    raw_id_fields = ('review',)


@admin.register(Report)
class ReviewReportAdmin(AutoUserAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'review', 'user')
    raw_id_fields = ('review',)