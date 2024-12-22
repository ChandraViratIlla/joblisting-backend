# jobs/urls.py

from django.urls import path, include  # Import include to include other apps' URLs

urlpatterns = [
    # Include the URLs from the joblisting app
    path('joblisting/', include('joblisting.urls')),  # Include joblisting URLs under 'joblisting/' path
]
