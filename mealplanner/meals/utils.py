import io
import cloudinary.uploader
from PIL import Image, ImageOps

def save_meal_picture(form_picture):
    output_size = (500, 500)
    i = Image.open(form_picture)
    i = ImageOps.exif_transpose(i)
    i.thumbnail(output_size)
    buffer = io.BytesIO()
    img_format = 'PNG' if i.mode in ('RGBA', 'LA', 'P') else 'JPEG'
    if img_format == 'JPEG' and i.mode != 'RGB':
        i = i.convert('RGB')
    i.save(buffer, format=img_format)
    buffer.seek(0)
    result = cloudinary.uploader.upload(buffer, folder="meal_pics")
    return result['secure_url']