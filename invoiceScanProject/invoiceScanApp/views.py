from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import Id
from .utils import preprocess_image, perform_ocr, organize_data
import cv2
import os

def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        results = []

        files = request.FILES.getlist('files')
        for uploaded_file in files:
            id_image = Id.objects.create(doc=uploaded_file)
            id_image.save()
            response_message = "\n image with id " + str(id_image.pk) + " uploaded: " + str(id_image.doc)
            image_path = id_image.doc.path
            preprocessed_image = preprocess_image(image_path)
            preprocessed_image_filename = f"preprocessed_{id_image.pk}.jpg" 
            preprocessed_image_path = os.path.join(settings.MEDIA_ROOT, preprocessed_image_filename)
            cv2.imwrite(preprocessed_image_path, preprocessed_image)
            extracted_text = perform_ocr(preprocessed_image)
            text = organize_data(extracted_text)
            results.append(f"Image: {id_image.doc.name}<br>Extracted Text: {text}")

            #extracting the results in a text file
            results_dir = settings.OUTPUT_ROOT
            filename = f"Results_{id_image.pk}.txt"
            with open(os.path.join(results_dir, filename), 'w', encoding='utf-8') as f:
                f.write(text)

        return HttpResponse("<br>".join(results), content_type="text/html; charset=utf-8")

    else:
        form = UploadFileForm() 

    return render(request, "home.html", {'form': form})