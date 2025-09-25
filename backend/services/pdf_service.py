import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text content from a given PDF file.

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        str: A single string containing all the text from the PDF.
             Returns an empty string if the file is not found or is empty.
    """
    try:
        document = fitz.open(pdf_path)
        full_text = ""
        for page in document:
            full_text += page.get_text()

        document.close()
        return full_text
    except Exception as e:
        print(f"Error processing PDF file at {pdf_path}: {e}")
        return ""
