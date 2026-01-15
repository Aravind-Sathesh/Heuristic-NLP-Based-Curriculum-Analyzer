"""Question-to-syllabus matching using hybrid semantic and keyword scoring."""

import torch
import re
import spacy
from sentence_transformers import util
from src.utils import load_sbert_model
from src.logic.bloom_classifier import get_bloom_level, BLOOM_LEVELS_INT

STRONG_MATCH_THRESHOLD = 0.48
PARTIAL_MATCH_THRESHOLD = 0.35

try:
    NLP = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    NLP = spacy.load("en_core_web_sm")


def clean_text_for_embedding(text):
    """Standardizes text for SBERT processing."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[|\-•*_]{2,}', ' ', text)
    text = text.replace('|', ' ').replace('*', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def calculate_keyword_score_with_specificity(question_text, topic_text):
    """Calculates keyword score and specificity using POS tagging."""
    question_tokens = set(question_text.lower().split())
    doc = NLP(topic_text)

    core_topic_tokens = {
        token.lemma_.lower() for token in doc
        if token.pos_ in {'NOUN', 'PROPN', 'ADJ', 'NUM'}
    }

    specificity = len(core_topic_tokens)
    if specificity == 0:
        return 0.0, 0

    common_tokens = question_tokens.intersection(core_topic_tokens)
    score = len(common_tokens) / specificity

    return score, specificity


def audit_bloom_alignment(q_score, s_score):
    """Determines if question cognitive load matches syllabus level."""
    diff = q_score - s_score
    if diff == 0:
        return "Perfect Alignment"
    elif diff == 1 or diff == -1:
        return "Acceptable"
    elif diff > 1:
        return "Too Hard"
    elif diff < -2:
        return "Too Easy"
    else:  # Covers diff == -2
        return "Acceptable"


def match_questions_to_syllabus(syllabus_data, exam_questions):
    """Links exam questions to syllabus topics using hybrid scoring."""
    model = load_sbert_model()

    syllabus_texts = []
    syllabus_meta = []
    for item in syllabus_data:
        topic = item['topic']
        if len(topic) < 3:
            continue
        syllabus_texts.append(topic)
        syllabus_meta.append(item)

    if not syllabus_texts:
        return []

    db_embeddings_clean = [clean_text_for_embedding(t) for t in syllabus_texts]
    db_embeddings = model.encode(db_embeddings_clean, convert_to_tensor=True)

    results = []

    for q in exam_questions:
        q_raw = q.get('text', '')
        q_clean = clean_text_for_embedding(q_raw)
        if len(q_clean) < 10 or "page" in q_clean[:10]:
            continue

        q_bloom_label, q_bloom_score, _ = get_bloom_level(q_raw)
        if q_bloom_score == -1:
            continue

        q_emb = model.encode(q_clean, convert_to_tensor=True)
        cosine_scores = util.cos_sim(q_emb, db_embeddings)[0]

        final_scores = []
        for idx, vec_s in enumerate(cosine_scores):
            vec_s = vec_s.item()
            kw_s, specificity = calculate_keyword_score_with_specificity(
                q_clean, syllabus_texts[idx])

            base_score = (vec_s * 0.8) + (kw_s * 0.2)
            specificity_bonus = (kw_s * (specificity / 10.0))
            combined_score = base_score + specificity_bonus
            final_scores.append(combined_score)

        final_scores = torch.tensor(final_scores)
        best_score, best_idx = torch.max(final_scores, dim=0)
        bs = min(best_score.item(), 1.0)

        matched_item = syllabus_meta[best_idx.item()]
        s_bloom_label = matched_item['bloom_level']
        s_bloom_score = BLOOM_LEVELS_INT.get(s_bloom_label, 2)

        match_status = "Gap / Unmatched"
        if bs > STRONG_MATCH_THRESHOLD:
            match_status = "Strong Match"
        elif bs > PARTIAL_MATCH_THRESHOLD:
            match_status = "Partial Match"

        if "Match" in match_status:
            audit_msg = audit_bloom_alignment(
                q_bloom_score, s_bloom_score)
        else:
            audit_msg = "N/A"

        results.append({
            "question_snippet": q_raw[:150] + "..." if len(q_raw) > 150 else q_raw,
            "matched_topic": matched_item['topic'],
            "similarity_score": round(bs, 2),
            "match_status": match_status,
            "question_bloom": f"{q_bloom_label} ({q_bloom_score})",
            "syllabus_bloom": f"{s_bloom_label} ({s_bloom_score})",
            "verdict": audit_msg
        })

    return results
