import pytesseract
import numpy as np
from src.parser.cleaner import clean_text, is_valid_block


def extract_text_from_layout(image_np, layout):
    extracted_data = []

    # Safe shape unpacking (Works for both RGB and Grayscale)
    h, w = image_np.shape[:2]

    # Fallback
    if len(layout) == 0:
        print("⚠️ No layout detected. Running Fallback OCR.")
        raw_text = pytesseract.image_to_string(image_np, lang='eng')
        cleaned = clean_text(raw_text)
        if cleaned:
            extracted_data.append({
                "type": "Text",
                "text": cleaned,
                "confidence": 1.0,
                "coordinates": [0, 0, w, h]
            })
        return extracted_data

    layout.sort(key=lambda b: (b.coordinates[1], b.coordinates[0]))

    for block in layout:
        coords = np.array(block.coordinates).astype(int)
        x1, y1, x2, y2 = coords

        pad = 5
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(w, x2 + pad)
        y2 = min(h, y2 + pad)

        segment = image_np[y1:y2, x1:x2]

        if block.type in ["Text", "Title", "List", "Table"]:
            raw_text = pytesseract.image_to_string(
                segment, lang='eng', config='--psm 6 --oem 1')
            cleaned = clean_text(raw_text)

            if is_valid_block(cleaned, block.type):
                extracted_data.append({
                    "type": block.type,
                    "text": cleaned,
                    "confidence": block.score,
                    "coordinates": [x1, y1, x2, y2]
                })

        elif block.type == "Figure":
            extracted_data.append({
                "type": "Figure",
                "text": "[IMAGE_CONTENT]",
                "image_crop": segment,
                "coordinates": [x1, y1, x2, y2]
            })

    return extracted_data
