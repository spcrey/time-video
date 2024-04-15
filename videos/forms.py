from django import forms

# form: UploadVideoForm, to upload video

class VideoUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'custom-file-input', "multi": False}))
    