import cv2
import pytesseract

def preprocess_image(image_path):
    """Preprocesses an image to enhance OCR accuracy."""

    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return gray

def perform_ocr(preprocessed_image, config='--psm 7'):
    """Performs OCR on a preprocessed image."""

    text = pytesseract.image_to_string(preprocessed_image, config=config)
    return text
