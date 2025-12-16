import spacy
import re
from collections import defaultdict

try:
    nlp = spacy.load("en_core_web_sm")
except:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

BLOOMS_TAXONOMY = {
    "Remember": {
        "verbs": {"define", "list", "recall", "identify", "state", "mention", "label", "quote", "outline", "introduce"},
        "nouns": {"definition", "introduction", "overview", "history", "concept", "motivation", "background", "basics", "fundamental"}
    },
    "Understand": {
        "verbs": {"explain", "describe", "interpret", "summarize", "paraphrase", "discuss", "exemplify", "demonstrate", "visualize"},
        "nouns": {"explanation", "summary", "meaning", "representation", "theory", "intuition", "understanding"}
    },
    "Apply": {
        "verbs": {"solve", "calculate", "compute", "apply", "use", "implement", "execute", "sketch", "run", "train", "fit", "predict"},
        "nouns": {"calculation", "application", "value", "code", "program", "regression", "classification", "clustering", "technique", "method", "algorithm", "vector", "matrix"}
    },
    "Analyze": {
        "verbs": {"analyze", "differentiate", "distinguish", "examine", "investigate", "correlate", "contrast", "compare", "debug", "profile"},
        "nouns": {"analysis", "relationship", "breakdown", "diagram", "graph", "plot", "difference", "comparison", "trade-off", "selection", "variance", "bias"}
    },
    "Evaluate": {
        "verbs": {"evaluate", "judge", "assess", "critique", "justify", "defend", "verify", "argue", "conclude", "recommend", "validate", "test", "optimize", "tune"},
        "nouns": {"evaluation", "critique", "justification", "validity", "argument", "accuracy", "performance", "metric", "error", "regularization", "validation"}
    },
    "Create": {
        "verbs": {"create", "design", "compose", "formulate", "develop", "generate", "invent", "assemble", "write", "derive", "propose", "build", "construct", "synthesize"},
        "nouns": {"design", "formulation", "creation", "derivation", "proposal", "architecture", "framework", "system", "project", "model", "pipeline"}
    }
}

BLOOM_LEVELS_INT = {
    "Remember": 1, "Understand": 2, "Apply": 3,
    "Analyze": 4, "Evaluate": 5, "Create": 6
}

PHRASE_OVERRIDES = {
    "maths behind": "Analyze",
    "mathematical foundations": "Analyze",
    "vs": "Analyze",
    "versus": "Analyze",
    "difference between": "Analyze",
    "derive": "Create",
    "hands-on": "Apply",
    "build": "Create",
    "building": "Create",
    "introduction to": "Understand",
    "overview of": "Understand",
    "fundamentals of": "Understand",
    "case study": "Evaluate"
}

IGNORE_PATTERNS = r'(?i)^(instructions|date:|marks:|duration:|page|scanned by|camscanner|evaluation component|birla institute|all the best|course title|closed book)'


def calculate_sentence_scores(doc):
    scores = defaultdict(float)
    text_lower = doc.text.lower()

    for phrase, level in PHRASE_OVERRIDES.items():
        if re.search(r'\b' + re.escape(phrase) + r'\b', text_lower):
            scores[level] += 4.0

    noun_count = 0
    verb_count = 0

    for token in doc:
        lemma = token.lemma_.lower()

        if token.pos_ in ["NOUN", "PROPN"]:
            noun_count += 1
        if token.pos_ == "VERB":
            verb_count += 1

        for level, keywords in BLOOMS_TAXONOMY.items():
            weight = 0

            if lemma in keywords["verbs"]:
                weight = 1.0 if token.dep_ != "ROOT" else 2.0
            elif lemma in keywords["nouns"]:
                weight = 1.0

            scores[level] += weight

    if noun_count > 0 and verb_count == 0:
        if scores["Remember"] == 0 and scores["Understand"] == 0:
            scores["Apply"] += 1.5

    return scores


def resolve_bloom_level(scores, text):
    """Decides the final level."""
    if not scores:
        if len(text.split()) > 3:
            return ("Apply", 3, "Technical Default")
        return ("Remember", 1, "Metadata/Noise")

    if scores["Analyze"] >= 1.0 and scores["Analyze"] >= (max(scores.values()) * 0.6):
        return ("Analyze", 4, "Comparator Detected")

    best_level = max(scores, key=scores.get)
    max_score = scores[best_level]

    sorted_levels = sorted(BLOOM_LEVELS_INT.keys(),
                           key=lambda k: BLOOM_LEVELS_INT[k], reverse=True)

    for level in sorted_levels:
        if scores[level] >= (max_score * 0.75):
            return (level, BLOOM_LEVELS_INT[level], "Weighted Decision")

    return (best_level, BLOOM_LEVELS_INT[best_level], "Max-Score")


def get_bloom_level(text):
    if not text or len(text.strip()) < 5:
        return ("Metadata", -1, "Noise")

    if re.search(IGNORE_PATTERNS, text):
        return ("Metadata", -1, "Header/Footer")

    doc = nlp(text.strip())
    scores = calculate_sentence_scores(doc)

    has_math = re.search(r'[=+\-><]|\d+', text)
    if has_math and scores.get("Remember", 0) > scores.get("Apply", 0):
        scores["Apply"] += 2.0

    final_level, level_int, reason = resolve_bloom_level(scores, text)
    return (final_level, level_int, reason)
