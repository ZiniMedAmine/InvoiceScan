import json
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
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
        files = request.FILES.getlist('files')

        if not files:
            return HttpResponseBadRequest("No files were uploaded.")

        results = []
        for uploaded_file in files:
            id_image = Img.objects.create(ref=uploaded_file)
            id_image.save()
            image_path = id_image.ref.path

            preprocessed_image = preprocess_image(image_path)
            preprocessed_image_filename = f"preprocessed_{id_image.pk}.jpg"
            preprocessed_image_path = os.path.join(settings.MEDIA_ROOT, 'Preprocessed', preprocessed_image_filename)
            cv2.imwrite(preprocessed_image_path, preprocessed_image)

            extracted_text = perform_ocr(preprocessed_image)
            organized_text = organize_data(extracted_text)

            # Extracting image name and document type
            image_name = id_image.ref.name.split('/')[-1]
            document_type = organized_text.split('\n')[0].replace('Document Type', '')
            document_type = re.sub(r'[^a-zA-Z\s]', '', document_type)

            lines = organized_text.splitlines()
            if lines:  
                organized_text = '\n'.join(lines[2:-1])
            
            organized_text = '\n'.join(organized_text.split('\n')[1:])

            # Save preprocessed image and extracted text to the database
            id_image.preprocessed_ref = f'preprocessed/{preprocessed_image_filename}'
            id_image.extracted_text = organized_text
            id_image.save()

            results.append({
                'image_name': image_name,
                'document_type': document_type,
                'text': organized_text,
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

        exported_files = []
        for format in formats:
            if format == 'json':
                matching_files = [f for f in os.listdir(settings.OUTPUT_ROOT) if f.endswith('.json')]
            elif format == 'csv':
                matching_files = [f for f in os.listdir(settings.OUTPUT_ROOT) if f.endswith('.csv')]
            elif format == 'word':
                matching_files = [f for f in os.listdir(settings.OUTPUT_ROOT) if f.endswith('.txt')]

            for file in matching_files:
                source_path = os.path.join(settings.OUTPUT_ROOT, file)
                destination_path = os.path.join(settings.MEDIA_ROOT, 'History', file)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.move(source_path, destination_path)

                # Extract image name from file name
                image_name, _ = os.path.splitext(file)

                # Get the corresponding Img instance using the image name
                try:
                    img_instance = Img.objects.get(ref__contains=image_name)
                except Img.DoesNotExist:
                    img_instance = None

                # Create ExportedFile instance linked to Img instance
                exported_file = ExportedFile(format=format, file=destination_path, img_id=img_instance)
                exported_file.save()
                exported_files.append((file, format))

        zip_file_path = os.path.join(settings.OUTPUT_ROOT, 'exported_files.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for filename, file_format in exported_files:
                zipf.write(os.path.join(settings.MEDIA_ROOT, 'History', filename), arcname=filename)

        with open(zip_file_path, 'rb') as f:
            response = HttpResponse(f, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=exported_files.zip'

        return response
    else:
        return JsonResponse({'status': 'error'}, status=400)
