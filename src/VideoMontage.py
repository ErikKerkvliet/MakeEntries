import os
import logging
import urllib.parse
from pathlib import Path
from typing import List
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
        self.montage_dir = glv.img_folder # os.getenv('DEFAULT_IMAGE_DIR')

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

            # Create output directory
            self._ensure_output_directory()

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

    def _resize_image(self, image: Image.Image, target_height: int) -> Image.Image:
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
        Private method to arrange snapshots in a 5x5 grid with margins.

        Args:
            snapshots: List of 25 PIL Image objects

        Returns:
            Image.Image: PIL Image object of the complete montage

        Raises:
            ValueError: If incorrect number of snapshots provided
        """
        if len(snapshots) != 25:
            raise ValueError(f"Expected 25 snapshots, got {len(snapshots)}")

        # Get dimensions of the first snapshot (all should be same height)
        sample_width, sample_height = snapshots[0].size

        # Verify all snapshots have the same height
        for i, snapshot in enumerate(snapshots):
            if snapshot.size[1] != self.snapshot_height:
                self.logger.warning(f"Snapshot {i} has incorrect height: {snapshot.size[1]}")

        # Calculate montage dimensions
        # Total width = 5 snapshots + 6 margins (before first, between each, after last)
        # Total height = 5 snapshots + 6 margins (before first, between each, after last)

        # Find the maximum width among all snapshots for consistent layout
        max_width = max(snapshot.size[0] for snapshot in snapshots)

        montage_width = (max_width * self.grid_size) + (self.margin_size * (self.grid_size + 1))
        montage_height = (self.snapshot_height * self.grid_size) + (self.margin_size * (self.grid_size + 1))

        self.logger.debug(f"Montage dimensions: {montage_width}x{montage_height}")

        # Create montage canvas with margin color background
        montage = Image.new('RGB', (montage_width, montage_height), self.margin_color)

        # Place snapshots in grid
        for i, snapshot in enumerate(snapshots):
            row = i // self.grid_size
            col = i % self.grid_size

            # Calculate position with margins
            x = self.margin_size + (col * (max_width + self.margin_size))
            y = self.margin_size + (row * (self.snapshot_height + self.margin_size))

            # Center the snapshot if it's narrower than max_width
            if snapshot.size[0] < max_width:
                x += (max_width - snapshot.size[0]) // 2

            montage.paste(snapshot, (x, y))

            self.logger.debug(f"Placed snapshot {i} at position ({x}, {y})")

        self.logger.info(f"Created {self.grid_size}x{self.grid_size} montage: {montage_width}x{montage_height}")
        return montage

    def _get_output_path(self, video_path: str) -> str:
        """
        Private method to generate output file path for the montage.

        Args:
            video_path: Path to the input video file

        Returns:
            str: String path for montage file (montages/{video_filename}.jpg)
        """
        video_filename = Path(video_path).stem  # Get filename without extension
        output_filename = f"{video_filename}.jpg"
        output_path = os.path.join(self.montage_dir, output_filename)

        self.logger.debug(f"Output path: {output_path}")
        return output_path

    def _ensure_output_directory(self) -> None:
        """
        Ensure the output directory exists, create if necessary.

        Raises:
            OSError: If directory cannot be created due to permissions or disk space
        """
        try:
            os.makedirs(self.montage_dir, exist_ok=True)
            self.logger.debug(f"Output directory ready: {self.montage_dir}")

            # Check write permissions
            test_file = os.path.join(self.montage_dir, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except (OSError, IOError) as e:
                raise OSError(f"No write permission in directory {self.montage_dir}: {str(e)}")

        except OSError as e:
            self.logger.error(f"Cannot create output directory {self.montage_dir}: {str(e)}")
            raise

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


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    generator = VideoMontageGenerator(log_level=logging.DEBUG)

    # Test with a video file (replace with actual video path)
    try:
        video_path = "/home/erik/Desktop/t.mkv"  # Replace with your video file
        if os.path.isfile(video_path):
            # Get video info first
            info = generator.get_video_info(video_path)
            print(f"Video Info: {info}")

            # Create montage
            montage_path = generator.create_montage(video_path)
            print(f"Montage created: {montage_path}")
        else:
            print(f"Video file not found: {video_path}")
            print("Please provide a valid video file path to test the generator.")

    except Exception as e:
        print(f"Error: {str(e)}")