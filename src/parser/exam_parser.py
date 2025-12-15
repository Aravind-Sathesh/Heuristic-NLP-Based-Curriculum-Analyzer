import fitz
import re


def extract_clean_text_from_page(page):
    """Extract text using physical coordinates, sorted top-to-bottom, left-to-right."""
    words = page.get_text("words")

    # Sort strictly: Top-to-bottom (y0), then Left-to-right (x0)
    # Round y0 to nearest 3 pixels to handle slight misalignments
    words.sort(key=lambda w: (round(w[1] / 3), w[0]))

    current_line_y = -1
    page_text = ""

    for w in words:
        y = round(w[1] / 3)
        word = w[4]

        # New line detection
        if current_line_y != -1 and y > current_line_y:
            page_text += "\n" + word
        else:
            page_text += (" " + word) if page_text else word

        current_line_y = y

    return page_text


def is_header_row(text):
    """Filter metadata rows like page numbers, dates, marks."""
    t = text.lower()
    if len(t) < 3:
        return False

    # Page numbers
    if re.search(r'page\s*\d+', t):
        return True

    # Standard metadata
    meta_keys = [
        "duration:",
        "weightage",
        "marks:",
        "date:",
        "semester",
        "course code",
        "course title",
        "id no",
        "name:"
    ]
    if any(k in t for k in meta_keys):
        return True

    # Structural headers
    struct_keys = [
        "comprehensive examination",
        "mid-semester",
        "final exam",
        "open book",
        "closed book",
        "instructions:",
        "scanned by"
    ]
    if any(k in t for k in struct_keys):
        return True

    return False


def get_question_id(text):
    """Extract question ID if line starts with a valid question number."""
    text = text.strip()
    if not text:
        return None

    pattern = r'^(?:Q\.?\s*|Question\s*|Part\s+)?(\d+)(?:[\.\)])'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        try:
            num = int(match.group(1))
            # Sanity check
            if 0 < num < 200:
                return num
        except ValueError:
            pass

    return None


def parse_exam_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    print(f"Parsing Exam (Stateful Coordinate Logic): {pdf_path}")

    full_text = ""

    # 1. Extract all pages
    for i in range(len(doc)):
        page_text = extract_clean_text_from_page(doc.load_page(i))
        full_text += page_text + "\n"

    # 2. Remove headers
    lines = full_text.split('\n')
    clean_lines = []
    for line in lines:
        if is_header_row(line):
            continue
        clean_lines.append(line)

    # 3. Stateful grouping
    final_questions = []
    current_q_text = ""
    current_id = -1

    for line in clean_lines:
        line = line.strip()
        if not line:
            continue

        line_id = get_question_id(line)

        if line_id is not None:
            # New question number encountered
            if line_id != current_id:
                if current_q_text:
                    final_questions.append(current_q_text)

                current_q_text = line
                current_id = line_id
            else:
                # Same question ID (e.g., sub-parts like 1.a, 1.b)
                current_q_text += "\n" + line
        else:
            # Continuation text
            if current_q_text:
                current_q_text += "\n" + line
            else:
                # Preamble / noise before Q1
                pass

    # Save last question
    if current_q_text:
        final_questions.append(current_q_text)

    return [{"text": q} for q in final_questions]
