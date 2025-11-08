"""
工具函数模块
"""

import io
import shutil
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

def restore_transparent_background(original_image_path: Path, processed_image_data: bytes) -> bytes:
    """
    智能透明背景恢复功能
    通过对比原始图片和处理后图片，只将原始图片中透明的区域在处理后图片中恢复为透明
    """
    try:
        # 打开原始图片
        original_image = Image.open(original_image_path)
        
        # 如果原始图片不是RGBA模式，转换为RGBA
        if original_image.mode != 'RGBA':
            original_image = original_image.convert('RGBA')
        
        # 获取原始图片的透明度信息
        original_alpha = original_image.split()[-1]
        
        # 将处理后的图片数据转换为PIL图像
        processed_image = Image.open(io.BytesIO(processed_image_data))
        
        # 确保处理后图片是RGBA模式
        if processed_image.mode != 'RGBA':
            processed_image = processed_image.convert('RGBA')
        
        # 如果尺寸不匹配，调整处理后图片的尺寸以匹配原始图片
        if processed_image.size != original_image.size:
            logger.warning(f"图片尺寸不匹配，调整处理后的图片尺寸: {processed_image.size} -> {original_image.size}")
            processed_image = processed_image.resize(original_image.size, Image.LANCZOS)
        
        # 创建新的图像数据，应用原始透明度
        new_data = []
        original_pixels = original_image.getdata()
        processed_pixels = processed_image.getdata()
        
        for i, (orig_pixel, proc_pixel) in enumerate(zip(original_pixels, processed_pixels)):
            # 如果原始像素是透明的，保持处理后像素的透明度
            if len(orig_pixel) == 4 and orig_pixel[3] < 10:  # 透明度阈值
                # 保持透明
                new_data.append((proc_pixel[0], proc_pixel[1], proc_pixel[2], 0))
            else:
                # 保持处理后像素的不透明度
                new_data.append(proc_pixel)
        
        # 更新图像数据
        processed_image.putdata(new_data)
        
        # 将图像转换回字节
        output_buffer = io.BytesIO()
        processed_image.save(output_buffer, format='PNG')
        return output_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"智能透明背景恢复失败: {str(e)}")
        return processed_image_data  # 如果失败，返回原始数据

def verify_image(image_data: bytes) -> bool:
    """验证返回的图片数据是否有效"""
    try:
        image = Image.open(io.BytesIO(image_data))
        image.verify()  # 验证图片完整性
        return True
    except Exception as e:
        logger.error(f"图片验证失败: {str(e)}")
        return False

def create_output_structure(input_folder: Path, output_folder: Path, overwrite_existing: bool = False):
    """
    创建输出文件夹结构
    
    Args:
        input_folder: 输入文件夹路径
        output_folder: 输出文件夹路径
        overwrite_existing: 是否覆盖已存在的输出文件夹
    """
    if output_folder.exists() and overwrite_existing:
        logger.info(f"输出文件夹已存在，将覆盖: {output_folder}")
        shutil.rmtree(output_folder)
    
    # 确保输出文件夹存在
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # 复制原始文件夹结构（只创建目录，不删除任何文件）
    for item in input_folder.rglob('*'):
        if item.is_dir():
            relative_path = item.relative_to(input_folder)
            new_dir = output_folder / relative_path
            new_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"确保目录存在: {new_dir}")
    
    logger.info(f"输出文件夹结构已准备: {output_folder}")

def copy_original_file(original_path: Path, output_path: Path):
    """
    将原始文件复制到输出位置
    
    Args:
        original_path: 原始文件路径
        output_path: 输出文件路径
    """
    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制原始文件
        shutil.copy2(original_path, output_path)
        logger.info(f"已复制原始文件到: {output_path}")
        return True
    except Exception as e:
        logger.error(f"复制原始文件失败 {original_path} -> {output_path}: {str(e)}")
        return False