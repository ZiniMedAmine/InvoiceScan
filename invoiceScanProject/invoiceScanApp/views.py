from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import Id

def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Handle the single file
                single_file = form.cleaned_data['file']
                id_single = Id.objects.create(doc=single_file)
                id_single.save()
                response_message = "Single image with id " + str(id_single.pk) + " uploaded: " + str(id_single.doc)

                # Handle multiple files
                files = request.FILES.getlist('files')
                for uploaded_file in files:
                    id_multiple = Id.objects.create(doc=uploaded_file)
                    id_multiple.save()
                    response_message += "\nMultiple image with id " + str(id_multiple.pk) + " uploaded: " + str(id_multiple.doc)

                return HttpResponse(response_message)
            except Exception as e:
                return HttpResponse("Error: " + str(e))
    else:
        form = UploadFileForm()

    return render(request, "home.html", {'form': form})
