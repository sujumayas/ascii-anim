"""
Dithering ASCII Converter

Uses Floyd-Steinberg and other dithering algorithms to create
ASCII art with better tonal gradients and smoother transitions.
Dithering distributes quantization error to achieve the illusion
of more gray levels.
"""
import numpy as np
from PIL import Image
from .base import BaseConverter


class DitheringConverter(BaseConverter):
    """
    Dithering-based ASCII converter.

    Uses error diffusion dithering (Floyd-Steinberg, Atkinson, etc.)
    to create smoother tonal transitions in ASCII art. This produces
    results with better gradient representation than simple mapping.
    """

    @property
    def name(self) -> str:
        return "Dithering"

    @property
    def description(self) -> str:
        return "ASCII art using Floyd-Steinberg or Atkinson dithering for smoother gradients and better tonal representation."

    def convert(self, image_path: str, width: int = None,
                algorithm: str = "floyd-steinberg",
                levels: int = 10, invert: bool = False) -> str:
        """
        Convert image to ASCII using dithering.

        Args:
            image_path: Path to input image
            width: Output width in characters
            algorithm: Dithering algorithm ('floyd-steinberg', 'atkinson',
                      'jarvis-judice-ninke', 'stucki', 'ordered')
            levels: Number of gray levels (maps to charset length)
            invert: Invert brightness

        Returns:
            Dithered ASCII art
        """
        if width is None:
            width = self.width

        image = self.load_image(image_path)
        image = self.resize_image(image, width)
        pixels = np.array(image.convert("L"), dtype=float)

        if invert:
            pixels = 255 - pixels

        # Apply dithering based on algorithm
        if algorithm == "ordered":
            dithered = self._ordered_dither(pixels, levels)
        elif algorithm == "atkinson":
            dithered = self._atkinson_dither(pixels, levels)
        elif algorithm == "jarvis-judice-ninke":
            dithered = self._jarvis_dither(pixels, levels)
        elif algorithm == "stucki":
            dithered = self._stucki_dither(pixels, levels)
        else:  # floyd-steinberg (default)
            dithered = self._floyd_steinberg_dither(pixels, levels)

        # Convert quantized pixels to ASCII
        ascii_lines = []
        for row in dithered:
            line = ""
            for pixel in row:
                # Map quantized value to character
                index = int(pixel / 256 * len(self.chars))
                index = min(max(index, 0), len(self.chars) - 1)
                line += self.chars[index]
            ascii_lines.append(line)

        return "\n".join(ascii_lines)

    def _quantize(self, pixel: float, levels: int) -> float:
        """Quantize pixel value to specified number of levels."""
        step = 256 / levels
        return np.floor(pixel / step) * step + step / 2

    def _floyd_steinberg_dither(self, pixels: np.ndarray, levels: int) -> np.ndarray:
        """
        Floyd-Steinberg dithering.

        Error distribution pattern:
            * 7/16
        3/16 5/16 1/16
        """
        height, width = pixels.shape
        result = pixels.copy()

        for y in range(height):
            for x in range(width):
                old_pixel = result[y, x]
                new_pixel = self._quantize(old_pixel, levels)
                result[y, x] = new_pixel
                error = old_pixel - new_pixel

                # Distribute error to neighbors
                if x + 1 < width:
                    result[y, x + 1] += error * 7 / 16
                if y + 1 < height:
                    if x > 0:
                        result[y + 1, x - 1] += error * 3 / 16
                    result[y + 1, x] += error * 5 / 16
                    if x + 1 < width:
                        result[y + 1, x + 1] += error * 1 / 16

        return np.clip(result, 0, 255)

    def _atkinson_dither(self, pixels: np.ndarray, levels: int) -> np.ndarray:
        """
        Atkinson dithering (used by Apple Macintosh).

        Only distributes 6/8 of error (loses some), creating higher contrast.
        Error distribution pattern:
            * 1/8 1/8
        1/8 1/8 1/8
            1/8
        """
        height, width = pixels.shape
        result = pixels.copy()

        for y in range(height):
            for x in range(width):
                old_pixel = result[y, x]
                new_pixel = self._quantize(old_pixel, levels)
                result[y, x] = new_pixel
                error = (old_pixel - new_pixel) / 8

                # Distribute error (only 6/8 total, creates contrast)
                if x + 1 < width:
                    result[y, x + 1] += error
                if x + 2 < width:
                    result[y, x + 2] += error
                if y + 1 < height:
                    if x > 0:
                        result[y + 1, x - 1] += error
                    result[y + 1, x] += error
                    if x + 1 < width:
                        result[y + 1, x + 1] += error
                if y + 2 < height:
                    result[y + 2, x] += error

        return np.clip(result, 0, 255)

    def _jarvis_dither(self, pixels: np.ndarray, levels: int) -> np.ndarray:
        """
        Jarvis-Judice-Ninke dithering.

        Larger kernel for smoother gradients.
        Error distribution pattern:
                * 7/48 5/48
        3/48 5/48 7/48 5/48 3/48
        1/48 3/48 5/48 3/48 1/48
        """
        height, width = pixels.shape
        result = pixels.copy()

        for y in range(height):
            for x in range(width):
                old_pixel = result[y, x]
                new_pixel = self._quantize(old_pixel, levels)
                result[y, x] = new_pixel
                error = old_pixel - new_pixel

                # Row 0 (current row)
                if x + 1 < width:
                    result[y, x + 1] += error * 7 / 48
                if x + 2 < width:
                    result[y, x + 2] += error * 5 / 48

                # Row 1
                if y + 1 < height:
                    if x >= 2:
                        result[y + 1, x - 2] += error * 3 / 48
                    if x >= 1:
                        result[y + 1, x - 1] += error * 5 / 48
                    result[y + 1, x] += error * 7 / 48
                    if x + 1 < width:
                        result[y + 1, x + 1] += error * 5 / 48
                    if x + 2 < width:
                        result[y + 1, x + 2] += error * 3 / 48

                # Row 2
                if y + 2 < height:
                    if x >= 2:
                        result[y + 2, x - 2] += error * 1 / 48
                    if x >= 1:
                        result[y + 2, x - 1] += error * 3 / 48
                    result[y + 2, x] += error * 5 / 48
                    if x + 1 < width:
                        result[y + 2, x + 1] += error * 3 / 48
                    if x + 2 < width:
                        result[y + 2, x + 2] += error * 1 / 48

        return np.clip(result, 0, 255)

    def _stucki_dither(self, pixels: np.ndarray, levels: int) -> np.ndarray:
        """
        Stucki dithering.

        Similar to Jarvis but different weights.
        """
        height, width = pixels.shape
        result = pixels.copy()

        for y in range(height):
            for x in range(width):
                old_pixel = result[y, x]
                new_pixel = self._quantize(old_pixel, levels)
                result[y, x] = new_pixel
                error = old_pixel - new_pixel

                # Row 0
                if x + 1 < width:
                    result[y, x + 1] += error * 8 / 42
                if x + 2 < width:
                    result[y, x + 2] += error * 4 / 42

                # Row 1
                if y + 1 < height:
                    if x >= 2:
                        result[y + 1, x - 2] += error * 2 / 42
                    if x >= 1:
                        result[y + 1, x - 1] += error * 4 / 42
                    result[y + 1, x] += error * 8 / 42
                    if x + 1 < width:
                        result[y + 1, x + 1] += error * 4 / 42
                    if x + 2 < width:
                        result[y + 1, x + 2] += error * 2 / 42

                # Row 2
                if y + 2 < height:
                    if x >= 2:
                        result[y + 2, x - 2] += error * 1 / 42
                    if x >= 1:
                        result[y + 2, x - 1] += error * 2 / 42
                    result[y + 2, x] += error * 4 / 42
                    if x + 1 < width:
                        result[y + 2, x + 1] += error * 2 / 42
                    if x + 2 < width:
                        result[y + 2, x + 2] += error * 1 / 42

        return np.clip(result, 0, 255)

    def _ordered_dither(self, pixels: np.ndarray, levels: int) -> np.ndarray:
        """
        Ordered (Bayer) dithering.

        Uses a threshold matrix for predictable, pattern-based dithering.
        """
        height, width = pixels.shape

        # 4x4 Bayer matrix
        bayer_matrix = np.array([
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5]
        ]) / 16.0 * 255

        result = pixels.copy()

        for y in range(height):
            for x in range(width):
                threshold = bayer_matrix[y % 4, x % 4]
                adjusted = pixels[y, x] + (threshold - 128) * (256 / levels)
                result[y, x] = self._quantize(adjusted, levels)

        return np.clip(result, 0, 255)


if __name__ == "__main__":
    converter = DitheringConverter(width=80)
    print(f"Converter: {converter.name}")
    print(f"Description: {converter.description}")
