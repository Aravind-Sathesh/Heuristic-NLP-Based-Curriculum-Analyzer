"""
Parser for extracting individual questions from an exam paper PDF.
This module uses a hybrid approach:
- For native text PDFs, it uses a fast, coordinate-based parser.
- For scanned PDFs, it uses the Florence-2 Vision-Language Model for robust,
  end-to-end question extraction.
"""

import fitz
import re
import numpy as np
from pdf2image import convert_from_path
from src.utils import load_florence_model
from src.parser.ocr_parser import is_scanned_pdf
from src.logic.structured import (
    is_header_or_separator,
    is_bibliographic_junk,
    get_junk_density_score,
)


def is_header_row(line: str) -> bool:
    return (
        is_header_or_separator(line)
        or is_bibliographic_junk(line)
        or get_junk_density_score(line) > 0.5
    )


def chunk_ocr_text(text, max_len=120):
    """Break OCR text into semantic chunks at sentence boundaries."""
    tokens = re.split(r'(?<=[\.\?\:])\s+', text)
    chunks, buf = [], ""

    for t in tokens:
        if len(buf) + len(t) < max_len:
            buf += " " + t
        else:
            chunks.append(buf.strip())
            buf = t

    if buf:
        chunks.append(buf.strip())

    return chunks


def score_question_likeness(chunk, question_proto_emb, embed_fn):
    """Score how question-like a chunk is using cosine similarity."""
    from sentence_transformers import util
    emb = embed_fn(chunk)
    return util.cos_sim(emb, question_proto_emb)[0][0].item()


def extract_clean_text_from_page(page):
    """Extracts and sorts text from a native PDF page based on coordinates."""
    words = page.get_text("words")
    words.sort(key=lambda w: (round(w[1] / 3), w[0]))
    page_text = ""
    current_line_y = -1
    for w in words:
        y = round(w[1] / 3)
        word = w[4]
        if current_line_y != -1 and y > current_line_y:
            page_text += "\n" + word
        else:
            page_text += (" " + word) if page_text else word
        current_line_y = y
    return page_text


