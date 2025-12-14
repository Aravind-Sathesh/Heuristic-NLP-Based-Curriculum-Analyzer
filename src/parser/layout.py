import layoutparser as lp
import numpy as np
import pytesseract
import pandas as pd
from pdf2image import convert_from_path
from src.utils import LP_CONFIG_PATH, LP_WEIGHTS_PATH, validate_paths

_layout_model = None


def get_model():
    """Load Detectron2 for Structure Detection (Figures/Tables only)."""
    global _layout_model
    if _layout_model is None:
        validate_paths()
        print("🧠 Loading LayoutParser Model (Structure Only)...")
        _layout_model = lp.Detectron2LayoutModel(
            config_path=LP_CONFIG_PATH,
            model_path=LP_WEIGHTS_PATH,
            label_map={0: "Text", 1: "Title",
                       2: "List", 3: "Table", 4: "Figure"},
            extra_config=["MODEL.DEVICE", "cpu"]
        )
    return _layout_model


def get_tesseract_blocks(image_np):
    """
    Uses Tesseract to find EXACT text regions.
    Returns a Layout object containing Text blocks.
    """
    # 1. Get detailed data from Tesseract
    # output_type=dict gives us left, top, width, height, conf, text, block_num
    data = pytesseract.image_to_data(
        image_np, output_type=pytesseract.Output.DICT)

    # 2. Convert to DataFrame for easier grouping
    df = pd.DataFrame(data)

    # Filter out empty text or low confidence garbage
    df = df[df.conf != '-1']  # -1 is structural noise
    df['conf'] = pd.to_numeric(df['conf'])
    df = df[df.conf > 30]    # Filter low confidence artifacts
    df = df[df.text.str.strip().str.len() > 1]  # Filter single char noise

    if df.empty:
        return lp.Layout([])

    # 3. Group by 'block_num' (Tesseract's internal paragraph detection)
    blocks = []
    for block_num, group in df.groupby('block_num'):
        x1 = group['left'].min()
        y1 = group['top'].min()
        # Rough approx of right edge
        x2 = group['left'].max() + group['width'].max()
        # Better x2 calculation: max(left + width)
        x2 = (group['left'] + group['width']).max()
        y2 = (group['top'] + group['height']).max()

        # Create LayoutParser Block
        # We assign type="Text" to everything Tesseract finds
        rect = lp.Rectangle(x1, y1, x2, y2)
        blocks.append(
            # Score 1.0 because ink exists
            lp.TextBlock(block=rect, type="Text", score=1.0)
        )

    return lp.Layout(blocks)


def merge_nearby_blocks(layout, vertical_thresh=25):
    """
    Merges text blocks that are vertically close (reconstructing questions).
    """
    # Separate Text from Structure
    structure = [b for b in layout if b.type in ["Figure", "Table", "Title"]]
    text = [b for b in layout if b.type == "Text"]

    if not text:
        return layout

    # Sort top-to-bottom
    text.sort(key=lambda b: b.coordinates[1])

    merged = []
    current = text[0]

    for next_b in text[1:]:
        # Calculate Gap
        gap = next_b.coordinates[1] - current.coordinates[3]

        # Merge if close enough
        if gap < vertical_thresh:
            # Union the boxes
            x1 = min(current.coordinates[0], next_b.coordinates[0])
            y1 = current.coordinates[1]
            x2 = max(current.coordinates[2], next_b.coordinates[2])
            y2 = next_b.coordinates[3]

            current = lp.TextBlock(
                block=lp.Rectangle(x1, y1, x2, y2),
                type="Text",
                score=1.0
            )
        else:
            merged.append(current)
            current = next_b

    merged.append(current)
    return lp.Layout(merged + structure)


def parse_pdf(pdf_stream):
    # High DPI for Tesseract
    images = convert_from_path(pdf_stream, dpi=300)
    model = get_model()
    processed_pages = []

    for i, pil_image in enumerate(images):
        image_np = np.array(pil_image)

        # STEP 1: AI for Structure (Diagrams/Tables)
        # We only keep Figures, Tables, and Titles from Detectron
        ai_layout = model.detect(image_np)
        structure_blocks = [b for b in ai_layout if b.type in [
            "Figure", "Table", "Title"] and b.score > 0.4]

        # STEP 2: OCR for Text (The "Truth")
        text_blocks = get_tesseract_blocks(image_np)

        # STEP 3: Filter Text inside Figures
        # If Tesseract found text INSIDE a Figure box, ignore it (it's label text)
        clean_text = []
        for t_block in text_blocks:
            is_inside_figure = False
            for s_block in structure_blocks:
                if s_block.type == "Figure":
                    # Check if text is mostly inside figure
                    intersect = t_block.intersect(s_block).area
                    if intersect / t_block.area > 0.5:
                        is_inside_figure = True
                        break
            if not is_inside_figure:
                clean_text.append(t_block)

        # STEP 4: Combine & Merge
        combined_layout = lp.Layout(clean_text + structure_blocks)
        final_layout = merge_nearby_blocks(combined_layout, vertical_thresh=30)

        processed_pages.append({
            "page_num": i + 1,
            "image": image_np,
            "layout": final_layout
        })

    return processed_pages
