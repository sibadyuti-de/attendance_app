import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from src.config import Config


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def resize_and_compress(image_file):
    """
    Resizes uploaded image to 600x600 and compresses it.
    Returns saved image path.
    """

    if not allowed_file(image_file.filename):
        raise ValueError("Invalid image format. Only PNG, JPG, JPEG allowed.")

    # Generate safe unique filename
    filename = secure_filename(image_file.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    save_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)

    # Open image with Pillow
    image = Image.open(image_file)
    image = image.convert("RGB")  # Ensure JPEG compatible
    image = image.resize(Config.IMAGE_SIZE)

    # Save compressed
    image.save(save_path, format="JPEG", quality=Config.IMAGE_QUALITY, optimize=True)

    relative_path = os.path.join("uploads", unique_name)

    return relative_path.replace("\\", "/")
