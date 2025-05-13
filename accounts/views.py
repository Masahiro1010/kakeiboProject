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
import random
import string

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

        return super().form_valid(form)

class LineLinkView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/link_link.html'

    # ✅ 重複しない連携コード（6桁）を生成する関数
    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(string.digits, k=6))
            if not UserProfile.objects.filter(link_code=code).exists():
                return code

    def get(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        # まだ連携済みでない場合はコードを発行
        if not profile.line_user_id and not profile.link_code:
            profile.link_code = self.generate_unique_code()
            profile.save()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.userprofile
        context['line_user_id'] = profile.line_user_id
        context['link_code'] = profile.link_code
        return context
    
class LinkSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/link_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['line_user_id'] = self.request.user.userprofile.line_user_id
        return context
