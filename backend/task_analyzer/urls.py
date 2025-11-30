from django.urls import path, include
from . import views 

urlpatterns = [
    path("", views.home),          # root page
    path("api/", include("tasks.urls")),  
]