import re


def clean_text(text):
    """
    Standardizes text extracted from OCR.
    """
    if not text:
        return ""

    # 1. Replace multiple newlines/spaces with single space
    # (Exam questions often span multiple lines, we want them as one block)
    text = re.sub(r'\s+', ' ', text)

    # 2. Fix common OCR artifacts
    # (e.g., '1l' -> 'll', spaces before punctuation)
    text = re.sub(r'\s([?.!,"](?:\s|$))', r'\1', text)

    # 3. Strip leading/trailing whitespace
    return text.strip()


def is_valid_block(text, block_type):
    """
    Filters out noise (e.g. page numbers, empty headers).
    """
    if len(text) < 3:
        return False

    # Ignore purely numeric blocks unless they are specifically figures/tables
    if text.replace('.', '').isdigit() and block_type == "Text":
        return False

    return True
