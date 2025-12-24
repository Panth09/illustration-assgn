import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Clean up old uploaded files to save storage

    Args:
        directory: Directory to clean
        max_age_hours: Delete files older than this
    """
    try:
        from time import time

        current_time = time()
        cutoff_time = current_time - (max_age_hours * 3600)

        deleted_count = 0
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_time = file_path.stat().st_mtime
                if file_time < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old files from {directory}")

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")


def validate_image_file(file_path: Path) -> bool:
    """
    Validate that file is a proper image

    Args:
        file_path: Path to image file

    Returns:
        True if valid image, False otherwise
    """
    try:
        import cv2

        img = cv2.imread(str(file_path))
        return img is not None and img.size > 0

    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        return False


def log_request(method: str, endpoint: str, user_id: str = None):
    """
    Log API requests for monitoring

    Args:
        method: HTTP method
        endpoint: API endpoint
        user_id: Optional user identifier
    """
    timestamp = datetime.now().isoformat()
    user_info = f" - User: {user_id}" if user_id else ""
    logger.info(f"{timestamp} - {method} {endpoint}{user_info}")
