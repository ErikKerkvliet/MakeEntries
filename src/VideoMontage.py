import math
import os
import logging
import urllib.parse
from pathlib import Path
from typing import List, Tuple
import cv2
from PIL import Image
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class VideoMontageGenerator:
    """
    A class for extracting snapshots from videos and creating 5x5 grid montages.

    This class processes video files to extract 25 evenly-distributed snapshots
    and combines them into a single montage image with specified formatting.
    """

    def __init__(self, glv, log_level: int = logging.INFO):
        """
        Initialize the VideoMontageGenerator.

        Args:
            log_level: Logging level (default: logging.INFO)
        """
        self.snapshot_height = 120
        self.grid_size = 5
        self.margin_size = 6
        self.margin_color = (184, 184, 184)  # #b8b8b8 in RGB
        self.output_format = 'JPEG'
        self.glv = glv

        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def create_montage(self, video_path: str) -> str:
        """
        Main method that orchestrates the entire montage creation process.

        Args:
            video_path: Path to the input video file

        Returns:
            str: Path to the created montage file

        Raises:
            FileNotFoundError: If the video file doesn't exist
            ValueError: If the video file is invalid or corrupted
            OSError: If there are file system or permission issues
            RuntimeError: If video processing fails
        """
        try:
            # Validate input file
            video_path = self._clean_path(video_path)
            if not os.path.isfile(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")

            self.logger.info(f"Starting montage creation for: {video_path}")

            # Extract snapshots
            snapshots = self._extract_snapshots(video_path)

            if len(snapshots) != 25:
                raise RuntimeError(f"Expected 25 snapshots, got {len(snapshots)}")

            # Create grid montage
            montage_image = self._create_grid_montage(snapshots)

            # Get output path and save
            output_path = self._get_output_path(video_path)
            montage_image.save(output_path, self.output_format, quality=95, optimize=True)

            self.logger.info(f"Montage created successfully: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Failed to create montage for {video_path}: {str(e)}")
            raise

    def _extract_snapshots(self, video_path: str) -> List[Image.Image]:
        """
        Private method to extract 25 evenly-distributed snapshots from the video.

        Args:
            video_path: Path to the input video file

        Returns:
            List[Image.Image]: List of 25 PIL Image objects

        Raises:
            ValueError: If video cannot be opened or processed
            RuntimeError: If snapshot extraction fails
        """
        snapshots = []
        cap = None

        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            if total_frames <= 0 or fps <= 0:
                raise ValueError(f"Invalid video properties: frames={total_frames}, fps={fps}")

            self.logger.info(f"Video info: {total_frames} frames, {fps:.2f} fps")

            # Calculate frame indices for 25 snapshots
            if total_frames < 25:
                # For very short videos, use available frames and pad with duplicates
                frame_indices = list(range(total_frames))
                # Pad with last frame if needed
                while len(frame_indices) < 25:
                    frame_indices.append(total_frames - 1)
            else:
                # Evenly distribute 25 snapshots across the video duration
                # Include first frame (0) and last frame (total_frames - 1)
                frame_indices = []
                for i in range(25):
                    frame_idx = int(i * (total_frames - 1) / 24)
                    frame_indices.append(frame_idx)

            self.logger.debug(f"Frame indices: {frame_indices[:5]}...{frame_indices[-5:]}")

            # Extract snapshots
            for i, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    self.logger.warning(f"Failed to read frame {frame_idx}, using black frame")
                    # Create a black frame as fallback
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    frame = np.zeros((height, width, 3), dtype=np.uint8)

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)

                # Resize to target height while maintaining aspect ratio
                resized_image = self._resize_image(pil_image, self.snapshot_height)
                snapshots.append(resized_image)

                if (i + 1) % 5 == 0:
                    self.logger.debug(f"Extracted {i + 1}/25 snapshots")

            self.logger.info(f"Successfully extracted {len(snapshots)} snapshots")
            return snapshots

        except Exception as e:
            self.logger.error(f"Error extracting snapshots: {str(e)}")
            raise RuntimeError(f"Failed to extract snapshots: {str(e)}")

        finally:
            if cap is not None:
                cap.release()

    @staticmethod
    def _resize_image(image: Image.Image, target_height: int) -> Image.Image:
        """
        Resize image to target height while maintaining aspect ratio.

        Args:
            image: PIL Image to resize
            target_height: Target height in pixels

        Returns:
            Image.Image: Resized PIL Image
        """
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        target_width = int(target_height * aspect_ratio)

        return image.resize((target_width, target_height), Image.Resampling.LANCZOS)

    def _create_grid_montage(self, snapshots: List[Image.Image]) -> Image.Image:
        """
        Private method to arrange snapshots in a 5x5 grid with margins and gradient shadow effects.

        Args:
            snapshots: List of 25 PIL Image objects

        Returns:
            Image.Image: PIL Image object of the complete montage with gradient shadows

        Raises:
            ValueError: If incorrect number of snapshots provided
        """
        if len(snapshots) != 25:
            raise ValueError(f"Expected 25 snapshots, got {len(snapshots)}")

        # Enhanced shadow settings for gradient effect
        shadow_offset = (3, 3)  # (x_offset, y_offset) - slightly larger for more dramatic effect
        shadow_blur = 4  # Increased blur for smoother gradient
        shadow_color = (96, 96, 96, 140)  # Darker gray with moderate transparency

        # Verify all snapshots have the same height
        for i, snapshot in enumerate(snapshots):
            if snapshot.size[1] != self.snapshot_height:
                self.logger.warning(f"Snapshot {i} has incorrect height: {snapshot.size[1]}")

        # Find the maximum width among all snapshots for consistent layout
        max_width = max(snapshot.size[0] for snapshot in snapshots)

        # Add extra space for gradient shadows (more padding needed for gradient)
        shadow_padding = shadow_blur + max(shadow_offset[0], shadow_offset[1]) + 2
        cell_width = max_width + shadow_padding
        cell_height = self.snapshot_height + shadow_padding

        # Calculate montage dimensions with shadow padding
        montage_width = (cell_width * self.grid_size) + (self.margin_size * (self.grid_size + 1))
        montage_height = (cell_height * self.grid_size) + (self.margin_size * (self.grid_size + 1))

        self.logger.debug(f"Montage dimensions: {montage_width}x{montage_height}")

        # Create montage canvas with margin color background
        montage = Image.new('RGB', (montage_width, montage_height), self.margin_color)

        # Place snapshots in grid with gradient shadows
        for i, snapshot in enumerate(snapshots):
            row = i // self.grid_size
            col = i % self.grid_size

            # Calculate base position with margins
            base_x = self.margin_size + (col * (cell_width + self.margin_size))
            base_y = self.margin_size + (row * (cell_height + self.margin_size))

            # Center the snapshot within its cell if it's narrower than max_width
            x_offset = 0
            if snapshot.size[0] < max_width:
                x_offset = (max_width - snapshot.size[0]) // 2

            snapshot_x = base_x + x_offset
            snapshot_y = base_y

            # Create gradient shadow
            self._add_shadow_to_montage(montage, snapshot,
                                        snapshot_x, snapshot_y,
                                        shadow_offset, shadow_blur, shadow_color)

            # Place the actual snapshot on top of the shadow
            montage.paste(snapshot, (snapshot_x, snapshot_y))

            self.logger.debug(f"Placed snapshot {i} with gradient shadow at position ({snapshot_x}, {snapshot_y})")

        self.logger.info(
            f"Created {self.grid_size}x{self.grid_size} montage with gradient shadows: {montage_width}x{montage_height}")
        return montage

    def _add_shadow_to_montage(self, montage: Image.Image, snapshot: Image.Image,
                               x: int, y: int, offset: Tuple[int, int],
                               blur: int, shadow_color: Tuple[int, int, int, int]) -> None:
        """
        Add a realistic gradient drop shadow effect for a snapshot on the montage.

        Args:
            montage: The main montage image to draw the shadow on
            snapshot: The snapshot image to create shadow for
            x: X position where snapshot will be placed
            y: Y position where snapshot will be placed
            offset: Shadow offset as (x_offset, y_offset)
            blur: Shadow blur amount
            shadow_color: Shadow color as (R, G, B, A)
        """
        try:
            # Calculate shadow position
            shadow_x = x + offset[0]
            shadow_y = y + offset[1]

            # Create larger canvas for gradient shadow effect
            blur_margin = blur + 2
            shadow_width = snapshot.size[0] + (blur_margin * 2)
            shadow_height = snapshot.size[1] + (blur_margin * 2)

            # Create shadow with gradient effect
            shadow_img = Image.new('RGBA', (shadow_width, shadow_height), (0, 0, 0, 0))
            shadow_array = np.array(shadow_img)

            # Define the core shadow area (where the snapshot would be)
            core_left = blur_margin
            core_top = blur_margin
            core_right = core_left + snapshot.size[0]
            core_bottom = core_top + snapshot.size[1]

            # Create gradient shadow using distance-based alpha
            for y_pos in range(shadow_height):
                for x_pos in range(shadow_width):
                    # Calculate distance from the core shadow area
                    if core_left <= x_pos < core_right and core_top <= y_pos < core_bottom:
                        # Inside the core area - full shadow
                        distance = 0
                    else:
                        # Outside core area - calculate minimum distance to core
                        dx = max(0, max(core_left - x_pos, x_pos - core_right + 1))
                        dy = max(0, max(core_top - y_pos, y_pos - core_bottom + 1))
                        distance = math.sqrt(dx * dx + dy * dy)

                    # Calculate alpha based on distance (gradient falloff)
                    if distance <= blur:
                        # Smooth falloff using cosine function for more natural gradient
                        falloff = math.cos((distance / blur) * (math.pi / 2))
                        alpha = int(shadow_color[3] * falloff * falloff)  # Square for softer edge

                        if alpha > 0:
                            shadow_array[y_pos, x_pos] = [
                                shadow_color[0],  # R
                                shadow_color[1],  # G
                                shadow_color[2],  # B
                                alpha  # A
                            ]

            # Convert back to PIL Image
            gradient_shadow = Image.fromarray(shadow_array, 'RGBA')

            # Calculate position for the gradient shadow on montage
            gradient_x = shadow_x - blur_margin
            gradient_y = shadow_y - blur_margin

            # Make sure shadow stays within montage boundaries
            if (gradient_x + shadow_width > 0 and gradient_y + shadow_height > 0 and
                    gradient_x < montage.size[0] and gradient_y < montage.size[1]):

                # Crop shadow if it extends beyond montage boundaries
                crop_left = max(0, -gradient_x)
                crop_top = max(0, -gradient_y)
                crop_right = min(shadow_width, montage.size[0] - gradient_x)
                crop_bottom = min(shadow_height, montage.size[1] - gradient_y)

                if crop_right > crop_left and crop_bottom > crop_top:
                    cropped_shadow = gradient_shadow.crop((crop_left, crop_top, crop_right, crop_bottom))
                    paste_x = max(0, gradient_x)
                    paste_y = max(0, gradient_y)

                    # Composite shadow onto montage
                    temp_montage = montage.convert('RGBA')
                    temp_montage.paste(cropped_shadow, (paste_x, paste_y), cropped_shadow)
                    montage.paste(temp_montage.convert('RGB'), (0, 0))

        except Exception as e:
            self.logger.warning(f"Failed to create gradient shadow effect: {str(e)}")
            # Continue without shadow if there's an error

    def _get_output_path(self, video_path: str) -> str:
        """
        Private method to generate output file path for the montage.

        Args:
            video_path: Path to the input video file

        Returns:
            str: String path for montage file (samples/{video_filename}.jpg)
        """
        video_filename = Path(video_path).stem  # Get filename without extension
        output_filename = f"{video_filename}.jpg"
        # Save directly to the samples folder
        output_path = f'{self.glv.app_folder}/{self.glv.vndb_id}/samples/{output_filename}'

        self.logger.debug(f"Output path: {output_path}")
        return output_path

    def get_video_info(self, video_path: str) -> dict:
        """
        Get basic information about a video file.

        Args:
            video_path: Path to the video file

        Returns:
            dict: Video information including duration, fps, resolution, etc.
        """
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")

            info = {
                'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration_seconds': 0,
                'file_size_mb': 0
            }

            if info['fps'] > 0:
                info['duration_seconds'] = info['total_frames'] / info['fps']

            if os.path.isfile(video_path):
                info['file_size_mb'] = os.path.getsize(video_path) / (1024 * 1024)

            return info

        except Exception as e:
            self.logger.error(f"Error getting video info: {str(e)}")
            raise
        finally:
            if cap is not None:
                cap.release()

    def create_image(self, video_path: str) -> None:
        try:
            video_path = self._clean_path(video_path)

            if os.path.isfile(video_path):
                # Get video info first
                info = self.get_video_info(video_path)
                print(f"Video Info: {info}")

                # Create montage
                montage_path = self.create_montage(video_path)
                print(f"Montage created: {montage_path}")
            else:
                print(f"Video file not found: {video_path}")
                print("Please provide a valid video file path to test the generator.")

        except Exception as e:
            print(f"Error: {str(e)}")

    @staticmethod
    def _clean_path(file_path):
        """Decodes URL-encoded file paths."""
        return urllib.parse.unquote(file_path).replace('file://', '')