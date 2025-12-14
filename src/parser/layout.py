import layoutparser as lp
import numpy as np
import pytesseract
import pandas as pd
from pdf2image import convert_from_path
from src.utils import LP_CONFIG_PATH, LP_WEIGHTS_PATH, validate_paths

_layout_model = None


def get_model():
    """Load Detectron2 for Structure Detection."""
    global _layout_model
    if _layout_model is None:
        validate_paths()
        print("Loading LayoutParser Model (Structure Only)...")
        _layout_model = lp.Detectron2LayoutModel(
            config_path=LP_CONFIG_PATH,
            model_path=LP_WEIGHTS_PATH,
            label_map={0: "Text", 1: "Title",
                       2: "List", 3: "Table", 4: "Figure"},
            extra_config=["MODEL.DEVICE", "cpu"]
        )
    return _layout_model


def get_tesseract_blocks(image_np):
    """Uses Tesseract to find EXACT text regions."""
    data = pytesseract.image_to_data(
        image_np, output_type=pytesseract.Output.DICT)
    df = pd.DataFrame(data)

    # Filter noise
    df = df[df.conf != '-1']
    df['conf'] = pd.to_numeric(df['conf'])
    df = df[df.conf > 40]
    df = df[df.text.str.strip().str.len() > 1]

    if df.empty:
        return lp.Layout([])

    blocks = []
    for block_num, group in df.groupby('block_num'):
        x1 = group['left'].min()
        y1 = group['top'].min()
        x2 = (group['left'] + group['width']).max()
        y2 = (group['top'] + group['height']).max()

        rect = lp.Rectangle(x1, y1, x2, y2)
        blocks.append(lp.TextBlock(block=rect, type="Text", score=1.0))

    return lp.Layout(blocks)


def merge_nearby_blocks(layout, vertical_thresh=15):
    """Merges text blocks that are vertically close."""
    # We allow merging of TableContent with TableContent, and Text with Text, but NOT mixed types.

    special_blocks = [
        b for b in layout if b.type not in ["Text", "TableContent"]]
    text_blocks = [b for b in layout if b.type in ["Text", "TableContent"]]

    if not text_blocks:
        return layout

    text_blocks.sort(key=lambda b: b.coordinates[1])

    merged = []
    current = text_blocks[0]

    for next_b in text_blocks[1:]:
        gap = next_b.coordinates[1] - current.coordinates[3]

        # Merge if close AND types match
        if gap < vertical_thresh and current.type == next_b.type:
            x1 = min(current.coordinates[0], next_b.coordinates[0])
            y1 = current.coordinates[1]
            x2 = max(current.coordinates[2], next_b.coordinates[2])
            y2 = next_b.coordinates[3]

            current = lp.TextBlock(
                block=lp.Rectangle(x1, y1, x2, y2),
                type=current.type,
                score=1.0
            )
        else:
            merged.append(current)
            current = next_b

    merged.append(current)
    return lp.Layout(merged + special_blocks)


def parse_pdf(pdf_stream):
    images = convert_from_path(pdf_stream, dpi=300)
    model = get_model()
    processed_pages = []

    for i, pil_image in enumerate(images):
        image_np = np.array(pil_image)

        # Structure Detection (Tables/Figures)
        ai_layout = model.detect(image_np)
        structure_blocks = [b for b in ai_layout if b.type in [
            "Figure", "Table", "Title"] and b.score > 0.4]

        # OCR Text Detection
        text_blocks = get_tesseract_blocks(image_np)

        # Context Classification
        final_text_blocks = []
        for t_block in text_blocks:
            assigned = False

            # Check if text is inside a Figure or Table
            for s_block in structure_blocks:
                intersect = t_block.intersect(s_block).area
                if intersect / t_block.area > 0.5:
                    if s_block.type == "Figure":
                        assigned = True
                    elif s_block.type == "Table":
                        t_block.type = "TableContent"
                        final_text_blocks.append(t_block)
                        assigned = True
                    break

            if not assigned:
                final_text_blocks.append(t_block)

        # Merge
        combined_layout = lp.Layout(final_text_blocks + structure_blocks)
        final_layout = merge_nearby_blocks(combined_layout, vertical_thresh=15)

        processed_pages.append({
            "page_num": i + 1,
            "image": image_np,
            "layout": final_layout
        })

    return processed_pages
