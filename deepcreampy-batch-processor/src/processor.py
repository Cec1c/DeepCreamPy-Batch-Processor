"""
主要处理器类
"""

import os
import requests
import io
from pathlib import Path
import shutil
import time
import logging
from PIL import Image

from src.config import API_ENDPOINTS, MODE_DESCRIPTIONS, SUPPORTED_FORMATS
from src.utils import restore_transparent_background, verify_image, create_output_structure, copy_original_file

logger = logging.getLogger(__name__)

class DeepCreamPyBatchProcessor:
    def __init__(self, base_url: str = "http://localhost:8001", mode: int = 2, transparent_bg: bool = False, overwrite_existing: bool = False):
        self.base_url = base_url.rstrip('/')
        self.mode = mode
        self.transparent_bg = transparent_bg
        self.overwrite_existing = overwrite_existing  # 控制是否覆盖已存在的文件
        self.api_endpoint = API_ENDPOINTS.get(mode, "/deepcreampy-mosaic-rcnn-esrgan")
        self.api_url = f"{self.base_url}{self.api_endpoint}"
        self.session = requests.Session()
        self.supported_formats = SUPPORTED_FORMATS
        
        logger.info(f"初始化处理器 - 模式 {mode}: {MODE_DESCRIPTIONS.get(mode, '未知模式')}")
        logger.info(f"API端点: {self.api_url}")
        if transparent_bg:
            logger.info("启用智能透明背景恢复功能")
        if overwrite_existing:
            logger.info("启用覆盖已存在文件模式")
    
    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def is_image_file(self, file_path: Path) -> bool:
        """检查文件是否为支持的图片格式"""
        return file_path.suffix.lower() in self.supported_formats
    
    def get_all_images(self, folder_path: Path) -> list:
        """获取文件夹中所有图片文件的路径"""
        if not folder_path.exists():
            raise ValueError(f"文件夹不存在: {folder_path}")
        
        image_files = []
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and self.is_image_file(file_path):
                image_files.append(file_path)
        
        return image_files
    
    def process_single_image(self, image_path: Path) -> bytes:
        """处理单张图片"""
        try:
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 发送到API处理
            files = {'image': (image_path.name, image_data, 'image/jpeg')}
            response = self.session.post(self.api_url, files=files, timeout=120)
            
            if response.status_code == 200:
                processed_data = response.content
                
                # 如果启用了透明背景恢复功能，处理返回的图片
                if self.transparent_bg:
                    processed_data = restore_transparent_background(image_path, processed_data)
                
                return processed_data
            else:
                logger.error(f"API返回错误: HTTP {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"处理图片时出错 {image_path}: {str(e)}")
            return None
    
    def check_transparency(self, image_path: Path) -> bool:
        """检查图片是否有透明通道"""
        try:
            with Image.open(image_path) as img:
                if img.mode == 'RGBA':
                    # 检查是否有透明像素
                    alpha = img.split()[-1]
                    if min(alpha.getdata()) < 255:
                        return True
            return False
        except Exception as e:
            logger.warning(f"无法检查图片透明度: {image_path.name} - {str(e)}")
            return False
    
    def process_folder(self, input_folder: str, output_folder: str = None):
        """处理整个文件夹中的图片"""
        input_path = Path(input_folder)
        
        # 自动生成输出文件夹名
        if output_folder is None:
            parent_dir = input_path.parent
            folder_name = input_path.name
            output_path = parent_dir / f"new_{folder_name}"
        else:
            output_path = Path(output_folder)
        
        logger.info(f"开始处理文件夹")
        logger.info(f"输入文件夹: {input_path}")
        logger.info(f"输出文件夹: {output_path}")
        logger.info(f"处理模式: {self.mode} - {MODE_DESCRIPTIONS.get(self.mode, '未知模式')}")
        if self.transparent_bg:
            logger.info("智能透明背景恢复: 已启用")
        if self.overwrite_existing:
            logger.info("覆盖模式: 已启用 - 将覆盖已存在的文件")
        else:
            logger.info("覆盖模式: 未启用 - 将跳过已存在的文件")
        
        # 获取所有图片文件
        image_files = self.get_all_images(input_path)
        logger.info(f"找到 {len(image_files)} 张图片需要处理")
        
        if not image_files:
            logger.warning("未找到任何图片文件")
            return
        
        # 创建输出文件夹结构（不删除现有文件）
        create_output_structure(input_path, output_path, self.overwrite_existing)
        
        # 处理统计和失败文件记录
        success_count = 0
        failed_count = 0
        skipped_count = 0
        failed_files = []  # 记录失败的文件信息
        
        # 处理每张图片
        for i, image_path in enumerate(image_files, 1):
            logger.info(f"处理进度: {i}/{len(image_files)} - {image_path.name}")
            
            # 计算输出路径（保持相对路径结构）
            relative_path = image_path.relative_to(input_path)
            output_file_path = output_path / relative_path
            
            # 检查原始图片是否有透明通道
            has_transparency = False
            if self.transparent_bg:
                has_transparency = self.check_transparency(image_path)
                if has_transparency:
                    logger.info(f"检测到透明背景: {image_path.name}")
            
            # 检查输出文件是否已存在（用于断点续传），除非启用了覆盖模式
            if output_file_path.exists() and not self.overwrite_existing:
                logger.info(f"跳过已存在的文件: {output_file_path}")
                skipped_count += 1
                continue
            
            # 处理图片
            processed_image_data = self.process_single_image(image_path)
            
            if processed_image_data and verify_image(processed_image_data):
                # 保存处理后的图片
                with open(output_file_path, 'wb') as f:
                    f.write(processed_image_data)
                
                success_count += 1
                logger.info(f"✓ 成功处理: {image_path.name}")
                if self.transparent_bg and has_transparency:
                    logger.info(f"  已恢复透明背景")
            else:
                # 处理失败，复制原始文件到输出位置
                logger.warning(f"处理失败，将复制原始文件: {image_path.name}")
                if copy_original_file(image_path, output_file_path):
                    failed_count += 1
                    # 记录失败文件信息（相对路径）
                    failed_files.append(str(relative_path))
                    logger.info(f"✓ 已复制原始文件: {output_file_path}")
                else:
                    failed_count += 1
                    # 即使复制失败也记录文件信息
                    failed_files.append(str(relative_path))
                    logger.error(f"✗ 复制原始文件失败: {image_path.name}")
            
            # 添加短暂延迟避免服务器过载
            time.sleep(0.5)
        
        # 输出统计信息
        logger.info(f"\n处理完成!")
        logger.info(f"总计: {len(image_files)}")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {failed_count}")
        logger.info(f"跳过: {skipped_count}")
        logger.info(f"输出文件夹: {output_path}")
        if self.transparent_bg:
            logger.info("智能透明背景恢复: 已应用")
        
        # 输出失败文件列表
        if failed_files:
            logger.info("\n" + "="*50)
            logger.info("失败文件列表 (已复制原始文件到输出目录):")
            for i, failed_file in enumerate(failed_files, 1):
                logger.info(f"  {i}. {failed_file}")
            logger.info("="*50)
        
        return {
            'total': len(image_files),
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'failed_files': failed_files,  # 新增失败文件列表
            'output_folder': str(output_path),
            'transparent_bg': self.transparent_bg,
            'overwrite_mode': self.overwrite_existing
        }