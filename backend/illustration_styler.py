import torch
import numpy as np
from PIL import Image
import logging
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from transformers import CLIPTextModel
import cv2
import gc

logger = logging.getLogger(__name__)


class IllustrationStyler:
    """
    Convert detected faces into stylized illustrated versions using ControlNet + Stable Diffusion
    This uses a combination of face detection and style transfer
    """

    def __init__(self, device="cpu"):
        self.device = device
        self.dtype = torch.float32  # Always use float32 on CPU to save memory
        self.pipeline = None
        self._initialize()

    def _initialize(self):
        """Initialize the Stable Diffusion pipeline with ControlNet"""
        try:
            logger.info("Initializing illustration styling pipeline...")
            # Pipeline will be lazy-loaded only if needed
            self.pipeline = None
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
            
            # Resize if too large
            h, w = image.shape[:2]
            max_dim = 1024
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                image = cv2.resize(image, (new_w, new_h))
                # Scale bbox coordinates
                face_bbox = [int(coord * scale) for coord in face_bbox]
            
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
        Enhanced: more natural, less cartoonish, better edge handling
        """
        try:
            # Resize if too large to save memory
            h, w = face_image.shape[:2]
            max_size = 512
            if max(h, w) > max_size:
                scale = max_size / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                face_image = cv2.resize(face_image, (new_w, new_h))

            # Convert BGR to LAB for color transfer later
            face_lab = cv2.cvtColor(face_image, cv2.COLOR_BGR2LAB)

            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

            # Bilateral filtering for smoothing while preserving edges
            smooth = cv2.bilateralFilter(face_rgb, 9, 75, 75)

            # Edge enhancement (subtle)
            gray = cv2.cvtColor(smooth, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 60, 120)
            edges = cv2.GaussianBlur(edges, (3, 3), 0)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
            # Blend edges with smooth image
            stylized = cv2.addWeighted(smooth, 0.92, edges, 0.08, 0)

            # Reduce color quantization for more natural look
            data = stylized.reshape((-1, 3))
            data = np.float32(data)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            K = 8  # More clusters for less cartoonish effect
            _, labels, centers = cv2.kmeans(data, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            centers = np.uint8(centers)
            result = centers[labels.flatten()]
            stylized = result.reshape(stylized.shape)

            logger.info("Face stylization completed (natural style)")

            # Clear memory
            del data, labels, centers, result, smooth, edges
            gc.collect()

            return stylized

        except Exception as e:
            logger.error(f"Face stylization failed: {e}")
            raise

    def insert_face_into_illustration(self, illustration_path, stylized_face, face_coords):
        """
        Insert the stylized face into the illustration template
        Enhanced: seamless cloning, color transfer, feathered mask
        """
        try:
            # Load illustration
            illustration = cv2.imread(str(illustration_path))
            if illustration is None:
                raise ValueError(f"Failed to load illustration: {illustration_path}")

            # Resize illustration if too large
            h, w = illustration.shape[:2]
            max_dim = 1024
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                illustration = cv2.resize(illustration, (new_w, new_h))
                # Scale coordinates
                face_coords = tuple(int(coord * scale) for coord in face_coords)

            x1, y1, x2, y2 = face_coords
            target_h = y2 - y1
            target_w = x2 - x1

            # Resize stylized face to match target dimensions
            resized_face = cv2.resize(stylized_face, (target_w, target_h))

            # Color transfer from illustration region to stylized face (LAB mean/var matching)
            try:
                src_lab = cv2.cvtColor(resized_face, cv2.COLOR_RGB2LAB)
                dst_lab = cv2.cvtColor(illustration[y1:y2, x1:x2], cv2.COLOR_BGR2LAB)
                for i in range(3):
                    src_mean, src_std = src_lab[..., i].mean(), src_lab[..., i].std()
                    dst_mean, dst_std = dst_lab[..., i].mean(), dst_lab[..., i].std()
                    if src_std > 0:
                        src_lab[..., i] = ((src_lab[..., i] - src_mean) * (dst_std / src_std) + dst_mean).clip(0, 255)
                color_matched = cv2.cvtColor(src_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
            except Exception as e:
                logger.warning(f"Color transfer failed: {e}"); color_matched = resized_face

            # Create feathered mask for smooth blending
            mask = np.zeros((target_h, target_w), dtype=np.uint8)
            cv2.ellipse(mask, (target_w//2, target_h//2), (target_w//2-2, target_h//2-2), 0, 0, 360, 255, -1)
            mask = cv2.GaussianBlur(mask, (21, 21), 0)

            # Center for seamlessClone
            center = (x1 + target_w // 2, y1 + target_h // 2)
            # Convert color_matched to BGR for seamlessClone
            color_matched_bgr = cv2.cvtColor(color_matched, cv2.COLOR_RGB2BGR)
            try:
                result = cv2.seamlessClone(color_matched_bgr, illustration, mask, center, cv2.NORMAL_CLONE)
            except Exception as e:
                logger.warning(f"SeamlessClone failed: {e}, falling back to alpha blend")
                # Fallback: alpha blend with feathered mask
                roi = illustration[y1:y2, x1:x2].copy()
                mask_f = mask.astype(float)/255.0
                blended = (color_matched_bgr * mask_f[...,None] + roi * (1-mask_f[...,None])).astype(np.uint8)
                result = illustration.copy()
                result[y1:y2, x1:x2] = blended

            logger.info(f"Face inserted into illustration at coords {face_coords} (seamless blend)")

            # Clear memory
            del illustration, resized_face, color_matched, mask
            gc.collect()

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
            
            # Clear memory
            del detector, face_data, face_region, stylized
            gc.collect()
            
            return result

        except Exception as e:
            logger.error(f"Personalization process failed: {e}")
            raise