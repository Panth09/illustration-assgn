# Getting Started with Illustration Personalizer

This guide walks you through the complete setup and usage of the Illustration Personalizer project.

## System Requirements

- **OS:** Windows, macOS, or Linux
- **Python:** 3.10 or higher
- **Node.js:** 16.0 or higher
- **RAM:** Minimum 4GB (8GB recommended)
- **Disk Space:** 2GB for models and dependencies
- **GPU (Optional):** CUDA 11.8+ for faster processing

## Installation & Setup

### 1. Clone or Download the Project

```bash
cd illustration-assgn
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies (this will take 5-10 minutes)
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# (Optional) Edit .env for AWS or GPU settings

# Start the server
python main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Initializing models...
INFO:     InsightFace model initialized successfully
INFO:     Models initialized successfully
```

✅ Backend is now running at `http://localhost:8000`

### 3. Frontend Setup (New Terminal)

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

**Expected Output:**
```
▲ Next.js 14.0.0
- Local:        http://localhost:3000
```

✅ Frontend is now running at `http://localhost:3000`

### 4. Verify Installation

Open your browser and navigate to:
```
http://localhost:3000
```

You should see the Illustration Personalizer interface with:
- "Step 1: Child Photo" upload area
- "Step 2: Illustration" upload area
- "Personalize Illustration" button

## Basic Usage

### Step 1: Prepare Your Images

**Child Photo:**
- Clear, well-lit face photo
- JPG or PNG format
- Minimum 300x300 pixels
- Face should fill 30-80% of image

**Illustration Template:**
- Illustration or drawing
- Should have a defined area for face (centered)
- JPG or PNG format
- Same aspect ratio as child photo (or will be resized)

### Step 2: Upload & Process

1. **Click upload area** or **drag-drop** child photo
   - Preview will show the selected image
   
2. **Click upload area** or **drag-drop** illustration template
   - Preview will show the template

3. **Click "Personalize Illustration"**
   - Progress spinner appears
   - Backend processes the images
   - Takes 10-20 seconds on CPU

### Step 3: Download Result

When complete:
- Preview of personalized illustration displays
- Click **"Download Image"** to save as PNG
- Click **"Create Another"** to process new images

## API Usage (Curl/Postman)

### Health Check

```bash
curl http://localhost:8000/health

Response:
{
  "status": "healthy",
  "timestamp": "2025-12-24T10:30:00.000000"
}
```

### Face Detection

```bash
curl -X POST "http://localhost:8000/detect-face" \
  -F "file=@path/to/child_photo.jpg"

Response:
{
  "success": true,
  "file_id": "abc123-def456",
  "detection_results": {
    "detected": true,
    "faces": [
      {
        "bbox": [100, 50, 200, 150],
        "gender": "M",
        "age": 7
      }
    ]
  }
}
```

### Personalize (Full Pipeline)

```bash
curl -X POST "http://localhost:8000/personalize" \
  -F "child_photo=@path/to/child.jpg" \
  -F "illustration=@path/to/template.png" \
  -o result.png

Response:
{
  "success": true,
  "output_file_id": "xyz789",
  "message": "Illustration personalized successfully"
}
```

### Download Result

```bash
curl -X GET "http://localhost:8000/download/xyz789" \
  -o personalized.png
```

## Directory Structure During Use

After first run, these directories are created:

```
backend/
├── uploads/          # Temporary user uploads
│   ├── abc123_child.jpg
│   └── def456_template.png
├── outputs/          # Processed results
│   ├── xyz789_personalized.png
│   └── ...
└── models/          # Downloaded ML models (~1GB)
    ├── buffalo_l
    └── ...
```

**Note:** Files are auto-deleted after 24 hours (configurable)

## Configuration

### Backend Config (.env)

```bash
# Device selection
DEVICE=cpu  # Use 'cuda' if GPU available

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# File size limit (in MB)
MAX_UPLOAD_SIZE=50

# AWS S3 (for production)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket
```

### Frontend Config (.env.local)

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production:
# NEXT_PUBLIC_API_URL=https://api.example.com
```

## GPU Acceleration (Optional)

If you have NVIDIA GPU:

```bash
# 1. Install CUDA 11.8+
# https://developer.nvidia.com/cuda-11-8-0-download-archive

# 2. Install cuDNN
# https://developer.nvidia.com/cudnn

