import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 
def preprocess_image(image_path):
    """Preprocesses an image to enhance OCR accuracy."""

    img = cv2.imread(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    adaptive_thresh = cv2.adaptiveThreshold(
        gray , 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 7,2
    )

    return adaptive_thresh

def perform_ocr(preprocessed_image, config='--psm 12 --oem 1 '):
    """Performs OCR on a preprocessed image."""

    text = pytesseract.image_to_string(preprocessed_image, config=config)
    return text
#--tessedit_char_whitelist: Restrict character recognition to a specific set (e.g., --tessedit_char_whitelist ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789).
#--tesssedit_char_blacklist: Exclude specific characters from recognition.
#--oem_lstm_mode: Control LSTM engine mode (0: standard, 1: alternative).
#--image_denoise_noise_norm: Adjust image denoising level (0.0 to 1.0).