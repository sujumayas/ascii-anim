"""
Edge Detection ASCII Converter (Rotoscoping Style)

Uses Canny edge detection to create outline-style ASCII art,
similar to rotoscoping in animation. This produces clean line
drawings rather than shaded images.
"""
import cv2
import numpy as np
from PIL import Image
from .base import BaseConverter


class EdgeDetectionConverter(BaseConverter):
    """
    Canny edge detection-based ASCII converter.

    This converter uses OpenCV's Canny edge detection algorithm to extract
    edges from the image, creating a rotoscoping-like effect. The result
    emphasizes outlines and contours rather than shading.
    """

    # Characters optimized for edge representation
    EDGE_CHARS = " .-+*#@"
    LINE_CHARS = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

    @property
    def name(self) -> str:
        return "Edge Detection (Canny)"

    @property
    def description(self) -> str:
        return "Rotoscoping-style ASCII art using Canny edge detection. Creates clean outlines emphasizing contours and boundaries."

    def convert(self, image_path: str, width: int = None, invert: bool = True,
                low_threshold: int = 50, high_threshold: int = 150,
                blur_kernel: int = 5) -> str:
        """
        Convert image to ASCII using edge detection.

        Args:
            image_path: Path to input image
            width: Output width in characters
            invert: Invert output (edges as dark on light)
            low_threshold: Canny low threshold (edges sensitivity)
            high_threshold: Canny high threshold
            blur_kernel: Gaussian blur kernel size (must be odd)

        Returns:
            ASCII art string with edge-detected outlines
        """
        if width is None:
            width = self.width

        # Ensure blur kernel is odd
        if blur_kernel % 2 == 0:
            blur_kernel += 1

        # Load image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Calculate new dimensions maintaining aspect ratio
        height, orig_width = gray.shape
        aspect_ratio = height / orig_width
        new_height = int(aspect_ratio * width * 0.55)

        # Resize
        gray = cv2.resize(gray, (width, new_height))

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

        # Apply Canny edge detection
        edges = cv2.Canny(blurred, low_threshold, high_threshold)

        # Optionally dilate edges for thicker lines
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Convert edges to ASCII
        ascii_lines = []
        for row in edges:
            line = ""
            for pixel in row:
                if invert:
                    # Edge pixels (255) become dense chars, background stays empty
                    char = "#" if pixel > 128 else " "
                else:
                    char = " " if pixel > 128 else "#"
                line += char
            ascii_lines.append(line)

        return "\n".join(ascii_lines)

    def convert_with_intensity(self, image_path: str, width: int = None,
                                low_threshold: int = 30, high_threshold: int = 100) -> str:
        """
        Alternative conversion that preserves some intensity information
        along with edges for a more detailed result.

        Args:
            image_path: Path to input image
            width: Output width in characters
            low_threshold: Canny low threshold
            high_threshold: Canny high threshold

        Returns:
            ASCII art combining edges with intensity
        """
        if width is None:
            width = self.width

        # Load and process image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Resize
        height, orig_width = gray.shape
        aspect_ratio = height / orig_width
        new_height = int(aspect_ratio * width * 0.55)
        gray = cv2.resize(gray, (width, new_height))

        # Get edges
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, low_threshold, high_threshold)

        # Combine edges with grayscale
        # Where there's an edge, use edge character; otherwise use brightness
        ascii_lines = []
        for y in range(gray.shape[0]):
            line = ""
            for x in range(gray.shape[1]):
                if edges[y, x] > 128:
                    # Edge detected - use edge character
                    line += "@"
                else:
                    # No edge - use brightness-based character
                    pixel = 255 - gray[y, x]  # Invert for typical display
                    index = int(pixel / 256 * len(self.LINE_CHARS))
                    index = min(index, len(self.LINE_CHARS) - 1)
                    line += self.LINE_CHARS[index]
            ascii_lines.append(line)

        return "\n".join(ascii_lines)


if __name__ == "__main__":
    converter = EdgeDetectionConverter(width=80)
    print(f"Converter: {converter.name}")
    print(f"Description: {converter.description}")
