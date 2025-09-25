# LLM Based Curriculum Analyzer 📚

An intelligent system that leverages Large Language Models to analyze university curricula and question papers, providing structured insights into course content, learning outcomes, and cognitive complexity using Bloom's Taxonomy classification.

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![Google AI](https://img.shields.io/badge/Google_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)
![PDF](https://img.shields.io/badge/PDF_Processing-FF0000?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)

![PyMuPDF](https://img.shields.io/badge/PyMuPDF-40826D?style=for-the-badge&logo=pdf&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-FF4B4B?style=for-the-badge&logo=uvicorn&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-3776AB?style=for-the-badge&logo=python&logoColor=white)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/downloads/)

</div>

---

## Features

### **Intelligent Document Analysis**

- **PDF Text Extraction**: Advanced text extraction from curriculum and question paper PDFs
- **LLM-Powered Analysis**: Uses Google's Gemini AI for sophisticated content understanding
- **Bloom's Taxonomy Classification**: Categorizes learning objectives by cognitive complexity

### **Curriculum Analysis**

- **Topic Consolidation**: Identifies and groups related topics into broader categories
- **Learning Outcome Assessment**: Analyzes and validates learning objectives
- **Cognitive Depth Profiling**: Provides percentage distribution across Bloom's taxonomy levels
- **Complete Coverage Validation**: Ensures all syllabus content is accounted for

### **Question Paper Analysis**

- **Question Classification**: Categorizes questions by topic and difficulty
- **Bloom's Level Mapping**: Maps each question to appropriate cognitive level
- **Coverage Analysis**: Identifies curriculum coverage gaps in assessments

### **RESTful API**

- **FastAPI Framework**: High-performance, modern API with automatic documentation
- **File Upload Support**: Secure PDF upload and processing
- **CORS Enabled**: Cross-origin resource sharing for web integration
- **Error Handling**: Comprehensive error responses and validation

---

## Use Cases

### **For Educators**

- **Curriculum Design**: Analyze and improve course structure and learning outcomes
- **Assessment Quality**: Evaluate question papers for cognitive balance and coverage
- **Bloom's Alignment**: Ensure assessments match intended learning objectives
- **Gap Analysis**: Identify missing topics or cognitive levels in curricula

### **For Academic Administrators**

- **Quality Assurance**: Standardize curriculum analysis across departments
- **Accreditation Support**: Generate detailed reports for accreditation bodies
- **Curriculum Mapping**: Map courses to program learning outcomes
- **Benchmarking**: Compare curricula against educational standards

### **For Researchers**

- **Educational Analytics**: Study patterns in curriculum design and assessment
- **Bloom's Taxonomy Research**: Analyze cognitive complexity trends
- **Automated Analysis**: Scale curriculum analysis across large datasets
- **Comparative Studies**: Compare curricula across institutions or programs

---

## Tech Stack

<div align="center">

| Layer                 | Technology         | Purpose                                       |
| --------------------- | ------------------ | --------------------------------------------- |
| **Backend Framework** | FastAPI            | High-performance, modern Python web framework |
| **AI/ML**             | Google Gemini AI   | Advanced language model for content analysis  |
| **PDF Processing**    | PyMuPDF            | Robust PDF text and image extraction          |
| **Image Processing**  | Pillow + pdf2image | PDF to image conversion and processing        |
| **Server**            | Uvicorn            | Lightning-fast ASGI server                    |
| **Environment**       | python-dotenv      | Environment variable management               |
| **File Handling**     | python-multipart   | Multipart file upload support                 |

</div>

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Google AI API key (Gemini)

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd "LLM Based Curriculum Analyzer"
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Environment configuration**

   ```bash
   # Create .env file in backend directory
   echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

---

## Usage

### API Endpoints

#### Curriculum Analysis

```bash
POST /curriculum/analyze
```

Upload a curriculum PDF and receive structured analysis with:

- Broad topic identification
- Bloom's taxonomy classification
- Learning outcome validation
- Coverage analysis

#### Question Paper Analysis

```bash
POST /qpaper/analyze
```

Upload a question paper PDF and receive:

- Question categorization
- Cognitive level mapping
- Topic coverage assessment
- Difficulty distribution

### Example Usage

```python
import requests

# Analyze curriculum
with open('curriculum.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/curriculum/analyze',
        files={'file': f}
    )
    analysis = response.json()
    print(analysis)
```

### API Documentation

Once the server is running, visit:

- **Interactive API docs**: `http://localhost:8000/docs`
- **Alternative docs**: `http://localhost:8000/redoc`

---

## Project Structure

```
LLM Based Curriculum Analyzer/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── api/                    # API route handlers
│   │   ├── curriculum_routes.py
│   │   └── qpaper_routes.py
│   ├── core/                   # Core business logic
│   │   └── analysis_logic.py
│   ├── services/               # External service integrations
│   │   ├── llm_service.py     # Google Gemini AI integration
│   │   └── pdf_service.py     # PDF processing utilities
│   ├── prompts/               # LLM prompt templates
│   │   ├── curriculum_parser.md
│   │   └── qpaper_parser.md
│   └── uploads/               # Temporary file storage
├── handout.pdf                # Project documentation
├── README.md                  # This file
├── LICENSE                    # Apache 2.0 license
└── .gitignore                # Git ignore patterns
```

---

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Google AI Configuration
GOOGLE_API_KEY=your_google_ai_api_key

# Optional: Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### Customizing Prompts

The system uses Markdown-based prompt templates located in `backend/prompts/`:

- `curriculum_parser.md`: Template for curriculum analysis
- `qpaper_parser.md`: Template for question paper analysis

Modify these files to customize the analysis behavior and output format.

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include unit tests for new features
- Update documentation as needed

---

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)

---

## Acknowledgments

- **Google AI**: For providing the powerful Gemini language model
- **FastAPI Community**: For the excellent web framework
- **PyMuPDF**: For robust PDF processing capabilities
- **Educational Research Community**: For Bloom's Taxonomy framework

---

## Support

If you encounter any issues or have questions:

1. Check the [API documentation](http://localhost:8000/docs) for endpoint details
2. Review the prompt templates in `backend/prompts/` for customization options
3. Ensure your Google AI API key is properly configured
4. Verify that all dependencies are installed correctly

For additional support, please open an issue in the repository.
