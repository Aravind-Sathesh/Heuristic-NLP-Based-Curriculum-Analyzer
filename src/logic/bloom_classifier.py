import spacy
import re

# Load English model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

BLOOMS_VERBS = {
    "Remember": ["define", "list", "recall", "identify", "name", "state", "describe", "label", "match", "select", "outline", "reproduce", "what", "which", "who", "fill", "find", "step", "mention", "where", "when"],
    "Understand": ["explain", "summarize", "interpret", "paraphrase", "classify", "compare", "infer", "demonstrate", "illustrate", "predict", "discuss", "contrast", "give"],
    "Apply": ["solve", "apply", "use", "calculate", "compute", "modify", "construct", "determine", "show", "perform", "assume", "predict"],
    "Analyze": ["analyze", "distinguish", "differentiate", "examine", "investigate", "categorize", "deconstruct", "deduce", "diagram"],
    "Evaluate": ["evaluate", "judge", "assess", "critique", "justify", "defend", "prioritize", "rate", "verify", "argue", "conclude"],
    "Create": ["create", "design", "compose", "formulate", "propose", "develop", "generate", "invent", "assemble", "write"]
}

STRONG_NOUNS = {
    "Understand": ["mechanism", "role", "function", "significance", "conversion", "process", "difference"],
    "Analyze": ["relationship", "comparison", "contrast"],
    "Evaluate": ["justification", "consequence", "validity"],
    "Create": ["derivation"]
}

BLOOM_LEVELS = {
    "Remember": 1, "Understand": 2, "Apply": 3,
    "Analyze": 4, "Evaluate": 5, "Create": 6
}

IGNORE_PATTERNS = r'(?i)^(instructions|date:|marks:|duration:|page|scanned by|camscanner|evaluation component|birla institute|all the best)'


def get_bloom_level(text):
    if re.search(IGNORE_PATTERNS, text):
        return ("Metadata", -1, None)

    if len(text) < 10:
        return ("Metadata", -1, "Noise")

    doc = nlp(text.lower().strip())
    max_level = ("Unknown", 0, None)

    for token in doc:
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            lemma = token.lemma_
            for level, verbs in BLOOMS_VERBS.items():
                if lemma in verbs:
                    return (level, BLOOM_LEVELS[level], lemma)

    for token in doc:
        if token.pos_ == "VERB":
            lemma = token.lemma_
            for level, verbs in BLOOMS_VERBS.items():
                if lemma in verbs:
                    if BLOOM_LEVELS[level] > max_level[1]:
                        max_level = (level, BLOOM_LEVELS[level], lemma)

    if max_level[1] == 0:
        for token in doc:
            lemma = token.lemma_
            for level, nouns in STRONG_NOUNS.items():
                if lemma in nouns:
                    if BLOOM_LEVELS[level] > max_level[1]:
                        max_level = (level, BLOOM_LEVELS[level], lemma)

    if max_level[0] == "Unknown":
        return ("Understand", 2, "Implicit")

    return max_level
