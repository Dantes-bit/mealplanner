import io
import cloudinary.uploader
from PIL import Image

def save_meal_picture(form_picture):
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    buffer = io.BytesIO()
    img_format = i.format if i.format else 'PNG'
    i.save(buffer, format=img_format)
    buffer.seek(0)

    result = cloudinary.uploader.upload(buffer, folder="meal_pics")
    return result['secure_url']