#set page(
  margin: (top: 1in, bottom: 1in, left: 1.15in, right: 1.15in)
)

#set text(
  font: "JetBrains Mono",
  size: 12pt,
)

#set list(
  indent: 1.4em,
  spacing: 1.5em
)

#set par(
  justify: true,
)

= Heuristic NLP Curriculum Analyzer

#set text(size: 10.5pt)
Aravind Sathesh,  
BITS Pilani · December 2025

== Introduction
The process of ensuring alignment between a course curriculum and its corresponding examinations is a critical but labor-intensive task in academic settings. Manual verification is often subjective, time-consuming, and does not scale effectively. This project introduces the Heuristic NLP Curriculum Analyzer, an automated tool designed to provide an objective, data-driven analysis of this alignment. The system ingests a course syllabus and an exam paper in PDF format and generates a comprehensive report evaluating two primary dimensions: (1) *Topic Coverage*, determining how well exam questions map to the topics outlined in the syllabus, and (2) *Cognitive Level Alignment*, assessing whether the cognitive demand of the questions, based on Bloom's Taxonomy, is consistent with the level intended for the topics. The primary objective is to equip educators and curriculum designers with a powerful tool to rapidly and objectively validate their assessment strategies.

== Methodology
The system is architected as a multi-stage, hybrid heuristic-semantic pipeline. It deliberately avoids a monolithic LLM-based approach in favor of specialized models and algorithms at each stage to maximize precision, control, and repeatability. The pipeline consists of four primary stages:

=== 1. Document Parsing and Content Extraction
The initial stage focuses on accurately extracting structured content from unstructured PDF documents. Different strategies are employed for the syllabus and the exam paper due to their distinct layouts.
-   *Exam Paper Parsing*: The `exam_parser.py` module utilizes the `PyMuPDF (fitz)` library to extract text blocks along with their precise coordinates. Text is sorted first by its vertical position (y0) and then horizontal (x0), faithfully reconstructing the reading order. A stateful grouping algorithm iterates through the sorted text lines, segmenting them into discrete questions by identifying question number patterns (e.g., "Q1.", "2(a)"). This coordinate-aware method is robust against multi-line questions and complex layouts.
-   *Syllabus Parsing*: The `syllabus_parser.py` performs an initial conversion of the syllabus PDF into a raw text or Markdown format, which serves as the input for the subsequent structuring stage.

=== 2. Syllabus Structuring and Topic Atomization
Raw text from the syllabus is processed by the `structured.py` module to produce a clean, atomic list of topics. This is achieved through a series of heuristic filters designed to remove administrative and bibliographic noise. These filters identify and discard common patterns related to grading schemes, textbook references, and instructional boilerplate. A key step is topic atomization, where lines containing multiple topics separated by delimiters (e.g., commas, semicolons) are split into individual entries. This ensures that the matching engine operates on granular, single-concept topics, significantly improving match precision.

=== 3. Bloom's Taxonomy Classification
The cognitive level of both syllabus topics and exam questions is determined by the `bloom_classifier.py` module. This is not a simple keyword search but a weighted scoring system powered by the `spaCy` NLP library. For each text input, the module performs Part-of-Speech (POS) tagging to identify verbs and nouns. These are then matched against a curated dictionary of terms associated with each of the six levels of Bloom's Taxonomy. The score is influenced by grammatical context (e.g., root verbs are weighted higher) and is further refined by high-impact phrase overrides (e.g., "difference between" strongly implies "Analyze"). The final level is determined by a resolving function that evaluates the weighted scores.

=== 4. Hybrid Semantic Matching
The core of the alignment analysis resides in the `matcher.py` module. It employs a hybrid scoring model that synergizes semantic similarity with keyword specificity.
-   *Semantic Similarity*: The `Sentence-BERT` model (`all-MiniLM-L6-v2`) is used to generate 384-dimensional vector embeddings for each question and all syllabus topics. The cosine similarity between a question's vector and each topic's vector provides a robust measure of contextual relatedness.
-   *Keyword Specificity*: To complement the semantic score, a keyword analysis is performed. Using `spaCy`'s POS tagger, the core concepts (nouns, proper nouns, adjectives) of a topic are extracted. The keyword score is the ratio of these core concepts found within the question text.
-   *Specificity-Aware Scoring Logic*: The final match score is a non-linear combination of the two signals. A "Specificity Bonus" is added, which is proportional to both the keyword score and the number of core concepts in the topic. This ensures that a perfect match on a detailed, multi-word topic like "Cryptographic Hash Functions" is scored significantly higher than a perfect match on a generic, single-word topic like "Bitcoin," making the system highly effective at identifying the most precise match.

== Results
The output of the analysis is a definitive, static report generated and displayed in the `Streamlit` web interface. The report provides both a high-level summary and a detailed, question-by-question breakdown of the alignment.
-   *Overall Alignment Score*: At the top of the report, a single, aggregated percentage is displayed. This metric provides an immediate, at-a-glance summary of the exam's overall alignment with the syllabus, calculated from the quality of both topic matches and cognitive level consistency across all questions.
-   *Detailed Analysis Table*: The main body of the report is a table where each row corresponds to a single exam question. The table presents the following automatically generated metrics: the question snippet, its assigned Bloom's level, the Bloom's level of the best-matched syllabus topic, a similarity score indicating match confidence, and a final, color-coded "Verdict" (e.g., "Perfect Alignment", "Too Hard", "Too Easy"). This granular view allows educators to pinpoint specific areas of misalignment without any manual intervention.

== Conclusion
The Heuristic NLP Curriculum Analyzer successfully automates the complex task of syllabus-exam alignment. By employing a hybrid pipeline of specialized models and heuristic algorithms, it provides a repeatable, objective, and data-driven analysis of both topic coverage and cognitive demand. The system's key innovation lies in its specificity-aware scoring logic, which allows it to discern between merely related and precisely correct topic matches. The final output, a comprehensive and static report, removes human subjectivity from the evaluation process, providing educators with a powerful and efficient tool for curriculum validation and refinement.

=== Future Work
While the current system is highly effective on text-based PDFs, several avenues for future enhancement exist:
-   *OCR Integration*: The most critical next step is to integrate an Optical Character Recognition (OCR) engine, such as Tesseract. This would enable the system to process scanned or image-based PDFs, significantly broadening its applicability.
-   *Vision Analysis*: The project architecture includes loaders for vision models (`Florence-2`, `YOLO`) that are currently unused. Future work could leverage these to analyze figures, diagrams, and graphs within exam questions, appending their descriptions to the question text for a more holistic semantic understanding.