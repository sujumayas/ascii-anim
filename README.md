# ASCII Art Generator

A Flask web application that converts images to ASCII art using 5 different algorithms, including a rotoscoping-style edge detection mode.

## Features

- **5 Conversion Methods:**
  1. **Classic Brightness** - Traditional grayscale-to-character mapping
  2. **Edge Detection (Canny)** - Rotoscoping-style outlines using OpenCV
  3. **Sobel Gradient** - Directional characters based on edge orientation
  4. **Block/Braille Characters** - High-resolution Unicode output
  5. **Dithering** - Floyd-Steinberg and other error diffusion algorithms

- **Web Interface** with drag-and-drop image upload
- **Adjustable parameters** for each conversion method
- **Copy to clipboard** and **download** options

## Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Make sure venv is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the app
python app.py
```

Open http://localhost:5000 in your browser.

## API Endpoints

- `GET /` - Web interface
- `GET /api/converters` - List available converters
- `GET /api/convert/<converter_id>/options` - Get options for a converter
- `POST /api/convert` - Convert an image (multipart form data)

## Project Structure

```
├── app.py                 # Flask application
├── requirements.txt       # Dependencies
├── converters/            # Conversion algorithms
│   ├── base.py           # Abstract base class
│   ├── brightness.py     # Classic brightness mapping
│   ├── edge_detection.py # Canny edge detection
│   ├── sobel_gradient.py # Sobel gradients
│   ├── block_chars.py    # Unicode blocks & Braille
│   └── dithering.py      # Error diffusion dithering
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## Requirements

- Python 3.8+
- Flask
- Pillow
- NumPy
- OpenCV

## License

MIT
