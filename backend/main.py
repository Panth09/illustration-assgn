import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path
import uuid
from datetime import datetime
import cv2

from config import UPLOAD_DIR, OUTPUT_DIR, MAX_UPLOAD_SIZE, API_HOST, API_PORT
from face_detector import FaceDetector
from illustration_styler import IllustrationStyler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Child Photo Personalization API",
    description="API for personalizing illustrations with child photos",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
face_detector = None
illustration_styler = None


def initialize_models():
    """Initialize ML models on startup"""
    global face_detector, illustration_styler
    try:
        logger.info("Initializing models...")
        face_detector = FaceDetector()
        illustration_styler = IllustrationStyler()
        logger.info("Models initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        raise


@app.on_event("startup")
async def startup_event():
    """Initialize models on application startup"""
    initialize_models()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/detect-face")
async def detect_face(file: UploadFile = File(...)):
    """
    Detect faces in uploaded image

    Args:
        file: Uploaded image file

    Returns:
        Face detection results with embeddings and bounding boxes
    """
    if not face_detector:
        raise HTTPException(status_code=503, detail="Face detector not initialized")

    try:
        # Validate file size
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        with open(file_path, "wb") as f:
            f.write(content)

        # Detect faces
        results = face_detector.detect_face(str(file_path))

        return {
            "success": True,
            "file_id": file_id,
            "file_path": str(file_path),
            "detection_results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@app.post("/personalize")
async def personalize_illustration(
    child_photo: UploadFile = File(...),
    illustration: UploadFile = File(...),
):
    """
    Personalize an illustration with a child's photo

    Args:
        child_photo: Uploaded child's photo
        illustration: Uploaded illustration template

    Returns:
        Personalized illustration image
    """
    if not face_detector or not illustration_styler:
        raise HTTPException(status_code=503, detail="Services not initialized")

    child_photo_path = None
    illustration_path = None

    try:
        # Save child photo
        child_content = await child_photo.read()
        if len(child_content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="Child photo file too large")

        child_file_id = str(uuid.uuid4())
        child_file_ext = Path(child_photo.filename).suffix
        child_photo_path = UPLOAD_DIR / f"{child_file_id}_child{child_file_ext}"

        with open(child_photo_path, "wb") as f:
            f.write(child_content)

        # Save illustration
        illust_content = await illustration.read()
        if len(illust_content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="Illustration file too large")

        illust_file_id = str(uuid.uuid4())
        illust_file_ext = Path(illustration.filename).suffix
        illustration_path = UPLOAD_DIR / f"{illust_file_id}_template{illust_file_ext}"

        with open(illustration_path, "wb") as f:
            f.write(illust_content)

        # Process personalization
        result_image = illustration_styler.process(
            str(child_photo_path), str(illustration_path)
        )

        # Save output
        output_file_id = str(uuid.uuid4())
        output_path = OUTPUT_DIR / f"{output_file_id}_personalized.png"

        cv2.imwrite(str(output_path), result_image)

        return {
            "success": True,
            "output_file_id": output_file_id,
            "output_path": str(output_path),
            "message": "Illustration personalized successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Personalization error: {e}")
        raise HTTPException(status_code=500, detail=f"Personalization failed: {str(e)}")


@app.get("/download/{file_id}")
async def download_result(file_id: str):
    """
    Download personalized illustration

    Args:
        file_id: Output file ID

    Returns:
        Personalized image file
    """
    try:
        # Find file with this ID
        file_path = None
        for f in OUTPUT_DIR.glob(f"{file_id}*"):
            file_path = f
            break

        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(str(file_path), filename=file_path.name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.post("/upload-illustration-template")
async def upload_template(file: UploadFile = File(...)):
    """
    Upload an illustration template for future use

    Args:
        file: Illustration template file

    Returns:
        Template file ID and path
    """
    try:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = UPLOAD_DIR / f"{file_id}_template{file_ext}"

        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "success": True,
            "template_id": file_id,
            "file_path": str(file_path),
            "message": "Template uploaded successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import os

    # Use PORT env var if available (Heroku), otherwise use API_PORT
    port = int(os.getenv("PORT", API_PORT))

    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=port,
        reload=False,
        workers=1,
    )
