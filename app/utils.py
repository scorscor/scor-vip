"""
图片上传工具模块
"""
import os
import uuid
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename


# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# 图片配置
IMAGE_CONFIG = {
    'max_size': 5 * 1024 * 1024,  # 最大 5MB
    'thumb_width': 800,  # 缩略图宽度
    'thumb_height': 1000,  # 缩略图高度 (4:5 比例)
    'quality': 85,  # 图片质量
}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image_aspect_ratio(image_path, target_ratio=4/5, tolerance=0.1):
    """
    验证图片长宽比例
    :param image_path: 图片路径
    :param target_ratio: 目标比例 (宽/高)，默认 4:5 = 0.8
    :param tolerance: 允许的误差范围
    :return: (是否通过，实际比例)
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            actual_ratio = width / height

            min_ratio = target_ratio * (1 - tolerance)
            max_ratio = target_ratio * (1 + tolerance)

            is_valid = min_ratio <= actual_ratio <= max_ratio
            return is_valid, actual_ratio
    except Exception as e:
        return False, 0


def crop_image_to_ratio(image_path, output_path, target_ratio=4/5):
    """
    裁剪图片到目标比例
    :param image_path: 原图路径
    :param output_path: 输出路径
    :param target_ratio: 目标比例 (宽/高)
    """
    with Image.open(image_path) as img:
        # 转换为 RGB (处理 PNG 透明背景)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        width, height = img.size
        current_ratio = width / height

        if current_ratio > target_ratio:
            # 图片太宽，裁剪宽度
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        elif current_ratio < target_ratio:
            # 图片太高，裁剪高度
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))

        # 调整到目标尺寸
        img = img.resize((IMAGE_CONFIG['thumb_width'], IMAGE_CONFIG['thumb_height']), Image.Resampling.LANCZOS)

        # 保存
        img.save(output_path, 'JPEG', quality=IMAGE_CONFIG['quality'], optimize=True)


def process_uploaded_image(file, upload_folder='static/uploads/projects', auto_crop=True):
    """
    处理上传的图片文件
    :param file: FileStorage 对象
    :param upload_folder: 上传目录
    :param auto_crop: 是否自动裁剪（前端已裁剪则设为 False）
    :return: (成功/失败，消息/图片 URL)
    """
    # 检查文件
    if not file or file.filename == '':
        return False, '未选择文件'

    if not allowed_file(file.filename):
        return False, '不支持的图片格式，仅支持 PNG, JPG, JPEG, WebP'

    # 检查文件大小
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()
    file.seek(0)  # 重置到文件开头

    if file_size > IMAGE_CONFIG['max_size']:
        return False, '图片大小超过 5MB 限制'

    # 确保上传目录存在
    os.makedirs(upload_folder, exist_ok=True)

    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    temp_path = os.path.join(upload_folder, f"temp_{filename}")
    output_path = os.path.join(upload_folder, filename)

    try:
        # 保存临时文件
        file.save(temp_path)

        if auto_crop:
            # 验证并裁剪图片（旧版自动裁剪逻辑）
            is_valid, ratio = validate_image_aspect_ratio(temp_path)
            # 裁剪并保存
            crop_image_to_ratio(temp_path, output_path)
            # 删除临时文件
            os.remove(temp_path)
        else:
            # 前端已裁剪，直接调整尺寸并保存
            with Image.open(temp_path) as img:
                # 转换为 RGB (处理 PNG 透明背景)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background

                # 调整到目标尺寸
                img = img.resize((IMAGE_CONFIG['thumb_width'], IMAGE_CONFIG['thumb_height']), Image.Resampling.LANCZOS)
                # 保存
                img.save(output_path, 'JPEG', quality=IMAGE_CONFIG['quality'], optimize=True)

            # 删除临时文件
            os.remove(temp_path)

        # 返回图片 URL
        normalized_path = output_path.replace("\\", "/")
        image_url = f'/{normalized_path}'
        return True, image_url

    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        return False, f'图片处理失败：{str(e)}'
