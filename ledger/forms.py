from django import forms
from .models import TemplateItem

class TemplateRecordForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=TemplateItem.objects.none(),
        label='テンプレート',
    )
    quantity = forms.IntegerField(min_value=1, label='個数')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # ログインユーザーを受け取る
        super().__init__(*args, **kwargs)
        self.fields['template'].queryset = TemplateItem.objects.filter(user=user)