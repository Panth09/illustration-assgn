import cv2
import numpy as np
from insightface.app import FaceAnalysis
import logging
from config import INSIGHTFACE_MODEL, DEVICE

logger = logging.getLogger(__name__)


class FaceDetector:
    """Face detection and embedding extraction using InsightFace"""

    def __init__(self):
        self.app = None
        self.device = DEVICE
        self._initialize()

    def _initialize(self):
        """Initialize the face analysis model"""
        try:
            self.app = FaceAnalysis(
                name=INSIGHTFACE_MODEL,
                root="models",
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
                if self.device == "cuda"
                else ["CPUExecutionProvider"],
            )
            self.app.prepare(ctx_id=0 if self.device == "cuda" else -1)
            logger.info("InsightFace model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize InsightFace: {e}")
            raise

    def detect_face(self, image_path):
        """
        Detect face in an image and extract embeddings

        Args:
            image_path: Path to input image

        Returns:
            dict with detected faces and embeddings
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")

            # Detect faces
            faces = self.app.get(image)

            if not faces:
                logger.warning(f"No faces detected in image: {image_path}")
                return {"detected": False, "faces": []}

            results = []
            for face in faces:
                results.append(
                    {
                        "bbox": face.bbox.tolist(),
                        "kps": face.kps.tolist() if hasattr(face, "kps") else None,
                        "embedding": face.embedding.tolist(),
                        "gender": face.sex,
                        "age": face.age,
                    }
                )

            logger.info(f"Detected {len(faces)} face(s) in image")
            return {"detected": True, "faces": results, "image_shape": image.shape}

        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            raise

    def get_largest_face(self, image_path):
        """
        Get the largest face in the image (best for portrait photos)

        Args:
            image_path: Path to input image

        Returns:
            dict with the largest face
        """
        results = self.detect_face(image_path)

        if not results["detected"]:
            return None

        # Find largest face by bounding box area
        largest = max(
            results["faces"],
            key=lambda f: (f["bbox"][2] - f["bbox"][0])
            * (f["bbox"][3] - f["bbox"][1]),
        )

        return largest
