from django import forms

class UploadFileForm(forms.Form):
    file = forms.ImageField(required=True, label='Select Image')