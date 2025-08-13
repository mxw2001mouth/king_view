#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的瀑布流布局组件 v4.3 - 性能优化版
在交互优化版基础上，专注于提升大量图片（500+）加载时的性能
"""

import os
import sys
import logging
import subprocess
import time
from typing import List, Optional, Dict, Tuple
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QScrollArea  # 显式导入QScrollArea以确保类型检查正常工作

# 导入文件工具模块
from file_utils import move_to_recycle_bin

class OptimizedImageThumbnail(QLabel):
    """优化的图片缩略图组件 v4.3 - 性能优化版"""
    
    clicked = pyqtSignal(str, int)
    load_completed = pyqtSignal()
    delete_requested = pyqtSignal(str)  # 删除请求信号
    
    def __init__(self, image_path: str, index: int, image_processor, config_manager):
        super().__init__()
        self.image_path = image_path
        self.index = index
        self.image_processor = image_processor
        self.config_manager = config_manager
        self.pixmap = None
        self.loading = False
        self.worker = None
        self.loaded = False
        
        # 图片尺寸缓存 - 性能优化点1：缓存图片尺寸信息，避免重复计算
        self.image_size = None
        self.aspect_ratio = None
        
        # 右键双击相关
        self.right_click_timer = QTimer()
        self.right_click_timer.setSingleShot(True)
        self.right_click_timer.timeout.connect(self.handle_right_double_click)
        self.right_click_count = 0
        
        self.setCursor(Qt.PointingHandCursor)
        self.setScaledContents(False)
        
        # 设置工具提示显示文件名
        filename = os.path.basename(self.image_path)
        self.setToolTip(filename)
        
        # 设置初始状态
        self.setText("等待加载...<br><br><span style='color: #cccccc; font-size: 12px;font-weight: 400; font-family: 'Microsoft YaHei';'>ℒℴѵℯ时光微醉⁰ɞ</span>")
        self.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #e9ecef;
                font-size: 14px;
                border-radius: 6px;
                color: #999999;
                font-weight: 700;
                letter-spacing: 3px;
                qproperty-alignment: AlignCenter;
            }
            QLabel:hover {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
    
    def apply_appearance_settings(self):
        """应用外观设置"""
        try:
            config = self.config_manager.get_config()
            
            # 基础样式 - 与optimized_waterfall_widget_v4_3.py保持一致
            base_style = """
                QLabel {
                    background-color: white;
                    padding: 4px;
                }
            """
            
            # 悬停样式
            hover_style = ""
            if config.get('hover_enabled', True):
                hover_color = config.get('hover_color', '#e3f2fd')
                hover_border_color = config.get('hover_border_color', '#2196f3')
                hover_style = f"""
                QLabel:hover {{
                    background-color: {hover_color};
                }}
                """
            
            # 边框设置 - 默认不添加边框，除非明确指定
            if config.get('image_border', False):
                border_width = config.get('border_width', 1)  # 减小默认边框宽度
                border_color = config.get('border_color', '#e9ecef')
                base_style = base_style.replace(
                    "background-color: white;",
                    f"background-color: white; border: {border_width}px solid {border_color};"
                )
                if hover_style and config.get('hover_enabled', True):
                    hover_border_color = config.get('hover_border_color', '#2196f3')
                    hover_style = hover_style.replace(
                        f"background-color: {config.get('hover_color', '#e3f2fd')};",
                        f"background-color: {config.get('hover_color', '#e3f2fd')}; border-color: {hover_border_color};"
                    )
            else:
                base_style = base_style.replace(
                    "background-color: white;",
                    "background-color: white; border: none;"
                )
            
            # 圆角设置
            if config.get('image_rounded', True):
                rounded_size = config.get('rounded_size', 4)  # 减小默认圆角大小
                if "border: none;" in base_style:
                    base_style = base_style.replace(
                        "border: none;",
                        f"border: none; border-radius: {rounded_size}px;"
                    )
                else:
                    # 为有边框的样式添加圆角
                    border_width = config.get('border_width', 1)
                    border_color = config.get('border_color', '#e9ecef')
                    base_style = base_style.replace(
                        f"border: {border_width}px solid {border_color};",
                        f"border: {border_width}px solid {border_color}; border-radius: {rounded_size}px;"
                    )
                
                # 为悬停样式也添加圆角
                if hover_style and "border-color:" in hover_style:
                    hover_border_color = config.get('hover_border_color', '#2196f3')
                    hover_style = hover_style.replace(
                        f"border-color: {hover_border_color};",
                        f"border-color: {hover_border_color}; border-radius: {rounded_size}px;"
                    )
            
            # 阴影设置 - 使用QGraphicsDropShadowEffect
            if config.get('image_shadow', False):
                shadow_size = config.get('shadow_size', 5)
                shadow_color = config.get('shadow_color', '#808080')
                
                # 创建阴影效果
                from PyQt5.QtWidgets import QGraphicsDropShadowEffect
                from PyQt5.QtGui import QColor
                
                shadow_effect = QGraphicsDropShadowEffect()
                shadow_effect.setBlurRadius(shadow_size)
                shadow_effect.setOffset(2, 2)  # 阴影偏移
                shadow_effect.setColor(QColor(shadow_color))
                
                self.setGraphicsEffect(shadow_effect)
            else:
                # 移除阴影效果
                self.setGraphicsEffect(None)
            
            # 应用样式
            final_style = base_style + hover_style
            self.setStyleSheet(final_style)
            
        except Exception as e:
            logging.error(f"应用外观设置失败: {e}")
            # 使用默认样式 - 修复边框和响应问题
            self.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 2px;
                    margin: 2px;
                }
                QLabel:hover {
                    background-color: #e3f2fd;
                }
            """)
            # 移除阴影效果
            self.setGraphicsEffect(None)
    
    def start_loading(self):
        """开始加载缩略图"""
        if self.loading:
            return
        
        if self.loaded and self.pixmap and not hasattr(self, 'was_cleaned'):
            return
        
        config = self.config_manager.get_config()
        thumbnail_size = config.get('thumbnail_size', 200)
        
        # 简单缓存检查
        cache_path = self.image_processor._get_cache_path(self.image_path, thumbnail_size)
        if os.path.exists(cache_path):
            self.set_thumbnail_from_cache(cache_path)
            return
        
        self.loading = True
        self.setText("照片正在加载中...<br><br><span style='color: #cccccc; font-size: 12px;font-weight: 400; font-family: 'Microsoft YaHei';'>ℒℴѵℯ时光微醉⁰ɞ</span>")
        self.setStyleSheet("font-size: 14px; color: #999999; font-weight: 700; letter-spacing: 3px; qproperty-alignment: AlignCenter;")
        
        # 创建工作线程
        self.worker = OptimizedThumbnailWorker(
            self.image_path, 
            thumbnail_size, 
            self.image_processor
        )
        self.worker.thumbnail_ready.connect(self.set_thumbnail)
        self.worker.error_occurred.connect(self.on_load_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
    
    def set_thumbnail_from_cache(self, thumbnail_path: str):
        """从缓存设置缩略图"""
        if thumbnail_path and os.path.exists(thumbnail_path):
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                self.pixmap = pixmap
                self.loading = False
                self.loaded = True
                self.setText("")
                
                if hasattr(self, 'was_cleaned'):
                    delattr(self, 'was_cleaned')
                
                # 性能优化点2：缓存图片尺寸和比例
                self.cache_image_size(pixmap)
                
                self.original_loaded = True
                self.update_display()
                # 重要：发射加载完成信号
                self.load_completed.emit()
    
    def set_thumbnail(self, thumbnail_path: str):
        """设置缩略图"""
        if thumbnail_path and os.path.exists(thumbnail_path):
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                self.pixmap = pixmap
                self.loading = False
                self.loaded = True
                self.setText("")
                
                if hasattr(self, 'was_cleaned'):
                    delattr(self, 'was_cleaned')
                
                # 性能优化点2：缓存图片尺寸和比例
                self.cache_image_size(pixmap)
                
                self.original_loaded = True
                self.update_display()
                self.load_completed.emit()
    
    def cache_image_size(self, pixmap):
        """缓存图片尺寸和比例 - 性能优化"""
        if pixmap and not pixmap.isNull():
            self.image_size = (pixmap.width(), pixmap.height())
            if pixmap.width() > 0:
                self.aspect_ratio = pixmap.height() / pixmap.width()
                # 限制比例范围，避免极端情况
                self.aspect_ratio = max(0.6, min(self.aspect_ratio, 1.8))
    
    def on_load_error(self, error_msg: str):
        """处理加载错误"""
        self.loading = False
        self.loaded = True
        self.setText("加载失败")
        self.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                padding: 4px;
                text-align: center;
            }
        """)
        self.load_completed.emit()
    
    def on_worker_finished(self):
        """工作线程完成"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def update_display(self):
        """更新缩略图显示 - 优化图片质量和边距"""
        if not self.pixmap or self.loading:
            return
        
        size = self.size()
        if size.width() <= 0 or size.height() <= 0:
            return
        
        # 获取当前视图模式
        view_mode = 'waterfall'
        try:
            parent_widget = self.parent()
            while parent_widget:
                if hasattr(parent_widget, 'layout') and hasattr(parent_widget.layout, 'view_mode'):
                    view_mode = parent_widget.layout.view_mode
                    break
                parent_widget = parent_widget.parent()
        except:
            pass
        
        # 根据视图模式设置边距 - 优化边距设置
        if view_mode == 'grid':
            margin_horizontal = 5
            margin_vertical = 5
        else:
            margin_horizontal = 5
            margin_vertical = 5
        
        # 应用外观设置
        self.apply_appearance_settings()
        
        # 计算图片的最大允许尺寸
        max_width = size.width() - (margin_horizontal * 2)
        max_height = size.height() - (margin_vertical * 2)
        
        if max_width > 0 and max_height > 0:
            # 始终使用高质量缩放以解决模糊问题
            transform_method = Qt.SmoothTransformation
            
            # 缩放图片
            scaled_pixmap = self.pixmap.scaled(
                max_width, max_height,
                Qt.KeepAspectRatio,
                transform_method
            )
            
            # 创建结果画布
            result_pixmap = QPixmap(size.width(), size.height())
            result_pixmap.fill(Qt.transparent)
            
            painter = QPainter(result_pixmap)
            
            # 计算图片位置（居中）
            x = margin_horizontal + (max_width - scaled_pixmap.width()) // 2
            y = margin_vertical + (max_height - scaled_pixmap.height()) // 2
            
            # 边界检查
            x = max(0, min(x, size.width() - scaled_pixmap.width()))
            y = max(0, min(y, size.height() - scaled_pixmap.height()))
            
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
            
            self.setPixmap(result_pixmap)
    
    def resizeEvent(self, event):
        """大小改变事件"""
        super().resizeEvent(event)
        if self.loaded and self.pixmap:
            self.update_display()
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            if self.loaded and self.pixmap:
                self.clicked.emit(self.image_path, self.index)
        elif event.button() == Qt.RightButton:
            # 处理右键双击
            self.right_click_count += 1
            if self.right_click_count == 1:
                self.right_click_timer.start(300)  # 300ms内检测双击
            elif self.right_click_count == 2:
                self.right_click_timer.stop()
                self.right_click_count = 0
                self.open_file_location()
    
    def handle_right_double_click(self):
        """处理右键双击超时"""
        self.right_click_count = 0
    
    def open_file_location(self):
        """打开文件所在目录并定位到文件"""
        try:
            if os.path.exists(self.image_path):
                # 确保使用绝对路径
                abs_path = os.path.abspath(self.image_path)
                logging.info(f"尝试打开文件位置: {abs_path}")
                
                if os.name == 'nt':  # Windows
                    # Windows: 使用explorer /select命令
                    subprocess.run(['explorer', '/select,', abs_path], check=False)
                elif os.name == 'posix':  # macOS/Linux
                    if sys.platform == 'darwin':  # macOS
                        subprocess.run(['open', '-R', abs_path], check=False)
                    else:  # Linux
                        # Linux: 尝试多种文件管理器
                        dir_path = os.path.dirname(abs_path)
                        try:
                            # 尝试使用nautilus (GNOME)
                            subprocess.run(['nautilus', '--select', abs_path], check=True)
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            try:
                                # 尝试使用dolphin (KDE)
                                subprocess.run(['dolphin', '--select', abs_path], check=True)
                            except (subprocess.CalledProcessError, FileNotFoundError):
                                try:
                                    # 尝试使用thunar (XFCE)
                                    subprocess.run(['thunar', abs_path], check=True)
                                except (subprocess.CalledProcessError, FileNotFoundError):
                                    # 最后使用xdg-open打开目录
                                    subprocess.run(['xdg-open', dir_path], check=False)
            else:
                logging.warning(f"文件不存在: {self.image_path}")
                
        except Exception as e:
            logging.error(f"打开文件位置失败: {e}")
            # 尝试至少打开目录
            try:
                dir_path = os.path.dirname(os.path.abspath(self.image_path))
                if os.name == 'nt':
                    subprocess.run(['explorer', dir_path], check=False)
                else:
                    subprocess.run(['xdg-open', dir_path], check=False)
            except:
                pass
    
    def keyPressEvent(self, event):
        """键盘事件 - 处理DELETE键"""
        if event.key() == Qt.Key_Delete:
            self.delete_image()
        else:
            super().keyPressEvent(event)
    
    def delete_image(self):
        """删除图片文件 - 移动到回收站"""
        try:
            if os.path.exists(self.image_path):
                # 尝试移动到回收站
                if move_to_recycle_bin(self.image_path):
                    logging.info(f"已将图片移动到回收站: {self.image_path}")
                else:
                    # 如果移动到回收站失败，询问用户是否直接删除
                    reply = QMessageBox.question(
                        None, 
                        "删除确认", 
                        f"无法将图片移动到回收站。\n是否直接删除文件？\n\n{os.path.basename(self.image_path)}",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        os.remove(self.image_path)
                        logging.info(f"已直接删除图片: {self.image_path}")
                    else:
                        return  # 用户取消删除
                
                # 发射删除信号
                self.delete_requested.emit(self.image_path)
                
                # 隐藏缩略图
                self.hide()
                
        except Exception as e:
            logging.error(f"删除图片失败: {e}")
            QMessageBox.warning(None, "删除失败", f"无法删除图片:\n{str(e)}")
    
    def cleanup(self):
        """清理资源"""
        if self.worker:
            self.worker.terminate()
            self.worker.wait()
            self.worker.deleteLater()
            self.worker = None

class OptimizedThumbnailWorker(QThread):
    """优化的缩略图加载工作线程"""
    
    thumbnail_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, image_path: str, size: int, image_processor):
        super().__init__()
        self.image_path = image_path
        self.size = size
        self.image_processor = image_processor
        self._stop_requested = False
    
    def run(self):
        """运行线程"""
        try:
            if self._stop_requested:
                return
            
            thumbnail_path = self.image_processor.generate_thumbnail(
                self.image_path, self.size, fast_mode=True  # 性能优化点4：使用快速模式生成缩略图
            )
            
            if self._stop_requested:
                return
            
            if thumbnail_path:
                self.thumbnail_ready.emit(thumbnail_path)
            else:
                self.error_occurred.emit("无法生成缩略图")
        except Exception as e:
            if not self._stop_requested:
                error_msg = f"生成缩略图失败: {str(e)}"
                logging.error(error_msg)
                self.error_occurred.emit(error_msg)
    
    def stop(self):
        """停止线程"""
        self._stop_requested = True

