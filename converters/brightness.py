"""
Classic Brightness-Based ASCII Converter

This is the traditional approach to ASCII art - mapping pixel brightness
values directly to ASCII characters. Darker pixels get denser characters,
lighter pixels get sparser characters.
"""
from PIL import Image
import numpy as np
from .base import BaseConverter


class BrightnessConverter(BaseConverter):
    """
    Classic brightness-to-ASCII converter.

    This converter maps each pixel's grayscale intensity to a corresponding
    ASCII character. The character set ranges from dense (dark) to sparse (light).
    """

    @property
    def name(self) -> str:
        return "Classic Brightness"

    @property
    def description(self) -> str:
        return "Traditional ASCII art using grayscale intensity mapping. Each pixel's brightness is mapped to a character from a density ramp."

    def convert(self, image_path: str, width: int = None, invert: bool = False,
                contrast: float = 1.0, brightness: float = 1.0) -> str:
        """
        Convert image to ASCII using brightness mapping.

        Args:
            image_path: Path to input image
            width: Output width in characters (default: self.width)
            invert: Invert the brightness (light chars on dark background)
            contrast: Contrast adjustment multiplier (1.0 = no change)
            brightness: Brightness adjustment (1.0 = no change)

        Returns:
            ASCII art string
        """
        if width is None:
            width = self.width

        # Load and prepare image
        image = self.load_image(image_path)
        image = self.resize_image(image, width)
        pixels = self.image_to_grayscale(image)

        # Apply brightness and contrast adjustments
        pixels = pixels.astype(float)
        pixels = (pixels - 128) * contrast + 128  # Contrast
        pixels = pixels * brightness  # Brightness
        pixels = np.clip(pixels, 0, 255).astype(np.uint8)

        # Convert to ASCII
        ascii_lines = []
        for row in pixels:
            line = "".join(self.pixel_to_char(pixel, invert) for pixel in row)
            ascii_lines.append(line)

        return "\n".join(ascii_lines)


# Quick test function
if __name__ == "__main__":
    converter = BrightnessConverter(width=80)
    print(f"Converter: {converter.name}")
    print(f"Description: {converter.description}")
