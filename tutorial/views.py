from django.shortcuts import render
from django.views.generic import TemplateView

class TutorialView(TemplateView):
    template_name = "tutorial/tutorial.html"

class SignupView(TemplateView):
    template_name = "tutorial/signup.html"

class TutorialTemplateView(TemplateView):
    template_name = "tutorial/templates.html"
