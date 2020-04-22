from django import forms
from sync.models import *


class UploadForm(forms.Form):
    description = forms.CharField(max_length=255, required=True, help_text='Certificate Description')
    file = forms.FileField()

    class Meta:
        model = UploadZip
        fields = ('description', 'file')

