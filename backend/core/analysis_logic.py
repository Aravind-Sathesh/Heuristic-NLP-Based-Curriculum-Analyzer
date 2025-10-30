from services.pdf_service import extract_text_from_pdf
from services.llm_service import call_gemini_api, call_gemini_api_with_images
from services.image_service import convert_pdf_pages_to_images


def load_prompt_from_md(filepath):
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except FileNotFoundError:
        raise RuntimeError(f"ERROR: Prompt file not found at '{filepath}'.")


def analyze_curriculum_from_pdf(pdf_path: str):
    curriculum_text = extract_text_from_pdf(pdf_path)
    if not curriculum_text:
        return {"status": "error", "reason": "Could not extract text from the curriculum PDF."}

    prompt_template = load_prompt_from_md("prompts/curriculum_parser.md")
    final_prompt = prompt_template.format(curriculum_text=curriculum_text)

    analysis_result = call_gemini_api(final_prompt)
    return analysis_result


def analyze_qpaper_from_pdf(pdf_path: str, curriculum_topics: list = None):
    """
    Analyze question paper using text extraction (traditional method).
    Best for text-heavy papers without complex diagrams.
    """
    qpaper_text = extract_text_from_pdf(pdf_path)
    if not qpaper_text:
        return {"status": "error", "reason": "Could not extract text from the question paper PDF."}

    prompt_template = load_prompt_from_md("prompts/qpaper_parser.md")

    if curriculum_topics:
        topics_list = "\n".join([f"- {topic}" for topic in curriculum_topics])
        final_prompt = prompt_template.format(
            page_text=qpaper_text,
            curriculum_topics=topics_list
        )
    else:
        final_prompt = prompt_template.format(
            page_text=qpaper_text,
            curriculum_topics="No curriculum topics provided. Infer topics from question content."
        )

    analysis_result = call_gemini_api(final_prompt)
    return analysis_result


def analyze_qpaper_from_pdf_images(pdf_path: str, curriculum_topics: list = None):
    """
    Analyze question paper using image-based vision analysis.
    Best for papers with diagrams, graphs, charts, or complex visual elements.
    Converts each PDF page to an image and uses Gemini Vision API.
    """
    try:
        print("🖼️  Converting PDF pages to images...")
        page_images = convert_pdf_pages_to_images(pdf_path, dpi=200)

        if not page_images:
            return {"status": "error", "reason": "Could not convert PDF pages to images."}

        print(f"✓ Successfully converted {len(page_images)} pages")

        # Load vision-specific prompt
        prompt_template = load_prompt_from_md(
            "prompts/qpaper_parser_vision.md")

        # Format prompt with curriculum topics
        if curriculum_topics:
            topics_list = "\n".join(
                [f"- {topic}" for topic in curriculum_topics])
            final_prompt = prompt_template.format(
                curriculum_topics=topics_list
            )
        else:
            final_prompt = prompt_template.format(
                curriculum_topics="No curriculum topics provided. Infer topics from question content."
            )

        print("🤖 Analyzing question paper images with vision model...")
        analysis_result = call_gemini_api_with_images(
            final_prompt, page_images)

        return analysis_result

    except Exception as e:
        print(f"❌ Image-based analysis failed: {str(e)}")
        return {"status": "error", "reason": f"Image-based analysis failed: {str(e)}"}
