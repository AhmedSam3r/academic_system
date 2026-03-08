from django.urls import path
from .views import (
    EnrollmentCreateView,
    EnrollmentStatsView,
)
urlpatterns = [
    path("import/", EnrollmentCreateView.as_view(), name="enroll_creation"),
    path("export/", EnrollmentStatsView.as_view(), name="enroll_stats"),
]
