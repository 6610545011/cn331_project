from django.db import models
from django.conf import settings
from core.models import Course, Section, Prof
from django.utils import timezone

# Main Review Entity
class Review(models.Model):
    id = models.AutoField(primary_key=True)
    
    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    prof = models.ForeignKey(Prof, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    
    # Content and Metadata
    head = models.CharField(max_length=255)
    body = models.TextField()
    rating = models.IntegerField() # Assuming rating is an integer score (e.g., 1 to 5)
    incognito = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Review by {self.user.email} for {self.course.course_code}"

    class Meta:
        ordering = ['-date_created']


class ReviewUpvote(models.Model):
    """Records user votes (upvote/downvote) on a specific review."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.IntegerField() # e.g., 1 for Upvote, -1 for Downvote

    class Meta:
        # Ensures a user can only vote once per review
        unique_together = (('user', 'review'),)

    def __str__(self):
        return f"Vote {self.vote_type} on Review {self.review.id} by {self.user.email}"


class Bookmark(models.Model):
    """Allows users to bookmark specific reviews or courses."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    
    # Note: DBML included both review_id and course_id. 
    # Since a review always belongs to a course, if review is set, course is redundant.
    # However, to maintain the schema integrity, we include both, assuming a user might bookmark 
    # the entire Course (review=None) or a specific Review (review=X).
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, related_name='bookmarked_by')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='bookmarked_by')

    class Meta:
        # Prevents bookmarking the same course/review combination multiple times
        unique_together = (('user', 'review'), ('user', 'course')) 
        
    def __str__(self):
        target = self.review if self.review else self.course.course_code
        return f"Bookmark by {self.user.email} for {target}"


class Report(models.Model):
    """Records reports against abusive or inappropriate reviews."""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_reports')
    comment = models.TextField()

    class Meta:
        # Ensures a user can only report a specific review once
        unique_together = (('user', 'review'),)

    def __str__(self):
        return f"Report on Review {self.review.id} by {self.user.email}"