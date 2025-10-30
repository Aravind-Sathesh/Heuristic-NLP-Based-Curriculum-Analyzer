from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import shutil
import os
import uuid
from core.analysis_logic import analyze_curriculum_from_pdf, analyze_qpaper_from_pdf, analyze_qpaper_from_pdf_images
from typing import Optional

router = APIRouter()


def analyze_coverage(curriculum_data, qpaper_data):
    try:
        curriculum_topics = curriculum_data.get(
            "data", {}).get("topicProfiles", [])
        qpaper_questions = qpaper_data.get("data", {}).get("questions", [])

        # Get exam type and scope information
        exam_type = qpaper_data.get("data", {}).get(
            "examType", "Comprehensive")
        exam_scope = qpaper_data.get("data", {}).get("examScope", "")

        # Determine if this is a mid-semester exam (partial coverage expected)
        is_mid_semester = exam_type == "Mid-Semester"

        if not curriculum_topics or not qpaper_questions:
            return {
                "coveragePercentage": 0,
                "testedTopics": [],
                "missedTopics": [],
                "topicAnalysis": [],
                "examType": exam_type,
                "examScope": exam_scope
            }

        # Build topic map: topic_name -> {curriculum details, questions}
        topic_map = {}
        for topic in curriculum_topics:
            topic_map[topic["topicName"]] = {
                "curriculumBloom": topic.get("bloomProfile", {}),
                "questions": []
            }

        # Collect all questions per topic
        for question in qpaper_questions:
            q_num = question.get('questionNumber', '?')

            # Main question
            topic = question.get("topic", "")
            if topic in topic_map:
                topic_map[topic]["questions"].append({
                    "number": q_num,
                    "bloomLevel": question.get("bloomLevel", "Understanding"),
                    "marks": question.get("marks", 0)
                })

            # Sub-questions
            for sub_q in question.get("subQuestions", []):
                sub_topic = sub_q.get("topic", "")
                if sub_topic in topic_map:
                    part = sub_q.get('part', '')
                    topic_map[sub_topic]["questions"].append({
                        "number": f"{q_num}{part}",
                        "bloomLevel": sub_q.get("bloomLevel", "Understanding"),
                        "marks": sub_q.get("marks", 0)
                    })

        # Analyze each topic
        tested_topics = []
        missed_topics = []
        topic_analysis = []

        bloom_order = ["Remembering", "Understanding",
                       "Applying", "Analyzing", "Evaluating", "Creating"]

        for topic_name, data in topic_map.items():
            questions = data["questions"]
            curriculum_bloom = data["curriculumBloom"]

            if questions:
                tested_topics.append(topic_name)

                # Count bloom levels in questions
                question_bloom_counts = {}
                total_marks = 0
                for q in questions:
                    level = q["bloomLevel"]
                    marks = q["marks"]
                    question_bloom_counts[level] = question_bloom_counts.get(
                        level, 0) + 1
                    total_marks += marks

                # Calculate dominant bloom level
                dominant_level = max(question_bloom_counts.items(), key=lambda x: x[1])[
                    0] if question_bloom_counts else "Understanding"

                # Get expected bloom from curriculum
                curriculum_max_level = None
                if curriculum_bloom:
                    curriculum_max_level = max(
                        ((level, pct)
                         for level, pct in curriculum_bloom.items() if pct > 0),
                        key=lambda x: x[1],
                        default=(None, 0)
                    )[0]

                topic_analysis.append({
                    "topic": topic_name,
                    "tested": True,
                    "questionCount": len(questions),
                    "totalMarks": total_marks,
                    "questionNumbers": [q["number"] for q in questions],
                    "bloomDistribution": question_bloom_counts,
                    "dominantBloom": dominant_level,
                    "curriculumExpectedBloom": curriculum_max_level,
                    "bloomMatch": dominant_level == curriculum_max_level if curriculum_max_level else None
                })
            else:
                missed_topics.append(topic_name)
                topic_analysis.append({
                    "topic": topic_name,
                    "tested": False,
                    "curriculumExpectedBloom": max(
                        ((level, pct)
                         for level, pct in curriculum_bloom.items() if pct > 0),
                        key=lambda x: x[1],
                        default=(None, 0)
                    )[0] if curriculum_bloom else None
                })

        coverage_percentage = (len(tested_topics) /
                               len(topic_map)) * 100 if topic_map else 0

        return {
            "coveragePercentage": round(coverage_percentage),
            "testedTopics": tested_topics,
            "missedTopics": missed_topics,
            "topicAnalysis": topic_analysis,
            "examType": exam_type,
            "examScope": exam_scope,
            "isMidSemester": is_mid_semester
        }

    except Exception as e:
        print(f"❌ Coverage analysis failed: {e}")
        return {
            "coveragePercentage": 0,
            "testedTopics": [],
            "missedTopics": [],
            "topicAnalysis": [],
            "examType": "Comprehensive",
            "examScope": "",
            "isMidSemester": False
        }


