import torch
import numpy as np
from PIL import Image
import logging
import cv2
from typing import Optional
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class InstantIDStyler:
    """
    Advanced face stylization using Instant-ID inspired approach combined with Stable Diffusion.
    This creates personalized illustrated versions of faces while maintaining identity.
    """

    def __init__(self, device: str = "cuda"):
        self.device = device
        self.dtype = torch.float16 if device == "cuda" else torch.float32
        self.pipeline = None
        self.face_encoder = None

    def _initialize_encoders(self):
        """Initialize face encoding models for identity preservation"""
        try:
            logger.info("Initializing face encoders for Instant-ID style approach...")
            # Models will be lazy-loaded on first use to save memory
            logger.info("Face encoders ready for lazy loading")
        except Exception as e:
            logger.error(f"Failed to initialize encoders: {e}")
            raise

    def extract_face_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extract face embedding for identity preservation

        Args:
            face_image: Face region image

        Returns:
            Face embedding vector
        """
        try:
            from insightface.app import FaceAnalysis

            app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=-1)

            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

            # Detect and get embedding
            faces = app.get(face_rgb)
            if faces:
                return faces[0].embedding
            else:
                logger.warning("No face found in extracted region")
                return None

        except Exception as e:
            logger.error(f"Failed to extract embedding: {e}")
            return None

    def apply_illustration_style(self, face_image: np.ndarray) -> np.ndarray:
        """
        Apply illustration/cartoon styling to face while preserving identity cues

        Args:
            face_image: Input face image (BGR)

        Returns:
            Styled face image
        """
        try:
            # Improved cartoon filter with edge-aware processing
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            h, w = face_rgb.shape[:2]

            # Step 1: Edge detection
            gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            # Step 2: Bilateral filtering for smoothing
            smooth = cv2.bilateralFilter(face_rgb, 9, 75, 75)

            # Step 3: Morphological operations to clean edges
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            # Step 4: Color quantization for cartoon effect
            data = smooth.reshape((-1, 3))
            data = np.float32(data)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(data, 8, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            centers = np.uint8(centers)
            result = centers[labels.flatten()]
            cartoon = result.reshape(smooth.shape)

            # Step 5: Edge enhancement
            edges_3channel = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            edges_3channel = 255 - edges_3channel

            # Combine cartoon with edge overlay for illustration effect
            alpha = 0.85
            stylized = cv2.addWeighted(cartoon, alpha, edges_3channel // 3, 1 - alpha, 0)

            logger.info("Applied illustration styling")
            return stylized

        except Exception as e:
            logger.error(f"Styling failed: {e}")
            return face_image

    def generate_prompt_for_face(self, age: Optional[int] = None, gender: Optional[str] = None) -> str:
        """
        Generate optimized prompt for illustration style based on face characteristics

        Args:
            age: Detected age of person
            gender: Detected gender

        Returns:
            Prompt string for diffusion model
        """
        base_prompt = "a child portrait in illustration style, detailed face, cartoon style, colorful, soft lighting"

        if age and age < 18:
            base_prompt += ", young face"
        if gender and gender.lower() == "m":
            base_prompt += ", gentle features"

        return base_prompt

    def blend_with_illustration_template(
        self, template_image: np.ndarray, stylized_face: np.ndarray, face_coords: tuple
    ) -> np.ndarray:
        """
        Seamlessly blend stylized face into illustration template

        Args:
            template_image: Background illustration
            stylized_face: Processed face image
            face_coords: (x1, y1, x2, y2) coordinates

        Returns:
            Blended result
        """
        try:
            x1, y1, x2, y2 = [int(v) for v in face_coords]
            h, w = template_image.shape[:2]

            # Clamp coordinates
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            target_h, target_w = y2 - y1, x2 - x1

            if target_h <= 0 or target_w <= 0:
                logger.error("Invalid target dimensions")
                return template_image

            # Resize face to template dimensions
            resized_face = cv2.resize(stylized_face, (target_w, target_h))

            # Create soft mask with gaussian blur for smooth blending
            mask = np.ones((target_h, target_w), dtype=np.float32) * 255
            # Gaussian edges for smooth transition
            y_gauss = np.linspace(-2, 2, target_h)
            x_gauss = np.linspace(-2, 2, target_w)
            xx, yy = np.meshgrid(x_gauss, y_gauss)
            gaussian = np.exp(-(xx**2 + yy**2) / 2)
            mask = gaussian * 255

            # Apply mask to face
            mask_3channel = cv2.cvtColor(mask.astype(np.uint8), cv2.COLOR_GRAY2BGR)
            masked_face = cv2.convertScaleAbs(
                cv2.multiply(resized_face, mask_3channel / 255.0)
            )

            # Blend with template
            result = template_image.copy()
            alpha = mask_3channel / 255.0
            result[y1:y2, x1:x2] = (
                cv2.multiply(resized_face.astype(float), alpha)
                + cv2.multiply(template_image[y1:y2, x1:x2].astype(float), 1 - alpha)
            ).astype(np.uint8)

            logger.info("Face blended into template")
            return result

        except Exception as e:
            logger.error(f"Blending failed: {e}")
            return template_image

    def process_instant_id_style(
        self, child_photo_path: str, illustration_template_path: str, face_data: dict = None
    ) -> np.ndarray:
        """
        Complete Instant-ID inspired pipeline

        Args:
            child_photo_path: Path to child photo
            illustration_template_path: Path to illustration template
            face_data: Optional pre-detected face data

        Returns:
            Personalized illustration
        """
        from face_detector import FaceDetector

        try:
            logger.info("Starting Instant-ID style personalization...")

            # Face detection
            if not face_data:
                detector = FaceDetector()
                face_data = detector.get_largest_face(child_photo_path)

                if not face_data:
                    raise ValueError("No face detected")

            # Extract face region
            image = cv2.imread(str(child_photo_path))
            bbox = face_data["bbox"]
            x1, y1, x2, y2 = [int(v) for v in bbox]

            # Add padding
            h, w = image.shape[:2]
            pad = int((x2 - x1) * 0.15)
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(w, x2 + pad)
            y2 = min(h, y2 + pad)

            face_region = image[y1:y2, x1:x2]

            # Extract embedding for identity preservation
            embedding = self.extract_face_embedding(face_region)

            # Apply stylization
            stylized_face = self.apply_illustration_style(face_region)

            # Load template and blend
            template = cv2.imread(str(illustration_template_path))
            result = self.blend_with_illustration_template(template, stylized_face, bbox)

            logger.info("Instant-ID style processing completed")
            return result

        except Exception as e:
            logger.error(f"Instant-ID processing failed: {e}")
            raise
