from django.db import models
from django.conf import settings
from core.models import Course, Section, Prof
from django.utils import timezone

# --- โมเดลสำหรับ Tag ---
# สร้างขึ้นเพื่อใช้กับ Review ผ่าน ManyToManyField
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# --- โมเดลหลักสำหรับรีวิว ---
class Review(models.Model):
    id = models.AutoField(primary_key=True)
    
    # --- Relationships ---
    # ผู้เขียนรีวิว (จำเป็นต้องมีเสมอ)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    
    # เป้าหมายของการรีวิว (สามารถเป็นค่าว่างได้ทั้งหมด แต่ต้องมีอย่างน้อย 1 อย่างตอน validate ในฟอร์ม)
    # on_delete=SET_NULL: ถ้ารายวิชาถูกลบ รีวิวจะยังคงอยู่ แต่ฟิลด์ course จะเป็น NULL
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    prof = models.ForeignKey(Prof, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    
    # Tag ที่เกี่ยวข้อง (สามารถไม่มีเลยก็ได้)
    tags = models.ManyToManyField(Tag, blank=True, related_name='reviews')
    
    # --- Content and Metadata ---
    head = models.CharField(max_length=255)
    body = models.TextField()
    rating = models.IntegerField() # คะแนน 1-5
    incognito = models.BooleanField(default=False)
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        # ทำให้ __str__ ฉลาดขึ้น สามารถแสดงผลได้แม้ course หรือ prof จะเป็น None
        target = "Review"
        if self.course:
            target = self.course.course_code
        elif self.prof:
            target = self.prof.prof_name
        return f"Review by {self.user.email} for {target}"

    class Meta:
        ordering = ['-date_created']


# --- โมเดลเสริมอื่นๆ (ไม่ต้องแก้ไข) ---

class ReviewUpvote(models.Model):
    """บันทึกการโหวต (upvote/downvote) ของผู้ใช้ในรีวิว"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.IntegerField() # เช่น 1 สำหรับ Upvote, -1 สำหรับ Downvote

    class Meta:
        # ผู้ใช้ 1 คน โหวตได้ 1 ครั้งต่อ 1 รีวิว
        unique_together = (('user', 'review'),)

    def __str__(self):
        return f"Vote {self.vote_type} on Review {self.review.id} by {self.user.email}"


class Bookmark(models.Model):
    """ให้ผู้ใช้ bookmark รีวิวหรือรายวิชาที่สนใจ"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    
    # ผู้ใช้อาจจะ bookmark รีวิวที่เจาะจง หรือ bookmark ทั้งรายวิชา
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, related_name='bookmarked_by')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='bookmarked_by')

    class Meta:
        # A user can bookmark a specific review only once.
        # A user can bookmark a course (without a specific review) only once.
        # This handles both cases: bookmarking a review (review_id is not null)
        # and bookmarking a course (review_id is null).
        unique_together = ('user', 'review', 'course')
        
    def __str__(self):
        target = self.review if self.review else self.course.course_code
        return f"Bookmark by {self.user.email} for {target}"


class Report(models.Model):
    """บันทึกการรายงานรีวิวที่ไม่เหมาะสม"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_reports')
    comment = models.TextField()

    class Meta:
        # ผู้ใช้ 1 คน รายงานได้ 1 ครั้งต่อ 1 รีวิว
        unique_together = (('user', 'review'),)

    def __str__(self):
        return f"Report on Review {self.review.id} by {self.user.email}"