import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path
import uuid
from datetime import datetime
import cv2
import asyncio
from threading import Thread
from PIL import Image
import io
import gc

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
models_ready = False


def compress_image(file_content: bytes, max_size: tuple = (1024, 1024)) -> bytes:
    """Compress image to reduce memory usage"""
    try:
        img = Image.open(io.BytesIO(file_content))
        
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Resize if too large
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Image compression failed: {e}")
        raise


def initialize_models():
    """Initialize ML models in background"""
    global face_detector, illustration_styler, models_ready
    try:
        logger.info("Initializing models in background...")
        face_detector = FaceDetector()
        illustration_styler = IllustrationStyler()
        models_ready = True
        logger.info("Models initialized successfully")
        
        # Force garbage collection after loading
        gc.collect()
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        models_ready = False


@app.on_event("startup")
async def startup_event():
    """Start model initialization in background thread"""
    logger.info("Starting background model initialization...")
    thread = Thread(target=initialize_models, daemon=True)
    thread.start()
    logger.info("Server ready - models loading in background")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Illustration Personalization API",
        "models_ready": models_ready,
        "status": "ready" if models_ready else "loading models..."
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_ready": models_ready,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/detect-face")
async def detect_face(file: UploadFile = File(...)):
    """
    Detect faces in uploaded image
    """
    if not models_ready:
        raise HTTPException(
            status_code=503, 
            detail="Models still loading, please wait a moment and try again"
        )
    
    if not face_detector:
        raise HTTPException(status_code=503, detail="Face detector not initialized")

    temp_file_path = None
    try:
        # Validate file size
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum 5MB allowed.")

        # Compress image
        logger.info(f"Original size: {len(content)} bytes")
        content = compress_image(content, max_size=(800, 800))
        logger.info(f"Compressed size: {len(content)} bytes")

        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_ext = ".jpg"  # Always save as JPEG after compression
        temp_file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        with open(temp_file_path, "wb") as f:
            f.write(content)

        # Detect faces
        results = face_detector.detect_face(str(temp_file_path))

        # Clean up immediately
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
        
        gc.collect()

        return {
            "success": True,
            "file_id": file_id,
            "detection_results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    finally:
        # Ensure cleanup
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass
        gc.collect()


@app.post("/personalize")
async def personalize_illustration(
    child_photo: UploadFile = File(...),
    illustration: UploadFile = File(...),
):
    """
    Personalize an illustration with a child's photo
    """
    if not models_ready:
        raise HTTPException(
            status_code=503, 
            detail="Models still loading, please wait a moment and try again"
        )
    
    if not face_detector or not illustration_styler:
        raise HTTPException(status_code=503, detail="Services not initialized")

    child_photo_path = None
    illustration_path = None
    output_path = None

    try:
        logger.info("Starting personalization request...")
        
        # Save and compress child photo
        child_content = await child_photo.read()
        if len(child_content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="Child photo too large. Maximum 5MB.")

        logger.info(f"Child photo original size: {len(child_content)} bytes")
        child_content = compress_image(child_content, max_size=(800, 800))
        logger.info(f"Child photo compressed size: {len(child_content)} bytes")

        child_file_id = str(uuid.uuid4())
        child_photo_path = UPLOAD_DIR / f"{child_file_id}_child.jpg"

        with open(child_photo_path, "wb") as f:
            f.write(child_content)

        # Save and compress illustration
        illust_content = await illustration.read()
        if len(illust_content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="Illustration too large. Maximum 5MB.")

        logger.info(f"Illustration original size: {len(illust_content)} bytes")
        illust_content = compress_image(illust_content, max_size=(1024, 1024))
        logger.info(f"Illustration compressed size: {len(illust_content)} bytes")

        illust_file_id = str(uuid.uuid4())
        illustration_path = UPLOAD_DIR / f"{illust_file_id}_template.jpg"

        with open(illustration_path, "wb") as f:
            f.write(illust_content)

        logger.info("Files saved, starting processing...")
        
        # Process with timeout
        async def process_with_timeout():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                illustration_styler.process,
                str(child_photo_path),
                str(illustration_path)
            )
        
        try:
            result_image = await asyncio.wait_for(
                process_with_timeout(), 
                timeout=120.0  # 2 minute timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504, 
                detail="Processing timeout - please try with smaller images"
            )

        # Save output
        output_file_id = str(uuid.uuid4())
        output_path = OUTPUT_DIR / f"{output_file_id}_personalized.png"

        # Compress output before saving
        cv2.imwrite(str(output_path), result_image, [cv2.IMWRITE_PNG_COMPRESSION, 6])
        
        logger.info("Processing completed successfully")

        # Clean up input files immediately
        if child_photo_path and child_photo_path.exists():
            child_photo_path.unlink()
        if illustration_path and illustration_path.exists():
            illustration_path.unlink()
        
        # Force garbage collection
        del result_image, child_content, illust_content
        gc.collect()

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
    finally:
        # Cleanup all temporary files
        for path in [child_photo_path, illustration_path]:
            if path and path.exists():
                try:
                    path.unlink()
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup failed for {path}: {cleanup_error}")
        gc.collect()


@app.get("/download/{file_id}")
async def download_result(file_id: str):
    """
    Download personalized illustration
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
    """
    try:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum 5MB.")

        # Compress template
        content = compress_image(content, max_size=(1024, 1024))

        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}_template.jpg"

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

    # CRITICAL: Use PORT from environment (Render requirement)
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Must be 0.0.0.0 for Render
        port=port,
        reload=False,
        workers=1,
    )