from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from core.analysis_logic import analyze_curriculum_from_pdf

# Create an APIRouter instance
router = APIRouter()


@router.post("/analyze")
async def analyze_curriculum_endpoint(file: UploadFile = File(...)):
    """
    API endpoint to upload a curriculum PDF and get a structured analysis.
    """
    # Ensure the uploads directory exists
    os.makedirs("uploads", exist_ok=True)

    temp_filename = f"{uuid.uuid4()}.pdf"
    temp_filepath = os.path.join("uploads", temp_filename)

    try:
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        analysis_result = analyze_curriculum_from_pdf(temp_filepath)

        if analysis_result.get("status") == "error":
            raise HTTPException(
                status_code=400, detail=analysis_result.get("reason"))

        return analysis_result
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
