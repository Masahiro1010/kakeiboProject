from django import forms

class LineLinkForm(forms.Form):
    line_user_id = forms.CharField(label='LINEユーザーID', max_length=64)