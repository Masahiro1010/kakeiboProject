from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from .views import LineLoginView, LineCallbackView

urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', DjangoLogoutView.as_view(), name='logout'),
    path('link-line/', views.LineLinkView.as_view(), name='link_line'),
    path('link-line/success/', views.LinkSuccessView.as_view(), name='link_success'),
    path("line/login/", LineLoginView.as_view(), name="line_login"),
    path("callback/", LineCallbackView.as_view(), name="line_callback"),
]

handler403 = 'accounts.views.csrf_failure'