class OptimizedWaterfallLayout(QLayout):
    """优化的瀑布流布局 - 性能优化版"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.column_count = 0
        self.spacing_value = 10 #默认列间距和行间距
        self.view_mode = 'waterfall'
        
        # 性能优化点5：缓存布局计算结果
        self._cached_item_positions = {}  # 缓存每个项目的位置
        self._cached_item_heights = {}    # 缓存每个项目的高度
        self._cached_layout_width = 0     # 缓存布局宽度
        self._cached_layout_height = 0    # 缓存布局高度
        self._layout_dirty = True         # 布局是否需要重新计算
    
    def reset(self):
        """完全重置布局状态和缓存"""
        self._cached_item_positions.clear()
        self._cached_item_heights.clear()
        self._cached_layout_width = 0
        self._cached_layout_height = 0
        self._layout_dirty = True
        self.invalidate()

    def addItem(self, item):
        """添加项目"""
        self.items.append(item)
        self._layout_dirty = True
    
    def count(self):
        """项目数量"""
        return len(self.items)
    
    def itemAt(self, index):
        """获取指定索引的项目"""
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def takeAt(self, index):
        """移除指定索引的项目"""
        if 0 <= index < len(self.items):
            item = self.items.pop(index)
            self._layout_dirty = True
            # 清除被移除项目的缓存
            if id(item) in self._cached_item_positions:
                del self._cached_item_positions[id(item)]
            if id(item) in self._cached_item_heights:
                del self._cached_item_heights[id(item)]
            return item
        return None
    
    def setGeometry(self, rect):
        """设置几何形状"""
        super().setGeometry(rect)
        
        # 检查布局宽度是否变化，如果变化则标记布局需要重新计算
        if self._cached_layout_width != rect.width():
            self._layout_dirty = True
            self._cached_layout_width = rect.width()
        
        self.do_layout(rect)
    
    def sizeHint(self):
        """大小提示"""
        return QSize(600, 400)
    
    def minimumSize(self):
        """最小大小"""
        return QSize(300, 200)
    
    def invalidate(self):
        """使布局无效，强制重新计算"""
        self._layout_dirty = True
        super().invalidate()
    
    def calculate_item_height(self, widget, column_width):
        """计算项目高度 - 性能优化版"""
        # 检查缓存
        widget_id = id(widget)
        if widget_id in self._cached_item_heights:
            return self._cached_item_heights[widget_id]
        
        # 设置固定的padding为5像素，不随窗口大小变化
        padding = 5  # 图片与容器边框之间的固定间距，保持不变
        
        if self.view_mode == 'grid':
            height = column_width + padding
            self._cached_item_heights[widget_id] = height
            return height
        
        # 瀑布流模式：优先使用缓存的图片比例
        if hasattr(widget, 'aspect_ratio') and widget.aspect_ratio is not None:
            calculated_height = int(column_width * widget.aspect_ratio) + padding
            self._cached_item_heights[widget_id] = calculated_height
            return calculated_height
        
        # 如果已经加载了缩略图，使用缩略图比例
        if hasattr(widget, 'pixmap') and widget.pixmap and not widget.pixmap.isNull():
            original_width = widget.pixmap.width()
            original_height = widget.pixmap.height()
            if original_width > 0:
                aspect_ratio = original_height / original_width
                # 允许更大范围的宽高比，以保持图片原始比例
                aspect_ratio = max(0.4, min(aspect_ratio, 2.5))
                calculated_height = int(column_width * aspect_ratio) + padding
                self._cached_item_heights[widget_id] = calculated_height
                return calculated_height
        
        # 尝试从图片文件获取比例
        if hasattr(widget, 'image_path') and widget.image_path:
            try:
                from PIL import Image
                with Image.open(widget.image_path) as img:
                    width, height = img.size
                    if width > 0:
                        aspect_ratio = height / width
                        # 允许更大范围的宽高比，以保持图片原始比例
                        aspect_ratio = max(0.4, min(aspect_ratio, 2.5))
                        calculated_height = int(column_width * aspect_ratio) + padding
                        self._cached_item_heights[widget_id] = calculated_height
                        return calculated_height
            except Exception:
                pass
        
        # 默认使用黄金比例
        default_height = int(column_width * 1.2) + padding
        self._cached_item_heights[widget_id] = default_height
        return default_height
    
    def do_layout(self, rect):
        """执行布局 - 性能优化版"""
        if not self.items:
            return
        
        # 如果布局没有变化且所有项目都有缓存的位置，直接应用缓存的位置
        if not self._layout_dirty and all(id(item) in self._cached_item_positions for item in self.items):
            for item in self.items:
                widget = item.widget()
                if widget and id(item) in self._cached_item_positions:
                    pos = self._cached_item_positions[id(item)]
                    widget.setGeometry(pos[0], pos[1], pos[2], pos[3])
            return
        
        # 使用一致的边距，减少20像素以避免贴近窗口边缘
        available_width = rect.width() - 20
        
        # 从配置获取列数设置
        try:
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, 'config_manager'):
                parent_widget = parent_widget.parent()
            
            if parent_widget and hasattr(parent_widget, 'config_manager'):
                config_data = parent_widget.config_manager.get_config()
                waterfall_columns = config_data.get('waterfall_columns', 4)
                grid_columns = config_data.get('grid_columns', 6)
            else:
                waterfall_columns = 4
                grid_columns = 6
        except:
            waterfall_columns = 4
            grid_columns = 6
        
        # 根据视图模式计算列数
        if self.view_mode == 'waterfall':
            columns = waterfall_columns
            min_column_width = 150
        else:  # grid
            columns = grid_columns
            min_column_width = 100
        
        # 确保列数合理
        max_possible_columns = available_width // (min_column_width + self.spacing_value)
        columns = min(columns, max(1, max_possible_columns))
        
        # 计算实际列宽 - 与optimized_waterfall_widget_v4_3.py保持一致
        total_spacing = (columns + 1) * self.spacing_value  # 包括左右边距和列间距
        column_width = (available_width - total_spacing) // columns
        
        # 初始化列高度 - 与optimized_waterfall_widget_v4_3.py保持一致
        column_heights = [self.spacing_value] * columns
        
        # 布局每个项目
        for item in self.items:
            widget = item.widget()
            if not widget:
                continue
            
            # 找最短列 - 真正的瀑布流布局核心
            column_index = column_heights.index(min(column_heights))
            
            # 计算位置 - 确保间距一致
            # 计算位置 - 与optimized_waterfall_widget_v4_3.py保持一致
            x = rect.x() + self.spacing_value + column_index * (column_width + self.spacing_value)
            y = rect.y() + column_heights[column_index]
            
            # 计算高度 - 根据图片实际比例
            height = self.calculate_item_height(widget, column_width)
            
            # 设置几何形状
            widget.setGeometry(x, y, column_width, height)
            
            # 缓存位置
            self._cached_item_positions[id(item)] = (x, y, column_width, height)
            
            # 更新列高度 - 与optimized_waterfall_widget_v4_3.py保持一致
            column_heights[column_index] += height + self.spacing_value
        
        # 缓存布局高度
        self._cached_layout_height = max(column_heights) if column_heights else self.spacing_value
        
        # 布局已更新，标记为干净
        self._layout_dirty = False
    
    def heightForWidth(self, width):
        """根据宽度计算高度 - 性能优化版"""
        # 如果宽度没有变化且布局没有变化，直接返回缓存的高度
        if width == self._cached_layout_width and not self._layout_dirty and self._cached_layout_height > 0:
            return self._cached_layout_height
        
        if not self.items:
            return 100
        
        available_width = width - 20
        
        if self.view_mode == 'waterfall':
            min_column_width = 180
            columns = max(2, min(available_width // (min_column_width + self.spacing_value), 5))
        else:  # grid
            min_column_width = 120
            columns = max(4, min(available_width // (min_column_width + self.spacing_value), 8))
        
        # 计算列宽 - 使用与do_layout一致的计算方法
        left_right_margin = self.spacing_value
        total_spacing = (columns - 1) * self.spacing_value
        usable_width = available_width - (2 * left_right_margin)
        column_width = (usable_width - total_spacing) // columns
        
        # 模拟布局计算实际高度
        column_heights = [self.spacing_value] * columns
        
        for i in range(len(self.items)):
            widget = self.items[i].widget()
            if widget:
                item_height = self.calculate_item_height(widget, column_width)
            else:
                item_height = int(column_width * 1.2) + 20
            
            column_index = column_heights.index(min(column_heights))
            column_heights[column_index] += item_height + self.spacing_value
        
        max_height = max(column_heights) if column_heights else self.spacing_value
        
        # 缓存计算结果
        if width == self._cached_layout_width:
            self._cached_layout_height = max_height + self.spacing_value
        
        return max_height + self.spacing_value

class OptimizedWaterfallWidget(QWidget):
    """优化的瀑布流组件 v4.3 - 性能优化版"""
    
    image_clicked = pyqtSignal(str, int)
    image_deleted = pyqtSignal(str)  # 图片删除信号
    image_loaded = pyqtSignal()  # 图片加载完成信号
    
    def __init__(self, image_processor, config_manager, parent=None):
        super().__init__(parent)
        self.image_processor = image_processor
        self.config_manager = config_manager
        self.image_files = []
        self.thumbnails = []
        self.current_view_mode = 'waterfall'
        
        # 恢复原始参数
        self.batch_size = 30
        self.loaded_count = 0
        self.visible_count = 0
        self.max_concurrent_workers = 6
        self.active_workers = 0
        self.pending_loads = []
        self.is_loading_more = False
        
        # 定时器
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.process_next_batch)
        self.loading_timer.setSingleShot(True)
        
        # 恢复原始参数
        self.scroll_debounce_timer = QTimer()
        self.scroll_debounce_timer.timeout.connect(self.handle_scroll_load)
        self.scroll_debounce_timer.setSingleShot(True)
        
        self.last_visible_range = (0, 0)
        
        # 智能内存管理
        self.visible_range = (0, 0)
        self.memory_cleanup_timer = QTimer()
        self.memory_cleanup_timer.timeout.connect(self.cleanup_invisible_images)
        self.memory_cleanup_timer.start(60000)  # 恢复原始值
        
        # 性能优化点9：缓存图片尺寸信息
        self.image_size_cache = {}
        
        # 性能优化点10：虚拟滚动相关
        self.recycled_thumbnails = []  # 回收的缩略图容器
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.layout = OptimizedWaterfallLayout()
        self.setLayout(self.layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
        """)
        
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.StrongFocus)
    
    def set_images(self, image_files: List[str]):
        """设置图片列表"""
        self.clear_thumbnails()
        
        self.image_files = image_files
        self.loaded_count = 0
        self.visible_count = 0
        self.active_workers = 0
        self.pending_loads.clear()
        self.is_loading_more = False
        
        if not self.image_files:
            return
        
        initial_create_count = min(100, len(self.image_files))
        self.create_thumbnail_containers(0, initial_create_count)
        self.start_lazy_loading()
    
    def get_recycled_thumbnail(self, image_path: str, index: int):
        """从回收池获取缩略图容器 - 性能优化"""
        if self.recycled_thumbnails:
            thumbnail = self.recycled_thumbnails.pop()
            thumbnail.image_path = image_path
            thumbnail.index = index
            thumbnail.loaded = False
            thumbnail.loading = False
            thumbnail.pixmap = None
            thumbnail.setText("等待加载...<br><br><span style='color: #cccccc; font-size: 12px;font-weight: 400; font-family: 'Microsoft YaHei';'>ℒℴѵℯ时光微醉⁰ɞ</span>")
            thumbnail.setToolTip(os.path.basename(image_path))
            return thumbnail
        return None
    
    def create_thumbnail_containers(self, start_index, end_index):
        """创建缩略图容器 - 性能优化版"""
        for i in range(start_index, end_index):
            if i >= len(self.image_files):
                break
                
            image_path = self.image_files[i]
            
            # 性能优化点12：重用缩略图容器
            thumbnail = self.get_recycled_thumbnail(image_path, i)
            
            if thumbnail is None:
                thumbnail = OptimizedImageThumbnail(
                    image_path, i, 
                    self.image_processor, 
                    self.config_manager
                )
                # 连接到处理函数，动态计算索引
                thumbnail.clicked.connect(self.on_thumbnail_clicked)
                thumbnail.load_completed.connect(self.on_thumbnail_loaded)
                thumbnail.delete_requested.connect(self.on_image_delete_requested)
            
            self.thumbnails.append(thumbnail)
            self.layout.addWidget(thumbnail)
        
        self.loaded_count = min(end_index, len(self.image_files))
        self.update_widget_size()
    
    def on_thumbnail_clicked(self, image_path: str, thumbnail_index: int):
        """处理缩略图点击 - 动态计算正确的索引"""
        try:
            # 根据图片路径在当前图片列表中查找正确的索引
            correct_index = -1
            for i, file_path in enumerate(self.image_files):
                if file_path == image_path:
                    correct_index = i
                    break
            
            if correct_index >= 0:
                # 发射正确的索引
                self.image_clicked.emit(image_path, correct_index)
            else:
                logging.warning(f"无法找到图片在列表中的索引: {image_path}")
                
        except Exception as e:
            logging.error(f"处理缩略图点击失败: {e}")
    
    def on_image_delete_requested(self, image_path: str):
        """处理图片删除请求"""
        try:
            # 从缩略图列表中移除
            removed_index = -1
            for i, thumbnail in enumerate(self.thumbnails):
                if thumbnail.image_path == image_path:
                    # 移除缩略图
                    self.thumbnails.pop(i)
                    self.layout.removeWidget(thumbnail)
                    
                    # 性能优化点13：回收缩略图容器而不是销毁
                    if len(self.recycled_thumbnails) < 50:  # 限制回收池大小
                        self.recycled_thumbnails.append(thumbnail)
                        thumbnail.hide()
                    else:
                        thumbnail.deleteLater()
                        
                    removed_index = i
                    break
            
            # 发射删除信号给主窗口
            self.image_deleted.emit(image_path)
            
            # 如果找到并移除了缩略图，需要更新后续缩略图的索引
            if removed_index >= 0:
                self.update_thumbnail_indices(removed_index)
            
            # 更新布局
            self.update_widget_size()
            
        except Exception as e:
            logging.error(f"处理图片删除请求失败: {e}")
    
    def remove_thumbnail_by_path(self, image_path: str):
        """根据路径移除缩略图 - 用于主窗口删除回调"""
        try:
            # 从缩略图列表中移除对应的缩略图
            removed_index = -1
            for i, thumbnail in enumerate(self.thumbnails):
                if thumbnail.image_path == image_path:
                    # 移除缩略图
                    self.thumbnails.pop(i)
                    self.layout.removeWidget(thumbnail)
                    
                    # 性能优化点13：回收缩略图容器而不是销毁
                    if len(self.recycled_thumbnails) < 50:  # 限制回收池大小
                        self.recycled_thumbnails.append(thumbnail)
                        thumbnail.hide()
                    else:
                        thumbnail.deleteLater()
                        
                    removed_index = i
                    break
            
            # 如果找到并移除了缩略图，需要更新后续缩略图的索引
            if removed_index >= 0:
                self.update_thumbnail_indices(removed_index)
                # 更新布局
                self.update_widget_size()
                    
        except Exception as e:
            logging.error(f"根据路径移除缩略图失败: {e}")
    
    def update_thumbnail_indices(self, removed_index: int):
        """更新缩略图索引 - 删除后重新分配索引"""
        try:
            # 更新被删除索引之后的所有缩略图的索引
            for i in range(removed_index, len(self.thumbnails)):
                thumbnail = self.thumbnails[i]
                thumbnail.index = i  # 重新分配索引
                
                # 重新连接信号，使用动态索引计算
                try:
                    thumbnail.clicked.disconnect()
                except:
                    pass
                thumbnail.clicked.connect(self.on_thumbnail_clicked)
                
        except Exception as e:
            logging.error(f"更新缩略图索引失败: {e}")
    
    def start_lazy_loading(self):
        """开始懒加载 - 性能优化版"""
        if not self.thumbnails:
            return
        
        # 强制重新计算可见范围
        self.last_visible_range = (0, 0)
        visible_start, visible_end = self.calculate_visible_range()
        
        # 确保顶部图片优先加载
        if visible_start == 0:
            # 如果可见区域从顶部开始，优先加载前面的图片
            load_start = 0
            load_end = min(len(self.thumbnails), visible_end + 30)  # 增加预加载数量
        else:
            # 正常预加载范围
            load_start = max(0, visible_start - 10)  # 增加上方预加载数量
            load_end = min(len(self.thumbnails), visible_end + 20)  # 增加下方预加载数量
        
        for i in range(load_start, load_end):
            if i < len(self.thumbnails):
                thumbnail = self.thumbnails[i]
                
                needs_loading = False
                
                if "等待加载" in thumbnail.text():
                    needs_loading = True
                elif not thumbnail.loaded and not thumbnail.loading:
                    needs_loading = True
                elif hasattr(thumbnail, 'was_cleaned') and thumbnail.was_cleaned and not thumbnail.loading:
                    needs_loading = True
                
                if needs_loading:
                    config = thumbnail.config_manager.get_config()
                    thumbnail_size = config.get('thumbnail_size', 200)
                    cache_path = thumbnail.image_processor._get_cache_path(thumbnail.image_path, thumbnail_size)
                    
                    if os.path.exists(cache_path):
                        # 缓存存在，直接加载，不占用worker
                        thumbnail.start_loading()
                    else:
                        # 需要异步加载，检查worker限制
                        if self.active_workers < self.max_concurrent_workers:
                            thumbnail.start_loading()
                            self.active_workers += 1
                        else:
                            if thumbnail not in self.pending_loads:
                                self.pending_loads.append(thumbnail)
    
    def calculate_visible_range(self):
        """计算可见区域 - 增强版"""
        if not self.thumbnails:
            return 0, 0
        
        # 查找滚动区域
        if not hasattr(self, '_cached_scroll_area'):
            scroll_area = None
            parent = self.parent()
            while parent:
                if hasattr(parent, 'scroll_area'):
                    scroll_area = parent.scroll_area
                    break
                parent = parent.parent()
            self._cached_scroll_area = scroll_area
        
        scroll_area = self._cached_scroll_area
        if not scroll_area:
            return 0, min(50, len(self.thumbnails))  # 增加默认可见数量
        
        # 获取滚动位置
        scroll_value = scroll_area.verticalScrollBar().value()
        viewport_height = scroll_area.viewport().height()
        
        # 检测是否在顶部
        if scroll_value <= 5:  # 如果滚动值很小，认为是在顶部
            # 在顶部时，确保从第一个开始加载
            return 0, min(50, len(self.thumbnails))  # 增加默认可见数量
        
        visible_top = scroll_value
        visible_bottom = scroll_value + viewport_height
        
        # 使用二分查找快速定位可见范围
        visible_start = self.binary_search_visible_start(visible_top)
        visible_end = self.binary_search_visible_end(visible_bottom, visible_start)
        
        # 确保范围有效
        visible_start = max(0, visible_start)
        visible_end = min(len(self.thumbnails), visible_end + 5)  # 增加额外的可见项
        if visible_end <= visible_start:
            visible_end = visible_start + 20  # 增加默认范围
        
        return visible_start, visible_end
    
    def binary_search_visible_start(self, visible_top):
        """二分查找可见区域起始索引 - 性能优化"""
        if not self.thumbnails:
            return 0
            
        # 如果缩略图数量较少，直接线性搜索
        if len(self.thumbnails) < 50:
            for i, thumbnail in enumerate(self.thumbnails):
                if thumbnail.geometry().bottom() >= visible_top:
                    return i
            return 0
        
        # 二分查找
        left, right = 0, len(self.thumbnails) - 1
        while left <= right:
            mid = (left + right) // 2
            thumbnail = self.thumbnails[mid]
            bottom = thumbnail.geometry().bottom()
            
            if bottom < visible_top:
                left = mid + 1
            else:
                if mid == 0 or self.thumbnails[mid-1].geometry().bottom() < visible_top:
                    return mid
                right = mid - 1
        
        return 0
    
    def binary_search_visible_end(self, visible_bottom, start_index=0):
        """二分查找可见区域结束索引 - 性能优化"""
        if not self.thumbnails:
            return 0
            
        # 如果缩略图数量较少，直接线性搜索
        if len(self.thumbnails) < 50:
            for i in range(start_index, len(self.thumbnails)):
                if self.thumbnails[i].geometry().top() > visible_bottom:
                    return i
            return len(self.thumbnails)
        
        # 二分查找
        left, right = start_index, len(self.thumbnails) - 1
        while left <= right:
            mid = (left + right) // 2
            thumbnail = self.thumbnails[mid]
            top = thumbnail.geometry().top()
            
            if top <= visible_bottom:
                left = mid + 1
            else:
                if mid == start_index or self.thumbnails[mid-1].geometry().top() <= visible_bottom:
                    return mid
                right = mid - 1
        
        return len(self.thumbnails)
    
    def process_next_batch(self):
        """处理下一批缩略图容器创建"""
        if self.loaded_count >= len(self.image_files):
            return
        
        start_index = self.loaded_count
        end_index = min(start_index + self.batch_size, len(self.image_files))
        
        self.create_thumbnail_containers(start_index, end_index)
    
    def on_thumbnail_loaded(self):
        """缩略图加载完成回调"""
        if self.active_workers > 0:
            self.active_workers -= 1
        
        # 发射图片加载完成信号
        self.image_loaded.emit()
        
        while self.pending_loads and self.active_workers < self.max_concurrent_workers:
            next_thumbnail = self.pending_loads.pop(0)
            if not next_thumbnail.loaded and not next_thumbnail.loading:
                config = next_thumbnail.config_manager.get_config()
                thumbnail_size = config.get('thumbnail_size', 200)
                cache_path = next_thumbnail.image_processor._get_cache_path(next_thumbnail.image_path, thumbnail_size)
                
                if os.path.exists(cache_path):
                    # 缓存存在，直接加载，不占用worker
                    next_thumbnail.start_loading()
                    continue
                else:
                    # 需要异步加载，占用worker
                    next_thumbnail.start_loading()
                    self.active_workers += 1
                    break
        
        self.update_widget_size()
    
    def clear_thumbnails(self):
        """清除所有缩略图"""
        if self.layout:
            self.layout.reset()

        self.loading_timer.stop()
        
        # 性能优化点16：回收而不是销毁缩略图
        for thumbnail in self.thumbnails:
            thumbnail.cleanup()
            
            # 回收部分缩略图容器
            if len(self.recycled_thumbnails) < 50:  # 限制回收池大小
                self.recycled_thumbnails.append(thumbnail)
                thumbnail.hide()
            else:
                thumbnail.deleteLater()
        
        self.thumbnails.clear()
        self.pending_loads.clear()
        self.active_workers = 0
        
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item and item.widget() and item.widget() not in self.recycled_thumbnails:
                item.widget().deleteLater()
    
    def load_more(self):
        """加载更多"""
        if self.is_loading_more:
            return
        
        self.is_loading_more = True
        
        if self.loaded_count < len(self.image_files):
            self.process_next_batch()
        
        self.start_lazy_loading()
        
        QTimer.singleShot(100, lambda: setattr(self, 'is_loading_more', False))
    
    def on_scroll_changed(self):
        """滚动处理 - 增强版"""
        # 检查是否滚动到顶部
        scroll_area = self._cached_scroll_area if hasattr(self, '_cached_scroll_area') else None
        if not scroll_area:
            # 如果没有缓存的滚动区域，尝试查找并缓存
            parent = self.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    self._cached_scroll_area = parent
                    scroll_area = parent
                    break
                elif hasattr(parent, 'scroll_area') and parent.scroll_area:
                    self._cached_scroll_area = parent.scroll_area
                    scroll_area = parent.scroll_area
                    break
                parent = parent.parent()
        
        if scroll_area and scroll_area.verticalScrollBar().value() <= 5:
            # 如果滚动到顶部，立即重置可见范围并开始加载
            self.last_visible_range = (0, 0)
            self.start_lazy_loading()
        
        # 使用较短的延迟时间，提高响应速度
        self.scroll_debounce_timer.start(50)
    
    def handle_scroll_load(self):
        """处理滚动加载 - 增强版"""
        # 重新计算可见范围
        visible_start, visible_end = self.calculate_visible_range()
        
        # 如果可见范围与上次不同，才进行处理
        if visible_start != self.last_visible_range[0] or visible_end != self.last_visible_range[1]:
            self.last_visible_range = (visible_start, visible_end)
            
            # 确保有足够的缩略图容器
            while visible_end > self.loaded_count - 30 and self.loaded_count < len(self.image_files):
                self.process_next_batch()
            
            # 开始加载可见区域的图片
            self.start_lazy_loading()
    
    def cleanup_invisible_images(self):
        """清理不可见图片 - 性能优化版"""
        if not self.thumbnails:
            return
        
        loaded_count = sum(1 for t in self.thumbnails if t.loaded and hasattr(t, 'pixmap') and t.pixmap)
        
        memory_pressure_threshold = 2000
        
        if loaded_count < memory_pressure_threshold:
            return
        
        visible_start, visible_end = self.calculate_visible_range()
        
        protection_zone = 150
        protect_start = max(0, visible_start - protection_zone)
        protect_end = min(len(self.thumbnails), visible_end + protection_zone)
        
        cleaned_count = 0
        
        for i, thumbnail in enumerate(self.thumbnails):
            if i < protect_start or i >= protect_end:
                if thumbnail.loaded and hasattr(thumbnail, 'pixmap') and thumbnail.pixmap:
                    thumbnail.pixmap = None
                    thumbnail.loaded = False
                    thumbnail.was_cleaned = True
                    thumbnail.setText("等待加载...<br><br><span style='color: #cccccc; font-size: 12px;font-weight: 400; font-family: 'Microsoft YaHei';'>ℒℴѵℯ时光微醉⁰ɞ</span>")
                    cleaned_count += 1
                    if cleaned_count >= 100:
                        break
    
    def update_widget_size(self):
        """更新组件大小"""
        if self.layout:
            height = self.layout.heightForWidth(self.width())
            self.setMinimumHeight(height)
    
    def _reset_scroll_position(self):
        """重置滚动位置到顶部 - 增强版"""
        # 强制更新布局，确保所有项目都已正确布局
        if hasattr(self, 'layout') and hasattr(self.layout, 'invalidate'):
            self.layout.invalidate()
            self.layout._layout_dirty = True
            self.update_widget_size()
            QApplication.processEvents()
        
        # 直接使用缓存的滚动区域（如果有）
        if hasattr(self, '_cached_scroll_area') and self._cached_scroll_area:
            self._cached_scroll_area.verticalScrollBar().setValue(0)
            QApplication.processEvents()
        
        # 立即尝试一次滚动重置
        self._immediate_scroll_to_top()
        
        # 使用多次延迟执行滚动重置，确保布局已完全更新
        QTimer.singleShot(50, lambda: self._delayed_scroll_to_top())
        QTimer.singleShot(150, lambda: self._delayed_scroll_to_top())
        QTimer.singleShot(300, lambda: self._delayed_scroll_to_top())
        
        return True
        
    def _immediate_scroll_to_top(self):
        """立即尝试滚动到顶部"""
        # 首先检查是否有缓存的滚动区域
        if hasattr(self, '_cached_scroll_area') and self._cached_scroll_area:
            self._cached_scroll_area.verticalScrollBar().setValue(0)
            QApplication.processEvents()
            return
        
        # 如果没有缓存，则查找并缓存
        parent = self.parent()
        while parent:
            # 检查是否是QScrollArea
            if isinstance(parent, QScrollArea):
                parent.verticalScrollBar().setValue(0)
                self._cached_scroll_area = parent
                break
            
            # 检查是否有verticalScrollBar方法
            if hasattr(parent, 'verticalScrollBar'):
                parent.verticalScrollBar().setValue(0)
                self._cached_scroll_area = parent
                break
            
            # 检查是否有滚动区域属性
            if hasattr(parent, 'scroll_area'):
                parent.scroll_area.verticalScrollBar().setValue(0)
                self._cached_scroll_area = parent.scroll_area
                break
            
            # 向上查找父级
            parent = parent.parent()
        
        # 强制处理事件，确保滚动生效
        QApplication.processEvents()
        
    def _force_scroll_to_top(self):
        """强制滚动到顶部的辅助方法 - 增强版"""
        # 重置可见范围计算
        self.last_visible_range = (0, 0)
        
        # 强制重新计算布局
        if hasattr(self, 'layout'):
            self.layout.invalidate()
            self.layout._layout_dirty = True
        
        # 直接使用缓存的滚动区域（如果有）
        if hasattr(self, '_cached_scroll_area') and self._cached_scroll_area:
            self._cached_scroll_area.verticalScrollBar().setValue(0)
            QApplication.processEvents()
        
        # 重置滚动位置
        result = self._reset_scroll_position()
        
        # 强制重新加载可见区域的图片
        QTimer.singleShot(100, lambda: self.start_lazy_loading())
        
        # 再次尝试滚动到顶部，确保滚动生效
        QTimer.singleShot(200, self._immediate_scroll_to_top)
        
        return result
    
    def _delayed_scroll_to_top(self):
        """延迟执行滚动到顶部，确保布局已完全更新"""
        # 强制再次更新布局
        if hasattr(self, 'layout') and hasattr(self.layout, 'invalidate'):
            self.layout.invalidate()
            self.layout._layout_dirty = True
            self.update_widget_size()
            QApplication.processEvents()
        
        # 首先检查是否有缓存的滚动区域
        if hasattr(self, '_cached_scroll_area') and self._cached_scroll_area:
            self._cached_scroll_area.verticalScrollBar().setValue(0)
            QApplication.processEvents()
            return True
        
        parent = self.parent()
        scroll_reset = False
        
        # 1. 直接检查父级
        while parent and not scroll_reset:
            # 检查是否是QScrollArea
            if isinstance(parent, QScrollArea):
                parent.verticalScrollBar().setValue(0)
                self._cached_scroll_area = parent
                scroll_reset = True
                break
            
            # 检查是否有verticalScrollBar方法
            if hasattr(parent, 'verticalScrollBar'):
                parent.verticalScrollBar().setValue(0)
                self._cached_scroll_area = parent
                scroll_reset = True
                break
            
            # 检查是否有滚动区域属性
            if hasattr(parent, 'scroll_area'):
                parent.scroll_area.verticalScrollBar().setValue(0)
                self._cached_scroll_area = parent.scroll_area
                scroll_reset = True
                break
            
            # 向上查找父级
            parent = parent.parent()
        
        # 2. 如果还没找到，在主窗口中查找QScrollArea
        if not scroll_reset:
            main_window = None
            parent = self.parent()
            while parent and not main_window:
                if parent.objectName() == "MainWindow" or hasattr(parent, 'content_stack'):
                    main_window = parent
                parent = parent.parent()
            
            if main_window:
                for widget in main_window.findChildren(QScrollArea):
                    if widget.widget() == self:
                        widget.verticalScrollBar().setValue(0)
                        self._cached_scroll_area = widget
                        scroll_reset = True
                        break
        
        # 3. 最后的尝试：强制更新布局
        if not scroll_reset:
            # 强制重新计算布局
            if hasattr(self, 'layout') and hasattr(self.layout, 'invalidate'):
                self.layout.invalidate()
                self.layout._layout_dirty = True
            
            # 强制更新大小
            self.update_widget_size()
            
            # 强制处理事件
            QApplication.processEvents()
            
            # 再次尝试滚动到顶部
            parent = self.parent()
            while parent and not scroll_reset:
                if isinstance(parent, QScrollArea):
                    parent.verticalScrollBar().setValue(0)
                    self._cached_scroll_area = parent
                    scroll_reset = True
                    break
                parent = parent.parent()
        
        return scroll_reset
    
    def set_view_mode(self, mode: str):
        """设置视图模式"""
        if self.current_view_mode == mode:
            return  # 如果模式没有变化，不做任何操作
            
        self.current_view_mode = mode
        if hasattr(self.layout, 'view_mode'):
            self.layout.view_mode = mode
            # 强制重新计算布局
            self.layout.invalidate()
            # 清除布局缓存
            self.layout._layout_dirty = True
            self.layout._cached_item_positions.clear()
            self.layout._cached_item_heights.clear()
        
        # 重新布局
        self.update()
        self.update_widget_size()
        
        # 强制更新所有缩略图
        for thumbnail in self.thumbnails:
            if hasattr(thumbnail, 'apply_appearance_settings'):
                thumbnail.apply_appearance_settings()
        
        # 确保滚动区域可见
        QTimer.singleShot(100, lambda: self._force_scroll_to_top())
    
    def keyPressEvent(self, event):
        """键盘事件 - 处理DELETE键"""
        if event.key() == Qt.Key_Delete:
            # 找到当前有焦点的缩略图
            focused_widget = self.focusWidget()
            if isinstance(focused_widget, OptimizedImageThumbnail):
                focused_widget.delete_image()
        else:
            super().keyPressEvent(event)
    
    def apply_appearance_settings(self, config=None):
        """应用外观设置到所有缩略图"""
        try:
            if config is None:
                config = self.config_manager.get_config()
            
            # 应用设置到所有现有的缩略图
            for thumbnail in self.thumbnails:
                thumbnail.apply_appearance_settings()
                
        except Exception as e:
            logging.error(f"应用外观设置到瀑布流组件失败: {e}")
    
    def cleanup_resources(self):
        """清理资源"""
        try:
            # 停止所有定时器
            if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
                self.loading_timer.stop()
            
            if hasattr(self, 'scroll_debounce_timer') and self.scroll_debounce_timer.isActive():
                self.scroll_debounce_timer.stop()
                
            if hasattr(self, 'memory_cleanup_timer') and self.memory_cleanup_timer.isActive():
                self.memory_cleanup_timer.stop()
            
            # 清理所有缩略图
            for thumbnail in self.thumbnails:
                if hasattr(thumbnail, 'pixmap') and thumbnail.pixmap:
                    thumbnail.pixmap = None
                if hasattr(thumbnail, 'worker') and thumbnail.worker:
                    thumbnail.worker.stop()
                    thumbnail.worker = None
            
            # 清理回收的缩略图
            self.recycled_thumbnails.clear()
            
            # 清理缓存
            self.image_size_cache.clear()
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            logging.info("瀑布流组件资源已清理")
        except Exception as e:
            logging.error(f"清理瀑布流组件资源失败: {e}")