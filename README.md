# Heuristic NLP Curriculum Analyzer

This project is a tool designed to analyze the alignment between a course syllabus (or handout) and its corresponding exam paper. It evaluates alignment on two primary dimensions: topic coverage and the cognitive level of questions, based on Bloom's Taxonomy. The final output is an interactive report where the user can validate and override the AI's initial analysis.

## How It Works

The system follows a five-step pipeline, orchestrated by the main application file:

1.  **Input:** The user uploads a syllabus PDF and an exam paper PDF through the Streamlit web interface.

2.  **Syllabus Parsing:** The syllabus PDF is converted to raw text. This text is then processed by a series of heuristic filters that clean administrative noise (e.g., grading policies, reference books) and extract a clean, structured list of individual course topics.

3.  **Exam Parsing:** The exam paper PDF is carefully parsed using a coordinate-based text extraction method. This preserves the reading order and allows a stateful algorithm to accurately group lines of text into distinct questions, even when they span multiple lines or include sub-parts.

4.  **Bloom's Level Classification:** Both the extracted syllabus topics and the exam questions are individually analyzed to determine their cognitive level according to Bloom's Taxonomy (e.g., Remember, Apply, Analyze). This is done using a linguistic model that considers verbs, nouns, and key instructional phrases.

5.  **Alignment Analysis & Reporting:** Each exam question is matched against the entire list of syllabus topics using a sophisticated hybrid scoring model. This model combines semantic similarity (from Sentence-BERT) with a linguistics-based keyword analysis (from SpaCy) that rewards specificity. The results are compiled into a report, and an overall alignment score is calculated.

## Tech Stack

The application is built with a combination of a web framework for the user interface and a specialized set of NLP and PDF processing libraries for the core analysis logic.

- **Python 3.9+**: The core programming language for the entire project.
- **Streamlit**: Used to build the interactive, web-based user interface and orchestrate the analysis pipeline.
- **spaCy (`en_core_web_sm` model)**: The engine for linguistic analysis. It performs Part-of-Speech (POS) tagging and lemmatization, which are critical for the heuristic Bloom's classifier and for identifying the core noun concepts in syllabus topics.
- **Sentence-Transformers (`all-MiniLM-L6-v2` model)**: Used to generate the dense vector embeddings for both questions and syllabus topics. This model is the foundation of the semantic similarity scoring in the matching engine.
- **PyMuPDF (`fitz`)**: The primary tool for parsing PDF documents. It is used for its ability to extract text along with its precise coordinates, which is essential for the `exam_parser` to accurately reconstruct the document's layout and group questions correctly.
- **PyTorch**: Serves as the underlying deep learning framework for the `sentence-transformers` library.

## Project Structure

The project is organized into several key directories and files:

```
.
├── app.py                  # Main Streamlit application file
├── install_models.py       # Script to download and cache ML models
├── requirements.txt        # Project dependencies
|
├── data/
│   ├── temp/               # Temporary storage for uploaded PDF files
│   └── feedback/           # Directory for storing user feedback
│
├── src/
│   ├── logic/
│   │   ├── bloom_classifier.py  # Bloom's Taxonomy classification engine
│   │   ├── matcher.py           # Core alignment and matching engine
│   │   └── structured.py        # Syllabus text structuring engine
│   │
│   ├── parser/
│   │   ├── exam_parser.py       # Exam PDF content extractor
│   │   └── syllabus_parser.py   # Syllabus PDF to text converter
│   │
│   └── utils.py                 # Centralized model loader utility
│
└── assets/
    └── taxonomy guide.png    # Image asset for the UI
```

## File Breakdown

This section provides a detailed report on the role of each file in the project.

### Core Application Files

- **`app.py`**: This is the entry point for the application. It uses the Streamlit library to create the web-based user interface, including file uploaders and buttons. It orchestrates the entire analysis pipeline by calling functions from the other modules in the correct sequence. It is responsible for displaying the final, interactive report and handling real-time updates when the user edits the Bloom's levels.

- **`install_models.py`**: This is a one-time setup script. Its purpose is to download and cache all the required machine learning models from online repositories like HuggingFace. Running this script ensures that the application has all the necessary model files available locally before it is run for the first time.

### `src/parser/` - PDF Parsing and Text Extraction

- **`syllabus_parser.py`**: A simple module that handles the initial conversion of the syllabus PDF into raw, unstructured Markdown or text, preparing it for the structuring logic.
- **`exam_parser.py`**: This module is dedicated to parsing the exam paper PDF. It uses the `fitz` (PyMuPDF) library to extract text along with its coordinates on the page. This allows it to sort the text in the correct reading order, filter out common headers and footers, and use a stateful grouping algorithm to accurately segment the document into a list of individual questions.

### `src/logic/` - Analysis and Intelligence

- **`structured.py`**: This module takes the raw text from the syllabus and transforms it into a clean, structured list of topics. It contains a series of heuristic functions that act as filters to identify and remove irrelevant content like bibliographic information, grading schemes, and descriptive sentences.
- **`bloom_classifier.py`**: This is the Bloom's Taxonomy analysis engine. It uses the `spaCy` NLP library to perform linguistic analysis. Its classification is based on a multi-layered heuristic model that scores text based on the presence of specific verbs and nouns, high-impact phrase overrides, and the grammatical structure of the text.
- **`matcher.py`**: This is the heart of the analysis. It takes the list of questions and the list of syllabus topics as input. For each question, it calculates a match score against every topic using a specificity-aware hybrid model. This model intelligently blends a semantic vector score (from `Sentence-BERT`) with a keyword score derived from Part-of-Speech tagging.

### `src/utils.py` - Utilities

- **`utils.py`**: This utility script acts as a singleton loader for all the machine learning models used in the project. It contains functions to load models like `Sentence-BERT`, ensuring that each large model is loaded into memory only once, improving efficiency and resource management.

## Setup and Usage

1.  **Install Dependencies:** Install all required Python packages from the requirements file.

    ```
    pip install -r requirements.txt
    ```

2.  **Run the Application:** Start the Streamlit web server.
    ```
    streamlit run app.py
    ```

**Note on Models:** The first time you run the application, the necessary NLP models from `spaCy` (for linguistic analysis) and `sentence-transformers` (for semantic analysis) will be downloaded and cached automatically. This may take a few minutes, but it is a one-time process. No manual model download is required.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