def generate_insights(analysis):
    insights = {
        "strengths": [],
        "weaknesses": [],
        "recommendations": []
    }

    coverage = analysis["coveragePercentage"]
    tested = analysis["testedTopics"]
    missed = analysis["missedTopics"]
    topics = analysis["topicAnalysis"]
    exam_type = analysis.get("examType", "Comprehensive")
    exam_scope = analysis.get("examScope", "")
    is_mid_semester = analysis.get("isMidSemester", False)

    # Coverage insights - adjusted based on exam type
    if is_mid_semester:
        # Mid-semester exams: Expect 40-60% coverage, which is NORMAL
        insights["strengths"].append(
            f"📋 **Mid-Semester Exam** detected{f' (Scope: {exam_scope})' if exam_scope else ''} - Partial syllabus coverage is expected."
        )

        if coverage >= 40:
            insights["strengths"].append(
                f"✓ Good coverage at {coverage}% for a mid-semester exam - appropriate scope for the exam type."
            )
        elif coverage >= 25:
            insights["strengths"].append(
                f"Moderate coverage at {coverage}% - acceptable for a mid-semester exam, though slightly narrow."
            )
        else:
            insights["weaknesses"].append(
                f"Limited coverage at {coverage}% - even for a mid-semester exam, this seems restrictive."
            )

        # For mid-semester, only mention missed topics if coverage is unusually low
        if missed and coverage < 30:
            insights["recommendations"].append(
                f"Consider including questions from additional topics within the mid-semester scope to broaden assessment."
            )
    else:
        # Comprehensive exam: Expect 70-100% coverage
        insights["strengths"].append(
            f"📋 **Comprehensive Exam** detected{f' (Scope: {exam_scope})' if exam_scope else ''} - Full syllabus coverage is expected."
        )

        if coverage >= 80:
            insights["strengths"].append(
                f"✓ Excellent curriculum coverage at {coverage}% - the question paper addresses most topics comprehensively."
            )
        elif coverage >= 60:
            insights["strengths"].append(
                f"Good curriculum coverage at {coverage}%, though there's room for improvement."
            )
        elif coverage >= 40:
            insights["weaknesses"].append(
                f"⚠ Moderate coverage at {coverage}% - several curriculum topics are not assessed in this comprehensive exam."
            )
        else:
            insights["weaknesses"].append(
                f"❌ Low coverage at {coverage}% - many curriculum topics are missing from this comprehensive assessment."
            )

        # Comprehensive exams should mention missed topics more prominently
        if missed:
            missed_count = len(missed)
            total_topics = len(tested) + missed_count
            missed_percentage = (
                missed_count / total_topics * 100) if total_topics > 0 else 0

            insights["weaknesses"].append(
                f"{missed_count} topics ({round(missed_percentage)}%) are completely untested: {', '.join(missed[:3])}{'...' if len(missed) > 3 else ''}."
            )
            insights["recommendations"].append(
                f"For a comprehensive exam, add questions covering the missed topics: {', '.join(missed[:5])}{'...' if len(missed) > 5 else ''}."
            )

    # Bloom's taxonomy alignment
    misaligned_topics = []
    well_aligned_topics = []

    for topic in topics:
        if topic["tested"]:
            if topic.get("bloomMatch") == False:
                misaligned_topics.append({
                    "name": topic["topic"],
                    "expected": topic.get("curriculumExpectedBloom", "?"),
                    "actual": topic.get("dominantBloom", "?")
                })
            elif topic.get("bloomMatch") == True:
                well_aligned_topics.append(topic["topic"])

    if well_aligned_topics:
        insights["strengths"].append(
            f"{len(well_aligned_topics)} topics have questions matching the intended cognitive level.")

    if misaligned_topics:
        insights["weaknesses"].append(
            f"{len(misaligned_topics)} topics are tested at the wrong cognitive level.")
        for topic in misaligned_topics[:3]:  # Show first 3
            insights["recommendations"].append(
                f"'{topic['name']}': Adjust questions from {topic['actual']} level to {topic['expected']} level as per curriculum."
            )

    # Question distribution insights
    tested_topics_data = [t for t in topics if t["tested"]]
    if tested_topics_data:
        marks_per_topic = [t["totalMarks"] for t in tested_topics_data]
        avg_marks = sum(marks_per_topic) / len(marks_per_topic)
        uneven_topics = [t for t in tested_topics_data if t["totalMarks"]
                         < avg_marks * 0.5 or t["totalMarks"] > avg_marks * 1.5]

        if len(uneven_topics) >= len(tested_topics_data) * 0.3:
            insights["weaknesses"].append(
                "Uneven mark distribution across topics - some topics are over/under-emphasized.")
            insights["recommendations"].append(
                "Balance the marks allocation to give fair weight to all curriculum topics.")

    # Cognitive depth insights
    all_bloom_levels = set()
    for topic in tested_topics_data:
        all_bloom_levels.update(topic.get("bloomDistribution", {}).keys())

    if "Creating" in all_bloom_levels or "Evaluating" in all_bloom_levels:
        insights["strengths"].append(
            "Questions include higher-order thinking skills (Evaluating/Creating).")
    elif all_bloom_levels and max(all_bloom_levels, key=lambda x: ["Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"].index(x)) in ["Remembering", "Understanding"]:
        insights["weaknesses"].append(
            "Questions are predominantly lower-order (Remembering/Understanding) - limited higher-order thinking.")
        insights["recommendations"].append(
            "Include more questions at Applying, Analyzing, and Evaluating levels to challenge students.")

    return insights


