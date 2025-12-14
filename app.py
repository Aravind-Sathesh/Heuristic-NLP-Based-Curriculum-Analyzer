import streamlit as st
import numpy as np
import cv2
from PIL import Image
import tempfile
import os
from src.parser.layout import parse_pdf
from src.parser.ocr import extract_text_from_layout


def draw_layout_boxes(image_np, layout):
    """
    Draws bounding boxes and labels directly on the numpy image using OpenCV.
    Bypasses layoutparser's broken visualization code.
    """
    img_copy = image_np.copy()

    # Define colors for different types
    colors = {
        "Text": (0, 255, 0),      # Green
        "Title": (255, 0, 0),     # Blue
        "List": (0, 255, 255),    # Yellow
        "Table": (255, 0, 255),   # Magenta
        "Figure": (0, 0, 255)     # Red
    }

    for block in layout:
        # Get coordinates
        coords = np.array(block.coordinates).astype(int)
        x1, y1, x2, y2 = coords

        # Get Color
        color = colors.get(block.type, (200, 200, 200))

        # Draw Rectangle
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)

        # Draw Label Background
        label = f"{block.type} ({block.score:.2f})"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img_copy, (x1, y1 - 20), (x1 + w, y1), color, -1)

        # Draw Label Text
        cv2.putText(img_copy, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return img_copy


st.set_page_config(layout="wide", page_title="Layout Parser Debug")

st.title("️ Local Layout Parser Debugger")
st.warning("Running on Local CPU (Mac Optimized)")

uploaded_file = st.file_uploader("Upload a PDF (Exam or Syllabus)", type="pdf")

if uploaded_file:
    with st.spinner("Processing PDF with Detectron2..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        try:
            results = parse_pdf(tmp_path)
            st.success(f"Processed {len(results)} pages.")

            for page in results:
                st.markdown(f"### Page {page['page_num']}")
                col1, col2 = st.columns([1, 1])

                # Retrieve Data
                img = page['image']
                layout = page['layout']

                with col1:
                    # USE CUSTOM VISUALIZER
                    viz_img = draw_layout_boxes(img, layout)
                    st.image(Image.fromarray(viz_img),
                             use_container_width=True)

                with col2:
                    st.subheader("Extracted Text")
                    with st.spinner("Reading text..."):
                        text_blocks = extract_text_from_layout(img, layout)

                    for block in text_blocks:
                        if block['type'] == 'Title':
                            st.markdown(f"### {block['text']}")
                        elif block['type'] == 'Figure':
                            st.info(
                                f"️ [Figure detected at {block['coordinates']}]")
                        else:
                            st.write(block['text'])
                        st.divider()

        except Exception as e:
            st.error(f"Pipeline Error: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
