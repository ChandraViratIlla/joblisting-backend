# joblisting/urls.py

from django.urls import path
from . import views  # Import views from the current app

urlpatterns = [
    # Define the URL patterns for the joblisting app
    path('', views.index, name='index'),  # Home page or job listing page
    path('job/<int:id>/', views.job_detail, name='job_detail'),  # Job detail page by ID
]
