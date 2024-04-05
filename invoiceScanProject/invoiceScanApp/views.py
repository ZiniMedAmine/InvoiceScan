import json
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpRequest
from .forms import UploadFileForm
from .models import Id
from .utils import preprocess_image, perform_ocr, organize_data
import cv2
import os
import re

results = []

def home(request):
  if request.method == 'POST':
    form = UploadFileForm(request.POST, request.FILES)
    results = []

    files = request.FILES.getlist('files')
    for uploaded_file in files:
      id_image = Id.objects.create(doc=uploaded_file)
      id_image.save()
      image_path = id_image.doc.path

      preprocessed_image = preprocess_image(image_path)
      preprocessed_image_filename = f"preprocessed_{id_image.pk}.jpg"
      preprocessed_image_path = os.path.join(settings.MEDIA_ROOT, preprocessed_image_filename)
      cv2.imwrite(preprocessed_image_path, preprocessed_image)

      extracted_text = perform_ocr(preprocessed_image)
      text = organize_data(extracted_text)

      # Extracting image name and document type
      image_name = id_image.doc.name.split('/')[-1]
      document_type = text.split('\n')[0].replace('Document Type', '').strip()
      document_type = re.sub(r'[^a-zA-Z]', '', document_type)
        
      text = '\n'.join(text.split('\n')[3:])
      results.append({
          'image_name': image_name,
          'document_type': document_type,
          'text': text,  # Store initial text for comparison later
      })

    return render(request, "selectFormat.html", {'results': results})
  else:
    form = UploadFileForm()

  return render(request, "home.html", {'form': form})


def save_edited_text(request):
  
  if request.method == 'POST':
    # Access edited text data from request body (assuming JSON format)
    edited_results = json.loads(request.body)

    output_directory = settings.OUTPUT_ROOT

    for edited_result in edited_results:
        # Extract image name and text
        image_name = edited_result['image_name']
        text = edited_result['text']

        # Construct the file path
        file_path = os.path.join(output_directory, f"{image_name}.txt")

            # Write the text content to the file
        with open(file_path, 'w') as file:
            file.write(text)


    return JsonResponse({'status': 'success'})  # Send success response
  else:
    return JsonResponse({'status': 'error'}, status=400)  # Handle invalid requests