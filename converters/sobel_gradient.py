"""
Sobel Gradient ASCII Converter

Uses Sobel operators to detect gradients and edge directions,
then selects ASCII characters that best represent the local
edge orientation (|, -, /, \, etc.).
"""
import cv2
import numpy as np
from PIL import Image
from .base import BaseConverter


class SobelGradientConverter(BaseConverter):
    """
    Sobel gradient-based ASCII converter with directional characters.

    This converter analyzes the gradient direction at each pixel using
    Sobel operators and selects ASCII characters that visually represent
    the edge direction (vertical, horizontal, diagonal lines).
    """

    # Directional characters based on gradient angle
    DIRECTION_CHARS = {
        'horizontal': '-',
        'vertical': '|',
        'diagonal_right': '/',
        'diagonal_left': '\\',
        'none': ' ',
        'strong': '#'
    }

    # Extended directional character mapping
    ANGLE_CHARS = " -\\|/-\\|/"  # Indexed by angle octant

    @property
    def name(self) -> str:
        return "Sobel Gradient"

    @property
    def description(self) -> str:
        return "Edge-aware ASCII using Sobel gradients. Selects directional characters (|, -, /, \\) based on local edge orientation."

    def convert(self, image_path: str, width: int = None,
                magnitude_threshold: float = 30.0,
                show_magnitude: bool = True) -> str:
        """
        Convert image to ASCII using Sobel gradient analysis.

        Args:
            image_path: Path to input image
            width: Output width in characters
            magnitude_threshold: Minimum gradient magnitude to show edges
            show_magnitude: If True, vary character density by magnitude

        Returns:
            ASCII art with directional edge characters
        """
        if width is None:
            width = self.width

        # Load image
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Resize
        height, orig_width = img.shape
        aspect_ratio = height / orig_width
        new_height = int(aspect_ratio * width * 0.55)
        img = cv2.resize(img, (width, new_height))

        # Apply Gaussian blur
        img = cv2.GaussianBlur(img, (3, 3), 0)

        # Compute Sobel gradients
        sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)

        # Compute magnitude and angle
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        angle = np.arctan2(sobel_y, sobel_x)  # Returns angle in radians (-pi to pi)

        # Normalize magnitude for display
        max_mag = magnitude.max() if magnitude.max() > 0 else 1
        magnitude_normalized = magnitude / max_mag * 255

        # Convert to ASCII
        ascii_lines = []
        for y in range(img.shape[0]):
            line = ""
            for x in range(img.shape[1]):
                mag = magnitude_normalized[y, x]
                ang = angle[y, x]

                if mag < magnitude_threshold:
                    # Below threshold - no significant edge
                    if show_magnitude:
                        # Show faint background based on original brightness
                        pixel = 255 - img[y, x]
                        index = int(pixel / 256 * len(self.chars))
                        index = min(index, len(self.chars) - 1)
                        line += self.chars[index]
                    else:
                        line += ' '
                else:
                    # Significant edge - choose directional character
                    char = self._angle_to_char(ang, mag, max_mag)
                    line += char

            ascii_lines.append(line)

        return "\n".join(ascii_lines)

    def _angle_to_char(self, angle: float, magnitude: float, max_magnitude: float) -> str:
        """
        Convert gradient angle to appropriate ASCII character.

        Args:
            angle: Gradient angle in radians (-pi to pi)
            magnitude: Gradient magnitude
            max_magnitude: Maximum magnitude in image

        Returns:
            ASCII character representing the edge direction
        """
        # Normalize angle to 0-360 degrees
        angle_deg = np.degrees(angle) % 180  # Edges are symmetric

        # Map angle to character
        # 0° or 180°: horizontal edge -> |
        # 90°: vertical edge -> -
        # 45°: diagonal -> /
        # 135°: diagonal -> \

        if 0 <= angle_deg < 22.5 or 157.5 <= angle_deg <= 180:
            char = '|'  # Horizontal gradient = vertical edge
        elif 22.5 <= angle_deg < 67.5:
            char = '/'  # Diagonal
        elif 67.5 <= angle_deg < 112.5:
            char = '-'  # Vertical gradient = horizontal edge
        elif 112.5 <= angle_deg < 157.5:
            char = '\\'  # Diagonal

        # Optionally strengthen character based on magnitude
        intensity = magnitude / max_magnitude
        if intensity > 0.7:
            # Strong edges get bolder characters
            bold_map = {'|': '#', '-': '=', '/': '%', '\\': '%'}
            char = bold_map.get(char, char)

        return char

    def convert_combined(self, image_path: str, width: int = None,
                         edge_weight: float = 0.7) -> str:
        """
        Combine Sobel edge detection with brightness mapping.

        Args:
            image_path: Path to input image
            width: Output width in characters
            edge_weight: Weight given to edges vs brightness (0-1)

        Returns:
            ASCII art combining edges and brightness
        """
        if width is None:
            width = self.width

        # Load and resize
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")

        height, orig_width = img.shape
        aspect_ratio = height / orig_width
        new_height = int(aspect_ratio * width * 0.55)
        img = cv2.resize(img, (width, new_height))

        # Blur
        blurred = cv2.GaussianBlur(img, (3, 3), 0)

        # Compute edges using Sobel
        sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)

        # Normalize
        max_mag = magnitude.max() if magnitude.max() > 0 else 1
        edge_normalized = (magnitude / max_mag * 255).astype(np.uint8)

        # Combine edge and brightness
        brightness = 255 - img  # Invert for typical display
        combined = (edge_weight * edge_normalized + (1 - edge_weight) * brightness).astype(np.uint8)

        # Convert to ASCII
        ascii_lines = []
        for row in combined:
            line = ""
            for pixel in row:
                index = int(pixel / 256 * len(self.chars))
                index = min(index, len(self.chars) - 1)
                line += self.chars[index]
            ascii_lines.append(line)

        return "\n".join(ascii_lines)


if __name__ == "__main__":
    converter = SobelGradientConverter(width=80)
    print(f"Converter: {converter.name}")
    print(f"Description: {converter.description}")
