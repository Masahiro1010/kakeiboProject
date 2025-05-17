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
from django.conf import settings
from django.views import View
import requests
from django.shortcuts import redirect
from django.contrib.auth.models import User
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
    
class LineLoginView(View):
    def get(self, request):
        url = (
            "https://access.line.me/oauth2/v2.1/authorize"
            f"?response_type=code"
            f"&client_id={settings.LINE_CHANNEL_ID}"
            f"&redirect_uri={settings.LINE_REDIRECT_URI}"
            f"&state=random"
            f"&scope=openid%20profile"
        )
        return redirect(url)


class LineCallbackView(View):
    def get(self, request):
        code = request.GET.get("code")
        token_url = "https://api.line.me/oauth2/v2.1/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINE_REDIRECT_URI,
            "client_id": settings.LINE_CHANNEL_ID,
            "client_secret": settings.LINE_CHANNEL_SECRET,
        }

        token_res = requests.post(token_url, headers=headers, data=data)
        token_data = token_res.json()

        access_token = token_data.get("access_token")
        profile_url = "https://api.line.me/v2/profile"
        profile_res = requests.get(profile_url, headers={"Authorization": f"Bearer {access_token}"})
        profile = profile_res.json()

        line_user_id = profile.get("userId")
        display_name = profile.get("displayName")

        # UserProfileからユーザーを取得または作成
        try:
            user_profile = UserProfile.objects.get(line_user_id=line_user_id)
            user = user_profile.user
        except UserProfile.DoesNotExist:
            # 新規作成（仮登録用ユーザー）
            user = User.objects.create(username=f"line_{line_user_id}")
            UserProfile.objects.create(user=user, line_user_id=line_user_id)

        login(request, user)
        return redirect("ledger")  # ログイン後の遷移先
    
from django.shortcuts import render

def csrf_failure(request, reason=""):
    return render(request, 'accounts/csrf_error.html', status=403)
