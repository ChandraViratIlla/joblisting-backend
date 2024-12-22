from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    posted_date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return self.title
# joblisting/models.py
from django.db import models

class Job(models.Model):
    job_id = models.CharField(max_length=255, unique=True)  # Unique job identifier
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField()
    posted_date = models.DateTimeField()
    
    def __str__(self):
        return self.title
