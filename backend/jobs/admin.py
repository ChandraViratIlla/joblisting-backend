from django.contrib import admin
from .models import Job

if not admin.site.is_registered(Job):
    admin.site.register(Job)
