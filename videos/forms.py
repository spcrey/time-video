from django import forms

# form: UploadVideoForm, to upload video

class UploadVideoForm(forms.Form):
    file = forms.FileField()