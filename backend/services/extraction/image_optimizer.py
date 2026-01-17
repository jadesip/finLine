"""
Image optimization utilities for LLM processing.
"""

import io
import logging

import numpy as np
from PIL import Image, ImageEnhance
from scipy.ndimage import median_filter

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Optimizes images for better LLM extraction results."""

    def __init__(self):
        logger.info("ImageOptimizer initialized")

    def optimize_for_extraction(self, image_bytes: bytes) -> bytes:
        """Optimize image for financial data extraction."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            original_size = img.size
            logger.debug(f"Optimizing image: {original_size[0]}x{original_size[1]}")

            if img.mode != "RGB":
                img = img.convert("RGB")

            # Enhance contrast for better table readability
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)

            # Remove noise while preserving text
            img = self._denoise_image(img)

            # Optimize size without losing quality
            img = self._optimize_dimensions(img)

            # Convert back to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True, quality=95)
            optimized_bytes = buffer.getvalue()

            size_reduction = (1 - len(optimized_bytes) / len(image_bytes)) * 100
            logger.debug(f"Image optimized: {size_reduction:.1f}% size reduction")

            return optimized_bytes

        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return image_bytes

    def _denoise_image(self, img: Image.Image) -> Image.Image:
        """Apply gentle denoising to improve text clarity."""
        img_array = np.array(img)
        filtered = median_filter(img_array, size=1)
        return Image.fromarray(filtered.astype("uint8"))

    def _optimize_dimensions(self, img: Image.Image) -> Image.Image:
        """Optimize image dimensions for LLM processing."""
        max_dimension = 4096

        if img.width > max_dimension or img.height > max_dimension:
            ratio = min(max_dimension / img.width, max_dimension / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Resized to {new_size[0]}x{new_size[1]}")

        return img
