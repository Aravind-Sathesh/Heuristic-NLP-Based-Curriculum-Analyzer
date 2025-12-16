import streamlit as st
import pandas as pd
from src.parser.syllabus_parser import pdf_to_markdown
from src.logic.structured import extract_structured_syllabus
from src.parser.exam_parser import parse_exam_pdf
from src.logic.matcher import match_questions_to_syllabus

st.set_page_config(layout="wide", page_title="Curriculum Analyzer")


def simplify_bloom_audit(audit_string):
    """Converts audit string to simple verdict."""
    if "Too Hard" in audit_string:
        return "Too Hard"
    if "Under-testing" in audit_string:
        return "Too Easy"
    if "Acceptable" in audit_string:
        return "Acceptable"
    if "Perfect Alignment" in audit_string:
        return "Perfect Alignment"
    return "N/A"  # For unmatched questions


def calculate_overall_score(df):
    """Calculates overall alignment percentage."""
    if df.empty:
        return 0

    total_questions = len(df)
    current_score = 0

    for _, row in df.iterrows():
        match_quality_score = 0
        if row['match_status'] == 'Strong Match':
            match_quality_score = 1.0
        elif row['match_status'] == 'Partial Match':
            match_quality_score = 0.5

        bloom_quality_score = 0
        verdict = row['verdict']
        if verdict in ['Perfect Alignment', 'Acceptable']:
            bloom_quality_score = 1.0
        elif verdict == 'Too Easy':
            bloom_quality_score = 0.5

        current_score += (match_quality_score * bloom_quality_score)

    return (current_score / total_questions) * 100


col_title, col_info = st.columns([6, 1])
with col_title:
    st.title("AI Curriculum & Exam Analyzer")
with col_info:
    with st.popover("Taxonomy Guide"):
        st.image("assets/taxonomy guide.png", width=300)

col1, col2 = st.columns(2)
syllabus_file = col1.file_uploader(
    "Upload Syllabus / Handout (PDF)", type=["pdf"])
exam_file = col2.file_uploader("Upload Exam Paper / QP (PDF)", type=["pdf"])

if syllabus_file and exam_file:
    if st.button("Analyze Alignment", type="primary"):

        with st.status("Analyzing Syllabus...", expanded=True) as status:
            s_path = f"data/temp/{syllabus_file.name}"
            with open(s_path, "wb") as f:
                f.write(syllabus_file.getbuffer())

            md_text = pdf_to_markdown(s_path)
            syllabus_struct = extract_structured_syllabus(md_text)

            with st.expander("View Raw Extracted Syllabus Topics"):
                st.json(syllabus_struct)

            status.update(label="Syllabus Ready", state="complete")

        with st.status("Scanning Exam Paper...", expanded=True) as status:
            e_path = f"data/temp/{exam_file.name}"
            with open(e_path, "wb") as f:
                f.write(exam_file.getbuffer())

            exam_questions = parse_exam_pdf(e_path)

            with st.expander("View Raw Extracted Questions"):
                st.json(exam_questions)

            status.update(label="Exam Ready", state="complete")

        st.divider()

        if syllabus_struct and exam_questions:
            results = match_questions_to_syllabus(
                syllabus_struct, exam_questions)

            if results:
                df = pd.DataFrame(results)
                df['verdict'] = df['bloom_audit'].apply(simplify_bloom_audit)

                overall_score = calculate_overall_score(df)
                st.subheader("Overall Alignment Score")
                st.metric(
                    label="Curriculum Alignment",
                    value=f"{overall_score:.0f}%",
                    help="This score measures how well the exam aligns with the syllabus, considering both topic coverage (match status) and cognitive level (Bloom's verdict)."
                )
                st.progress(int(overall_score))

                st.divider()

                def highlight_verdict(val):
                    color = ''
                    if val == "Too Hard":
                        color = '#f44336'
                    elif val == "Too Easy":
                        color = '#f44336'
                    elif val == "Acceptable":
                        color = '#ff9800'
                    elif val == "Perfect Alignment":
                        color = '#4caf50'
                    return f'color: {color}; font-weight: bold;'

                df_display = df[[
                    'question_snippet',
                    'question_bloom',
                    'syllabus_bloom',
                    'similarity_score',
                    'verdict'
                ]]

                st.subheader("Alignment Report")
                st.dataframe(
                    df_display.style.applymap(
                        highlight_verdict, subset=['verdict']),
                    column_config={
                        "question_snippet": st.column_config.TextColumn("Exam Question", width="large"),
                        "question_bloom": "Question Level",
                        "syllabus_bloom": "Handout Level",
                        "similarity_score": st.column_config.ProgressColumn(
                            "Score",
                            format="%.2f",
                            min_value=0.0,
                            max_value=1.0,
                        ),
                        "verdict": "Verdict"
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning("Could not generate an alignment report.")
