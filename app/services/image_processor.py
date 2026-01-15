"""Image processing service for social card images."""

from io import BytesIO
from PIL import Image

# Target dimensions per card type
DIMENSIONS = {
    'summary': (144, 144),           # 1:1 ratio, minimum 144px
    'summary_large_image': (1200, 628)  # ~1.91:1 ratio (Twitter recommended)
}

# Supported image types
ALLOWED_CONTENT_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
}

# Maximum file size (5MB)
MAX_SIZE = 5 * 1024 * 1024


class ImageProcessingError(Exception):
    """Raised when image processing fails."""
    pass


class ImageProcessor:
    """Process images for social card display."""

    def validate(self, file_data: bytes, content_type: str) -> None:
        """Validate file type and size.

        Args:
            file_data: Raw image bytes
            content_type: MIME type of the image

        Raises:
            ImageProcessingError: If validation fails
        """
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ImageProcessingError(
                f"Invalid file type: {content_type}. "
                f"Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )

        if len(file_data) > MAX_SIZE:
            raise ImageProcessingError(
                f"File too large: {len(file_data)} bytes. "
                f"Maximum size: {MAX_SIZE} bytes (5MB)"
            )

    def process(self, file_data: bytes, card_type: str) -> bytes:
        """Process image for social card display.

        Args:
            file_data: Raw image bytes
            card_type: Either 'summary' or 'summary_large_image'

        Returns:
            Processed image as PNG bytes

        Raises:
            ImageProcessingError: If processing fails
        """
        if card_type not in DIMENSIONS:
            raise ImageProcessingError(
                f"Invalid card type: {card_type}. "
                f"Valid types: {', '.join(DIMENSIONS.keys())}"
            )

        try:
            img = Image.open(BytesIO(file_data))
        except Exception as e:
            raise ImageProcessingError(f"Failed to open image: {e}")

        target_size = DIMENSIONS[card_type]

        # Handle transparency by converting to RGB with white background
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                # Use alpha channel as mask
                if img.mode == 'LA':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize and crop to target dimensions
        img = self._resize_and_crop(img, target_size)

        # Save as PNG
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
        return output.getvalue()

    def _resize_and_crop(self, img: Image.Image, target_size: tuple) -> Image.Image:
        """Resize image maintaining aspect ratio, then center crop.

        Args:
            img: PIL Image object
            target_size: (width, height) tuple

        Returns:
            Resized and cropped PIL Image
        """
        target_w, target_h = target_size
        target_ratio = target_w / target_h
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            # Image is wider - scale by height, crop width
            new_h = target_h
            new_w = int(img.width * (target_h / img.height))
        else:
            # Image is taller - scale by width, crop height
            new_w = target_w
            new_h = int(img.height * (target_w / img.width))

        # Resize with high-quality resampling
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Center crop to exact target dimensions
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return img.crop((left, top, left + target_w, top + target_h))

    def get_dimensions(self, card_type: str) -> tuple:
        """Get target dimensions for a card type.

        Args:
            card_type: Either 'summary' or 'summary_large_image'

        Returns:
            (width, height) tuple
        """
        return DIMENSIONS.get(card_type, DIMENSIONS['summary_large_image'])
