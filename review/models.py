from django.db import models
from django.conf import settings

# Create your models here.
from core.models import Course, Section, Professor

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL)
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL)
    professor = models.ForeignKey(Professor, null=True, blank=True, on_delete=models.SET_NULL)
    rating = models.IntegerField()
    header = models.TextField()
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    incognito = models.BooleanField(default=False)

    def __str__(self):
        # Use full name when available, otherwise username
        name = getattr(self.user, "get_full_name", None)
        if callable(name):
            display_name = self.user.get_full_name() or self.user.username
        else:
            display_name = getattr(self.user, "username", str(self.user))
        return f"{display_name} - {self.rating}"

class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL)
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL)
    review = models.ForeignKey(Review, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class ReviewVote(models.Model):
    VOTE_CHOICES = (
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote')
    )
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=8, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')

class ReviewReport(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved')
    )
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField()
    reported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
