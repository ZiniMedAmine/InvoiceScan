from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    """File input that lets the browser send several files at once."""

    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Image field that validates every file of a multi-file upload."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        clean_one = super().clean
        if isinstance(data, (list, tuple)):
            return [clean_one(item, initial) for item in data]
        return [clean_one(data, initial)]


class UploadForm(forms.Form):
    """Form of the home page: one or more document images to scan."""

    files = MultipleImageField(required=True)
