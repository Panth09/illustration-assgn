import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
MODELS_DIR = Path("models")

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_WORKERS = int(os.getenv("API_WORKERS", 1))

# Model configuration
DEVICE = os.getenv("DEVICE", "cpu")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 50)) * 1024 * 1024

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Model paths
INSIGHTFACE_MODEL = "buffalo_l"
