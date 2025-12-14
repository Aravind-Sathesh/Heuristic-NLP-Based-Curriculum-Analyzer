import re


def extract_syllabus_structure(extracted_pages):
    """Converts layout blocks into structured topic list."""
    raw_lines = []

    # Flatten text blocks
    for page in extracted_pages:
        for block in page['layout']:
            if block.type in ["Text", "List"]:
                lines = block.text.split('\n')
                raw_lines.extend([l.strip() for l in lines if l.strip()])

    structure = []
    current_topic = "General Content"
    current_outcomes = []

    for line in raw_lines:
        # Detect Headers (Start with Module/Unit or All Caps)
        is_header = False
        if re.match(r'^(Module|Unit|Chapter)\s+\d+', line, re.IGNORECASE):
            is_header = True
        elif line.isupper() and len(line) > 10:
            is_header = True

        if is_header:
            if current_outcomes:
                structure.append({
                    "topic": current_topic,
                    "outcomes": current_outcomes
                })
            current_topic = line
            current_outcomes = []
        else:
            # Filter noise (short lines, page numbers)
            if len(line) > 20 and not re.match(r'Page \d', line):
                current_outcomes.append(line)

    if current_outcomes:
        structure.append({
            "topic": current_topic,
            "outcomes": current_outcomes
        })

    return structure
