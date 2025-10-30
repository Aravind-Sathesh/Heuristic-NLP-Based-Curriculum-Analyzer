from pdf2image import convert_from_path
from PIL import Image
import io
import base64
import os


def convert_pdf_pages_to_images(pdf_path: str, dpi: int = 200) -> list:
    """
    Convert each page of a PDF to a high-quality image.

    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution for image conversion (higher = better quality, larger size)

    Returns:
        List of dictionaries containing page number and base64-encoded image data
    """
    try:
        # Convert PDF pages to PIL Image objects
        images = convert_from_path(pdf_path, dpi=dpi)

        page_images = []
        for page_num, image in enumerate(images, start=1):
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG', optimize=True)
            img_byte_arr = img_byte_arr.getvalue()

            # Encode as base64 for API transmission
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')

            page_images.append({
                "page": page_num,
                "data": img_base64,
                "mime_type": "image/png"
            })

        print(f"✓ Converted {len(page_images)} pages to images")
        return page_images

    except Exception as e:
        print(f"❌ Error converting PDF to images: {str(e)}")
        raise Exception(f"PDF to image conversion failed: {str(e)}")


def get_image_metadata(pdf_path: str) -> dict:
    """
    Get metadata about the PDF for image conversion.

    Returns:
        Dictionary with page count and estimated processing info
    """
    try:
        # Quick conversion to count pages
        # Low DPI just for counting
        images = convert_from_path(pdf_path, dpi=72)

        return {
            "total_pages": len(images),
            "estimated_size_mb": len(images) * 0.5,  # Rough estimate
            "recommended_dpi": 200 if len(images) <= 10 else 150
        }
    except Exception as e:
        print(f"❌ Error getting PDF metadata: {str(e)}")
        return {
            "total_pages": 0,
            "estimated_size_mb": 0,
            "recommended_dpi": 200
        }
