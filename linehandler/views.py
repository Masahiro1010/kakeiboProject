import os
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from ledger.models import TemplateItem, Record
from accounts.models import UserProfile  # ← ユーザー紐づけ用
from .utils import parse_template_message  # メッセージ解析用（utils.py）

# LINEチャンネルのトークンとシークレット
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
parser = WebhookParser(os.environ.get("LINE_CHANNEL_SECRET"))

@method_decorator(csrf_exempt, name='dispatch')
class LineWebhookView(View):
    def post(self, request, *args, **kwargs):
        signature = request.headers.get("X-Line-Signature")
        body = request.body.decode("utf-8")

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden("Invalid signature")

        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                user_message = event.message.text
                line_user_id = event.source.user_id  # LINEのユーザーID

                # 1. LINEユーザーをDjangoユーザーに紐づけ
                try:
                    user_profile = UserProfile.objects.get(line_user_id=line_user_id)
                    user = user_profile.user
                except UserProfile.DoesNotExist:
                    reply_text = "このLINEアカウントは未登録です。WebでログインしてLINEと連携してください。"
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply_text)
                    )
                    return HttpResponse("Unauthorized")

                # 2. メッセージをテンプレート入力として解析
                parsed = parse_template_message(user_message)

                if parsed:
                    name = parsed['name']
                    quantity = parsed['quantity']

                    try:
                        template = TemplateItem.objects.get(user=user, name=name)
                        total = template.price * quantity

                        Record.objects.create(
                            user=user,
                            title=f"{template.name} × {quantity}",
                            amount=total,
                            item_type=template.item_type
                        )
                        reply_text = f"「{template.name}」を{quantity}個、{total}円で記録しました！"

                    except TemplateItem.DoesNotExist:
                        reply_text = f"「{name}」はテンプレートに登録されていません。"

                else:
                    reply_text = "テンプレート形式で送ってください（例：弁当 2個）"

                # 3. LINEに返信
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )

        return HttpResponse("OK")

# Create your views here.
