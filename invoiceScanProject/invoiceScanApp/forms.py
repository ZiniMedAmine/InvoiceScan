from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(required=True, label='Select Image')

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.content_type.startswith('image/'):
            raise forms.ValidationError('Only image files are allowed.')
        
        return file