import streamlit as st
import pandas as pd
from src.parser.syllabus_parser import pdf_to_markdown
from src.logic.structured import extract_structured_syllabus
from src.parser.exam_parser import parse_exam_pdf
from src.logic.matcher import match_questions_to_syllabus

st.set_page_config(layout="wide", page_title="Curriculum Analyzer")
st.title("AI Curriculum & Exam Analyzer")

col1, col2 = st.columns(2)
syllabus_file = col1.file_uploader("Upload Syllabus (PDF)", type=["pdf"])
exam_file = col2.file_uploader("Upload Exam Paper (PDF)", type=["pdf"])

if syllabus_file and exam_file:
    if st.button("Analyze", type="primary"):

        with st.status("Analyzing Syllabus...", expanded=True) as status:
            s_path = f"data/temp/{syllabus_file.name}"
            with open(s_path, "wb") as f:
                f.write(syllabus_file.getbuffer())

            md_text = pdf_to_markdown(s_path)
            syllabus_struct = extract_structured_syllabus(md_text)

            st.success(
                f"Extracted {len(syllabus_struct)} topics with Bloom levels.")

            with st.expander("View Extracted Topics"):
                st.dataframe(syllabus_struct)

            status.update(label="Syllabus Ready", state="complete")

        with st.status("Scanning Exam...", expanded=True) as status:
            e_path = f"data/temp/{exam_file.name}"
            with open(e_path, "wb") as f:
                f.write(exam_file.getbuffer())

            exam_questions = parse_exam_pdf(e_path)
            st.write(f"Found {len(exam_questions)} questions.")

            with st.expander("View Extracted Questions"):
                for i, q in enumerate(exam_questions):
                    st.text_area(f"Question {i+1}", q['text'], height=100)

            status.update(label="Exam Ready", state="complete")

        st.divider()

        if syllabus_struct:
            results = match_questions_to_syllabus(
                syllabus_struct, exam_questions)

            if results:
                df = pd.DataFrame(results)

                def highlight_audit(val):
                    if 'Aligned' in val:
                        return 'color: #4caf50; font-weight: bold'
                    if 'Too Hard' in val:
                        return 'color: #f44336; font-weight: bold'
                    if 'Too Easy' in val:
                        return 'color: #ff9800; font-weight: bold'
                    return ''

                def highlight_status(val):
                    if 'Gap' in val:
                        return 'background-color: #ffebee; color: #c62828'
                    return ''

                st.subheader("Analyze Report")
                st.dataframe(
                    df.style.map(highlight_audit, subset=['bloom_audit'])
                    .map(highlight_status, subset=['match_status']),
                    width="stretch",
                    column_config={
                        "question": st.column_config.TextColumn("Exam Question", width="medium"),
                        "matched_topic": st.column_config.TextColumn("Matched Topic", width="small"),
                        "source_segment": "Source",
                        "match_status": st.column_config.TextColumn("Alignment", width="small"),
                        "q_bloom": "Q Level",
                        "s_bloom": "S Level",
                        "bloom_audit": "Bloom Check"
                    },
                    hide_index=True
                )
            else:
                st.warning("No matches found.")
