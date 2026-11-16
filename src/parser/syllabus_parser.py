"""
Parser for converting a syllabus PDF into structured text (Markdown).
"""

import pymupdf4llm
from src.parser.ocr_parser import pdf_to_text_ocr, is_scanned_pdf


def pdf_to_markdown(pdf_path):
    """
    Converts a PDF to markdown text.
    This function automatically detects if the PDF is scanned and applies OCR if necessary.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        str: Markdown formatted text extracted from the PDF.
    """
    if is_scanned_pdf(pdf_path):
        print(
            f"Info: Scanned PDF detected for syllabus '{pdf_path}'. Using Tesseract OCR.")
        return pdf_to_text_ocr(pdf_path)
    else:
        print(
            f"Info: Native text PDF detected for syllabus '{pdf_path}'. Using pymupdf4llm.")
        md_text = pymupdf4llm.to_markdown(pdf_path)
        return md_text
