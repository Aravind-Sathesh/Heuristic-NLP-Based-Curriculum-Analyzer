# Image-Based Analysis Workflow

## Overview

The LLM-Based Curriculum Analyzer now supports **dual analysis modes**:

1. **Text Mode** (Default) - Fast, efficient text extraction for standard question papers
2. **Vision Mode** (Optional) - Advanced image-based analysis for papers with diagrams, graphs, and visual elements

## When to Use Vision Mode

Enable vision mode when your question paper contains:

- ✅ Circuit diagrams (electrical/electronic engineering)
- ✅ Graphs and charts (data analysis, statistics)
- ✅ Mathematical figures and geometric diagrams
- ✅ Flowcharts and process diagrams
- ✅ Block diagrams (system architecture)
- ✅ Chemical structures or formulas as images
- ✅ Physics diagrams (forces, optics, mechanics)
- ✅ Tables with complex visual data

## How It Works

### Text Mode (Default)

```
PDF → Text Extraction (PyMuPDF) → Gemini Text API → JSON Response
```

- **Speed**: Fast (~5-10 seconds)
- **Cost**: Low API credits
- **Best for**: Text-heavy papers without critical visual elements

### Vision Mode (User-Selected)

```
PDF → Image Conversion (pdf2image) → Gemini Vision API → JSON Response
```

- **Speed**: Slower (~20-30 seconds)
- **Cost**: Higher API credits (vision models)
- **Best for**: Papers with diagrams, graphs, and visual content

## Features of Vision Mode

### 1. Comprehensive Visual Descriptions

Vision mode provides detailed descriptions of all visual elements:

**Example:**

```json
{
  "questionNumber": "3",
  "questionText": "For the circuit shown in Figure 3, calculate the equivalent impedance.",
  "imageDescription": "AC circuit diagram with the following components: Voltage source Vac (50V, 60Hz) connected to node A. From node A, three parallel branches: Branch 1 contains resistor R1 (10Ω) to node B; Branch 2 contains inductor L1 (20mH) in series with resistor R2 (5Ω) to node B; Branch 3 contains capacitor C1 (100µF) in series with resistor R3 (15Ω) to node B. Node B connects to ground."
}
```

### 2. Enhanced Topic Mapping

Visual elements help the LLM better understand question context:

- Circuit diagrams → "Electrical Circuits", "AC Analysis"
- Graphs → "Data Analysis", "Signal Processing"
- Flowcharts → "Algorithms", "System Design"

### 3. Improved Cognitive Depth Analysis

Visual complexity contributes to Bloom's taxonomy classification:

- Simple diagrams with labels → "Understanding"
- Complex circuits requiring analysis → "Analyzing"
- Design problems with visual requirements → "Creating"

## User Interface

### Frontend Changes

**New Checkbox in Uploader Component:**

```tsx
☐ Question paper contains images/graphs/diagrams
```

**Helper Text:**

> Enable this if your question paper includes circuit diagrams, graphs, mathematical figures, or other visual elements. Vision mode provides detailed descriptions of visual content for better topic mapping and cognitive depth analysis.

**Warning (when enabled):**

> ⚠️ Vision mode takes longer to process and uses more API credits.

## Backend Implementation

### New Files

1. **`backend/services/image_service.py`**

   - Converts PDF pages to high-quality PNG images (200 DPI)
   - Returns base64-encoded images for API transmission

2. **`backend/prompts/qpaper_parser_vision.md`**
   - Vision-specific prompt with instructions for visual analysis
   - Detailed guidelines for describing diagrams, graphs, and figures
   - Examples of excellent vs. poor visual descriptions

### Modified Files

1. **`backend/services/llm_service.py`**

   - New function: `call_gemini_api_with_images()`
   - Uses `gemini-2.0-flash-exp` vision-capable model
   - Constructs multimodal content (text + images)

2. **`backend/core/analysis_logic.py`**

   - New function: `analyze_qpaper_from_pdf_images()`
   - Orchestrates image conversion → vision analysis workflow

3. **`backend/api/combined_routes.py`**
   - Accepts new parameter: `useImageMode` (Form field, "true"/"false")
   - Routes to appropriate analysis function based on mode

## API Usage

### Request (with vision mode enabled)

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "curriculum=@handout.pdf" \
  -F "questionPaper=@question_paper.pdf" \
  -F "useImageMode=true"
