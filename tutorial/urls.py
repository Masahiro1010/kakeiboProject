from django.urls import path
from . import views

urlpatterns = [
    path("", views.TutorialView.as_view(), name="tutorial"),
    path("signup/", views.SignupView.as_view(), name="tutorial_signup"),
    path("templates/", views.TutorialTemplateView.as_view(), name="tutorial_template"),
    path("record/", views.TutorialRecordView.as_view(), name="tutorial_record"),
    path("graph/", views.TutorialGraphView.as_view(), name="tutorial_graph"),
    path("line/", views.TutorialLineView.as_view(), name="tutorial_line"),
    path("first/", views.FirstView.as_view(), name="tutorial_first"),
]