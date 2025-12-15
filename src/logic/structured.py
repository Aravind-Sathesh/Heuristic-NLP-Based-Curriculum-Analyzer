import torch
import json
from pydantic import BaseModel, Field
from typing import List, Literal
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
from src.utils import get_slm


class SyllabusItem(BaseModel):
    topic: str = Field(...,
                       description="The specific technical concept or algorithm.")
    bloom_level: Literal["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"] = Field(
        ..., description="The cognitive level implied by the verb used for this specific topic.")


class SyllabusExtraction(BaseModel):
    items: List[SyllabusItem]


def get_sliding_windows(text, window_size=3000, overlap=500):
    windows = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + window_size
        if end < text_len:
            last_newline = text.rfind('\n', start, end)
            if last_newline != -1 and last_newline > start + (window_size // 2):
                end = last_newline
        windows.append(text[start:end])
        if end >= text_len:
            break
        start = end - overlap
    return windows


def extract_topics_from_chunk(text_chunk, model, tokenizer):
    parser = JsonSchemaParser(SyllabusExtraction.model_json_schema())
    prefix_function = build_transformers_prefix_allowed_tokens_fn(
        tokenizer, parser)

    prompt = f"""
Analyze the course syllabus text and extract specific technical topics with their Bloom's Taxonomy level.

Level determination:
- Define, List, State -> Remember
- Explain, Describe, Discuss -> Understand
- Calculate, Apply, Implement -> Apply
- Analyze, Compare, Differentiate -> Analyze
- Evaluate, Justify -> Evaluate
- Design, Create, Develop -> Create

Ignore administrative details. Be specific with topic names.

Text:
{text_chunk[:2500]}

JSON Output:
"""

    messages = [{"role": "user", "content": prompt}]
    text_input = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text_input], return_tensors="pt").to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=1024,  # More tokens needed for detailed JSON
            do_sample=False,
            prefix_allowed_tokens_fn=prefix_function
        )

    output = tokenizer.decode(generated_ids[0][len(
        inputs.input_ids[0]):], skip_special_tokens=True)

    try:
        data = json.loads(output)
        return data.get("items", [])
    except json.JSONDecodeError:
        return []


def extract_structured_syllabus(markdown_text):
    """Extract structured topics with Bloom levels from syllabus text."""
    windows = get_sliding_windows(markdown_text)

    model, tokenizer = get_slm()
    unique_topics = {}

    bloom_order = {"Remember": 1, "Understand": 2,
                   "Apply": 3, "Analyze": 4, "Evaluate": 5, "Create": 6}

    for i, window in enumerate(windows):
        items = extract_topics_from_chunk(window, model, tokenizer)

        for item in items:
            topic_clean = item['topic'].strip()
            bloom = item['bloom_level']

            if len(topic_clean) < 3 or "..." in topic_clean:
                continue

            if topic_clean.lower() in unique_topics:
                existing_bloom = unique_topics[topic_clean.lower(
                )]['bloom_level']
                if bloom_order[bloom] > bloom_order[existing_bloom]:
                    unique_topics[topic_clean.lower()]['bloom_level'] = bloom
            else:
                unique_topics[topic_clean.lower()] = {
                    "topic": topic_clean,
                    "bloom_level": bloom,
                    "source_segment": f"Segment {i+1}"
                }

    return list(unique_topics.values())
