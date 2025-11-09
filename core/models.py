from django.db import models

# Create your models here.


class Campus(models.Model):
    name = models.CharField(max_length=255)
    img_url = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name
    
    def get_model_name(self):
        return "Campus"
    
class RoomMSTeam(models.Model):
    name = models.CharField(max_length=255)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Professor(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    email = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    img_url = models.URLField(max_length=200, blank=True, null=True)
    room = models.ForeignKey(RoomMSTeam, on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    def get_model_name(self):
        return "Professor"

class Course(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField()
    credit = models.IntegerField(default=3)

    def __str__(self):
        return self.name
    
    def get_model_name(self):
        return "Course"

class Section(models.Model):
    # Changed from section_number to number to match search template logic
    number = models.CharField(max_length=6)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    room = models.ForeignKey(RoomMSTeam, on_delete=models.CASCADE)
    date_time = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    
    def get_model_name(self):
        return "Section"

    def __str__(self):
        return f"{self.course.name} - {self.professor.name}"