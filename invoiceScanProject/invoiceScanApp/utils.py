import cv2
import pytesseract
import numpy as np
import re
from autocorrect import Speller
import pyarabic.araby as araby
import langid
import google.generativeai as genai
from django.conf import settings
import time
import os
from .global_variables import tunisian_names, universities, clubs, tech_words, companies, cities
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

#Gemini setup and configuration
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

#Preprocessing code
def preprocess_image(image_path):
    start_time = time.time()

    image = cv2.imread(image_path)
    height, width, _ = image.shape

    def auto_resize(image_path, target_width):

        height, width, _ = image.shape

        aspect_ratio = width / height

        target_height = int(target_width / aspect_ratio)

        resized_image = cv2.resize(image, (target_width, target_height))

        return resized_image

    

    Resizedimg=auto_resize(image_path,width*2)

    gray = cv2.cvtColor(Resizedimg, cv2.COLOR_BGR2GRAY)

    def noise_removal(img):
        kernel_size = (2,1)

        dilation_kernel = np.ones(kernel_size, np.uint8)
        img = cv2.dilate(img, dilation_kernel, iterations=1)

        erosion_kernel = np.ones(kernel_size, np.uint8)
        img = cv2.erode(img, erosion_kernel, iterations=1)

        closing_kernel = np.ones(kernel_size, np.uint8)
        img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, closing_kernel)

        return img

    def estimate_text_size(image):
        # Binarize the image
        thresh, binary_image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter potential character contours
        char_contours = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h
            if 0.2 < aspect_ratio < 1.5 and 5 < w < 20 and 5 < h < 30:
                char_contours.append(cnt)

        # Calculate average height if characters are found
        if char_contours:
            total_height = 0
            for cnt in char_contours:
                _, _, _, h = cv2.boundingRect(cnt)
                total_height += h
            return total_height / len(char_contours)
        else:
            return None

    def oddRound(x):
        """Ensures the returned value is an odd integer."""
        return 1 + 2 * round(x / 2)

    avg_char_height = estimate_text_size(noise_removal(gray))
    if avg_char_height is None:
        print("No text detected in image. Using default block size.")
        x = 75
        print("test case one x default value = ",x)
    else:
        height, _, _ = image.shape
        scaling_factor = height / avg_char_height
        x = oddRound(scaling_factor)
        print("test case two x calculated value = ",x)

    y = round(x / 10)

    def applyThresh(image, x):
        y = 2  # Starting value
        best_y = y
        best_ratio = 0

        while True:
            thresh = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, x, y-1)
            # Calculate foreground to background ratio
            foreground_pixels = cv2.countNonZero(thresh)
            background_pixels = image.size - foreground_pixels
            ratio = foreground_pixels / background_pixels

            # Update best y and ratio if current ratio is better
            if ratio > best_ratio:
                best_y = y
                best_ratio = ratio

            # Stop if ratio worsens significantly (potential over-thresholding)
            if ratio < 0.95 * best_ratio:
                break

            y += 1  # Increase y for next iteration
            print(y)
            pad_amount = 5
            thresh_padded = cv2.copyMakeBorder(thresh, pad_amount, pad_amount, pad_amount, pad_amount, cv2.BORDER_CONSTANT, value=255)

        return thresh_padded
    PreProcessed = applyThresh(noise_removal(gray), x)
    

    end_time = time.time()
    
    print("Preprocessing image took: {:.2f} seconds".format(end_time - start_time))

    return PreProcessed

#OCR Code 
def perform_ocr(preprocessed_image):
    start_time = time.time()

    text = pytesseract.image_to_string(preprocessed_image, config='--psm 12 --oem 1', lang='eng+french+ara')

    # # Exclude specific words from spell checking
    # words = text.split()
    # corrected_words = []
    # allowed_languages = {'en', 'fr', 'ar'}
    # excluded_words = tunisian_names | universities | clubs | tech_words | companies | cities 
    # for word in words:
    #     detected_lang, _ = langid.classify(word)
    #     detected_lang = detected_lang if detected_lang in ('en', 'fr', 'ar') else 'fr'
    #     lang_code = detected_lang[:2].lower()
    #     if lang_code in allowed_languages:
    #         if lang_code == 'ar':
    #             #spell = Speller(lang='ar')
    #             print("mezelt mal9itch solu lel aarbi (possible solutions : symspellpy + ar dictionary || autocorrect + new lang AR )")
    #             #corrected_word = spell(word)
    #             corrected_word = word
    #         else:
    #             if (word.lower() in excluded_words or ("@" in word.lower() and "." in word.lower())):
    #                 corrected_word = word
    #             else:
    #                 spell = Speller(lang=lang_code)
    #                 corrected_word = spell(word)

    #         corrected_words.append(corrected_word)

    # corrected_text = " ".join(corrected_words)
    #hedha ynahi l line breaks l zeydin
    cleaned_text = text.strip().replace("\n\n", "\n")
    #w hedha ynahi l espacet li wra baadhhom
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    #w hedha y5ali ken l chars w l nums w some special chars
    cleaned_text = re.sub(r"[^\w\s\-&\.\/%@+]", "", cleaned_text)

    end_time = time.time()
    print(cleaned_text)
    print("Performing OCR took: {:.2f} seconds".format(end_time - start_time))
    return cleaned_text

def organize_data(corrected_text):
    start_time = time.time()

    app_dir = os.path.dirname(os.path.abspath(__file__))  # Get app directory path
    prompt_file_path = os.path.join(app_dir, 'prompt.txt')

    with open(prompt_file_path, 'r', encoding='utf-8') as prompt_file:
        prompt_text = prompt_file.read()

    data = model.generate_content([prompt_text+corrected_text])
    
    end_time = time.time()

    print("Organizing data took: {:.2f} seconds".format(end_time - start_time))


    return data.text

