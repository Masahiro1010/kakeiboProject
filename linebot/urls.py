from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.LineWebhookView.as_view(), name='line_webhook'),
]