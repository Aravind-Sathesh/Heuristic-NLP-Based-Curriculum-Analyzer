"""Syllabus extraction using heuristic filtering and Bloom classification."""

import re
from difflib import SequenceMatcher
from src.logic.bloom_classifier import get_bloom_level


def is_bibliographic_junk(text):
    """Detects book citations and bibliographic content."""
    t = text.lower().strip()

    pub_keywords = [
        'springer', 'oreilly', 'o\'reilly', 'mcgraw', 'pearson', 'wiley',
        'university press', 'cambridge', 'oxford', 'edition', 'vol.',
        'pp.', 'isbn', 'handbook', 'publishing', 'editors'
    ]

    if any(k in t for k in pub_keywords):
        return True

    if re.search(r'[\(\s](19|20)\d{2}[\)\.\s]*$', t):
        if t.count(',') > 0 or len(t.split()) < 5:
            return True

    if re.match(r'^[tr]\d+\s+[a-z]', t, re.IGNORECASE):
        return True

    if re.match(r'^[\d\.\-\s,]+$', t):
        return True

    return False


def is_header_or_separator(text):
    """Detects section headers and separator lines."""
    t = text.lower().strip()

    if re.match(r'^[\-\=_]{3,}$', t):
        return True

    headers = [
        'scope', 'objectives', 'outcomes', 'evaluation', 'grading',
        'lecture plan', 'course plan', 'text books', 'reference books',
        'references', 'reading list', 'textbook', 'syllabus',
        'evaluation scheme', 'chamber consultation'
    ]

    if any(h in t for h in headers):
        if len(t.split()) < 6:
            return True

    return False


def is_descriptive_sentence(text):
    """Detects descriptive sentences rather than topic listings."""
    t = text.lower()

    starters = [
        'this course', 'the course', 'it empowers', 'given that',
        'the primary objective', 'in this', 'students will',
        'to test run', 'practical sessions', 'lecture plan',
        'in addition to'
    ]
    if any(t.startswith(s) for s in starters):
        return True

    if len(t.split()) > 15:
        if any(w in t for w in ['aims', 'provides', 'introduces', 'designed', 'integration']):
            return True

    return False


def get_junk_density_score(text):
    """Calculates probability of administrative noise."""
    t = text.lower()
    score = 0.0

    admin_roots = [
        'instruct', 'prof', 'faculty', 'evaluat', 'grad', 'weight',
        'semester', 'exam', 'book', 'sched', 'plan', 'objectiv',
        'outcom', 'honest', 'policy', 'date', 'page', 'notic',
        'consultation', 'chamber', 'scheme', 'scope'
    ]

    if any(root in t for root in admin_roots):
        score += 0.4

    if '---' in t or '|' in t:
        score += 0.5

    ref_count = len(re.findall(r'\b[TR]\d+\b', text))
    if ref_count > 0:
        if len(t) < 15:
            score += 0.4

    return score


