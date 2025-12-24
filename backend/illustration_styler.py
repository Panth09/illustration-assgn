import torch
import numpy as np
from PIL import Image
import logging
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from transformers import CLIPTextModel
import cv2

logger = logging.getLogger(__name__)


class IllustrationStyler:
    """
    Convert detected faces into stylized illustrated versions using ControlNet + Stable Diffusion
    This uses a combination of face detection and style transfer
    """

    def __init__(self, device="cuda"):
        self.device = device
        self.dtype = torch.float16 if device == "cuda" else torch.float32
        self.pipeline = None
        self._initialize()

    def _initialize(self):
        """Initialize the Stable Diffusion pipeline with ControlNet"""
        try:
            # Using a cartoon/illustration style prompt-based approach
            # For production, you'd use a specialized illustration ControlNet
            logger.info("Initializing illustration styling pipeline...")

            # Load base model
            self.pipeline = None  # Will be lazy-loaded on first use
            logger.info("Illustration pipeline ready for lazy loading")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise

    def extract_face_region(self, image_path, face_bbox):
        """
        Extract face region from image for processing

        Args:
            image_path: Path to input image
            face_bbox: Bounding box [x1, y1, x2, y2]

        Returns:
            Extracted face region and coordinates
        """
        try:
            image = cv2.imread(str(image_path))
            x1, y1, x2, y2 = [int(v) for v in face_bbox]

            # Add padding
            h, w = image.shape[:2]
            pad = int((x2 - x1) * 0.1)
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(w, x2 + pad)
            y2 = min(h, y2 + pad)

            face_region = image[y1:y2, x1:x2]
            return face_region, (x1, y1, x2, y2)

        except Exception as e:
            logger.error(f"Failed to extract face region: {e}")
            raise

    def stylize_face(self, face_image):
        """
        Convert face to stylized/illustrated version
        Currently uses a cartoon filter approach. In production, use specialized model.

        Args:
            face_image: Face image array (BGR)

        Returns:
            Stylized face image
        """
        try:
            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

            # Apply cartoon filter using edge-preserving filters
            # This is a simplified approach - in production use ML-based stylization

            # Bilateral filtering for smoothing while preserving edges
            smooth = cv2.bilateralFilter(face_rgb, 9, 75, 75)

            # Detect edges
            gray = cv2.cvtColor(smooth, cv2.COLOR_RGB2GRAY)
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)

            # Create inverted edges
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            edges = 255 - edges

            # Combine
            stylized = cv2.bitwise_and(smooth, smooth, mask=cv2.cvtColor(edges, cv2.COLOR_RGB2GRAY))

            # Quantize colors for cartoon effect
            data = stylized.reshape((-1, 3))
            data = np.float32(data)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(data, 6, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            centers = np.uint8(centers)
            result = centers[labels.flatten()]
            stylized = result.reshape(stylized.shape)

            logger.info("Face stylization completed")
            return stylized

        except Exception as e:
            logger.error(f"Face stylization failed: {e}")
            raise

    def insert_face_into_illustration(self, illustration_path, stylized_face, face_coords):
        """
        Insert the stylized face into the illustration template

        Args:
            illustration_path: Path to illustration template
            stylized_face: Stylized face image
            face_coords: (x1, y1, x2, y2) coordinates

        Returns:
            Final composite image
        """
        try:
            # Load illustration
            illustration = cv2.imread(str(illustration_path))
            if illustration is None:
                raise ValueError(f"Failed to load illustration: {illustration_path}")

            # Resize stylized face to fit coordinates
            x1, y1, x2, y2 = face_coords
            target_h = y2 - y1
            target_w = x2 - x1

            # Resize stylized face to match target dimensions
            resized_face = cv2.resize(stylized_face, (target_w, target_h))

            # Create mask for smooth blending
            mask = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255

            # Use Poisson blending for seamless integration
            # For simplicity, direct overlay with alpha blending
            alpha = 0.8
            result = illustration.copy()

            # Blend
            result[y1:y2, x1:x2] = cv2.addWeighted(
                resized_face, alpha, illustration[y1:y2, x1:x2], 1 - alpha, 0
            )

            logger.info(f"Face inserted into illustration at coords {face_coords}")
            return result

        except Exception as e:
            logger.error(f"Failed to insert face into illustration: {e}")
            raise

    def process(self, child_photo_path, illustration_template_path):
        """
        End-to-end process: detect face -> stylize -> insert into illustration

        Args:
            child_photo_path: Path to child's photo
            illustration_template_path: Path to illustration template

        Returns:
            Path to output image
        """
        from face_detector import FaceDetector

        try:
            logger.info("Starting end-to-end illustration personalization...")

            # Detect face
            detector = FaceDetector()
            face_data = detector.get_largest_face(child_photo_path)

            if not face_data:
                raise ValueError("No face detected in the provided image")

            # Extract face region
            face_region, coords = self.extract_face_region(child_photo_path, face_data["bbox"])

            # Stylize face
            stylized = self.stylize_face(face_region)

            # Insert into illustration
            result = self.insert_face_into_illustration(illustration_template_path, stylized, coords)

            logger.info("Personalization process completed successfully")
            return result

        except Exception as e:
            logger.error(f"Personalization process failed: {e}")
            raise
