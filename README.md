# ASCII Art Generator

A Flask web application that converts images to ASCII art using 5 different algorithms, plus a video frame extractor with green screen removal for creating ASCII animations.

## Features

### Image to ASCII
- **5 Conversion Methods:**
  1. **Classic Brightness** - Traditional grayscale-to-character mapping
  2. **Edge Detection (Canny)** - Rotoscoping-style outlines using OpenCV
  3. **Sobel Gradient** - Directional characters based on edge orientation
  4. **Block/Braille Characters** - High-resolution Unicode output
  5. **Dithering** - Floyd-Steinberg and other error diffusion algorithms

- **Web Interface** with drag-and-drop image upload
- **Adjustable parameters** for each conversion method
- **Copy to clipboard** and **download** options

### Video Frame Extractor
- **Green screen detection and removal** with adjustable HSV tolerance
- **Frame extraction** at configurable FPS (default: 12 FPS)
- **Background replacement** options: transparent, white, or black
- **Preview** before extraction to fine-tune settings
- **ZIP download** of all extracted frames

### Bulk Frame Converter
- **Upload ZIP** containing image frames (e.g., frame_0000.png, frame_0001.png, ...)
- **Preview** first frame with chosen converter settings
- **Batch convert** all frames to ASCII text files
- **Download ZIP** with .txt files preserving original frame names

### ASCII Animation Player
- **Upload ZIP** containing ASCII text frames (e.g., frame_0000.txt, frame_0001.txt, ...)
- **Preview animation** with adjustable FPS and font size
- **Play/Pause/Stop** controls for animation playback
- **Export code** for use in your applications:
  - **HTML/JavaScript** - Standalone web page with animation
  - **React Component** - Ready-to-use React component
  - **Python (Terminal)** - Terminal-based animation player
  - **Pygame** - Game-ready animation code

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

### Image Conversion
- `GET /` - Web interface
- `GET /api/converters` - List available converters
- `GET /api/convert/<converter_id>/options` - Get options for a converter
- `POST /api/convert` - Convert an image (multipart form data)

### Video Processing
- `POST /api/video/upload` - Upload video, returns metadata and preview
- `POST /api/video/preview` - Preview green screen removal on a frame
- `POST /api/video/extract` - Extract frames as ZIP with green screen removed
- `POST /api/video/cleanup` - Clean up uploaded video file

### Bulk Frame Conversion
- `POST /api/bulk/upload` - Upload ZIP with frames, returns frame list and preview
- `POST /api/bulk/preview` - Preview ASCII conversion of a single frame
- `POST /api/bulk/convert` - Convert all frames, returns ZIP with .txt files
- `POST /api/bulk/cleanup` - Clean up uploaded batch

### Animation Player
- `POST /api/animation/upload` - Upload ZIP with ASCII text frames
- `POST /api/animation/export-code` - Generate exportable code (HTML/JS, React, Python, Pygame)
- `POST /api/animation/cleanup` - Clean up animation files

## Project Structure

```
├── app.py                    # Flask application
├── requirements.txt          # Dependencies
├── converters/               # Conversion algorithms
│   ├── base.py              # Abstract base class
│   ├── brightness.py        # Classic brightness mapping
│   ├── edge_detection.py    # Canny edge detection
│   ├── sobel_gradient.py    # Sobel gradients
│   ├── block_chars.py       # Unicode blocks & Braille
│   ├── dithering.py         # Error diffusion dithering
│   └── video_processor.py   # Video frame extraction & green screen
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