def get_question_id(text):
    """Extracts a question number (e.g., 1., Q2) from the start of a line."""
    pattern = r'^(?:Q\.?\s*|Question\s*|Part\s+)?(\d+)(?:[\.\)\s(a-z)])'
    match = re.match(pattern, text.strip(), re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except (ValueError, IndexError):
            return None
    return None


def group_text_into_questions(full_text):
    """Groups a block of cleaned text into questions using heuristic rules."""
    lines = full_text.split('\n')
    final_questions = []
    current_q_text = ""
    current_id = -1
    for line in lines:
        line = line.strip()
        if not line:
            continue
        line_id = get_question_id(line)
        if line_id is not None and line_id != current_id:
            if current_q_text:
                final_questions.append(current_q_text)
            current_q_text = line
            current_id = line_id
        elif current_q_text:
            current_q_text += "\n" + line
    if current_q_text:
        final_questions.append(current_q_text)
    return [{"text": q} for q in final_questions]

# --- Pipeline B: Parser for Scanned PDFs using Florence-2 ---


def parse_scanned_pdf_with_florence(pdf_path, dpi=200):
    """

    Uses the Florence-2 Vision-Language Model to perform end-to-end question
    extraction from a scanned PDF.
    """
    try:
        model, processor = load_florence_model()
        images = convert_from_path(pdf_path, dpi=dpi)

        if not images:
            print("Error: No images extracted from PDF")
            return []

        all_questions = []

        for i, image in enumerate(images):
            if image is None:
                print(f"Warning: Page {i+1} returned None, skipping...")
                continue

            # Validate image
            if not hasattr(image, 'size') or image.size is None:
                print(
                    f"Warning: Page {i+1} has invalid image format, skipping...")
                continue

            try:
                # Use OCR with regions - a valid Florence-2 task
                prompt = "<OCR_WITH_REGION>"

                # Ensure image is in RGB format
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Process with Florence-2
                try:
                    inputs = processor(
                        text=prompt,
                        images=image,
                        return_tensors="pt"
                    )
                except Exception as proc_error:
                    print(
                        f"  Error in processor call: {type(proc_error).__name__}: {proc_error}")
                    import traceback
                    traceback.print_exc()
                    continue

                # Move inputs to model device
                try:
                    inputs = {k: v.to(model.device) if hasattr(v, 'to') else v
                              for k, v in inputs.items()}
                except Exception as device_error:
                    print(
                        f"  Error moving to device: {type(device_error).__name__}: {device_error}")
                    import traceback
                    traceback.print_exc()
                    continue

                try:
                    generated_ids = model.generate(
                        input_ids=inputs["input_ids"],
                        pixel_values=inputs["pixel_values"],
                        max_new_tokens=1024,
                        early_stopping=False,
                        do_sample=False,
                        num_beams=1,  # Use greedy decoding to avoid past_key_values issue
                        use_cache=False  # Disable cache to prevent related errors
                    )
                except Exception as gen_error:
                    print(
                        f"  Error in model.generate(): {type(gen_error).__name__}: {gen_error}")
                    import traceback
                    traceback.print_exc()
                    continue

                generated_text = processor.batch_decode(
                    generated_ids, skip_special_tokens=False)[0]

                parsed_output = processor.post_process_generation(
                    generated_text, task=prompt, image_size=image.size)

                if isinstance(parsed_output, dict):
                    # OCR_WITH_REGION returns {'<OCR_WITH_REGION>': {'quad_boxes': [...], 'labels': [...]}}
                    if prompt in parsed_output:
                        ocr_data = parsed_output[prompt]
                        if isinstance(ocr_data, dict) and 'labels' in ocr_data:
                            # Combine all OCR text
                            page_text = ' '.join(ocr_data['labels'])
                            all_questions.append({"text": page_text})
                        else:
                            print(
                                f"  Unexpected OCR data structure: {ocr_data}")
                else:
                    print(f"  Unexpected parsed output type")

            except Exception as e:
                print(f"Error processing page {i+1}: {e}")
                continue

        print(
            f"Florence-2 extracted OCR text from {len(all_questions)} pages.")

        # Now we have OCR text from each page, combine and parse into questions
        if not all_questions:
            return []

        # Combine all page text
        full_text = " ".join([q["text"] for q in all_questions])

        # Stage 1: Clean OCR artifacts
        full_text = re.sub(r'</s>|<s>', '', full_text)  # Remove special tokens
        full_text = re.sub(r'\s+', ' ', full_text)  # Normalize whitespace

        print(f"DEBUG: Combined OCR text length: {len(full_text)} chars")
        print(f"DEBUG: First 500 chars: {full_text[:500]}")

        # Stage 2: Semantic chunking with hierarchical scoring
        from src.utils import load_sbert_model
        model = load_sbert_model()

        # Two-level prototype system
        # Level 1: Main question starters (higher threshold)
        main_q_prototypes = [
            "Question 1: Solve the problem and explain",
            "Problem 8: Calculate the following values",
            "Q1. Define and describe in detail",
            "1) Explain the complete process"
        ]

        # Level 2: Continuation/content markers (lower threshold)
        content_prototypes = [
            "Calculate and find the solution to this problem",
            "Define, explain, and describe the concept in detail",
            "Prove, derive, and show your work for the solution",
            "Compare, analyze, and evaluate the given scenario"
        ]

        main_embs = [model.encode(p, convert_to_tensor=True)
                     for p in main_q_prototypes]
        content_embs = [model.encode(p, convert_to_tensor=True)
                        for p in content_prototypes]

        def embed_fn(text):
            return model.encode(text, convert_to_tensor=True)

        chunks = chunk_ocr_text(full_text, max_len=150)
        print(f"DEBUG: Created {len(chunks)} chunks")

        # Filter headers
        chunks = [c for c in chunks if not is_header_row(c)]
        print(f"DEBUG: After header filtering: {len(chunks)} chunks")

        # Score each chunk for both main question and content
        scored_chunks = []
        for c in chunks:
            main_scores = [score_question_likeness(
                c, emb, embed_fn) for emb in main_embs]
            content_scores = [score_question_likeness(
                c, emb, embed_fn) for emb in content_embs]

            main_score = max(main_scores)
            content_score = max(content_scores)

            scored_chunks.append((c, main_score, content_score))

        print(
            f"DEBUG: Sample scores (chunk, main, content): {[(c[:40], round(m, 3), round(co, 3)) for c, m, co in scored_chunks[:5]]}")

        # Filter out institutional headers with high specificity
        header_keywords = ['institute', 'university', 'bits', 'pilani', 'examination',
                           'semester', 'campus', 'marks)', 'end-semester', 'subjective']
        filtered_chunks = []
        for chunk, main_score, content_score in scored_chunks:
            chunk_lower = chunk.lower()
            keyword_count = sum(
                1 for kw in header_keywords if kw in chunk_lower)
            if keyword_count >= 3 or (keyword_count >= 2 and len(chunk) < 100):
                print(f"DEBUG: Filtering header: {chunk[:50]}")
                continue
            filtered_chunks.append((chunk, main_score, content_score))

        print(f"DEBUG: After header filter: {len(filtered_chunks)} chunks")

        # Hierarchical grouping with delta-based detection
        final_questions = []
        current = None

        for chunk, main_score, content_score in filtered_chunks:
            # New question if main score significantly exceeds content (delta > 0.08)
            # This catches numbered questions like "(8)" without being too aggressive
            if main_score > content_score + 0.08 and main_score > 0.25:
                if current and len(current) > 50:
                    final_questions.append({"text": current})
                current = chunk
            # Continue if content score decent or chunk is substantial
            elif current and (content_score > 0.15 or len(chunk) > 80):
                current += " " + chunk
            # Start first question if scores reasonable
            elif not current and (main_score > 0.18 or content_score > 0.16):
                current = chunk

        if current and len(current) > 30:
            final_questions.append({"text": current})

        print(f"Parsed into {len(final_questions)} individual questions.")
        return final_questions

    except Exception as e:
        print(f"Error during Florence-2 processing: {e}")
        import traceback
        traceback.print_exc()
        return []


def parse_exam_pdf(pdf_path):
    """
    Parses an exam PDF to extract a list of questions.
    Automatically detects if the PDF is scanned and routes to the appropriate parser.
    """
    if is_scanned_pdf(pdf_path):
        print(f"Info: Scanned PDF detected. Using Florence-2 for robust extraction.")
        return parse_scanned_pdf_with_florence(pdf_path)
    else:
        print(f"Info: Native text PDF detected. Using standard coordinate-based parser.")
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += extract_clean_text_from_page(page) + "\n"
        doc.close()
        return group_text_into_questions(full_text)
