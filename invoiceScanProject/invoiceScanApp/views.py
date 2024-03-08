from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import Id
from .utils import preprocess_image, perform_ocr
import cv2
import os
def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        

                # Handle the single file

        files = request.FILES.getlist('files')
        for uploaded_file in files:
                    id_image = Id.objects.create(doc=uploaded_file)
                    id_image.save()
                    response_message = "\n image with id " + str(id_image.pk) + " uploaded: " + str(id_image.doc)
                    image_path = id_image.doc.path

                    preprocessed_image = preprocess_image(image_path)
                    preprocessed_image_filename = f"preprocessed_{id_image.pk}.jpg"  # Generate unique filename
                    preprocessed_image_path = os.path.join(settings.MEDIA_ROOT, preprocessed_image_filename)  # Construct save path
                    cv2.imwrite(preprocessed_image_path, preprocessed_image)
 
        return HttpResponse(response_message)

    else:
        form = UploadFileForm()

    return render(request, "home.html", {'form': form})