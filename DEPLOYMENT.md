# Deployment Guide

Complete guide for deploying Illustration Personalizer to production.

## Options Comparison

| Platform | Cost | Setup Time | Scalability | Cold Start |
|----------|------|-----------|------------|-----------|
| **Replicate** | $0.10/min | 5 min | ⭐⭐⭐⭐⭐ | ~2s |
| **AWS Lambda** | Pay-per-use | 20 min | ⭐⭐⭐⭐ | 30-60s ⚠️ |
| **AWS EC2** | ~$10/month | 30 min | ⭐⭐⭐⭐ | None |
| **Heroku** | Free (limited) | 5 min | ⭐⭐⭐ | 30s |
| **Railway** | Free tier | 10 min | ⭐⭐⭐ | <2s |
| **Vercel** (frontend) | Free | 5 min | ⭐⭐⭐⭐⭐ | <1s |

## 1. Local Development ✓ (COMPLETED)

Your current setup is production-ready locally.

```bash
# Backend
cd backend
python main.py

# Frontend (new terminal)
cd frontend  
npm run dev
```

Access at `http://localhost:3000`

---

## 2. Railway.app (Recommended for Quick Start)

### Pros
- Free tier with 500 hours/month
- No cold start issues
- Easy GitHub integration
- Auto-deploys on push

### Setup

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign in with GitHub

2. **Deploy Backend**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login
   railway login

   # From backend directory
   cd backend
   railway init
   railway up
   ```

3. **Configure Environment**
   - Go to Railway dashboard
   - Add variables:
     ```
     DEVICE=cpu
     API_PORT=8000
     ```

4. **Get API URL**
   - Railway generates: `https://xxx.railway.app`
   - Use this in frontend `.env.local`

5. **Deploy Frontend**
   ```bash
   cd frontend
   
   # Create .env.production
   echo "NEXT_PUBLIC_API_URL=https://xxx.railway.app" > .env.production
   
   # Build
   npm run build
   
   # Deploy to Vercel (see section 5)
   ```

---

## 3. AWS (Scalable Production)

### Option A: EC2 (Recommended)

#### Setup Instance

```bash
# 1. Create EC2 instance
# AMI: Ubuntu 22.04
# Type: t3.medium (2vCPU, 4GB RAM)
# Security: Allow ports 80, 443, 8000

# 2. Connect via SSH
ssh -i key.pem ubuntu@<instance-ip>

# 3. Install dependencies
sudo apt update
sudo apt install python3.10 python3-pip nodejs npm git
sudo apt install libsm6 libxext6  # For OpenCV

# 4. Clone repo
git clone <your-repo>
cd illustration-assgn/backend

# 5. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Create systemd service
sudo nano /etc/systemd/system/illustration.service
```

**Systemd Service File:**
```ini
[Unit]
Description=Illustration Personalizer API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/illustration-assgn/backend
ExecStart=/home/ubuntu/illustration-assgn/backend/venv/bin/python main.py
Restart=always
RestartSec=10
Environment="DEVICE=cpu"
Environment="API_PORT=8000"

[Install]
WantedBy=multi-user.target
```

**Enable Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable illustration
sudo systemctl start illustration
sudo systemctl status illustration
```

#### Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx

# Create config
sudo nano /etc/nginx/sites-available/illustration
```

