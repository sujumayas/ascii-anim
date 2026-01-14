"""
Video Frame Extractor with Green Screen Removal

Extracts frames from video files, detects and removes green screen
backgrounds, and prepares frames for ASCII art conversion.
"""
import cv2
import numpy as np
from PIL import Image
import os
import zipfile
import io
from typing import Tuple, List, Optional, Generator
from dataclasses import dataclass


@dataclass
class VideoInfo:
    """Video metadata."""
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float


@dataclass
class GreenScreenSettings:
    """Settings for green screen detection and removal."""
    # HSV range for green detection
    hue_center: int = 60  # Green hue (0-180 in OpenCV)
    hue_tolerance: int = 30
    saturation_min: int = 40
    saturation_max: int = 255
    value_min: int = 40
    value_max: int = 255

    # Morphological operations to clean up mask
    blur_size: int = 5
    erode_iterations: int = 1
    dilate_iterations: int = 2


class VideoProcessor:
    """Process videos: extract frames and remove green screen."""

    def __init__(self):
        self.current_video: Optional[cv2.VideoCapture] = None
        self.video_path: Optional[str] = None

    def load_video(self, video_path: str) -> VideoInfo:
        """Load a video file and return its metadata."""
        if self.current_video is not None:
            self.current_video.release()

        self.video_path = video_path
        self.current_video = cv2.VideoCapture(video_path)

        if not self.current_video.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        info = VideoInfo(
            width=int(self.current_video.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(self.current_video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=self.current_video.get(cv2.CAP_PROP_FPS),
            frame_count=int(self.current_video.get(cv2.CAP_PROP_FRAME_COUNT)),
            duration=0
        )
        info.duration = info.frame_count / info.fps if info.fps > 0 else 0

        return info

    def get_frame(self, frame_number: int) -> Optional[np.ndarray]:
        """Get a specific frame from the loaded video."""
        if self.current_video is None:
            raise ValueError("No video loaded")

        self.current_video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.current_video.read()

        if not ret:
            return None

        return frame

    def detect_green_screen(self, frame: np.ndarray,
                           settings: Optional[GreenScreenSettings] = None) -> Tuple[bool, np.ndarray]:
        """
        Detect if frame has green screen and create mask.

        Returns:
            Tuple of (has_green_screen, mask)
            mask is 255 where green screen is detected, 0 elsewhere
        """
        if settings is None:
            settings = GreenScreenSettings()

        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define green range
        hue_low = max(0, settings.hue_center - settings.hue_tolerance)
        hue_high = min(180, settings.hue_center + settings.hue_tolerance)

        lower_green = np.array([hue_low, settings.saturation_min, settings.value_min])
        upper_green = np.array([hue_high, settings.saturation_max, settings.value_max])

        # Create mask
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Clean up mask with morphological operations
        if settings.blur_size > 0:
            mask = cv2.GaussianBlur(mask, (settings.blur_size, settings.blur_size), 0)

        kernel = np.ones((3, 3), np.uint8)
        if settings.erode_iterations > 0:
            mask = cv2.erode(mask, kernel, iterations=settings.erode_iterations)
        if settings.dilate_iterations > 0:
            mask = cv2.dilate(mask, kernel, iterations=settings.dilate_iterations)

        # Check if significant portion is green (>10% of frame)
        green_ratio = np.sum(mask > 0) / mask.size
        has_green_screen = green_ratio > 0.10

        return has_green_screen, mask

    def remove_green_screen(self, frame: np.ndarray,
                           mask: np.ndarray,
                           background: str = "transparent",
                           bg_color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
        """
        Remove green screen from frame.

        Args:
            frame: BGR frame
            mask: Green screen mask (255 = green)
            background: 'transparent', 'white', 'black', or 'color'
            bg_color: RGB color if background='color'

        Returns:
            Frame with green screen removed (BGRA if transparent, BGR otherwise)
        """
        # Invert mask (255 = keep, 0 = remove)
        mask_inv = cv2.bitwise_not(mask)

        if background == "transparent":
            # Create BGRA image with alpha channel
            b, g, r = cv2.split(frame)
            bgra = cv2.merge([b, g, r, mask_inv])
            return bgra
        else:
            # Create solid background
            if background == "white":
                bg = np.full_like(frame, 255)
            elif background == "black":
                bg = np.zeros_like(frame)
            else:  # custom color
                bg = np.full_like(frame, bg_color[::-1])  # RGB to BGR

            # Blend foreground and background
            mask_3ch = cv2.merge([mask_inv, mask_inv, mask_inv])
            mask_normalized = mask_3ch.astype(float) / 255

            result = (frame * mask_normalized + bg * (1 - mask_normalized)).astype(np.uint8)
            return result

    def extract_frames(self, target_fps: float = 12.0,
                      settings: Optional[GreenScreenSettings] = None,
                      background: str = "transparent",
                      bg_color: Tuple[int, int, int] = (255, 255, 255),
                      max_frames: Optional[int] = None) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        Extract frames from video at target FPS with green screen removal.

        Args:
            target_fps: Desired output frame rate
            settings: Green screen detection settings
            background: Background replacement type
            bg_color: Custom background color
            max_frames: Maximum frames to extract (None = all)

        Yields:
            Tuple of (frame_number, processed_frame)
        """
        if self.current_video is None:
            raise ValueError("No video loaded")

        if settings is None:
            settings = GreenScreenSettings()

        # Calculate frame skip
        video_fps = self.current_video.get(cv2.CAP_PROP_FPS)
        frame_skip = max(1, int(video_fps / target_fps))

        self.current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)

        frame_count = 0
        extracted_count = 0

        while True:
            ret, frame = self.current_video.read()
            if not ret:
                break

            if frame_count % frame_skip == 0:
                # Detect and remove green screen
                has_green, mask = self.detect_green_screen(frame, settings)

                if has_green:
                    processed = self.remove_green_screen(frame, mask, background, bg_color)
                else:
                    if background == "transparent":
                        # Add alpha channel
                        b, g, r = cv2.split(frame)
                        processed = cv2.merge([b, g, r, np.full_like(b, 255)])
                    else:
                        processed = frame

                yield extracted_count, processed
                extracted_count += 1

                if max_frames and extracted_count >= max_frames:
                    break

            frame_count += 1

    def save_frame(self, frame: np.ndarray, output_path: str) -> None:
        """Save a frame to disk."""
        if frame.shape[2] == 4:  # BGRA
            # Convert to RGBA for PIL
            b, g, r, a = cv2.split(frame)
            rgba = cv2.merge([r, g, b, a])
            img = Image.fromarray(rgba, 'RGBA')
            img.save(output_path, 'PNG')
        else:  # BGR
            cv2.imwrite(output_path, frame)

    def create_frames_zip(self, frames: List[Tuple[int, np.ndarray]],
                         prefix: str = "frame") -> io.BytesIO:
        """
        Create a ZIP file containing all frames.

        Args:
            frames: List of (frame_number, frame_data) tuples
            prefix: Filename prefix for frames

        Returns:
            BytesIO containing the ZIP file
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for frame_num, frame in frames:
                # Convert frame to PNG bytes
                if frame.shape[2] == 4:  # BGRA
                    b, g, r, a = cv2.split(frame)
                    rgba = cv2.merge([r, g, b, a])
                    img = Image.fromarray(rgba, 'RGBA')
                else:  # BGR
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb, 'RGB')

                img_buffer = io.BytesIO()
                img.save(img_buffer, 'PNG')
                img_buffer.seek(0)

                filename = f"{prefix}_{frame_num:04d}.png"
                zf.writestr(filename, img_buffer.getvalue())

        zip_buffer.seek(0)
        return zip_buffer

    def preview_frame(self, frame_number: int = 0,
                     settings: Optional[GreenScreenSettings] = None,
                     background: str = "transparent",
                     bg_color: Tuple[int, int, int] = (255, 255, 255)) -> Tuple[np.ndarray, np.ndarray, bool]:
        """
        Get a preview of a frame with green screen processing.

        Returns:
            Tuple of (original_frame, processed_frame, has_green_screen)
        """
        frame = self.get_frame(frame_number)
        if frame is None:
            raise ValueError(f"Could not get frame {frame_number}")

        has_green, mask = self.detect_green_screen(frame, settings)
        processed = self.remove_green_screen(frame, mask, background, bg_color)

        return frame, processed, has_green

    def close(self):
        """Release video resources."""
        if self.current_video is not None:
            self.current_video.release()
            self.current_video = None


# Singleton instance
_processor: Optional[VideoProcessor] = None


def get_processor() -> VideoProcessor:
    """Get or create the video processor instance."""
    global _processor
    if _processor is None:
        _processor = VideoProcessor()
    return _processor
