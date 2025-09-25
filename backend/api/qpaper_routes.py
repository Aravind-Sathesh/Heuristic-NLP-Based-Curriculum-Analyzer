# api/qpaper_routes.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid
from core.analysis_logic import analyze_qpaper_from_pdf

router = APIRouter()


@router.post("/analyze")
async def analyze_qpaper_endpoint(file: UploadFile = File(...)):
    """
    API endpoint to upload a question paper PDF and extract all questions,
    handling text and images appropriately.
    """
    os.makedirs("uploads", exist_ok=True)
    temp_filename = f"{uuid.uuid4()}.pdf"
    temp_filepath = os.path.join("uploads", temp_filename)

    try:
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        analysis_result = analyze_qpaper_from_pdf(temp_filepath)

        if analysis_result.get("status") != "success":
            raise HTTPException(
                status_code=400, detail="Failed to analyze question paper.")

        return analysis_result
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
