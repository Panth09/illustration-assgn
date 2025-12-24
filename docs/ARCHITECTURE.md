```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (Browser)                         │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Next.js React Frontend (Port 3000)                            │   │
│  │  ├─ Upload Component (Drag & Drop)                             │   │
│  │  ├─ File Preview Component                                     │   │
│  │  ├─ Loading Spinner                                            │   │
│  │  ├─ Error Handling                                             │   │
│  │  └─ Result Display & Download                                  │   │
│  └──────────────────┬──────────────────────────────────────────────┘   │
│                     │ HTTP/REST API Calls                              │
└─────────────────────┼──────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKEND API SERVER (FastAPI)                         │
│                     Port 8000 - Python                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ API Endpoints:                                                  │   │
│  │ • POST /detect-face         - Detect faces in image            │   │
│  │ • POST /personalize          - Main personalization pipeline   │   │
│  │ • POST /upload-template      - Upload illustration templates   │   │
│  │ • GET /download/{file_id}    - Download results               │   │
│  │ • GET /health                - Health check                    │   │
│  └──────────────────┬───────────────────────────────────────────────┘   │
│                     │                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Core Processing Pipeline:                                       │   │
│  │                                                                 │   │
│  │  face_detector.py (InsightFace)                                 │   │
│  │  ├─ Load buffalo_l model                                       │   │
│  │  ├─ Detect faces with bounding boxes                           │   │
│  │  ├─ Extract face embeddings                                    │   │
│  │  └─ Return age & gender info                                   │   │
│  │                                                                 │   │
│  │  instant_id_styler.py                                           │   │
│  │  ├─ Extract face region from photo                             │   │
│  │  ├─ Apply cartoon/illustration filter                          │   │
│  │  ├─ Color quantization for stylization                         │   │
│  │  ├─ Edge preservation                                          │   │
│  │  └─ Seamless blending into template                            │   │
│  │                                                                 │   │
│  │  illustration_styler.py                                         │   │
│  │  ├─ Alternative stylization approach                           │   │
│  │  ├─ Bilateral filtering                                        │   │
│  │  └─ Poisson blending                                           │   │
│  │                                                                 │   │
│  │  config.py & utils.py                                           │   │
│  │  ├─ Configuration management                                   │   │
│  │  ├─ File cleanup utilities                                     │   │
│  │  └─ Logging setup                                              │   │
│  └──────────────────┬───────────────────────────────────────────────┘   │
│                     │ File I/O                                          │
└─────────────────────┼──────────────────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    ┌─────────┐  ┌────────┐  ┌─────────┐
    │ /uploads│  │/outputs│  │ /models │
    │ (temp)  │  │(results)  │(ML models)
    └─────────┘  └────────┘  └─────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DEPENDENCIES                                │
│                                                                          │
│  • InsightFace - Face detection & embedding extraction                  │
│  • OpenCV - Image processing (filters, blending)                        │
│  • PyTorch/TorchVision - Deep learning framework                        │
│  • Pillow - Image manipulation                                          │
│  • Transformers - NLP models (optional for future versions)             │
│  • Diffusers - Stable Diffusion (optional for advanced styling)         │
│                                                                          │
│  Optional Cloud Integration:                                            │
│  • AWS S3 - Object storage for images                                   │
│  • Replicate API - Serverless ML inference                              │
│  • AWS Lambda/EC2 - Deployment platforms                                │
└─────────────────────────────────────────────────────────────────────────┘

DATA FLOW:
═════════════════════════════════════════════════════════════════════════

1. User Upload
   Client Browser → POST /personalize → Backend receives files

2. Face Detection
   Child Photo → InsightFace model → Face bbox, embedding, age, gender

3. Face Extraction & Styling
   Face region → Cartoon filter → Color quantization → Styled face

4. Blending
   Styled face + Illustration template → Gaussian mask → Blended result

5. Result Storage & Download
   Result image → Save to /outputs → Return download URL → Client

DEPLOYMENT ARCHITECTURE:
═════════════════════════════════════════════════════════════════════════

Development:
┌──────────────┐  ┌──────────────┐
│   Next.js    │  │   FastAPI    │
│  localhost   │  │  localhost   │
│    :3000     │  │    :8000     │
└──────────────┘  └──────────────┘

Production (Cloud):
┌──────────────┐          ┌──────────────┐
│  Vercel CDN  │ ◄─────►  │ AWS/Replicate│
│  (Frontend)  │          │  (Backend API)
└──────────────┘          └──────────────┘
                               │
                               ▼
                          ┌─────────┐
                          │  S3     │
                          │ Storage │
                          └─────────┘
```
