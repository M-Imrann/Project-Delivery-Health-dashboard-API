from django.urls import path
from .views import HealthDashboardAPI

urlpatterns = [
    path("project-health/", HealthDashboardAPI.as_view(), name="project-health"),
]
