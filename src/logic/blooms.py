import spacy
import re

try:
    nlp = spacy.load("en_core_web_sm")
except:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

BLOOMS_VERBS = {
    "Remember": [
        "define", "list", "recall", "identify", "name", "state", "describe",
        "label", "match", "select", "outline", "reproduce", "what", "which",
        "who", "fill", "find", "step", "mention", "where", "when"
    ],
    "Understand": [
        "explain", "summarize", "interpret", "paraphrase", "classify", "compare",
        "infer", "demonstrate", "illustrate", "predict", "discuss", "contrast",
        "give"
    ],
    "Apply": [
        "solve", "apply", "use", "calculate", "compute", "modify", "construct",
        "determine", "show", "perform", "assume", "predict"
    ],
    "Analyze": [
        "analyze", "distinguish", "differentiate", "examine", "investigate",
        "categorize", "deconstruct", "deduce", "diagram"
    ],
    "Evaluate": [
        "evaluate", "judge", "assess", "critique", "justify", "defend",
        "prioritize", "rate", "verify", "argue", "conclude"
    ],
    "Create": [
        "create", "design", "compose", "formulate", "propose", "develop",
        "generate", "invent", "assemble", "write"
    ]
}

STRONG_NOUNS = {
    "Understand": ["mechanism", "role", "function", "significance", "conversion", "process", "difference"],
    "Analyze": ["relationship", "comparison", "contrast"],
    "Evaluate": ["justification", "consequence", "validity"],
    "Create": ["derivation"]
}

BLOOMS_SCORES = {
    "Remember": 1, "Understand": 2, "Apply": 3,
    "Analyze": 4, "Evaluate": 5, "Create": 6
}

IGNORE_PATTERNS = r'(?i)^(instructions|date:|marks:|duration:|page|scanned by|camscanner|evaluation component|birla institute|all the best)'


def get_bloom_level(text):
    """
    Returns (Level, Score, Trigger_Word).
    Strategy: Verb Detection + Noun Boosting.
    """
    # Filter Metadata
    if re.search(IGNORE_PATTERNS, text):
        return ("Metadata", -1, None)

    # Filter pure OCR garbage (sequences of random chars)
    if len(text) < 3 or re.search(r'[^\w\s.,?()\-]', text):
        if len(text) > 10 and sum(c.isalpha() for c in text) / len(text) < 0.5:
            return ("Metadata", -1, "Noise")

    sentences = re.split(r'(?<=[.?!])\s+', text)
    max_level = ("Unknown", 0, None)

    for sentence in sentences:
        doc = nlp(sentence.lower().strip())

        found_word = None
        current_score = 0
        current_level = "Unknown"

        # Verb Search
        target_verb = None
        for token in doc:
            if token.pos_ == "VERB" and token.dep_ == "ROOT":
                target_verb = token.lemma_
                break

        # Fallback to first word if it looks like a question starter
        if not target_verb and len(doc) > 0:
            if doc[0].text in ["what", "which", "name", "define", "fill", "assume", "mention", "give"]:
                target_verb = doc[0].text

        # Map Verb
        if target_verb:
            for level, verbs in BLOOMS_VERBS.items():
                if target_verb in verbs:
                    current_level = level
                    current_score = BLOOMS_SCORES[level]
                    found_word = target_verb
                    break

        # Scan for "Strong Nouns" that imply higher cognition
        for token in doc:
            noun = token.lemma_
            for level, nouns in STRONG_NOUNS.items():
                if noun in nouns:
                    noun_score = BLOOMS_SCORES[level]
                    if noun_score > current_score:
                        current_score = noun_score
                        current_level = level
                        found_word = noun

        if current_score > max_level[1]:
            max_level = (current_level, current_score, found_word)

    if max_level[0] == "Unknown" and len(text.split()) < 6:
        return ("Data", 0, None)

    return max_level