**Nginx Config:**
```nginx
upstream api_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long-running inference
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

**Enable:**
```bash
sudo ln -s /etc/nginx/sites-available/illustration /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Add HTTPS (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renew
sudo systemctl enable certbot.timer
```

#### Monitor & Scale

```bash
# View logs
sudo journalctl -u illustration -f

# Monitor CPU/Memory
htop

# For auto-scaling, use AWS Auto Scaling Groups
# with Launch Templates
```

### Option B: AWS Lambda + API Gateway

**Challenge:** InsightFace models exceed Lambda limits (250MB)

**Solution:** Use container image on ECR

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name illustration-api

# 2. Build and push image
docker build -t illustration-api .
docker tag illustration-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/illustration-api:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/illustration-api:latest

# 3. Create Lambda function from ECR image
# AWS Console → Lambda → Create Function
# Choose: Container Image
# Select pushed image from ECR

# 4. Create API Gateway
# API Gateway → Create API → REST API
# Create resource mapping to Lambda
```

---

## 4. Replicate.com (Serverless)

### Setup Guide

1. **Create Cog Model**
   ```bash
   # Install Cog
   pip install cog
   
   # Create cog.yaml
   cd backend
   ```

**cog.yaml:**
```yaml
build:
  gpu: true
  cuda: "11.8"
  system_packages:
    - "libsm6"
    - "libxext6"
  python_version: "3.10"
  python_packages:
    - "fastapi==0.109.0"
    - "uvicorn==0.27.0"
    - "insightface==0.7.3"
    - "opencv-python==4.9.0.80"
    - "pillow==10.1.0"
    - "torch==2.1.2"
    - "torchvision==0.16.2"

predict: "predict.py:Predictor"
```

2. **Create predict.py**
```python
from cog import BasePredictor, Input, Path
import torch
from fastapi import FastAPI, UploadFile, File
from main import app as fastapi_app

class Predictor(BasePredictor):
    def setup(self):
        # Load models
        pass
    
    def predict(self, child_photo: Path, illustration: Path) -> Path:
        # Process images
        # Return result path
        pass
```

3. **Push to Replicate**
```bash
cog login

# Enable GitHub syncing at replicate.com
# Or manually push:
cog push r8.im/username/illustration-personalizer
```

4. **Use API**
```bash
curl -X POST https://api.replicate.com/v1/predictions \
  -H "Authorization: Token $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "...",
    "input": {
      "child_photo": "https://...",
      "illustration": "https://..."
    }
  }'
```

---

## 5. Vercel (Frontend)

### Deploy Next.js Frontend

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to https://vercel.com/new
   - Select GitHub repository
   - Choose `/frontend` as root directory

3. **Configure Environment**
   - Add environment variable:
     ```
     NEXT_PUBLIC_API_URL=https://your-api-domain.com
     ```

4. **Deploy**
   - Click Deploy
   - Vercel automatically builds and deploys
   - Get URL like: `https://illustration-assgn.vercel.app`

### Auto-Deploy on Push
- Vercel automatically redeploys when you push to main branch

---

## 6. Docker Multi-Stage Build

### For Cloud Deployment

**Dockerfile (Optimized):**
```dockerfile
# Build stage
FROM python:3.10-slim as builder

WORKDIR /build
RUN apt-get update && apt-get install -y \
    build-essential \
    libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    libsm6 libxext6 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .
RUN mkdir -p uploads outputs models

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["python", "main.py"]
```

**Build & Test Locally:**
```bash
docker build -t illustration-api:latest .
docker run -p 8000:8000 illustration-api:latest
```

---

## 7. Environment Variables for Production

### Backend (.env)
```bash
# Security
DEVICE=cpu              # Use GPU if available
API_HOST=0.0.0.0
API_PORT=8000

# Rate limiting (v2)
MAX_REQUESTS_PER_HOUR=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/illustration/api.log

# AWS (if using S3)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_S3_BUCKET=your_bucket
```

### Frontend (.env.production)
```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_ENV=production
```

---

## 8. Monitoring & Analytics

### Logging
```bash
# AWS CloudWatch
# Set environment variable:
LOG_GROUP=/aws/lambda/illustration-api

# Or use Datadog
# pip install datadog
```

### Performance Monitoring
```python
# Add to main.py
from prometheus_client import Counter, Histogram
import time

request_duration = Histogram('request_duration_seconds', 'Request duration')
personalize_counter = Counter('personalize_requests_total', 'Total personalize requests')

@app.post("/personalize")
async def personalize_illustration(...):
    start = time.time()
    try:
        # ... processing ...
        personalize_counter.inc()
    finally:
        request_duration.observe(time.time() - start)
```

### Error Tracking
```bash
# Use Sentry
pip install sentry-sdk

# In main.py
import sentry_sdk
sentry_sdk.init("https://your-sentry-dsn@sentry.io/...")
```

---

## 9. Backup & Recovery

### Database Backup (v2)
```bash
# PostgreSQL backup
pg_dump illustration_db > backup_$(date +%Y%m%d).sql

# Restore
psql illustration_db < backup_20251224.sql
```

### File Backup
```bash
# AWS S3 sync
aws s3 sync ./outputs s3://your-bucket/backups/

# Automated daily
0 2 * * * aws s3 sync /app/outputs s3://your-bucket/daily/
```

---

## 10. Performance Optimization for Production

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_face_detector():
    return FaceDetector()
```

### Connection Pooling
```python
# Use connection pool for databases
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://...',
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

### CDN for Frontend
```bash
# Cloudflare CDN
# Free tier includes:
# - Global CDN
# - Automatic caching
# - Free SSL/TLS
```

---

## Recommendation

For starting:
1. **Local:** Current setup ✓
2. **Quick Testing:** Railway.app (free tier)
3. **Production:** 
   - Backend: AWS EC2 + Nginx
   - Frontend: Vercel (free)
   - Total cost: ~$10/month

For scaling:
- Use Replicate for serverless
- Add Redis cache
- Use CloudFront for CDN
- Implement queue system (RabbitMQ)

---

**Deployment Ready! Choose your platform above.**
