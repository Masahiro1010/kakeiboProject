from django.shortcuts import render
from django.views.generic import TemplateView

class TutorialView(TemplateView):
    template_name = "tutorial/tutorial.html"

class SignupView(TemplateView):
    template_name = "tutorial/signup.html"

class TutorialTemplateView(TemplateView):
    template_name = "tutorial/templates.html"

class TutorialRecordView(TemplateView):
    template_name = "tutorial/record.html"

class TutorialGraphView(TemplateView):
    template_name = "tutorial/graph.html"

class TutorialLineView(TemplateView):
    template_name = "tutorial/line.html"