from services.pdf_service import extract_text_from_pdf
from services.llm_service import call_gemini_api


def load_prompt_from_md(filepath):
    """Loads a prompt template from a Markdown file."""
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except FileNotFoundError:
        raise RuntimeError(f"ERROR: Prompt file not found at '{filepath}'.")


def analyze_curriculum_from_pdf(pdf_path: str):
    """
    The core logic for Phase 1: Extracts text from a PDF, builds the prompt,
    and gets the analysis.
    """
    curriculum_text = extract_text_from_pdf(pdf_path)
    if not curriculum_text:
        return {"status": "error", "reason": "Could not extract text from the curriculum PDF."}

    # The prompt path is relative to the root of the backend folder
    prompt_template = load_prompt_from_md("prompts/curriculum_parser.md")
    final_prompt = prompt_template.format(curriculum_text=curriculum_text)

    analysis_result = call_gemini_api(final_prompt)
    return analysis_result


def analyze_qpaper_from_pdf(pdf_path: str):
    """
    The core logic for Phase 2: Extracts questions from a PDF using text-only analysis.
    """
    print("Analyzing question paper PDF:", pdf_path)
    qpaper_text = extract_text_from_pdf(pdf_path)
    if not qpaper_text:
        return {"status": "error", "reason": "Could not extract text from the question paper PDF."}

    prompt_template = load_prompt_from_md("prompts/qpaper_parser.md")
    final_prompt = prompt_template.format(page_text=qpaper_text)

    analysis_result = call_gemini_api(final_prompt)
    return analysis_result
