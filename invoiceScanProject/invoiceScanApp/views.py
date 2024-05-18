import json
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpRequest
from .forms import UploadFileForm
from .models import Img, ExportedFile
from .etl import parse_text_to_csv, write_to_csv ,  json_to_text
from .utils import preprocess_image, perform_ocr, organize_data
import cv2
import os
import re
import shutil
import zipfile


results = []

def home(request):
  if request.method == 'POST':
    form = UploadFileForm(request.POST, request.FILES)
    results = []

    files = request.FILES.getlist('files')

    if not files:
        return HttpResponseBadRequest("No files were uploaded.")
    
    for uploaded_file in files:
      id_image = Img.objects.create(ref=uploaded_file)
      id_image.save()
      image_path = id_image.ref.path

      preprocessed_image = preprocess_image(image_path)
      preprocessed_image_filename = f"preprocessed_{id_image.pk}.jpg"
      preprocessed_image_path = os.path.join(settings.MEDIA_ROOT, preprocessed_image_filename)
      cv2.imwrite(preprocessed_image_path, preprocessed_image)

      extracted_text = perform_ocr(preprocessed_image)
      text = organize_data(extracted_text)

      # Extracting image name and refument type
      image_name = id_image.ref.name.split('/')[-1]
      document_type = text.split('\n')[0].replace('Document Type', '')
      document_type = re.sub(r'[^a-zA-Z\s]', '', document_type)
      
      lines = text.splitlines()  # Split text into a list of lines
      if lines:  # Check if there are any lines (handle empty text)
        text = '\n'.join(lines[2:-1])  # Join lines from index 1 (excluding first) to -1 (excluding last)
      
      text = '\n'.join(text.split('\n')[1:])

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

            # Construct the file paths
            json_file_path = os.path.join(output_directory, f"{image_name}.json")
            text_file_path = os.path.join(output_directory, f"{image_name}.txt")
            csv_file_path = os.path.join(output_directory, f"{image_name}.csv")

            # Write the edited text to JSON file
            with open(json_file_path, 'w', encoding='utf-8') as file:
                file.write(text)

            # Convert JSON to CSV and save the text content to a text file
            parsed_data = parse_text_to_csv(json_file_path)
            if parsed_data:
                write_to_csv(parsed_data, csv_file_path)
                # Convert JSON to text and save to a Word document
                json_to_text(parsed_data[1], text_file_path)

        return JsonResponse({'status': 'success'})  # Send success response
    else:
        return JsonResponse({'status': 'error'}, status=400)  # Handle invalImg requests


def export_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        formats = data.get('formats', [])

        output_directory = settings.OUTPUT_ROOT
        history_directory = settings.HISTORY_ROOT

        exported_files = []

        with zipfile.ZipFile(os.path.join(output_directory, 'exported_data.zip'), 'w') as zipf:
            for format in formats:
                if format == 'json':
                    json_files = [f for f in os.listdir(output_directory) if f.endswith('.json')]
                    for file in json_files:
                        json_filename = os.path.splitext(file)[0] + '.json'
                        zipf.write(os.path.join(output_directory, file), arcname=json_filename)
                        exported_files.append((json_filename, 'json'))

                elif format == 'csv':
                    csv_files = [f for f in os.listdir(output_directory) if f.endswith('.csv')]
                    for file in csv_files:
                        zipf.write(os.path.join(output_directory, file), file)
                        exported_files.append((file, 'csv'))

                elif format == 'word':
                    word_files = [f for f in os.listdir(output_directory) if f.endswith('.txt')]
                    for file in word_files:
                        word_filename = os.path.splitext(file)[0] + '.doc'
                        zipf.write(os.path.join(output_directory, file), arcname=word_filename)
                        exported_files.append((word_filename, 'word'))

            zipf.close()

        # Save information about exported files to the database
        for filename, file_format in exported_files:
            exported_file = ExportedFile(file=os.path.join(history_directory, filename), format=file_format)
            exported_file.save()

        # Return a response with the zip file
        with open(os.path.join(output_directory, 'exported_data.zip'), 'rb') as f:
            response = HttpResponse(f, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=exported_data.zip'

        # Move files to the history directory
        for filename in os.listdir(output_directory):
            source_path = os.path.join(output_directory, filename)
            destination_path = os.path.join(history_directory, filename)
            shutil.move(source_path, destination_path)

        return response

    else:
        return JsonResponse({'status': 'error'}, status=400)