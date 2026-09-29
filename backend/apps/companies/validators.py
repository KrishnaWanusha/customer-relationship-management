import os
from django.core.exceptions import ValidationError
from PIL import Image

MAX_LOGO_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_company_logo(file):
    if not file:
        return

    if file.size > MAX_LOGO_SIZE_BYTES:
        max_mb = MAX_LOGO_SIZE_BYTES / (1024 * 1024)
        file_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f"Logo file size exceeds the {max_mb:.0f}MB limit. Uploaded file is {file_mb:.1f}MB."
        )

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        raise ValidationError(
            f"Unsupported file extension '{ext}'. Allowed extensions are: {allowed}."
        )

    try:
        image = Image.open(file)
        image.verify()

        if image.format not in ALLOWED_IMAGE_FORMATS:
            allowed_fmt = ", ".join(sorted(ALLOWED_IMAGE_FORMATS))
            raise ValidationError(
                f"Unsupported image format '{image.format}'. Allowed formats are: {allowed_fmt}."
            )
    except ValidationError:
        raise
    except (IOError, SyntaxError, Exception) as exc:
        raise ValidationError("Uploaded file is not a valid or readable image.") from exc
    finally:
        if hasattr(file, "seek"):
            file.seek(0)
