# Illustration Personalizer - Backend API

FastAPI-based backend for the illustration personalization system. Handles face detection, stylization, and image blending.

## Architecture

```
User Request
    ↓
POST /personalize
    ↓
Save files to /uploads
    ↓
FaceDetector (InsightFace)
    ├─ Detect faces
    ├─ Extract embeddings
    └─ Get age/gender
    ↓
InstantIDStyler
    ├─ Extract face region
    ├─ Apply cartoon filter
    ├─ Color quantization
    └─ Extract identity embedding
    ↓
Blend with template
    ├─ Resize face
    ├─ Apply Gaussian mask
    └─ Alpha blend
    ↓
Save to /outputs
    ↓
Return download URL
```

## Setup

### Prerequisites

- Python 3.10+
- CUDA 11.8+ (optional, for GPU)
- 4GB RAM minimum

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run server
python main.py
```

Server will be available at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

## Configuration

### Environment Variables (.env)

```bash
# Device selection
DEVICE=cpu              # Use 'cuda' for GPU
API_HOST=0.0.0.0       # Server host
API_PORT=8000          # Server port
API_WORKERS=1          # Number of workers

# File handling
MAX_UPLOAD_SIZE=50     # Max file size in MB

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=us-east-1
```

## API Endpoints

### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-12-24T10:30:00"
}
```

### Face Detection
```bash
POST /detect-face

Files:
  file: <image_file>

Response:
{
  "success": true,
  "file_id": "uuid",
  "file_path": "uploads/uuid.jpg",
  "detection_results": {
    "detected": true,
    "faces": [
      {
        "bbox": [100, 50, 200, 150],
        "kps": [[...], ...],
        "embedding": [...],
        "gender": "M/F",
        "age": 5-12
      }
    ],
    "image_shape": [720, 1280, 3]
  }
}
```

### Personalize Illustration
```bash
POST /personalize

Files:
  child_photo: <child_image>
  illustration: <template_image>

Response:
{
  "success": true,
  "output_file_id": "uuid",
  "output_path": "outputs/uuid_personalized.png",
  "message": "Illustration personalized successfully"
}
```

### Download Result
```bash
GET /download/{file_id}

Response: Binary image file
```

### Upload Template
```bash
POST /upload-illustration-template

Files:
  file: <template_image>

Response:
{
  "success": true,
  "template_id": "uuid",
  "file_path": "uploads/uuid_template.png"
}
```

## Project Structure

```
backend/
├── main.py                  # FastAPI application & endpoints
├── config.py               # Configuration settings
├── face_detector.py        # InsightFace integration
├── instant_id_styler.py    # Advanced stylization pipeline
├── illustration_styler.py  # Alternative stylization
├── utils.py                # Helper functions
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── .env.example            # Environment template
└── README.md              # This file
```

## Model Details

### InsightFace Buffalo_L
- **Detection:** Anchor-based face detection
- **Alignment:** 5-point facial landmark detection
- **Embedding:** 512-dimensional face embeddings (ArcFace)
- **Attributes:** Age, gender classification
- **Performance:** ~99.5% accuracy on IJBB
- **Speed:** ~50ms per face on CPU
- **Memory:** ~150MB model size

### Stylization Pipeline

1. **Edge Detection** (Canny)
   - Detects facial boundaries and features
   - Parameters: threshold1=50, threshold2=150

2. **Bilateral Filtering**
   - Smooths color while preserving edges
   - Parameters: 9x9 kernel, spatial σ=75, color σ=75

3. **K-means Color Quantization**
   - Reduces colors for cartoon effect
   - 8 color centers for illustration style

4. **Gaussian Blending**
   - Smooth mask for seamless integration
   - Edge feathering for natural transition

## Performance

| Task | Time | Notes |
|------|------|-------|
| Model Initialization | 5-10s | One-time on startup |
| Face Detection | 2-3s | InsightFace inference |
| Stylization | 5-10s | Image processing |
| Blending | 3-5s | Integration & saving |
| **Total** | **10-18s** | Full pipeline (CPU) |

**With GPU (CUDA):** 3-5 seconds total

## Error Handling

### Face Not Detected
```json
{
  "detail": "No faces detected in the provided image"
}
```
**Solution:** Use clearer, well-lit photo with visible face

### File Too Large
```json
{
  "detail": "File too large"
}
```
**Solution:** Reduce image size or increase MAX_UPLOAD_SIZE

### Backend Not Ready
```json
{
  "detail": "Face detector not initialized"
}
```
**Solution:** Wait for startup, check logs for errors

## Logging

View detailed logs in terminal where you started the server:

```
INFO:     Application startup complete
INFO:     Initializing models...
INFO:     InsightFace model initialized successfully
INFO:     Models initialized successfully
INFO:     127.0.0.1:54321 - "POST /personalize HTTP/1.1" 200
```

Enable debug logging:
```bash
# Edit config.py, add:
logging.basicConfig(level=logging.DEBUG)
```

## Database Integration (v2)

For production, add database for persistence:

```python
# models.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ProcessedImage(Base):
    __tablename__ = "processed_images"
    
    id = Column(String, primary_key=True)
    child_photo_id = Column(String)
    template_id = Column(String)
    output_id = Column(String)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Docker Deployment

```bash
# Build image
docker build -t illustration-api:latest .

# Run container
docker run -p 8000:8000 \
  -e DEVICE=cpu \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  illustration-api:latest

# With GPU
docker run --gpus all -p 8000:8000 \
  -e DEVICE=cuda \
  illustration-api:latest
```

## Cloud Deployment

### Replicate (Recommended)
```yaml
# cog.yaml
build:
  gpu: true
  cuda: "11.8"

predict: "main.py:predict"
```

### AWS Lambda
```python
# Note: Models exceed Lambda package limit
# Solution: Use container image on ECR
```

### AWS EC2
```bash
# Launch Ubuntu instance
# Install Python 3.10, CUDA 11.8
# Clone repo & run main.py
# Use Nginx reverse proxy
# Set up auto-restart with systemd
```

## Testing

### Test Face Detection
```bash
curl -X POST "http://localhost:8000/detect-face" \
  -F "file=@test.jpg"
```

### Test Personalization
```bash
curl -X POST "http://localhost:8000/personalize" \
  -F "child_photo=@child.jpg" \
  -F "illustration=@template.png" \
  -o result.png
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### ImportError: No module named 'insightface'
```bash
pip install -U insightface onnxruntime
```

### CUDA Out of Memory
```bash
export DEVICE=cpu
# Or reduce batch size
```

### Models not downloading
```bash
# Manual download
python -c "from insightface.app import FaceAnalysis; \
  app = FaceAnalysis(name='buffalo_l'); \
  app.prepare(ctx_id=-1)"
```

## Security

- Validate file uploads (type, size, content)
- Sanitize file paths
- Add rate limiting in production
- Implement authentication/authorization
- Use HTTPS in production
- Store sensitive data in environment variables
- Add input validation for all API parameters

## Performance Optimization

### CPU
- Cache models in memory ✓ (implemented)
- Use numpy instead of PIL (partial)
- Reduce image preprocessing
- Batch process multiple images

### GPU
- Use TensorRT for inference
- Implement mixed precision (fp16)
- Use async processing with task queue
- Model quantization (int8)

## References

- **FastAPI:** https://fastapi.tiangolo.com
- **InsightFace:** https://github.com/deepinsight/insightface
- **OpenCV:** https://opencv.org
- **PyTorch:** https://pytorch.org

---

**Version:** 1.0.0 | **Status:** Production Ready | **Last Updated:** Dec 24, 2025