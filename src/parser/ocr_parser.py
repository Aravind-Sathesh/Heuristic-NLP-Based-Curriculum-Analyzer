"""
OCR utility parser for extracting text from images and scanned PDFs.
This version is primarily used as a fallback for scanned syllabi and provides
the core is_scanned_pdf detection function for the entire application.
"""

import fitz
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path


def deskew_image(image_array):
    """Detects and corrects the skew of a text image using OpenCV."""
    try:
        gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = image_array.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image_array, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
    except Exception:
        # If deskewing fails, return the original image array
        return image_array


def preprocess_image_for_ocr(image):
    """
    Preprocesses a PIL Image to improve OCR accuracy.
    Includes automatic deskewing and binarization.
    """
    try:
        img_array = np.array(image.convert('RGB'))
        deskewed_array = deskew_image(img_array)
        img_gray = cv2.cvtColor(deskewed_array, cv2.COLOR_BGR2GRAY)
        _, binary_img = cv2.threshold(
            img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(binary_img)
    except Exception as e:
        print(
            f"Warning: Image preprocessing failed. Using original image. Error: {e}")
        return image


def is_scanned_pdf(pdf_path, text_threshold=100):
    """
    Detects if a PDF is scanned (image-based) or has native, extractable text.
    A PDF is considered scanned if the character count on its first few pages is very low.
    """
    try:
        doc = fitz.open(pdf_path)
        pages_to_check = min(3, len(doc))
        if pages_to_check == 0:
            return False  # Empty PDF
        text_pages = 0
        for i in range(pages_to_check):
            page = doc.load_page(i)
            if len(page.get_text().strip()) > text_threshold:
                text_pages += 1
        doc.close()
        return text_pages < (pages_to_check / 2.0)
    except Exception as e:
        print(f"Error detecting PDF type: {e}. Defaulting to non-scanned.")
        return False


def extract_text_from_image(image):
    """Extracts text from a single PIL Image using Tesseract."""
    try:
        processed_image = preprocess_image_for_ocr(image)
        config = '--psm 3'  # Automatic page segmentation
        text = pytesseract.image_to_string(
            processed_image, lang='eng', config=config).strip()
        return text
    except Exception as e:
        print(f"Error during Tesseract OCR processing: {e}")
        return ""


def pdf_to_text_ocr(pdf_path, dpi=300):
    """Main function to extract text from a PDF using the Tesseract OCR pipeline."""
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        full_text = [extract_text_from_image(img) for img in images]
        return "\n\n--- Page Break ---\n\n".join(full_text)
    except Exception as e:
        print(f"Error converting PDF to images for OCR: {e}")
        return ""
