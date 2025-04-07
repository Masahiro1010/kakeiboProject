import os
import re
from django.http import HttpResponse, HttpResponseForbidden
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from ledger.models import Record, TemplateItem
from accounts.models import UserProfile

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
                message = event.message.text.strip()
                user_id = event.source.user_id

                try:
                    profile = UserProfile.objects.get(line_user_id=user_id)
                    user = profile.user
                except UserProfile.DoesNotExist:
                    reply = TextSendMessage(text="このLINEアカウントは未登録です。\nWebでログインしてLINE連携してください。")
                    line_bot_api.reply_message(event.reply_token, reply)
                    return HttpResponse("OK")

                # 全角・半角スペースに対応
                parts = re.split(r'[\s\u3000]+', message)

                reply_text = ""

                # 2語ならテンプレート入力
                if len(parts) == 2:
                    template_name, quantity_str = parts
                    if quantity_str.isdigit():
                        try:
                            template = TemplateItem.objects.get(user=user, name=template_name)
                            quantity = int(quantity_str)
                            Record.objects.create(
                                user=user,
                                title=f"{template.name} × {quantity}",
                                amount=template.price * quantity,
                                item_type=template.item_type,
                            )
                            reply_text = f"✅ テンプレート「{template.name}」を{quantity}個登録しました！"
                        except TemplateItem.DoesNotExist:
                            reply_text = f"「{template_name}」というテンプレートは見つかりませんでした。"

                # 3語なら個別入力
                elif len(parts) == 3:
                    title, amount_str, item_type_text = parts
                    if amount_str.isdigit() and item_type_text in ['支出', '収入']:
                        item_type = 'expense' if item_type_text == '支出' else 'income'
                        Record.objects.create(
                            user=user,
                            title=title,
                            amount=int(amount_str),
                            item_type=item_type,
                        )
                        reply_text = f"✅ 「{title}」を{amount_str}円（{item_type_text}）として登録しました！"
                    else:
                        reply_text = "形式が間違っているようです。\n「タイトル 金額 支出or収入」の形にしてください。"

                else:
                    # フォーマットミス or その他メッセージ
                    reply_text = (
                        "⚠️ メッセージ形式が認識できませんでした。\n\n"
                        "🟢 テンプレート入力（2語）：\n"
                        "例）水 2\n\n"
                        "🟡 個別入力（3語）：\n"
                        "例）昼ごはん 900 支出\n\n"
                        "※ スペースは半角でも全角でもOKです。"
                    )

                # LINEに返信
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )

        return HttpResponse("OK")

# Create your views here.