def heuristic_line_cleaner(text):
    """Cleans glued tokens, reference codes, and noise."""
    t = text.strip()

    t = re.sub(r'\s*\([^)]*\)\s*', ' ', t)
    t = re.sub(r'(?<=\d)(?=[A-Z])', ' ', t)
    t = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', t)
    t = re.sub(r'(?<=[a-z])\.(?=[TR]\d)', ' ', t, flags=re.IGNORECASE)
    t = t.replace('br', ' ')

    t = re.sub(r'^[\d\.\-\)\*\•\>]+\s+', '', t)
    t = re.sub(r'[\s\.,]+(T|R|Ch|Vol|Ref)\.?\s*[\d\.\-\,]*$',
               '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\s,]+etc\.?$', '', t, flags=re.IGNORECASE)

    fluff_patterns = [
        r'^(to|the)\s+(understand|get|know|learn|explore|introduce|build|test|identify|analyze)\s+(an|a|the)?',
        r'^introduction\s+to\s+',
        r'^overview\s+of\s+',
        r'^basics\s+of\s+',
        r'^foundations?\s+(of|in)\s+',
        r'^principles\s+of\s+',
        r'^methods?\s+(of|in)\s+',
        r'^concepts?\s+(of|in)\s+'
    ]
    for p in fluff_patterns:
        t = re.sub(p, '', t, flags=re.IGNORECASE)

    t = re.sub(r'[^\w\s\-\.,]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.strip('.,- ')

    return t


def get_candidate_lines(text):
    """Extracts text blocks and splits by boundaries like newlines and periods."""
    # 1. Try to isolate the main syllabus content between common headers
    meat_pattern = r'(?:Objectives|Outcomes|Scope|Plan|Syllabus|Topics|Schedule)[\s\S]*?(?=\n\s*(?:Evaluation|Grading|Text\s*Book|Reference|Reading|Comprehensive))'
    match = re.search(meat_pattern, text, re.IGNORECASE)
    target_text = match.group(0) if match else text

    # 2. Normalize newlines to a unique token to split on later
    normalized = target_text.replace('\n', ' <NL> ')

    # 3. Split by sentence-ending punctuation, avoiding abbreviations
    chunks = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', normalized)

    candidates = []
    for chunk in chunks:
        # Now split by the newline token
        lines = chunk.split('<NL>')
        for line in lines:
            clean = line.strip()
            if len(clean) > 3:  # Filter out empty or very short lines
                candidates.append(clean)

    return candidates


def deduplicate_fuzzy(entries):
    """Clusters similar topics."""
    if not entries:
        return []

    sorted_entries = sorted(
        entries, key=lambda x: len(x['topic']), reverse=True)

    final_list = []
    processed_indices = set()

    bloom_rank_map = {"Remember": 1, "Understand": 2,
                      "Apply": 3, "Analyze": 4, "Evaluate": 5, "Create": 6}

    for i in range(len(sorted_entries)):
        if i in processed_indices:
            continue

        current = sorted_entries[i]

        for j in range(i + 1, len(sorted_entries)):
            if j in processed_indices:
                continue

            candidate = sorted_entries[j]
            current_topic_lower = current['topic'].lower()
            candidate_topic_lower = candidate['topic'].lower()

            ratio = SequenceMatcher(
                None, current_topic_lower, candidate_topic_lower).ratio()
            is_substring = candidate_topic_lower in current_topic_lower

            if ratio > 0.8 or is_substring:
                curr_rank = bloom_rank_map.get(current['bloom_level'], 0)
                cand_rank = bloom_rank_map.get(candidate['bloom_level'], 0)

                if cand_rank > curr_rank:
                    current = candidate

                processed_indices.add(j)

        final_list.append(current)

    return final_list


def extract_structured_syllabus(markdown_text):
    """Main extraction pipeline."""
    raw_lines = get_candidate_lines(markdown_text)
    extracted_data = []

    for line in raw_lines:
        if is_header_or_separator(line):
            continue
        if get_junk_density_score(line) > 0.5:
            continue
        if is_bibliographic_junk(line):
            continue
        if is_descriptive_sentence(line):
            continue

        cleaned_line = heuristic_line_cleaner(line)

        if len(cleaned_line) < 5:
            continue

        potential_topics = re.split(r'[;,]|\s+and\s+', cleaned_line)
        level, score, _ = get_bloom_level(line)
        if level in ["Metadata", "Unknown"] or score < 1:
            continue

        for topic in potential_topics:
            topic_final = topic.strip()
            if len(topic_final) < 3:
                continue
            if topic_final[0].islower() and topic_final.split()[0] not in ['e.g.']:
                continue
            if re.match(r'^(or|of|the|in|with)\s+', topic_final, re.IGNORECASE):
                continue

            extracted_data.append({
                "topic": topic_final,
                "bloom_level": level
            })

    final_output = deduplicate_fuzzy(extracted_data)

    return final_output
