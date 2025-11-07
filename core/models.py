from django.db import models

# Create your models here.


class Campus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class RoomMSTeam(models.Model):
    name = models.CharField(max_length=255)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Professor(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Course(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    room = models.ForeignKey(RoomMSTeam, on_delete=models.CASCADE)
    date_time = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.course.name} - {self.professor.name}"