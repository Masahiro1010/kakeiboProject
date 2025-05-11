from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django.contrib.auth.views import LoginView as DjangoLoginView
from .forms import LineLinkForm
from .models import UserProfile
from django.views.generic import TemplateView
from django.contrib.auth import login

class SignupView(CreateView):
    form_class = UserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('login')

class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')

        if remember_me:
            self.request.session.set_expiry(60 * 10 * 1 * 1)  # 10分間
        else:
            self.request.session.set_expiry(0)  # ブラウザ閉じたらログアウト

        login(self.request, form.get_user())

        return super().form_valid(form)

class LineLinkView(LoginRequiredMixin, FormView):
    template_name = 'accounts/link_link.html'
    form_class = LineLinkForm
    success_url = reverse_lazy('link_success')

    def form_valid(self, form):
        line_id = form.cleaned_data['line_user_id']
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        profile.line_user_id = line_id
        profile.save()
        return super().form_valid(form)
    
class LinkSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/link_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['line_user_id'] = self.request.user.userprofile.line_user_id
        return context
