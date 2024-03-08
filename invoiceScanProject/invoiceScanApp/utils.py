import cv2
import pytesseract

def preprocess_image(image_path):
    """Preprocesses an image to enhance OCR accuracy."""

    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur for smoothing without excessive blurring
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Apply adaptive thresholding
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    return adaptive_thresh

def perform_ocr(preprocessed_image, config='--psm 7'):
    """Performs OCR on a preprocessed image."""

    text = pytesseract.image_to_string(preprocessed_image, config=config)
    return text