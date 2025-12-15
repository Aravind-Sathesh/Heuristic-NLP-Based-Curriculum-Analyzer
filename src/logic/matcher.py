from src.utils import load_sbert_model
from src.logic.bloom_classifier import get_bloom_level, BLOOM_LEVELS
from sentence_transformers import util
import torch
import re


def clean_text_for_embedding(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[|\-•*]{2,}', ' ', text)
    text = text.replace('|', ' ').replace('*', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def match_questions_to_syllabus(syllabus_data, exam_questions):
    """Match exam questions to syllabus topics using semantic similarity."""
    model = load_sbert_model()

    doc_embeddings = []
    doc_metadata = []

    # Index Syllabus
    for item in syllabus_data:
        topic = item['topic']
        bloom = item['bloom_level']

        clean_topic = clean_text_for_embedding(topic)
        if len(clean_topic) < 3:
            continue

        doc_embeddings.append(model.encode(
            clean_topic, convert_to_tensor=True))
        doc_metadata.append({"topic": clean_topic, "bloom_level": bloom})

    if not doc_embeddings:
        return []

    db_matrix = torch.stack(doc_embeddings)
    results = []

    for q in exam_questions:
        q_text = clean_text_for_embedding(q['text'])
        if len(q_text) < 15 or "page" in q_text.lower()[:10]:
            continue

        q_bloom, q_score, q_verb = get_bloom_level(q_text)

        if q_score == -1:
            continue

        q_emb = model.encode(q_text, convert_to_tensor=True)
        scores = util.cos_sim(q_emb, db_matrix)[0]
        best_score, best_idx = torch.max(scores, dim=0)

        bs = best_score.item()
        meta = doc_metadata[best_idx.item()]

        s_bloom = meta['bloom_level']
        s_score = BLOOM_LEVELS.get(s_bloom, 2)

        status = "Gap / Unmatched"
        if bs > 0.45:
            status = "Strong Match"
        elif bs > 0.32:
            status = "Partial Match"

        bloom_audit = "N/A"
        if "Match" in status:
            if q_score > s_score:
                bloom_audit = f"Too Hard ({q_bloom} > {s_bloom})"
            elif q_score < s_score:
                bloom_audit = f"Too Easy ({q_bloom} < {s_bloom})"
            else:
                bloom_audit = "Aligned"

        results.append({
            "question": q_text[:100] + "...",
            "matched_topic": meta['topic'],
            "match_status": status,
            "q_bloom": q_bloom,
            "s_bloom": s_bloom,
            "bloom_audit": bloom_audit
        })

    return results
