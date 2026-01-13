"""
Block/Braille Character ASCII Converter

Uses Unicode block elements and Braille patterns to achieve
higher visual resolution than standard ASCII characters.
Each Braille character can represent a 2x4 pixel pattern.
"""
import numpy as np
from PIL import Image
from .base import BaseConverter


class BlockCharConverter(BaseConverter):
    """
    High-resolution ASCII converter using Unicode block and Braille characters.

    Block characters (▀▄█░▒▓) provide shading, while Braille patterns
    (⠀-⣿) can encode 2x4 binary pixel grids, effectively increasing
    resolution by 8x compared to standard ASCII.
    """

    # Unicode block shading characters (light to dark)
    BLOCK_CHARS = " ░▒▓█"

    # Half-block characters for 2x1 pixel representation
    HALF_BLOCKS = " ▄▀█"

    # Braille Unicode offset (U+2800)
    BRAILLE_OFFSET = 0x2800

    @property
    def name(self) -> str:
        return "Block/Braille Characters"

    @property
    def description(self) -> str:
        return "High-resolution ASCII using Unicode blocks (░▒▓█) or Braille patterns for 8x pixel density increase."

    def convert(self, image_path: str, width: int = None,
                mode: str = "block", threshold: int = 128) -> str:
        """
        Convert image using block or Braille characters.

        Args:
            image_path: Path to input image
            width: Output width in characters
            mode: 'block' for shading blocks, 'braille' for Braille patterns,
                  'halfblock' for half-block vertical resolution
            threshold: Brightness threshold for binary modes

        Returns:
            ASCII art using Unicode block/Braille characters
        """
        if width is None:
            width = self.width

        if mode == "braille":
            return self._convert_braille(image_path, width, threshold)
        elif mode == "halfblock":
            return self._convert_halfblock(image_path, width)
        else:
            return self._convert_block(image_path, width)

    def _convert_block(self, image_path: str, width: int) -> str:
        """Convert using block shading characters."""
        image = self.load_image(image_path)
        image = self.resize_image(image, width)
        pixels = self.image_to_grayscale(image)

        ascii_lines = []
        for row in pixels:
            line = ""
            for pixel in row:
                # Map 0-255 to block characters (inverted - dark = dense)
                index = int((255 - pixel) / 256 * len(self.BLOCK_CHARS))
                index = min(index, len(self.BLOCK_CHARS) - 1)
                line += self.BLOCK_CHARS[index]
            ascii_lines.append(line)

        return "\n".join(ascii_lines)

    def _convert_halfblock(self, image_path: str, width: int) -> str:
        """
        Convert using half-block characters for 2x vertical resolution.
        Each output character represents 2 vertical pixels.
        """
        image = self.load_image(image_path)

        # Calculate dimensions - we need even height
        orig_width, orig_height = image.size
        aspect_ratio = orig_height / orig_width
        new_height = int(aspect_ratio * width * 1.1)  # Less vertical squish
        if new_height % 2 != 0:
            new_height += 1

        image = image.resize((width, new_height))
        pixels = np.array(image.convert("L"))

        ascii_lines = []
        # Process 2 rows at a time
        for y in range(0, pixels.shape[0] - 1, 2):
            line = ""
            for x in range(pixels.shape[1]):
                top_pixel = pixels[y, x]
                bottom_pixel = pixels[y + 1, x]

                # Threshold to binary
                top_on = top_pixel < 128  # Dark = on
                bottom_on = bottom_pixel < 128

                if top_on and bottom_on:
                    line += '█'  # Full block
                elif top_on and not bottom_on:
                    line += '▀'  # Upper half
                elif not top_on and bottom_on:
                    line += '▄'  # Lower half
                else:
                    line += ' '  # Empty

            ascii_lines.append(line)

        return "\n".join(ascii_lines)

    def _convert_braille(self, image_path: str, width: int, threshold: int) -> str:
        """
        Convert using Braille patterns.

        Each Braille character represents a 2x4 pixel grid:
        ⠁⠂⠄⠈⠐⠠⡀⢀ = individual dots
        ⣿ = all 8 dots

        Dot positions (bit values):
        1 8
        2 16
        4 32
        64 128
        """
        image = self.load_image(image_path)

        # Calculate dimensions for Braille (each char = 2x4 pixels)
        orig_width, orig_height = image.size
        aspect_ratio = orig_height / orig_width

        # Braille width in actual pixels = width * 2
        pixel_width = width * 2
        pixel_height = int(aspect_ratio * pixel_width * 0.5)  # Adjust for aspect

        # Round to multiples of 2 and 4
        pixel_width = (pixel_width // 2) * 2
        pixel_height = (pixel_height // 4) * 4

        image = image.resize((pixel_width, pixel_height))
        pixels = np.array(image.convert("L"))

        # Threshold to binary
        binary = (pixels < threshold).astype(np.uint8)

        ascii_lines = []
        # Process 4 rows at a time, 2 columns at a time
        for y in range(0, pixel_height, 4):
            line = ""
            for x in range(0, pixel_width, 2):
                # Build Braille character from 2x4 pixel block
                braille_value = 0

                # Check bounds and set bits
                if y < pixel_height and x < pixel_width:
                    if binary[y, x]: braille_value |= 0x01
                if y < pixel_height and x + 1 < pixel_width:
                    if binary[y, x + 1]: braille_value |= 0x08
                if y + 1 < pixel_height and x < pixel_width:
                    if binary[y + 1, x]: braille_value |= 0x02
                if y + 1 < pixel_height and x + 1 < pixel_width:
                    if binary[y + 1, x + 1]: braille_value |= 0x10
                if y + 2 < pixel_height and x < pixel_width:
                    if binary[y + 2, x]: braille_value |= 0x04
                if y + 2 < pixel_height and x + 1 < pixel_width:
                    if binary[y + 2, x + 1]: braille_value |= 0x20
                if y + 3 < pixel_height and x < pixel_width:
                    if binary[y + 3, x]: braille_value |= 0x40
                if y + 3 < pixel_height and x + 1 < pixel_width:
                    if binary[y + 3, x + 1]: braille_value |= 0x80

                # Convert to Braille character
                line += chr(self.BRAILLE_OFFSET + braille_value)

            ascii_lines.append(line)

        return "\n".join(ascii_lines)

    def convert_grayscale_braille(self, image_path: str, width: int = None) -> str:
        """
        Braille with grayscale dithering for better tonal representation.
        Uses error diffusion to convert grayscale to binary before Braille.
        """
        if width is None:
            width = self.width

        image = self.load_image(image_path)

        # Calculate dimensions
        orig_width, orig_height = image.size
        aspect_ratio = orig_height / orig_width
        pixel_width = width * 2
        pixel_height = int(aspect_ratio * pixel_width * 0.5)
        pixel_width = (pixel_width // 2) * 2
        pixel_height = (pixel_height // 4) * 4

        image = image.resize((pixel_width, pixel_height))
        pixels = np.array(image.convert("L"), dtype=float)

        # Floyd-Steinberg dithering
        for y in range(pixel_height):
            for x in range(pixel_width):
                old_pixel = pixels[y, x]
                new_pixel = 255 if old_pixel > 128 else 0
                pixels[y, x] = new_pixel
                error = old_pixel - new_pixel

                # Distribute error to neighbors
                if x + 1 < pixel_width:
                    pixels[y, x + 1] += error * 7 / 16
                if y + 1 < pixel_height:
                    if x > 0:
                        pixels[y + 1, x - 1] += error * 3 / 16
                    pixels[y + 1, x] += error * 5 / 16
                    if x + 1 < pixel_width:
                        pixels[y + 1, x + 1] += error * 1 / 16

        # Convert dithered image to Braille
        binary = (pixels < 128).astype(np.uint8)

        ascii_lines = []
        for y in range(0, pixel_height, 4):
            line = ""
            for x in range(0, pixel_width, 2):
                braille_value = 0
                if y < pixel_height and x < pixel_width and binary[y, x]:
                    braille_value |= 0x01
                if y < pixel_height and x + 1 < pixel_width and binary[y, x + 1]:
                    braille_value |= 0x08
                if y + 1 < pixel_height and x < pixel_width and binary[y + 1, x]:
                    braille_value |= 0x02
                if y + 1 < pixel_height and x + 1 < pixel_width and binary[y + 1, x + 1]:
                    braille_value |= 0x10
                if y + 2 < pixel_height and x < pixel_width and binary[y + 2, x]:
                    braille_value |= 0x04
                if y + 2 < pixel_height and x + 1 < pixel_width and binary[y + 2, x + 1]:
                    braille_value |= 0x20
                if y + 3 < pixel_height and x < pixel_width and binary[y + 3, x]:
                    braille_value |= 0x40
                if y + 3 < pixel_height and x + 1 < pixel_width and binary[y + 3, x + 1]:
                    braille_value |= 0x80
                line += chr(self.BRAILLE_OFFSET + braille_value)
            ascii_lines.append(line)

        return "\n".join(ascii_lines)


if __name__ == "__main__":
    converter = BlockCharConverter(width=80)
    print(f"Converter: {converter.name}")
    print(f"Description: {converter.description}")