# 3. Update requirements.txt with GPU versions
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 4. Update .env
DEVICE=cuda

# 5. Restart backend
python main.py
```

**Performance Improvement:** 3-5 seconds (vs 10-18 seconds on CPU)

## Common Issues & Solutions

### Issue: "Cannot reach backend"

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# If error, check port 8000
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -i :8000

# Kill process if needed and restart backend
python main.py
```

### Issue: "No module named 'insightface'"

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or manually install
pip install -U insightface onnxruntime
```

### Issue: "Out of memory" error

**Solution:**
```bash
# Reduce batch size in config.py
# Switch to CPU mode
export DEVICE=cpu

# Or close other applications
```

### Issue: "Face not detected"

**Solution:**
- Use clearer, well-lit photo
- Ensure face fills 30-80% of image
- Check image resolution (640+ pixels recommended)
- Try slightly different angles

### Issue: "Frontend shows blank page"

**Solution:**
```bash
# Clear browser cache
# Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)

# Verify API URL in .env.local
cat .env.local

# Restart frontend
npm run dev
```

## Production Deployment

For deploying to production:

1. **Backend Deployment:**
   - Option A: [Replicate.com](https://replicate.com) (serverless, recommended)
   - Option B: AWS EC2/ECS (more control)
   - Option C: Railway/Render (simple, free tier)

2. **Frontend Deployment:**
   - [Vercel.com](https://vercel.com) (recommended for Next.js)
   - AWS S3 + CloudFront
   - Netlify

See [PROJECT_NOTES.md](./docs/PROJECT_NOTES.md#deployment-instructions) for detailed guide.

## Advanced Usage

### Batch Processing

For processing multiple images:

```python
import requests
from pathlib import Path

API_URL = "http://localhost:8000"

for child_photo in Path("photos").glob("*.jpg"):
    for template in Path("templates").glob("*.png"):
        with open(child_photo, 'rb') as cf, open(template, 'rb') as tf:
            response = requests.post(
                f"{API_URL}/personalize",
                files={
                    'child_photo': cf,
                    'illustration': tf
                }
            )
            
            if response.json()['success']:
                file_id = response.json()['output_file_id']
                # Download result
                result = requests.get(f"{API_URL}/download/{file_id}")
                with open(f"results/{file_id}.png", 'wb') as f:
                    f.write(result.content)
```

### Custom Styling

To customize the illustration style:

Edit `backend/instant_id_styler.py`:

```python
# Line ~120 - Increase colors for less posterized effect
_, labels, centers = cv2.kmeans(data, 16, None, criteria, 10, ...)  # Change 8 to 16

# Line ~60 - Adjust edge sensitivity
edges = cv2.Canny(gray, 30, 100)  # Lower values = more edges
```

Then restart backend.

## Performance Monitoring

Monitor processing time in terminal:

```bash
# Backend logs show inference time
# Look for:
# - "Face detection completed in 2.3s"
# - "Stylization completed"
# - "Face blended into template"

# Frontend console shows upload time
# Open browser DevTools (F12) → Network tab
```

## Security & Privacy

- **Data:** Uploaded files are temporary (24-hour auto-delete)
- **Processing:** All ML inference is local (no cloud model calls)
- **Storage:** By default, results are not persisted
- **Recommendations:**
  - Don't share API publicly without authentication
  - Use HTTPS in production
  - Implement user authentication
  - Add rate limiting
  - Get parental consent for child photos

## Getting Help

1. **Check Documentation:**
   - [PROJECT_NOTES.md](./docs/PROJECT_NOTES.md) - Full technical docs
   - [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System design
   - [Backend README](./backend/README.md) - Backend specific
   - [Frontend README](./frontend/README.md) - Frontend specific

2. **Check Logs:**
   ```bash
   # Backend errors
   # Check terminal where you ran: python main.py
   
   # Frontend errors
   # Open browser DevTools (F12)
   # Check Console tab for JavaScript errors
   ```

3. **Common Fixes:**
   - Restart both services
   - Clear browser cache
   - Reinstall Python dependencies
   - Check Python version (3.10+)

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Try different child photos and illustration templates
- Read [PROJECT_NOTES.md](./docs/PROJECT_NOTES.md) for advanced features
- Plan v2 improvements (see roadmap)

---

**Happy personalizing! 🎨**
