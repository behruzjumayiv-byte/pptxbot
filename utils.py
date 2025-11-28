import logging
import os
from PIL import Image

logger = logging.getLogger(__name__)

def get_template_preview(template_num: int) -> str:
    """Shablon faylining yo'lini olish"""
    template_path = f"templates/{template_num}.png"
    
    if os.path.exists(template_path):
        return template_path
    else:
        logger.warning(f"Shablon topilmadi: {template_path}")
        return None

def create_thumbnail(image_path: str, output_path: str, size: tuple = (200, 150)) -> bool:
    """Rasm uchun kichik thumbnail yaratish"""
    try:
        img = Image.open(image_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(output_path)
        return True
    except Exception as e:
        logger.error(f"Thumbnail yaratishda xatolik: {e}")
        return False

def validate_template_exists(template_num: int) -> bool:
    """Shablon mavjudligini tekshirish"""
    template_path = f"templates/{template_num}.png"
    return os.path.exists(template_path)

def ensure_directories():
    """Kerakli papkalarni yaratish"""
    directories = ['templates', 'output']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Papka yaratildi: {directory}")

def format_currency(amount: int) -> str:
    """Pul summalarini formatlash"""
    return f"{amount:,} so'm"

def calculate_presentation_cost(slides_count: int, price_per_slide: int = 500) -> int:
    """Prezentatsiya narxini hisoblash"""
    return slides_count * price_per_slide
