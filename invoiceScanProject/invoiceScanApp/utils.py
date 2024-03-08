import cv2
import pytesseract

def preprocess_image(image_path):
    """Preprocesses an image to enhance OCR accuracy."""

    img = cv2.imread(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    adaptive_thresh = cv2.adaptiveThreshold(
        gray , 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 7, 2
    )

    return adaptive_thresh

def perform_ocr(preprocessed_image, config='--psm 7'):
    """Performs OCR on a preprocessed image."""

    text = pytesseract.image_to_string(preprocessed_image, config=config)
    return text