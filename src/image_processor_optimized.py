#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理器 - 性能优化版
负责图片加载、缩略图生成、EXIF信息提取等
"""

import os
import logging
import hashlib
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageOps, ExifTags
from PIL.ExifTags import TAGS
import rawpy
import numpy as np
from datetime import datetime
import warnings

# 抑制TIFF相关的警告
warnings.filterwarnings('ignore', category=UserWarning, module='PIL')
warnings.filterwarnings('ignore', message='.*TIFF.*')
warnings.filterwarnings('ignore', message='.*Old-style JPEG.*')
warnings.filterwarnings('ignore', message='.*Photometric tag.*')
warnings.filterwarnings('ignore', message='.*SamplesPerPixel.*')

class ImageProcessor:
    """图片处理器类 - 性能优化版"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp',
        '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef', '.srw',
        '.raf', '.3fr', '.fff', '.dcr', '.kdc', '.mdc', '.mos', '.mrw',
        '.nrw', '.ptx', '.r3d', '.rwl', '.rwz', '.x3f', '.bay', '.crw'
    }
    
    def __init__(self, cache_dir: str = 'cache'):
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        self._ensure_cache_dir()
        
        # 性能优化点1：添加内存缓存
        self._thumbnail_cache = {}
        self._size_cache = {}
        self._max_cache_entries = 500  # 最大缓存条目数
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS
    
    def _get_cache_path(self, file_path: str, size: int) -> str:
        """获取缓存文件路径"""
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        cache_name = f"{file_hash}_{size}.jpg"
        return os.path.join(self.cache_dir, cache_name)
    
    def _load_raw_image(self, file_path: str, fast_mode: bool = False) -> Optional[Image.Image]:
        """加载RAW格式图片 - 性能优化版"""
        # 临时抑制所有警告
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            try:
                # 首先尝试使用rawpy加载
                with rawpy.imread(file_path) as raw:
                    # 性能优化点2：快速模式使用更快的处理参数
                    if fast_mode:
                        # 快速模式：使用半尺寸和更快的算法
                        rgb = raw.postprocess(
                            use_camera_wb=True,
                            half_size=True,         # 使用半尺寸提高速度
                            no_auto_bright=True,    # 禁用自动亮度调整
                            output_color=rawpy.ColorSpace.sRGB,
                            gamma=(2.222, 4.5),
                            bright=1.0,
                            highlight_mode=rawpy.HighlightMode.Clip,
                            use_auto_wb=False,
                            output_bps=8,
                            demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD  # 更快的算法
                        )
                    else:
                        # 标准模式：使用更高质量的参数
                        rgb = raw.postprocess(
                            use_camera_wb=True,
                            half_size=False,
                            no_auto_bright=True,
                            output_color=rawpy.ColorSpace.sRGB,
                            gamma=(2.222, 4.5),
                            bright=1.0,
                            highlight_mode=rawpy.HighlightMode.Clip,
                            use_auto_wb=False,
                            output_bps=8
                        )
                    
                    # 转换为PIL图像
                    image = Image.fromarray(rgb)
                    
                    # 自动旋转（如果有EXIF信息）
                    try:
                        return ImageOps.exif_transpose(image)
                    except:
                        # 如果EXIF旋转失败，返回原图
                        return image
                        
            except Exception as e:
                self.logger.warning(f"rawpy加载RAW图片失败 {file_path}: {e}")
                
                # 如果rawpy失败，尝试使用PIL直接加载（某些RAW文件可能有嵌入的JPEG预览）
                try:
                    image = Image.open(file_path)
                    return ImageOps.exif_transpose(image)
                except Exception as e2:
                    self.logger.error(f"PIL加载RAW图片也失败 {file_path}: {e2}")
                    return None
    
    def _load_cr2_image(self, file_path: str, fast_mode: bool = False) -> Optional[Image.Image]:
        """专门处理CR2格式图片 - 性能优化版"""
        # 临时抑制所有警告
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            try:
                # 性能优化点3：快速模式优先使用嵌入缩略图
                if fast_mode:
                    try:
                        with rawpy.imread(file_path) as raw:
                            # 首先尝试提取嵌入的缩略图
                            try:
                                thumb = raw.extract_thumb()
                                if thumb.format == rawpy.ThumbFormat.JPEG:
                                    # 从JPEG数据创建PIL图像
                                    from io import BytesIO
                                    image = Image.open(BytesIO(thumb.data))
                                    return ImageOps.exif_transpose(image)
                            except:
                                pass
                            
                            # 如果没有缩略图，使用快速处理
                            rgb = raw.postprocess(
                                use_camera_wb=True,
                                half_size=True,          # 使用半尺寸提高速度
                                no_auto_bright=True,     # 禁用自动亮度
                                output_color=rawpy.ColorSpace.sRGB,
                                gamma=(2.222, 4.5),
                                bright=1.0,
                                highlight_mode=rawpy.HighlightMode.Clip,
                                use_auto_wb=False,
                                output_bps=8,
                                user_flip=0,              # 禁用自动翻转，避免TIFF问题
                                demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD  # 更快的算法
                            )
                            image = Image.fromarray(rgb)
                            return image
                    except Exception as e:
                        # 尝试使用PIL直接读取嵌入的预览图
                        try:
                            image = Image.open(file_path)
                            # 尝试获取最大的可用图像
                            if hasattr(image, 'n_frames'):
                                # 如果有多帧，选择最后一帧（通常是最大的预览图）
                                image.seek(image.n_frames - 1)
                            return ImageOps.exif_transpose(image)
                        except:
                            pass
                
                # 标准模式或快速模式失败后的处理
                try:
                    with rawpy.imread(file_path) as raw:
                        # 首先尝试提取嵌入的缩略图
                        try:
                            thumb = raw.extract_thumb()
                            if thumb.format == rawpy.ThumbFormat.JPEG:
                                # 从JPEG数据创建PIL图像
                                from io import BytesIO
                                image = Image.open(BytesIO(thumb.data))
                                return ImageOps.exif_transpose(image)
                        except:
                            pass
                        
                        # 如果没有缩略图，使用标准处理
                        rgb = raw.postprocess(
                            use_camera_wb=True,
                            half_size=False,
                            no_auto_bright=True,
                            output_color=rawpy.ColorSpace.sRGB,
                            gamma=(2.222, 4.5),
                            bright=1.0,
                            highlight_mode=rawpy.HighlightMode.Clip,
                            use_auto_wb=False,
                            output_bps=8,
                            user_flip=0
                        )
                        image = Image.fromarray(rgb)
                        return image
                        
                except Exception as e:
                    self.logger.warning(f"rawpy处理CR2失败 {file_path}: {e}")
                    
                    # 尝试使用PIL直接读取嵌入的预览图
                    try:
                        # CR2文件通常包含JPEG预览图
                        image = Image.open(file_path)
                        # 尝试获取最大的可用图像
                        if hasattr(image, 'n_frames'):
                            # 如果有多帧，选择最后一帧（通常是最大的预览图）
                            image.seek(image.n_frames - 1)
                        return ImageOps.exif_transpose(image)
                    except Exception as e2:
                        self.logger.warning(f"PIL读取CR2预览图失败 {file_path}: {e2}")
                        
                        # 使用更宽松的rawpy参数
                        try:
                            with rawpy.imread(file_path) as raw:
                                rgb = raw.postprocess(
                                    use_camera_wb=False,     # 不使用相机白平衡
                                    half_size=True,          # 使用半尺寸
                                    no_auto_bright=True,     # 禁用自动亮度
                                    output_color=rawpy.ColorSpace.sRGB,
                                    bright=1.0,
                                    use_auto_wb=True,        # 使用自动白平衡
                                    output_bps=8,
                                    user_flip=0,
                                    demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD  # 使用更简单的算法
                                )
                                image = Image.fromarray(rgb)
                                return image
                        except Exception as e3:
                            self.logger.error(f"所有CR2处理方法都失败 {file_path}: {e3}")
                            return None
                            
            except Exception as e:
                self.logger.error(f"CR2图片处理完全失败 {file_path}: {e}")
                return None
    
    def _load_standard_image(self, file_path: str) -> Optional[Image.Image]:
        """加载标准格式图片"""
        try:
            image = Image.open(file_path)
            # 自动旋转图片
            image = ImageOps.exif_transpose(image)
            return image
        except Exception as e:
            self.logger.error(f"加载图片失败 {file_path}: {e}")
            return None
    
    def load_image(self, file_path: str, fast_mode: bool = False) -> Optional[Image.Image]:
        """加载图片 - 性能优化版"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # RAW格式
        if ext in {'.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef', '.srw',
                   '.raf', '.3fr', '.fff', '.dcr', '.kdc', '.mdc', '.mos', '.mrw',
                   '.nrw', '.ptx', '.r3d', '.rwl', '.rwz', '.x3f', '.bay', '.crw'}:
            # 特殊处理CR2文件
            if ext == '.cr2':
                return self._load_cr2_image(file_path, fast_mode)
            else:
                return self._load_raw_image(file_path, fast_mode)
        else:
            return self._load_standard_image(file_path)
    
    def generate_thumbnail(self, file_path: str, size: int = 200, fast_mode: bool = False) -> Optional[str]:
        """生成缩略图 - 性能优化版"""
        # 性能优化点4：检查内存缓存
        cache_key = f"{file_path}_{size}_{fast_mode}"
        if cache_key in self._thumbnail_cache:
            return self._thumbnail_cache[cache_key]
        
        cache_path = self._get_cache_path(file_path, size)
        
        # 检查磁盘缓存是否存在且有效
        if os.path.exists(cache_path):
            try:
                cache_time = os.path.getmtime(cache_path)
                file_time = os.path.getmtime(file_path)
                if cache_time >= file_time:
                    # 添加到内存缓存
                    self._add_to_cache(cache_key, cache_path)
                    return cache_path
            except OSError:
                # 如果无法获取文件时间，删除缓存重新生成
                try:
                    os.remove(cache_path)
                except:
                    pass
        
        # 生成新的缩略图
        image = self.load_image(file_path, fast_mode)
        if image is None:
            return None
        
        try:
            # 获取原始尺寸
            original_width, original_height = image.size
            
            # 计算缩略图尺寸，保持宽高比
            if original_width > original_height:
                new_width = size
                new_height = int((size * original_height) / original_width)
            else:
                new_height = size
                new_width = int((size * original_width) / original_height)
            
            # 性能优化点5：根据模式选择重采样算法
            if fast_mode:
                # 快速模式使用更快的重采样算法
                resampling_method = Image.Resampling.BILINEAR
                quality = 80  # 降低质量以提高速度
            else:
                # 标准模式使用高质量重采样
                resampling_method = Image.Resampling.LANCZOS
                quality = 90
            
            # 调整图片大小
            image = image.resize((new_width, new_height), resampling_method)
            
            # 转换为RGB模式（如果需要）
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                image = background
            elif image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # 保存缩略图，使用更好的压缩设置
            image.save(cache_path, 'JPEG', quality=quality, optimize=True, progressive=True)
            
            # 添加到内存缓存
            self._add_to_cache(cache_key, cache_path)
            
            # 缓存图片尺寸信息
            self._size_cache[file_path] = (original_width, original_height)
            
            # 清理内存
            image.close()
            del image
            
            return cache_path
            
        except Exception as e:
            self.logger.error(f"生成缩略图失败 {file_path}: {e}")
            return None
    
    def _add_to_cache(self, key: str, value: str):
        """添加到内存缓存，并管理缓存大小"""
        # 如果缓存已满，移除最早添加的项
        if len(self._thumbnail_cache) >= self._max_cache_entries:
            # 简单的FIFO策略
            oldest_key = next(iter(self._thumbnail_cache))
            del self._thumbnail_cache[oldest_key]
        
        # 添加新项
        self._thumbnail_cache[key] = value
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """获取图片信息 - 性能优化版"""
        info = {
            'file_name': os.path.basename(file_path),
            'file_size': 0,
            'dimensions': (0, 0),
            'creation_time': None,
            'taken_time': None,
            'camera_info': None
        }
        
        try:
            # 文件基本信息
            stat = os.stat(file_path)
            info['file_size'] = stat.st_size
            info['creation_time'] = datetime.fromtimestamp(stat.st_ctime)
            
            # 性能优化点6：使用缓存的尺寸信息
            if file_path in self._size_cache:
                info['dimensions'] = self._size_cache[file_path]
                return info
            
            # 图片尺寸和EXIF信息
            image = self.load_image(file_path, fast_mode=True)  # 使用快速模式
            if image:
                info['dimensions'] = image.size
                
                # 缓存尺寸信息
                self._size_cache[file_path] = image.size
                
                # 提取EXIF信息
                if hasattr(image, '_getexif') and image._getexif():
                    exif = image._getexif()
                    
                    # 拍摄时间
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTime':
                            try:
                                info['taken_time'] = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            except:
                                pass
                        elif tag in ['Make', 'Model']:
                            if not info['camera_info']:
                                info['camera_info'] = {}
                            info['camera_info'][tag] = value
                
        except Exception as e:
            self.logger.error(f"获取图片信息失败 {file_path}: {e}")
        
        return info
    
    def get_optimal_size(self, image_path: str, container_size: Tuple[int, int]) -> Tuple[int, int]:
        """获取图片在容器中的最佳显示尺寸 - 性能优化版"""
        try:
            # 性能优化点7：使用缓存的尺寸信息
            if image_path in self._size_cache:
                img_width, img_height = self._size_cache[image_path]
            else:
                image = self.load_image(image_path, fast_mode=True)  # 使用快速模式
                if not image:
                    return container_size
                
                img_width, img_height = image.size
                # 缓存尺寸信息
                self._size_cache[image_path] = (img_width, img_height)
            
            container_width, container_height = container_size
            
            # 计算缩放比例
            scale_w = container_width / img_width
            scale_h = container_height / img_height
            scale = min(scale_w, scale_h)
            
            # 计算最终尺寸
            final_width = int(img_width * scale)
            final_height = int(img_height * scale)
            
            return (final_width, final_height)
            
        except Exception as e:
            self.logger.error(f"计算最佳尺寸失败 {image_path}: {e}")
            return container_size
    
    def clear_cache(self):
        """清除内存缓存"""
        self._thumbnail_cache.clear()
        self._size_cache.clear()