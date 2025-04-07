from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django.contrib.auth.views import LoginView as DjangoLoginView
from .forms import LineLinkForm
from .models import UserProfile

class SignupView(CreateView):
    form_class = UserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('login')

class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'

class LineLinkView(LoginRequiredMixin, FormView):
    template_name = 'accounts/link_line.html'
    form_class = LineLinkForm
    success_url = reverse_lazy('link_success')

    def form_valid(self, form):
        line_id = form.cleaned_data['line_user_id']
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        profile.line_user_id = line_id
        profile.save()
        return super().form_valid(form)