```

### Response

```json
{
  "status": "success",
  "coveragePercentage": 85,
  "testedTopics": [...],
  "missedTopics": [...],
  "topicAnalysis": [...],
  "insights": {...},
  "analysisMode": "vision",  // ← Indicates which mode was used
  "curriculumData": {...},
  "questionPaperData": {
    "questions": [
      {
        "questionNumber": "1",
        "questionText": "...",
        "imageDescription": "Circuit diagram showing...",  // ← Detailed visual description
        "topic": "AC Circuits",
        "bloomLevel": "Analyzing",
        "marks": 10
      }
    ]
  }
}
```

## Dependencies

Vision mode requires these packages (already in `requirements.txt`):

```txt
pdf2image      # PDF page → image conversion
Pillow         # Image processing (required by pdf2image)
```

**System Dependency:**

- `poppler-utils` (for `pdf2image`)
  - macOS: `brew install poppler`
  - Ubuntu: `apt-get install poppler-utils`
  - Windows: Install from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases)

## Performance Considerations

### Processing Time

| Paper Type                    | Text Mode   | Vision Mode |
| ----------------------------- | ----------- | ----------- |
| 5-page paper (text-only)      | ~8 seconds  | ~15 seconds |
| 5-page paper (with diagrams)  | ~8 seconds  | ~25 seconds |
| 10-page paper (with diagrams) | ~10 seconds | ~40 seconds |

### API Costs (Gemini)

- **Text Mode**: ~$0.01 per analysis (gemini-2.0-flash-exp text)
- **Vision Mode**: ~$0.05 per analysis (gemini-2.0-flash-exp vision)

_Note: Costs are approximate and depend on document size_

### Memory Usage

- **Text Mode**: ~50 MB RAM
- **Vision Mode**: ~200 MB RAM (image buffering)

## Deployment Considerations

### For Netlify/Vercel Serverless

⚠️ **Important**: `pdf2image` requires `poppler` system binary, which is **NOT available** in standard serverless environments.

**Solutions:**

1. **Use AWS Lambda Layer** with pre-compiled `poppler`
2. **Deploy backend on Railway/Render** (traditional hosting with system packages)
3. **Use containerized deployment** (Docker with poppler installed)

**Recommended for serverless:**

- Text mode by default
- Vision mode only for Railway/Render/containerized deployments

### For Traditional Hosting (Railway, Render, etc.)

✅ **Fully supported** - Install poppler during deployment:

**Railway/Render:**

```bash
# Add to deployment script
apt-get update && apt-get install -y poppler-utils
```

**Docker:**

```dockerfile
FROM python:3.11
RUN apt-get update && apt-get install -y poppler-utils
COPY requirements.txt .
RUN pip install -r requirements.txt
```

## Testing the Feature

### 1. Local Testing

**Start backend:**

```bash
cd backend
python -m uvicorn main:app --reload
```

**Start frontend:**

```bash
cd frontend
pnpm dev
```

**Test workflow:**

1. Upload curriculum PDF
2. Upload question paper PDF with diagrams
3. ✅ Check "Question paper contains images/graphs/diagrams"
4. Click "Analyze"
5. Observe detailed visual descriptions in results

### 2. Verify Vision Mode

**Check backend logs:**

```
🖼️  Converting PDF pages to images...
✓ Successfully converted 5 pages
📷 Adding page 1 image to analysis...
📷 Adding page 2 image to analysis...
🤖 Calling Gemini Vision API with 5 images...
✓ Vision API analysis complete
```

**Check response:**

```json
{
  "analysisMode": "vision", // Should be "vision" not "text"
  "questionPaperData": {
    "questions": [
      {
        "imageDescription": "Circuit diagram showing..." // Should have detailed descriptions
      }
    ]
  }
}
```

## Troubleshooting

### Issue: "poppler not found"

**Solution:**

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Verify installation
which pdftoppm  # Should show path
```

### Issue: Vision mode takes too long (>60 seconds)

**Causes:**

- Very large PDF (>20 pages)
- High DPI setting (>200)
- Slow network to Gemini API

**Solutions:**

- Reduce DPI in `image_service.py` (200 → 150)
- Use background processing for long documents
- Implement pagination (analyze 5 pages at a time)

### Issue: API quota exceeded

**Cause:** Gemini API has rate limits

**Solutions:**

- Implement rate limiting on frontend
- Add queue system for multiple requests
- Cache results for identical PDFs

## Future Enhancements

### Planned Features

1. **OCR for Scanned PDFs**

   - Detect scanned PDFs automatically
   - Apply OCR before vision analysis

2. **Selective Page Analysis**

   - Let users select which pages have diagrams
   - Hybrid mode: text for most pages, vision for specific pages

3. **Visual Element Extraction**

   - Save extracted diagrams separately
   - Allow users to download/view individual figures

4. **Batch Processing**

   - Analyze multiple question papers in one request
   - Compare visual complexity across papers

5. **Cost Optimization**
   - Automatically detect pages with no visuals
   - Skip vision API for text-only pages

## Summary

The image workflow provides a powerful option for analyzing question papers with visual content. Users can choose the appropriate mode based on their document type, balancing speed/cost (text mode) vs. comprehensive visual analysis (vision mode).

**Key Benefits:**

- ✅ Dual workflow gives users choice
- ✅ Vision mode captures critical visual context
- ✅ Enhanced topic mapping with visual understanding
- ✅ Better Bloom's taxonomy classification
- ✅ Clear UI indication of mode and warnings

**Key Trade-offs:**

- ⚠️ Slower processing in vision mode
- ⚠️ Higher API costs
- ⚠️ Requires poppler system dependency
- ⚠️ Not suitable for standard serverless deployments
