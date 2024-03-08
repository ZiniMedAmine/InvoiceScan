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
        single_file = request.FILES['file']
        id_single = Id.objects.create(doc=single_file)
        id_single.save()
        response_message = "\nSingle image with id " + str(id_single.pk) + " uploaded: " + str(id_single.doc)
        image_path = id_single.doc.path
                #preprocessing the image and saving it
        preprocessed_image = preprocess_image(image_path)
        preprocessed_image_filename = f"preprocessed_{id_single.pk}.jpg"  # Generate unique filename
        preprocessed_image_path = os.path.join(settings.MEDIA_ROOT, preprocessed_image_filename)  # Construct save path
        cv2.imwrite(preprocessed_image_path, preprocessed_image)

#                extracted_text = perform_ocr(preprocessed_image)
#                print(extracted_text)

        files = request.FILES.getlist('files')
        for uploaded_file in files:
                    id_multiple = Id.objects.create(doc=uploaded_file)
                    id_multiple.save()
                    response_message += "\nMultiple image with id " + str(id_multiple.pk) + " uploaded: " + str(id_multiple.doc)

        return HttpResponse(response_message)

    else:
        form = UploadFileForm()

    return render(request, "home.html", {'form': form})