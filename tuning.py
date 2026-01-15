import fitz
import re
import os
import torch
from sentence_transformers import util
from src.utils import load_sbert_model

files = [f for f in os.listdir("data/temp") if f.endswith(".pdf")]
TARGET_FILE = f"data/temp/{files[0]}" if files else None


def extract_clean_text_physically(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        words = page.get_text("words")
        # Sort Y then X
        words.sort(key=lambda w: (round(w[1] / 3), w[0]))
        current_line_y = -1
        page_text = ""
        for w in words:
            y = round(w[1] / 3)
            word = w[4]
            if current_line_y != -1 and y > current_line_y:
                page_text += "\n" + word
            else:
                page_text += (" " + word) if page_text else word
            current_line_y = y
        full_text += page_text + "\n"
    return full_text


def get_question_id(text):
    """Extract question ID from start of line."""
    text = text.strip()
    if not text:
        return None

    pattern = r'^(?:Q\.?\s*|Question\s*|Part\s+)?(\d+)(?:[\.\)]|[a-zA-Z])'

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        num_str = match.group(1)
        # Sanity Check: Avoid Year (2025) or Data (926681)
        try:
            num = int(num_str)
            if 0 < num < 200:
                return num
        except:
            pass

    return None


def stateful_segmentation(full_text):
    print("\n--- 2. Segmenting (Stateful ID Tracking) ---")

    # 1. Clean Headers
    lines = full_text.split('\n')
    clean_lines = []
    for line in lines:
        lower = line.lower()
        if any(x in lower for x in ["bits f452", "page ", "date:", "marks:", "semester", "duration:", "closed book"]):
            continue
        clean_lines.append(line)

    final_questions = []
    current_q_text = ""
    current_id = -1

    for line in clean_lines:
        line = line.strip()
        if not line:
            continue

        # Check for ID
        line_id = get_question_id(line)

        # LOGIC TREE
        if line_id is not None:
            # Found a number. Is it new?
            if line_id != current_id:
                # NEW QUESTION (e.g. Current=1, Found=2)
                if current_q_text:
                    final_questions.append(current_q_text)
                current_q_text = line
                current_id = line_id
            else:
                # SAME QUESTION (e.g. Current=1, Found=1 in "1.c")
                # Glue it
                current_q_text += "\n" + line
        else:
            # NO NUMBER (Text content, "a.", "(i)")
            # Glue it
            if current_q_text:
                current_q_text += "\n" + line
            else:
                # Preamble text before Q1
                if len(line) > 50:
                    current_q_text = line

    if current_q_text:
        final_questions.append(current_q_text)

    return final_questions


if __name__ == "__main__":
    if not TARGET_FILE:
        print("❌ No PDF found.")
        exit()

    text = extract_clean_text_physically(TARGET_FILE)
    questions = stateful_segmentation(text)

    print(f"\n✅ Found {len(questions)} Questions:")
    print("=" * 60)
    for i, q in enumerate(questions):
        first_line = q.split('\n')[0][:80]
        # Show which question we think it is vs content
        print(f"[{i+1}] {first_line}...")
    print("=" * 60)