@router.post("/analyze")
async def analyze_combined_endpoint(
    curriculum: UploadFile = File(...),
    questionPaper: UploadFile = File(...),
    useImageMode: Optional[str] = Form("false")
):
    """
    Combined analysis endpoint that supports both text-based and image-based analysis.

    Args:
        curriculum: PDF file of the curriculum
        questionPaper: PDF file of the question paper
        useImageMode: "true" or "false" - whether to use vision-based analysis for question paper
    """
    os.makedirs("uploads", exist_ok=True)

    curriculum_filename = f"curriculum_{uuid.uuid4()}.pdf"
    qpaper_filename = f"qpaper_{uuid.uuid4()}.pdf"
    curriculum_filepath = os.path.join("uploads", curriculum_filename)
    qpaper_filepath = os.path.join("uploads", qpaper_filename)

    # Convert string to boolean
    use_vision = useImageMode.lower() == "true"

    try:
        # Save uploaded files
        with open(curriculum_filepath, "wb") as buffer:
            shutil.copyfileobj(curriculum.file, buffer)

        with open(qpaper_filepath, "wb") as buffer:
            shutil.copyfileobj(questionPaper.file, buffer)

        print("📄 Step 1: Analyzing curriculum...")
        curriculum_result = analyze_curriculum_from_pdf(curriculum_filepath)

        if curriculum_result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=f"Curriculum analysis failed: {curriculum_result.get('reason')}"
            )

        topic_profiles = curriculum_result.get(
            "data", {}).get("topicProfiles", [])
        curriculum_topics = [topic["topicName"] for topic in topic_profiles]
        print(f"✓ Extracted {len(curriculum_topics)} topics")

        # Choose analysis method based on useImageMode parameter
        if use_vision:
            print("🖼️  Step 2: Analyzing question paper using VISION MODE (images)...")
            qpaper_result = analyze_qpaper_from_pdf_images(
                qpaper_filepath, curriculum_topics
            )
        else:
            print("📝 Step 2: Analyzing question paper using TEXT MODE...")
            qpaper_result = analyze_qpaper_from_pdf(
                qpaper_filepath, curriculum_topics
            )

        if qpaper_result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=f"Question paper analysis failed: {qpaper_result.get('reason')}"
            )

        print("💡 Step 3: Generating insights...")
        analysis = analyze_coverage(curriculum_result, qpaper_result)
        insights = generate_insights(analysis)

        # Log exam type detection
        exam_type = analysis.get("examType", "Comprehensive")
        exam_scope = analysis.get("examScope", "")
        print(
            f"✓ Detected exam type: {exam_type}{f' ({exam_scope})' if exam_scope else ''}")
        print(
            f"✓ Analysis complete: {analysis['coveragePercentage']}% coverage\n")

        return {
            "status": "success",
            "coveragePercentage": analysis["coveragePercentage"],
            "testedTopics": analysis["testedTopics"],
            "missedTopics": analysis["missedTopics"],
            "topicAnalysis": analysis["topicAnalysis"],
            "insights": insights,
            "examType": exam_type,
            "examScope": exam_scope,
            "isMidSemester": analysis.get("isMidSemester", False),
            "curriculumData": curriculum_result.get("data"),
            "questionPaperData": qpaper_result.get("data"),
            "analysisMode": "vision" if use_vision else "text"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    finally:
        # Clean up
        if os.path.exists(curriculum_filepath):
            os.remove(curriculum_filepath)
        if os.path.exists(qpaper_filepath):
            os.remove(qpaper_filepath)
