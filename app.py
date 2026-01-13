"""
ASCII Art Generator - Flask Application

A web application that converts images to ASCII art using
multiple algorithms: brightness mapping, edge detection,
Sobel gradients, block characters, and dithering.
"""
import os
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from converters import (
    BrightnessConverter,
    EdgeDetectionConverter,
    SobelGradientConverter,
    BlockCharConverter,
    DitheringConverter
)

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize converters
CONVERTERS = {
    'brightness': BrightnessConverter(),
    'edge_detection': EdgeDetectionConverter(),
    'sobel_gradient': SobelGradientConverter(),
    'block_chars': BlockCharConverter(),
    'dithering': DitheringConverter()
}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Render the main page."""
    converters_info = [
        {
            'id': key,
            'name': conv.name,
            'description': conv.description
        }
        for key, conv in CONVERTERS.items()
    ]
    return render_template('index.html', converters=converters_info)


@app.route('/api/converters', methods=['GET'])
def get_converters():
    """Return list of available converters with their info."""
    return jsonify([
        {
            'id': key,
            'name': conv.name,
            'description': conv.description
        }
        for key, conv in CONVERTERS.items()
    ])


@app.route('/api/convert', methods=['POST'])
def convert_image():
    """
    Convert an uploaded image to ASCII art.

    Expected form data:
    - image: The image file
    - converter: Converter ID (brightness, edge_detection, etc.)
    - width: Output width in characters (default: 100)
    - Additional converter-specific options as JSON
    """
    # Check for image file
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Get converter
    converter_id = request.form.get('converter', 'brightness')
    if converter_id not in CONVERTERS:
        return jsonify({'error': f'Unknown converter: {converter_id}'}), 400

    converter = CONVERTERS[converter_id]

    # Get options
    width = int(request.form.get('width', 100))

    # Save uploaded file temporarily
    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(filepath)

        # Get converter-specific options
        options = {'width': width}

        # Brightness converter options
        if converter_id == 'brightness':
            options['invert'] = request.form.get('invert', 'false').lower() == 'true'
            options['contrast'] = float(request.form.get('contrast', 1.0))
            options['brightness'] = float(request.form.get('brightness_adj', 1.0))

        # Edge detection options
        elif converter_id == 'edge_detection':
            options['invert'] = request.form.get('invert', 'true').lower() == 'true'
            options['low_threshold'] = int(request.form.get('low_threshold', 50))
            options['high_threshold'] = int(request.form.get('high_threshold', 150))
            options['blur_kernel'] = int(request.form.get('blur_kernel', 5))

        # Sobel gradient options
        elif converter_id == 'sobel_gradient':
            options['magnitude_threshold'] = float(request.form.get('magnitude_threshold', 30.0))
            options['show_magnitude'] = request.form.get('show_magnitude', 'true').lower() == 'true'

        # Block character options
        elif converter_id == 'block_chars':
            options['mode'] = request.form.get('mode', 'block')
            options['threshold'] = int(request.form.get('threshold', 128))

        # Dithering options
        elif converter_id == 'dithering':
            options['algorithm'] = request.form.get('algorithm', 'floyd-steinberg')
            options['levels'] = int(request.form.get('levels', 10))
            options['invert'] = request.form.get('invert', 'false').lower() == 'true'

        # Convert the image
        ascii_art = converter.convert(filepath, **options)

        return jsonify({
            'success': True,
            'ascii_art': ascii_art,
            'converter': converter.name,
            'width': width
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route('/api/convert/<converter_id>/options', methods=['GET'])
def get_converter_options(converter_id):
    """Return available options for a specific converter."""
    options = {
        'brightness': {
            'width': {'type': 'number', 'default': 100, 'min': 20, 'max': 200, 'label': 'Width (chars)'},
            'invert': {'type': 'checkbox', 'default': False, 'label': 'Invert colors'},
            'contrast': {'type': 'range', 'default': 1.0, 'min': 0.5, 'max': 2.0, 'step': 0.1, 'label': 'Contrast'},
            'brightness_adj': {'type': 'range', 'default': 1.0, 'min': 0.5, 'max': 2.0, 'step': 0.1, 'label': 'Brightness'}
        },
        'edge_detection': {
            'width': {'type': 'number', 'default': 100, 'min': 20, 'max': 200, 'label': 'Width (chars)'},
            'invert': {'type': 'checkbox', 'default': True, 'label': 'Invert (edges as dark)'},
            'low_threshold': {'type': 'range', 'default': 50, 'min': 10, 'max': 100, 'step': 5, 'label': 'Low threshold'},
            'high_threshold': {'type': 'range', 'default': 150, 'min': 100, 'max': 250, 'step': 5, 'label': 'High threshold'},
            'blur_kernel': {'type': 'range', 'default': 5, 'min': 1, 'max': 15, 'step': 2, 'label': 'Blur amount'}
        },
        'sobel_gradient': {
            'width': {'type': 'number', 'default': 100, 'min': 20, 'max': 200, 'label': 'Width (chars)'},
            'magnitude_threshold': {'type': 'range', 'default': 30, 'min': 10, 'max': 100, 'step': 5, 'label': 'Edge threshold'},
            'show_magnitude': {'type': 'checkbox', 'default': True, 'label': 'Show background shading'}
        },
        'block_chars': {
            'width': {'type': 'number', 'default': 100, 'min': 20, 'max': 200, 'label': 'Width (chars)'},
            'mode': {
                'type': 'select',
                'default': 'block',
                'options': [
                    {'value': 'block', 'label': 'Block shading (░▒▓█)'},
                    {'value': 'halfblock', 'label': 'Half blocks (▀▄█)'},
                    {'value': 'braille', 'label': 'Braille patterns (⠀-⣿)'}
                ],
                'label': 'Character mode'
            },
            'threshold': {'type': 'range', 'default': 128, 'min': 50, 'max': 200, 'step': 10, 'label': 'Threshold (for Braille)'}
        },
        'dithering': {
            'width': {'type': 'number', 'default': 100, 'min': 20, 'max': 200, 'label': 'Width (chars)'},
            'algorithm': {
                'type': 'select',
                'default': 'floyd-steinberg',
                'options': [
                    {'value': 'floyd-steinberg', 'label': 'Floyd-Steinberg'},
                    {'value': 'atkinson', 'label': 'Atkinson (Mac style)'},
                    {'value': 'jarvis-judice-ninke', 'label': 'Jarvis-Judice-Ninke'},
                    {'value': 'stucki', 'label': 'Stucki'},
                    {'value': 'ordered', 'label': 'Ordered (Bayer)'}
                ],
                'label': 'Dithering algorithm'
            },
            'levels': {'type': 'range', 'default': 10, 'min': 2, 'max': 20, 'step': 1, 'label': 'Gray levels'},
            'invert': {'type': 'checkbox', 'default': False, 'label': 'Invert colors'}
        }
    }

    if converter_id not in options:
        return jsonify({'error': f'Unknown converter: {converter_id}'}), 404

    return jsonify(options[converter_id])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
