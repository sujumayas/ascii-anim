"""Base class for all ASCII converters."""
from abc import ABC, abstractmethod
from PIL import Image
import numpy as np


class BaseConverter(ABC):
    """Abstract base class for ASCII art converters."""

    # Standard ASCII ramps from dark to light
    ASCII_CHARS_DETAILED = "@%#*+=-:. "
    ASCII_CHARS_EXTENDED = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    ASCII_CHARS_SIMPLE = "@#S%?*+;:,."

    def __init__(self, width: int = 100, char_set: str = "detailed"):
        """
        Initialize the converter.

        Args:
            width: Output width in characters
            char_set: Character set to use ('detailed', 'extended', 'simple')
        """
        self.width = width
        self.char_sets = {
            "detailed": self.ASCII_CHARS_DETAILED,
            "extended": self.ASCII_CHARS_EXTENDED,
            "simple": self.ASCII_CHARS_SIMPLE
        }
        self.chars = self.char_sets.get(char_set, self.ASCII_CHARS_DETAILED)

    def load_image(self, image_path: str) -> Image.Image:
        """Load an image from path."""
        return Image.open(image_path)

    def resize_image(self, image: Image.Image, new_width: int = None) -> Image.Image:
        """
        Resize image maintaining aspect ratio.
        ASCII characters are typically taller than wide, so we adjust.
        """
        if new_width is None:
            new_width = self.width

        width, height = image.size
        aspect_ratio = height / width
        # Adjust for character aspect ratio (chars are ~2x taller than wide)
        new_height = int(aspect_ratio * new_width * 0.55)
        return image.resize((new_width, new_height))

    def image_to_grayscale(self, image: Image.Image) -> np.ndarray:
        """Convert image to grayscale numpy array."""
        grayscale = image.convert("L")
        return np.array(grayscale)

    def pixel_to_char(self, pixel_value: int, invert: bool = False) -> str:
        """Map a pixel value (0-255) to an ASCII character."""
        if invert:
            pixel_value = 255 - pixel_value
        index = int(pixel_value / 256 * len(self.chars))
        index = min(index, len(self.chars) - 1)
        return self.chars[index]

    @abstractmethod
    def convert(self, image_path: str, **kwargs) -> str:
        """
        Convert an image to ASCII art.

        Args:
            image_path: Path to the input image
            **kwargs: Additional converter-specific options

        Returns:
            ASCII art as a string
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this converter."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of this converter."""
        pass
