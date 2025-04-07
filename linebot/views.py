import os
import json
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

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
            return HttpResponseForbidden()

        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                user_message = event.message.text

                # ここにメッセージ解析＆記録ロジックを後で入れる
                reply = f"受け取りました！「{user_message}」ですね。"

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply)
                )

        return HttpResponse("OK")

# Create your views here.
