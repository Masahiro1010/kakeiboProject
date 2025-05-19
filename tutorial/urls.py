from django.urls import path
from . import views

urlpatterns = [
    path("", views.TutorialView.as_view(), name="tutorial"),
    path("signup/", views.SignupView.as_view(), name="tutorial_signup"),
]