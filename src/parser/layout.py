import layoutparser as lp
import numpy as np
from pdf2image import convert_from_path
from src.utils import LP_CONFIG_PATH, LP_WEIGHTS_PATH, validate_paths

_layout_model = None


def get_model():
    global _layout_model
    if _layout_model is None:
        validate_paths()
        print("🧠 Loading LayoutParser Model (PubLayNet)...")
        _layout_model = lp.Detectron2LayoutModel(
            config_path=LP_CONFIG_PATH,
            model_path=LP_WEIGHTS_PATH,
            label_map={0: "Text", 1: "Title",
                       2: "List", 3: "Table", 4: "Figure"},
            extra_config=["MODEL.DEVICE", "cpu"]
        )
    return _layout_model


def parse_pdf(pdf_stream):
    # [FIX] Keep DPI=300 for clarity, but REMOVE grayscale=True
    # LayoutParser needs 3 channels (RGB) to function.
    images = convert_from_path(pdf_stream, dpi=300)

    model = get_model()
    processed_pages = []

    for i, pil_image in enumerate(images):
        image_np = np.array(pil_image)
        layout = model.detect(image_np)

        # --- DEDUPLICATION LOGIC ---

        # 1. Filter low confidence
        filtered_layout = lp.Layout([b for b in layout if b.score > 0.3])

        # 2. Sort by score
        filtered_layout.sort(key=lambda x: x.score, reverse=True)

        # 3. Non-Maximum Suppression (Remove overlapping duplicates)
        final_blocks = []
        for block in filtered_layout:
            is_redundant = False
            for kept_block in final_blocks:
                # If block is >80% inside an existing block, drop it
                intersection_area = block.intersect(kept_block).area
                if intersection_area > 0 and (intersection_area / block.area) > 0.8:
                    is_redundant = True
                    break

            if not is_redundant:
                final_blocks.append(block)

        clean_layout = lp.Layout(final_blocks)

        processed_pages.append({
            "page_num": i + 1,
            "image": image_np,
            "layout": clean_layout
        })

    return processed_pages
