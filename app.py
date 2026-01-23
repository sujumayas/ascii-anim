"""
ASCII Art Generator - Flask Application

A web application that converts images to ASCII art using
multiple algorithms: brightness mapping, edge detection,
Sobel gradients, block characters, and dithering.

Also includes video frame extraction with green screen removal,
and real-time screen capture to ASCII streaming.
"""
import os
import uuid
import base64
import io
import cv2
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

from converters import (
    BrightnessConverter,
    EdgeDetectionConverter,
    SobelGradientConverter,
    BlockCharConverter,
    DitheringConverter
)
from converters.video_processor import VideoProcessor, GreenScreenSettings

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ascii-art-secret-key'

# Initialize SocketIO with gevent for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['FRAMES_FOLDER'] = os.path.join(os.path.dirname(__file__), 'frames')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload (for videos)
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'webm', 'mkv'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FRAMES_FOLDER'], exist_ok=True)

# Video processor instance
video_processor = VideoProcessor()

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


def allowed_video(filename):
    """Check if video extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_VIDEO_EXTENSIONS']


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


# ============== VIDEO PROCESSING ENDPOINTS ==============

@app.route('/api/video/upload', methods=['POST'])
def upload_video():
    """
    Upload a video file and get its metadata.

    Returns video info and a preview frame.
    """
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_video(file.filename):
        return jsonify({'error': 'Invalid video format. Allowed: mp4, avi, mov, webm, mkv'}), 400

    # Save uploaded file
    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(filepath)

        # Load video and get info
        info = video_processor.load_video(filepath)

        # Get preview frame (middle of video)
        middle_frame = info.frame_count // 2
        frame = video_processor.get_frame(middle_frame)

        # Convert frame to base64 for preview
        _, buffer = cv2.imencode('.jpg', frame)
        preview_b64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'success': True,
            'video_path': filepath,
            'info': {
                'width': info.width,
                'height': info.height,
                'fps': info.fps,
                'frame_count': info.frame_count,
                'duration': round(info.duration, 2)
            },
            'preview': f"data:image/jpeg;base64,{preview_b64}"
        })

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/preview', methods=['POST'])
def preview_green_screen():
    """
    Preview green screen removal on a specific frame.
    """
    data = request.get_json()
    video_path = data.get('video_path')
    frame_number = data.get('frame_number', 0)

    # Green screen settings
    settings = GreenScreenSettings(
        hue_center=data.get('hue_center', 60),
        hue_tolerance=data.get('hue_tolerance', 30),
        saturation_min=data.get('saturation_min', 40),
        value_min=data.get('value_min', 40)
    )

    background = data.get('background', 'white')
    bg_color = tuple(data.get('bg_color', [255, 255, 255]))

    try:
        # Make sure video is loaded
        if video_processor.video_path != video_path:
            video_processor.load_video(video_path)

        original, processed, has_green = video_processor.preview_frame(
            frame_number, settings, background, bg_color
        )

        # Convert frames to base64
        _, orig_buffer = cv2.imencode('.jpg', original)
        orig_b64 = base64.b64encode(orig_buffer).decode('utf-8')

        # For processed frame with transparency, use PNG
        if processed.shape[2] == 4:
            # Convert BGRA to RGBA for proper encoding
            rgba = cv2.cvtColor(processed, cv2.COLOR_BGRA2RGBA)
            from PIL import Image
            import io
            img = Image.fromarray(rgba)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            proc_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            proc_format = 'png'
        else:
            _, proc_buffer = cv2.imencode('.jpg', processed)
            proc_b64 = base64.b64encode(proc_buffer).decode('utf-8')
            proc_format = 'jpeg'

        return jsonify({
            'success': True,
            'has_green_screen': bool(has_green),
            'original': f"data:image/jpeg;base64,{orig_b64}",
            'processed': f"data:image/{proc_format};base64,{proc_b64}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/extract', methods=['POST'])
def extract_frames():
    """
    Extract frames from video with green screen removal.

    Returns a ZIP file containing all extracted frames.
    """
    data = request.get_json()
    video_path = data.get('video_path')
    target_fps = data.get('fps', 12)
    max_frames = data.get('max_frames')

    # Green screen settings
    settings = GreenScreenSettings(
        hue_center=data.get('hue_center', 60),
        hue_tolerance=data.get('hue_tolerance', 30),
        saturation_min=data.get('saturation_min', 40),
        value_min=data.get('value_min', 40)
    )

    background = data.get('background', 'transparent')
    bg_color = tuple(data.get('bg_color', [255, 255, 255]))

    try:
        # Load video if needed
        if video_processor.video_path != video_path:
            video_processor.load_video(video_path)

        # Extract all frames
        frames = list(video_processor.extract_frames(
            target_fps=target_fps,
            settings=settings,
            background=background,
            bg_color=bg_color,
            max_frames=max_frames
        ))

        # Create ZIP file
        zip_buffer = video_processor.create_frames_zip(frames, prefix="frame")

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='frames.zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/extract-and-convert', methods=['POST'])
def extract_and_convert():
    """
    Extract frames and convert them to ASCII art.

    Returns JSON with ASCII art for each frame.
    """
    data = request.get_json()
    video_path = data.get('video_path')
    target_fps = data.get('fps', 12)
    max_frames = data.get('max_frames', 50)  # Limit for ASCII conversion

    # Green screen settings
    settings = GreenScreenSettings(
        hue_center=data.get('hue_center', 60),
        hue_tolerance=data.get('hue_tolerance', 30),
        saturation_min=data.get('saturation_min', 40),
        value_min=data.get('value_min', 40)
    )

    background = data.get('background', 'white')
    bg_color = tuple(data.get('bg_color', [255, 255, 255]))

    # ASCII conversion settings
    converter_id = data.get('converter', 'brightness')
    ascii_width = data.get('width', 80)

    try:
        if converter_id not in CONVERTERS:
            return jsonify({'error': f'Unknown converter: {converter_id}'}), 400

        converter = CONVERTERS[converter_id]

        # Load video if needed
        if video_processor.video_path != video_path:
            video_processor.load_video(video_path)

        ascii_frames = []

        for frame_num, frame in video_processor.extract_frames(
            target_fps=target_fps,
            settings=settings,
            background=background,
            bg_color=bg_color,
            max_frames=max_frames
        ):
            # Save frame temporarily
            temp_path = os.path.join(app.config['FRAMES_FOLDER'], f"temp_{frame_num}.png")
            video_processor.save_frame(frame, temp_path)

            try:
                # Convert to ASCII
                ascii_art = converter.convert(temp_path, width=ascii_width)
                ascii_frames.append({
                    'frame': frame_num,
                    'ascii': ascii_art
                })
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        return jsonify({
            'success': True,
            'frame_count': len(ascii_frames),
            'fps': target_fps,
            'frames': ascii_frames
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== BULK FRAME PROCESSING ENDPOINTS ==============

@app.route('/api/bulk/upload', methods=['POST'])
def bulk_upload_frames():
    """
    Upload a ZIP file containing frames for bulk ASCII conversion.
    Returns list of frames and a preview of the first frame.
    """
    if 'frames_zip' not in request.files:
        return jsonify({'error': 'No ZIP file provided'}), 400

    file = request.files['frames_zip']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.zip'):
        return jsonify({'error': 'Please upload a ZIP file'}), 400

    # Create a unique folder for this batch
    batch_id = str(uuid.uuid4())
    batch_folder = os.path.join(app.config['FRAMES_FOLDER'], batch_id)
    os.makedirs(batch_folder, exist_ok=True)

    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{batch_id}.zip")

    try:
        file.save(zip_path)

        # Extract ZIP
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(batch_folder)

        # Find all image files (sorted by name)
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
        frames = []

        for root, dirs, files in os.walk(batch_folder):
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext in image_extensions:
                    frames.append({
                        'filename': f,
                        'path': os.path.join(root, f)
                    })

        if not frames:
            raise ValueError("No image files found in ZIP")

        # Get preview of first frame
        first_frame_path = frames[0]['path']
        import cv2
        frame_img = cv2.imread(first_frame_path)
        _, buffer = cv2.imencode('.jpg', frame_img)
        preview_b64 = base64.b64encode(buffer).decode('utf-8')

        # Clean up ZIP file
        os.remove(zip_path)

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'frame_count': len(frames),
            'frames': [f['filename'] for f in frames],
            'preview': f"data:image/jpeg;base64,{preview_b64}"
        })

    except Exception as e:
        # Cleanup on error
        if os.path.exists(zip_path):
            os.remove(zip_path)
        import shutil
        if os.path.exists(batch_folder):
            shutil.rmtree(batch_folder)
        return jsonify({'error': str(e)}), 500


@app.route('/api/bulk/preview', methods=['POST'])
def bulk_preview_frame():
    """
    Preview ASCII conversion of a single frame from the batch.
    """
    data = request.get_json()
    batch_id = data.get('batch_id')
    frame_index = data.get('frame_index', 0)
    converter_id = data.get('converter', 'brightness')
    width = data.get('width', 80)

    if converter_id not in CONVERTERS:
        return jsonify({'error': f'Unknown converter: {converter_id}'}), 400

    batch_folder = os.path.join(app.config['FRAMES_FOLDER'], batch_id)
    if not os.path.exists(batch_folder):
        return jsonify({'error': 'Batch not found'}), 404

    try:
        # Find frames
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
        frames = []
        for root, dirs, files in os.walk(batch_folder):
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext in image_extensions:
                    frames.append(os.path.join(root, f))

        if frame_index >= len(frames):
            return jsonify({'error': 'Frame index out of range'}), 400

        frame_path = frames[frame_index]
        converter = CONVERTERS[converter_id]

        # Get converter-specific options
        options = {'width': width}
        if converter_id == 'brightness':
            options['invert'] = data.get('invert', False)
            options['contrast'] = data.get('contrast', 1.0)
            options['brightness'] = data.get('brightness_adj', 1.0)
        elif converter_id == 'edge_detection':
            options['invert'] = data.get('invert', True)
            options['low_threshold'] = data.get('low_threshold', 50)
            options['high_threshold'] = data.get('high_threshold', 150)
        elif converter_id == 'dithering':
            options['algorithm'] = data.get('algorithm', 'floyd-steinberg')
            options['levels'] = data.get('levels', 10)

        # Convert
        ascii_art = converter.convert(frame_path, **options)

        # Get original image for comparison
        import cv2
        frame_img = cv2.imread(frame_path)
        _, buffer = cv2.imencode('.jpg', frame_img)
        original_b64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'success': True,
            'frame_index': frame_index,
            'filename': os.path.basename(frame_path),
            'ascii_art': ascii_art,
            'original': f"data:image/jpeg;base64,{original_b64}"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bulk/convert', methods=['POST'])
def bulk_convert_frames():
    """
    Convert all frames in a batch to ASCII art.
    Returns a ZIP file with .txt files for each frame.
    """
    data = request.get_json()
    batch_id = data.get('batch_id')
    converter_id = data.get('converter', 'brightness')
    width = data.get('width', 80)

    if converter_id not in CONVERTERS:
        return jsonify({'error': f'Unknown converter: {converter_id}'}), 400

    batch_folder = os.path.join(app.config['FRAMES_FOLDER'], batch_id)
    if not os.path.exists(batch_folder):
        return jsonify({'error': 'Batch not found'}), 404

    try:
        converter = CONVERTERS[converter_id]

        # Get converter-specific options
        options = {'width': width}
        if converter_id == 'brightness':
            options['invert'] = data.get('invert', False)
            options['contrast'] = data.get('contrast', 1.0)
            options['brightness'] = data.get('brightness_adj', 1.0)
        elif converter_id == 'edge_detection':
            options['invert'] = data.get('invert', True)
            options['low_threshold'] = data.get('low_threshold', 50)
            options['high_threshold'] = data.get('high_threshold', 150)
        elif converter_id == 'dithering':
            options['algorithm'] = data.get('algorithm', 'floyd-steinberg')
            options['levels'] = data.get('levels', 10)

        # Find all frames
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
        frames = []
        for root, dirs, files in os.walk(batch_folder):
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext in image_extensions:
                    frames.append({
                        'filename': f,
                        'path': os.path.join(root, f)
                    })

        # Create ZIP with ASCII text files
        import zipfile
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for frame in frames:
                # Convert frame to ASCII
                ascii_art = converter.convert(frame['path'], **options)

                # Use same name but with .txt extension
                base_name = os.path.splitext(frame['filename'])[0]
                txt_filename = f"{base_name}.txt"

                zf.writestr(txt_filename, ascii_art)

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='ascii_frames.zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bulk/cleanup', methods=['POST'])
def bulk_cleanup():
    """Clean up batch folder."""
    data = request.get_json()
    batch_id = data.get('batch_id')

    if not batch_id:
        return jsonify({'error': 'No batch_id provided'}), 400

    batch_folder = os.path.join(app.config['FRAMES_FOLDER'], batch_id)

    try:
        import shutil
        if os.path.exists(batch_folder):
            shutil.rmtree(batch_folder)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/cleanup', methods=['POST'])
def cleanup_video():
    """Clean up uploaded video file."""
    data = request.get_json()
    video_path = data.get('video_path')

    try:
        video_processor.close()
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== ANIMATION PLAYER ENDPOINTS ==============

@app.route('/api/animation/upload', methods=['POST'])
def upload_animation_frames():
    """
    Upload a ZIP file containing ASCII text frames for animation.
    Returns the frames data for playback.
    """
    if 'ascii_zip' not in request.files:
        return jsonify({'error': 'No ZIP file provided'}), 400

    file = request.files['ascii_zip']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.zip'):
        return jsonify({'error': 'Please upload a ZIP file'}), 400

    # Create a unique folder for this animation
    anim_id = str(uuid.uuid4())
    anim_folder = os.path.join(app.config['FRAMES_FOLDER'], f"anim_{anim_id}")
    os.makedirs(anim_folder, exist_ok=True)

    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{anim_id}.zip")

    try:
        file.save(zip_path)

        # Extract ZIP
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(anim_folder)

        # Find all text files (sorted by name)
        frames = []
        for root, dirs, files in os.walk(anim_folder):
            for f in sorted(files):
                if f.lower().endswith('.txt'):
                    filepath = os.path.join(root, f)
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as tf:
                        content = tf.read()
                    frames.append({
                        'filename': f,
                        'content': content
                    })

        if not frames:
            raise ValueError("No .txt files found in ZIP")

        # Clean up ZIP file
        os.remove(zip_path)

        # Analyze first frame for dimensions
        first_frame = frames[0]['content']
        lines = first_frame.split('\n')
        height = len(lines)
        width = max(len(line) for line in lines) if lines else 0

        return jsonify({
            'success': True,
            'animation_id': anim_id,
            'frame_count': len(frames),
            'frames': frames,
            'dimensions': {
                'width': width,
                'height': height
            }
        })

    except Exception as e:
        # Cleanup on error
        if os.path.exists(zip_path):
            os.remove(zip_path)
        import shutil
        if os.path.exists(anim_folder):
            shutil.rmtree(anim_folder)
        return jsonify({'error': str(e)}), 500


@app.route('/api/animation/cleanup', methods=['POST'])
def cleanup_animation():
    """Clean up animation folder."""
    data = request.get_json()
    anim_id = data.get('animation_id')

    if not anim_id:
        return jsonify({'error': 'No animation_id provided'}), 400

    anim_folder = os.path.join(app.config['FRAMES_FOLDER'], f"anim_{anim_id}")

    try:
        import shutil
        if os.path.exists(anim_folder):
            shutil.rmtree(anim_folder)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/animation/export-code', methods=['POST'])
def export_animation_code():
    """
    Generate exportable code snippets for the animation.
    Returns code for HTML/JS, React, and Python.
    """
    data = request.get_json()
    frames = data.get('frames', [])
    fps = data.get('fps', 12)

    if not frames:
        return jsonify({'error': 'No frames provided'}), 400

    # Generate JSON representation of frames
    import json
    frames_json = json.dumps([f['content'] for f in frames], indent=2)

    # HTML/JavaScript code
    html_code = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ASCII Animation</title>
    <style>
        body {{
            background: #0f0f0f;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }}
        #ascii-display {{
            font-family: 'Courier New', monospace;
            font-size: 8px;
            line-height: 1;
            white-space: pre;
            color: #e0e0e0;
        }}
    </style>
</head>
<body>
    <pre id="ascii-display"></pre>
    <script>
        const frames = {frames_json};
        const fps = {fps};
        let currentFrame = 0;
        const display = document.getElementById('ascii-display');

        function animate() {{
            display.textContent = frames[currentFrame];
            currentFrame = (currentFrame + 1) % frames.length;
        }}

        setInterval(animate, 1000 / fps);
        animate();
    </script>
</body>
</html>'''

    # React component code
    react_code = f'''import React, {{ useState, useEffect }} from 'react';

const frames = {frames_json};

export default function ASCIIAnimation({{ fps = {fps} }}) {{
    const [currentFrame, setCurrentFrame] = useState(0);

    useEffect(() => {{
        const interval = setInterval(() => {{
            setCurrentFrame(prev => (prev + 1) % frames.length);
        }}, 1000 / fps);
        return () => clearInterval(interval);
    }}, [fps]);

    return (
        <pre style={{{{
            fontFamily: "'Courier New', monospace",
            fontSize: '8px',
            lineHeight: 1,
            whiteSpace: 'pre',
            color: '#e0e0e0',
            background: '#0f0f0f',
            padding: '1rem'
        }}}}>
            {{frames[currentFrame]}}
        </pre>
    );
}}'''

    # Python code (for terminal/pygame)
    python_code = f'''import time
import os

frames = {frames_json}
fps = {fps}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def play_animation():
    """Play ASCII animation in terminal (infinite loop)."""
    frame_delay = 1.0 / fps
    try:
        while True:
            for frame in frames:
                clear_screen()
                print(frame)
                time.sleep(frame_delay)
    except KeyboardInterrupt:
        print("\\nAnimation stopped.")

if __name__ == '__main__':
    play_animation()
'''

    # Pygame code for games
    pygame_code = f'''import pygame
import sys

# Initialize Pygame
pygame.init()

frames = {frames_json}
fps = {fps}

# Calculate dimensions based on first frame
first_frame = frames[0]
lines = first_frame.split('\\n')
char_width = 6  # Approximate monospace character width
char_height = 10  # Approximate monospace character height
width = max(len(line) for line in lines) * char_width + 20
height = len(lines) * char_height + 20

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('ASCII Animation')
font = pygame.font.SysFont('Courier New', 10)
clock = pygame.time.Clock()

current_frame = 0
bg_color = (15, 15, 15)
text_color = (224, 224, 224)

def draw_frame(frame_text):
    screen.fill(bg_color)
    lines = frame_text.split('\\n')
    y = 10
    for line in lines:
        text_surface = font.render(line, True, text_color)
        screen.blit(text_surface, (10, y))
        y += char_height
    pygame.display.flip()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_frame(frames[current_frame])
    current_frame = (current_frame + 1) % len(frames)
    clock.tick(fps)

pygame.quit()
sys.exit()
'''

    return jsonify({
        'success': True,
        'code': {
            'html': html_code,
            'react': react_code,
            'python': python_code,
            'pygame': pygame_code
        }
    })


# ============== LIVE SCREEN CAPTURE (WebSocket) ==============

# Store active streaming sessions
streaming_sessions = {}


def process_frame_to_ascii(image_data, converter_id, width, options=None):
    """
    Process a base64 image frame and convert it to ASCII art.

    Args:
        image_data: Base64 encoded image data (with or without data URL prefix)
        converter_id: ID of the converter to use
        width: Output width in characters
        options: Additional converter options

    Returns:
        ASCII art string
    """
    try:
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        # Decode base64 to image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Save to temporary file for converter
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"stream_{uuid.uuid4()}.jpg")
        image.save(temp_path, 'JPEG', quality=85)

        try:
            # Get converter
            if converter_id not in CONVERTERS:
                converter_id = 'brightness'
            converter = CONVERTERS[converter_id]

            # Build options
            convert_options = {'width': width}
            if options:
                convert_options.update(options)

            # Convert to ASCII
            ascii_art = converter.convert(temp_path, **convert_options)
            return ascii_art

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return f"Error processing frame: {str(e)}"


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'sid': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")
    # Clean up any streaming session
    if request.sid in streaming_sessions:
        del streaming_sessions[request.sid]


@socketio.on('start_stream')
def handle_start_stream(data):
    """
    Start a streaming session.

    Expected data:
    - converter: Converter ID
    - width: ASCII output width
    - options: Converter-specific options
    """
    converter_id = data.get('converter', 'brightness')
    width = data.get('width', 80)
    options = data.get('options', {})

    streaming_sessions[request.sid] = {
        'converter': converter_id,
        'width': width,
        'options': options,
        'frame_count': 0
    }

    emit('stream_started', {
        'status': 'started',
        'converter': converter_id,
        'width': width
    })
    print(f"Stream started for {request.sid}: {converter_id}, width={width}")


@socketio.on('stop_stream')
def handle_stop_stream():
    """Stop the streaming session."""
    if request.sid in streaming_sessions:
        frame_count = streaming_sessions[request.sid].get('frame_count', 0)
        del streaming_sessions[request.sid]
        emit('stream_stopped', {'status': 'stopped', 'total_frames': frame_count})
        print(f"Stream stopped for {request.sid}, total frames: {frame_count}")


@socketio.on('frame')
def handle_frame(data):
    """
    Process a single frame from the screen capture.

    Expected data:
    - image: Base64 encoded image data
    - timestamp: Optional timestamp for the frame
    """
    if request.sid not in streaming_sessions:
        emit('error', {'message': 'No active stream session'})
        return

    session = streaming_sessions[request.sid]
    image_data = data.get('image')

    if not image_data:
        emit('error', {'message': 'No image data received'})
        return

    # Process the frame
    ascii_art = process_frame_to_ascii(
        image_data,
        session['converter'],
        session['width'],
        session.get('options')
    )

    session['frame_count'] += 1

    # Send back the ASCII result
    emit('ascii_frame', {
        'ascii': ascii_art,
        'frame_number': session['frame_count'],
        'timestamp': data.get('timestamp')
    })


@socketio.on('update_settings')
def handle_update_settings(data):
    """
    Update streaming settings on the fly.

    Expected data:
    - converter: New converter ID (optional)
    - width: New width (optional)
    - options: New converter options (optional)
    """
    if request.sid not in streaming_sessions:
        emit('error', {'message': 'No active stream session'})
        return

    session = streaming_sessions[request.sid]

    if 'converter' in data:
        session['converter'] = data['converter']
    if 'width' in data:
        session['width'] = data['width']
    if 'options' in data:
        session['options'] = data['options']

    emit('settings_updated', {
        'converter': session['converter'],
        'width': session['width'],
        'options': session.get('options', {})
    })


if __name__ == '__main__':
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
