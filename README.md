# Project Plan

## Tech Stack

- **Language:** Python 3.9+
- **Layout Analysis:** `LayoutParser` (Model: Detectron2) + `Tesseract` (OCR)
- **NLP / Logic:** `spaCy` (Language parsing), `Rank-BM25` (Keyword search)
- **Embeddings:** `Sentence-BERT` (`all-MiniLM-L6-v2`)
- **Vision SLM:** `Microsoft Florence-2-base` (via HuggingFace)
- **UI:** `Streamlit`

---

## Proposed File Tree

```text
/
├── data/
│   ├── raw/                # Uploaded PDFs go here
│   └── processed/          # Intermediate JSONs (debug logs)
│
├── src/
│   ├── parser/
│   │   ├── layout.py       # Detectron2 logic (Block detection)
│   │   └── cleaner.py      # OCR & text cleaning rules
│   │
│   ├── content/
│   │   ├── syllabus.py     # Header/Topic extraction logic
│   │   ├── exam.py         # Question segmentation logic
│   │   └── vision.py       # Florence-2 inference for diagrams
│   │
│   ├── logic/
│   │   ├── blooms.py       # spaCy verb extraction & scoring
│   │   └── matcher.py      # Hybrid Search (BM25 + SBERT)
│   │
│   └── utils.py            # Image cropping helpers
│
├── app.py                  # Streamlit main UI
├── requirements.txt
└── Dockerfile
```

---

## Implementation Roadmap

### Phase 1: Core Setup & Layout Engine

1.  Setup local Python environment.
2.  Install `detectron2` and `layoutparser`.
3.  Create `src/parser/layout.py`:
    - Input: PDF Path.
    - Process: Convert pages to images -> Run LayoutParser.
    - Output: List of bounding boxes with labels (Text, Title, Figure).
4.  Integrate Tesseract to extract text from those boxes.

### Phase 2: Syllabus Processor (Structure & Depth)

1.  Create `src/content/syllabus.py`:
    - Use font size/weight metadata from Phase 1 to differentiate "Topics" from "Learning Outcomes".
    - Reconstruct hierarchy (Parent Topic -> Child Bullets).
2.  Create `src/logic/blooms.py`:
    - Define dictionary of Bloom's Taxonomy verbs (Level 1-6).
    - Use `spaCy` to extract the **root verb** from each learning outcome.
    - Assign a "Depth Score" to every topic.

### Phase 3: Exam Processor (Vision & Multimodality)

1.  Create `src/content/exam.py`:
    - Group text blocks into discrete questions (Regex/Spacing logic).
2.  Create `src/content/vision.py`:
    - Load `Florence-2` model.
    - Implement function: Crop image from PDF -> Send to Model -> Return Caption.
3.  Integrate: If a question has an image, append the caption to the question text.

### Phase 4: The Audit Logic

1.  Create `src/logic/matcher.py`:
    - Load SBERT model.
    - Implement **Hybrid Search**:
      - Run BM25 (Keyword) on Syllabus vs Questions.
      - Run Cosine Similarity (Vector) on Syllabus vs Questions.
      - Combine scores (Reciprocal Rank Fusion).
2.  Generate Audit Result:
    - For each question, find best matching Topic.
    - Compare Question Depth (Bloom's) vs Topic Depth.

### Phase 5: UI & Containerization

1.  Build `app.py`:
    - Two file uploaders (Syllabus, Exam).
    - Run pipeline.
    - Display results in a DataFrame/Table.
2.  Write `Dockerfile` to handle the heavy PyTorch/Detectron dependencies.
