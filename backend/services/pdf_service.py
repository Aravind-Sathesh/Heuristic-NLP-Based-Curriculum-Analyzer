import fitz


def extract_text_from_pdf(pdf_path: str) -> str:
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
