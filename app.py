import streamlit as st
import numpy as np
import cv2
from PIL import Image
import tempfile
import os
from src.parser.layout import parse_pdf
from src.parser.ocr import extract_text_from_layout
from src.logic.blooms import get_bloom_level


def draw_layout_boxes(image_np, layout):
    """Draws bounding boxes using OpenCV."""
    img_copy = image_np.copy()

    colors = {
        "Text": (0, 255, 0),
        "Title": (255, 0, 0),
        "List": (0, 255, 255),
        "Table": (255, 0, 255),
        "Figure": (0, 0, 255)
    }

    for block in layout:
        coords = np.array(block.coordinates).astype(int)
        x1, y1, x2, y2 = coords

        color = colors.get(block.type, (200, 200, 200))
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)

        label = f"{block.type} ({block.score:.2f})"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img_copy, (x1, y1 - 20), (x1 + w, y1), color, -1)
        cv2.putText(img_copy, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return img_copy


st.set_page_config(layout="wide", page_title="Layout Parser Debug")

st.title("Local Layout Parser Debugger")
st.warning("Running on Local CPU (Mac Optimized)")

uploaded_file = st.file_uploader("Upload a PDF (Exam or Syllabus)", type="pdf")

if uploaded_file:
    with st.spinner("Processing PDF..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        try:
            results = parse_pdf(tmp_path)
            st.success(f"Processed {len(results)} pages.")

            for page in results:
                st.markdown(f"### Page {page['page_num']}")
                col1, col2 = st.columns([1, 1])

                img = page['image']
                layout = page['layout']

                with col1:
                    if len(layout) > 0:
                        viz_img = draw_layout_boxes(img, layout)
                        st.image(Image.fromarray(viz_img),
                                 use_container_width=True)
                    else:
                        st.warning("No layout blocks detected")
                        st.image(img, use_container_width=True)

                with col2:
                    st.subheader("Analysis")
                    with st.spinner("Reading text..."):
                        text_blocks = extract_text_from_layout(img, layout)

                    for block in text_blocks:
                        if block['type'] == 'Title':
                            st.markdown(f"#### {block['text']}")

                        elif block['type'] == 'Figure':
                            st.info(f"Figure Detected: {block['text']}")

                        elif block['type'] == 'TableContent':
                            st.markdown(f"""
                            <div style="background-color: #f0f0f0; padding: 5px 10px; margin-bottom: 5px; font-family: monospace; font-size: 0.8em; color: #555;">
                                📅 Table Data: {block['text'][:50]}...
                            </div>
                            """, unsafe_allow_html=True)

                        elif block['type'] == 'Text':
                            level, score, verb = get_bloom_level(block['text'])

                            if level == "Metadata":
                                st.markdown(f"""
                                <div style="color: #bbb; font-size: 0.7em; margin-bottom: 5px;">
                                    <em>Metadata: {block['text'][:50]}...</em>
                                </div>
                                """, unsafe_allow_html=True)

                            elif level == "Data":
                                st.markdown(f"""
                                <div style="background-color: #f8f9fa; padding: 5px; border-radius: 4px; border: 1px solid #eee; margin-bottom: 5px; font-size: 0.8em; color: #666;">
                                    Table Data: {block['text']}
                                </div>
                                """, unsafe_allow_html=True)

                            else:
                                color = "gray"
                                if score >= 5:
                                    color = "#ff4b4b"
                                elif score >= 3:
                                    color = "#ffa500"
                                elif score > 0:
                                    color = "#09ab3b"

                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding-left: 10px; margin-bottom: 10px;">
                                    <p style="margin: 0; font-weight: bold;">{block['text']}</p>
                                    <span style="font-size: 0.8em; color: {color};">
                                        Blooms: <strong>{level}</strong> (Trigger: '{verb}')
                                    </span>
                                </div>
                                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
