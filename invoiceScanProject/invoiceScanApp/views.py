from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from django.core.exceptions import ValidationError
from .models import Id

def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Handle the single file
                file = form.cleaned_data['file']
                id = Id.objects.create(doc=file)
                id.save()
                response_message = "the image with id " + str(id.pk) + " uploaded this image : " + str(id.doc)

                # Handle multiple files
                files = request.FILES.getlist('files')
                for uploaded_file in files:
                    id = Id.objects.create(doc=uploaded_file)
                    id.save() #apparament lmochkla fl id model
                    response_message += "\nthe image with id " + str(id.pk) + " uploaded this image : " + str(id.doc)

                return HttpResponse(response_message)
            except ValidationError as e:
                form.add_error('file', e)
    else:
        form = UploadFileForm()

    return render(request, "home.html", {'form': form})
