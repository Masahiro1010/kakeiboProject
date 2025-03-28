from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView as DjangoLogoutView

urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', DjangoLogoutView.as_view(next_page='login'), name='logout'),
]