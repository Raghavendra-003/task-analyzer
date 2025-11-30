from django.urls import path
from . import views

urlpatterns = [
    path("tasks/analyze/", views.analyze_tasks),
]