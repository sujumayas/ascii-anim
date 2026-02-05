#!/usr/bin/env python3
"""
Convert an image to ASCII art and save as a PNG image.
"""
import sys
import os
import io
import base64

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from converters import BrightnessConverter


def ascii_to_image(ascii_art: str, font_size: int = 10,
                   bg_color: str = "black", text_color: str = "white") -> Image.Image:
    """
    Render ASCII art as a PNG image.

    Args:
        ascii_art: The ASCII art string
        font_size: Font size for rendering
        bg_color: Background color
        text_color: Text color

    Returns:
        PIL Image object
    """
    lines = ascii_art.split('\n')

    # Try to use a monospace font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSansMono.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
            except:
                font = ImageFont.load_default()

    # Calculate image dimensions
    # Use a sample character to get dimensions
    sample_char = "M"
    bbox = font.getbbox(sample_char)
    char_width = bbox[2] - bbox[0]
    char_height = bbox[3] - bbox[1] + 2  # Add a bit of padding

    max_line_length = max(len(line) for line in lines) if lines else 0
    img_width = char_width * max_line_length + 20  # padding
    img_height = char_height * len(lines) + 20  # padding

    # Create image
    img = Image.new('RGB', (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw text
    y = 10
    for line in lines:
        draw.text((10, y), line, font=font, fill=text_color)
        y += char_height

    return img


def convert_image_to_ascii_png(input_path: str, output_path: str,
                                width: int = 100, invert: bool = False,
                                font_size: int = 10):
    """
    Convert an image to ASCII art and save as PNG.

    Args:
        input_path: Path to input image
        output_path: Path to save output PNG
        width: Width of ASCII art in characters
        invert: Invert brightness
        font_size: Font size for output
    """
    # Convert to ASCII
    converter = BrightnessConverter(width=width)
    ascii_art = converter.convert(input_path, width=width, invert=invert)

    # Render to image
    img = ascii_to_image(ascii_art, font_size=font_size)

    # Save
    img.save(output_path)
    print(f"Saved ASCII art image to: {output_path}")

    return ascii_art


def save_base64_image(base64_data: str, output_path: str):
    """Save a base64-encoded image to a file."""
    # Remove data URL prefix if present
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]

    image_data = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)
    print(f"Saved image to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_ascii_image.py <input_image> [output_path] [width]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "ascii_output.png"
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    ascii_art = convert_image_to_ascii_png(input_path, output_path, width=width)
    print("\nASCII Art Preview:")
    print(ascii_art[:1000] + "..." if len(ascii_art) > 1000 else ascii_art)
