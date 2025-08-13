#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的图片预览窗口 v4.3 - 交互优化版
增加DELETE键删除、右键双击打开目录、左键双击关闭窗口等功能
"""

import os
import logging
import subprocess
import sys
from typing import List
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime

# 导入文件工具模块
from file_utils import move_to_recycle_bin

class OptimizedImageLoadWorker(QThread):
    """优化的图片加载工作线程"""
    
    image_loaded = pyqtSignal(QPixmap)
    info_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, image_path: str, image_processor):
        super().__init__()
        self.image_path = image_path
        self.image_processor = image_processor
        self._stop_requested = False
        self.setTerminationEnabled(True)
    
    def run(self):
        """运行线程"""
        try:
            if self._stop_requested:
                return
            
            if not os.path.exists(self.image_path):
                if not self._stop_requested:
                    self.error_occurred.emit("文件不存在")
                return
            
            # 加载图片
            pixmap = None
            
            # 检查是否是RAW格式
            ext = os.path.splitext(self.image_path)[1].lower()
            is_raw_format = ext in {'.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef', '.srw',
                                   '.raf', '.3fr', '.fff', '.dcr', '.kdc', '.mdc', '.mos', '.mrw',
                                   '.nrw', '.ptx', '.r3d', '.rwl', '.rwz', '.x3f', '.bay', '.crw'}
            
            if is_raw_format:
                try:
                    pil_image = self.image_processor.load_image(self.image_path)
                    if pil_image and not self._stop_requested:
                        if pil_image.mode != 'RGB':
                            pil_image = pil_image.convert('RGB')
                        
                        import numpy as np
                        from PyQt5.QtGui import QImage
                        
                        img_array = np.array(pil_image)
                        height, width, channel = img_array.shape
                        bytes_per_line = 3 * width
                        
                        qt_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qt_image)
                except Exception as e:
                    if not self._stop_requested:
                        logging.warning(f"使用image_processor加载RAW失败，尝试直接加载: {e}")
            
            # 如果RAW加载失败或不是RAW格式，尝试直接加载
            if pixmap is None or pixmap.isNull():
                pixmap = QPixmap(self.image_path)
            
            if self._stop_requested:
                return
            
            if not pixmap.isNull():
                # 限制图片大小以节省内存
                max_size = 2048
                if pixmap.width() > max_size or pixmap.height() > max_size:
                    pixmap = pixmap.scaled(
                        max_size, max_size,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                
                if not self._stop_requested:
                    self.image_loaded.emit(pixmap)
            else:
                if not self._stop_requested:
                    self.error_occurred.emit("无法加载图片文件")
            
            # 获取图片信息
            if not self._stop_requested:
                try:
                    info = {}
                    
                    try:
                        from PIL import Image
                        from PIL.ExifTags import TAGS
                        
                        with Image.open(self.image_path) as img:
                            exif_data = img._getexif()
                            if exif_data:
                                for tag_id, value in exif_data.items():
                                    tag = TAGS.get(tag_id, tag_id)
                                    if tag == 'DateTime':
                                        try:
                                            date_taken = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                            info['date_taken'] = date_taken.strftime('%Y-%m-%d')
                                        except:
                                            pass
                                        break
                    except:
                        pass
                    
                    self.info_loaded.emit(info)
                except:
                    pass
            
        except Exception as e:
            if not self._stop_requested:
                self.error_occurred.emit(f"加载图片时发生错误: {str(e)}")
    
    def stop(self):
        """停止线程"""
        self._stop_requested = True
        self.requestInterruption()

class OptimizedPreviewWindow(QWidget):
    """优化的预览窗口 v4.3 - 增强交互功能"""
    
    window_closed = pyqtSignal()
    image_deleted = pyqtSignal(str)  # 图片删除信号
    
    def __init__(self, image_files: List[str], current_index: int, 
                 image_processor, config_manager, parent=None):
        super().__init__(parent)
        
        # 基本属性
        self.image_files = image_files
        self.current_index = current_index
        self.image_processor = image_processor
        self.config_manager = config_manager
        self.current_pixmap = None
        self.worker = None
        self.loading = False
        
        # 双击相关
        self.left_click_timer = QTimer()
        self.left_click_timer.setSingleShot(True)
        self.left_click_timer.timeout.connect(self.handle_left_double_click)
        self.left_click_count = 0
        
        self.right_click_timer = QTimer()
        self.right_click_timer.setSingleShot(True)
        self.right_click_timer.timeout.connect(self.handle_right_double_click)
        self.right_click_count = 0
        
        # 性能优化参数
        self.max_cache_size = 5
        self.image_cache = {}
        self.preload_count = 2
        
        # 设置窗口属性
        self.setWindowTitle("图片预览")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        
        # 初始化界面
        self.init_ui()
        
        # 设置窗口几何
        self.setup_window_geometry()
        
        # 确保窗口能接收键盘焦点
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
        # 加载当前图片
        self.load_current_image()
    
    def init_ui(self):
        """初始化界面"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        
        # 创建图片显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent; border: none;")
        self.image_label.setScaledContents(False)
        
        # 创建加载提示
        self.loading_label = QLabel("加载中...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        self.loading_label.hide()
        
        # 创建信息栏
        self.info_bar = QLabel()
        self.info_bar.setFixedHeight(36)
        self.info_bar.setAlignment(Qt.AlignCenter)
        self.info_bar.setWordWrap(False)
        self.info_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.info_bar.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #6c757d;
                font-size: 12px;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
                padding: 8px 16px;
                border-top: 1px solid #e9ecef;
                border-bottom: 1px solid #e9ecef;
                margin: 0px;
                border-left: none;
                border-right: none;
            }
        """)
        
        # 添加到布局
        layout.addWidget(self.image_label)
        layout.addWidget(self.info_bar)
        
        # 创建叠加层用于加载提示
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setStyleSheet("background-color: transparent;")
        
        overlay_layout = QVBoxLayout(self.overlay_widget)
        overlay_layout.addStretch()
        overlay_layout.addWidget(self.loading_label, 0, Qt.AlignCenter)
        overlay_layout.addStretch()
    
    def setup_window_geometry(self):
        """设置窗口几何"""
        self.resize(800, 600)
        
        try:
            desktop = QApplication.desktop()
            screen_geometry = desktop.screenGeometry()
            x = (screen_geometry.width() - 800) // 2
            y = (screen_geometry.height() - 600) // 2
            self.move(x, y)
        except Exception as e:
            logging.warning(f"设置窗口位置失败: {e}")
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.setGeometry(self.rect())
        
        if hasattr(self, 'info_bar') and hasattr(self, '_last_info_text'):
            QTimer.singleShot(50, lambda: self._update_elided_text(self._last_info_text))
    
    def load_current_image(self):
        """加载当前图片"""
        if not self.image_files or self.current_index < 0 or self.current_index >= len(self.image_files):
            return
        
        current_path = self.image_files[self.current_index]
        
        # 检查是否是RAW格式
        ext = os.path.splitext(current_path)[1].lower()
        is_raw_format = ext in {'.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2', '.pef', '.srw',
                               '.raf', '.3fr', '.fff', '.dcr', '.kdc', '.mdc', '.mos', '.mrw',
                               '.nrw', '.ptx', '.r3d', '.rwl', '.rwz', '.x3f', '.bay', '.crw'}
        
        # 对于RAW格式，使用image_processor加载
        if is_raw_format:
            try:
                pil_image = self.image_processor.load_image(current_path)
                if pil_image:
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    
                    import numpy as np
                    from PyQt5.QtGui import QImage
                    
                    img_array = np.array(pil_image)
                    height, width, channel = img_array.shape
                    bytes_per_line = 3 * width
                    
                    qt_image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB888)
                    self.current_pixmap = QPixmap.fromImage(qt_image)
                    
                    if not self.current_pixmap.isNull():
                        self.display_pixmap = None
                        self.adjust_window_size()
                        self.update_image_display()
                        self.update_info_bar()
                        self._load_info_async(current_path)
                        self.add_to_cache(current_path, self.current_pixmap)
                        return
            except Exception as e:
                logging.error(f"使用image_processor加载RAW图片失败: {e}")
        
        # 对于标准格式或RAW加载失败的情况，尝试直接加载
        try:
            self.current_pixmap = QPixmap(current_path)
            if not self.current_pixmap.isNull():
                self.display_pixmap = None
                self.adjust_window_size()
                self.update_image_display()
                self.update_info_bar()
                self._load_info_async(current_path)
                self.add_to_cache(current_path, self.current_pixmap)
                return
        except Exception as e:
            logging.error(f"直接加载图片失败: {e}")
        
        # 停止之前的加载
        self.stop_current_loading()
        
        # 显示加载状态
        self.loading = True
        self.loading_label.show()
        self.image_label.clear()
        
        # 创建新的工作线程
        self.worker = OptimizedImageLoadWorker(current_path, self.image_processor)
        self.worker.image_loaded.connect(self.on_image_loaded)
        self.worker.info_loaded.connect(self.on_info_loaded)
        self.worker.error_occurred.connect(self.on_load_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
    
    def _load_info_async(self, image_path):
        """异步加载图片信息"""
        def load_info():
            try:
                info = {}
                try:
                    from PIL import Image
                    from PIL.ExifTags import TAGS
                    
                    with Image.open(image_path) as img:
                        exif_data = img._getexif()
                        if exif_data:
                            for tag_id, value in exif_data.items():
                                tag = TAGS.get(tag_id, tag_id)
                                if tag == 'DateTime':
                                    try:
                                        from datetime import datetime
                                        date_taken = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                        info['date_taken'] = date_taken.strftime('%Y-%m-%d')
                                    except:
                                        pass
                                    break
                except:
                    pass
                
                QTimer.singleShot(0, lambda: self.update_info_bar(info))
            except:
                pass
        
        QTimer.singleShot(10, load_info)
    
    def stop_current_loading(self):
        """停止当前加载"""
        if self.worker:
            self.worker.stop()
            self.worker.wait(1000)
            if self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait()
            self.worker.deleteLater()
            self.worker = None
    
    def on_image_loaded(self, pixmap):
        """图片加载完成"""
        if not self.loading:
            return
        
        self.current_pixmap = pixmap
        self.loading = False
        self.loading_label.hide()
        
        self.display_pixmap = None
        
        current_path = self.image_files[self.current_index]
        self.add_to_cache(current_path, pixmap)
        
        self.adjust_window_size()
        self.update_image_display()
        self.preload_adjacent_images()
    
    def on_info_loaded(self, info):
        """信息加载完成"""
        self.update_info_bar(info)
    
    def on_load_error(self, error_msg):
        """加载错误"""
        self.loading = False
        self.loading_label.setText(f"加载失败: {error_msg}")
        QTimer.singleShot(2000, self.loading_label.hide)
    
    def on_worker_finished(self):
        """工作线程完成"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def add_to_cache(self, path, pixmap):
        """添加到缓存"""
        if len(self.image_cache) >= self.max_cache_size:
            oldest_key = next(iter(self.image_cache))
            del self.image_cache[oldest_key]
        
        self.image_cache[path] = pixmap
    
    def preload_adjacent_images(self):
        """预加载相邻图片"""
        next_index = self.current_index + 1
        if next_index < len(self.image_files):
            next_path = self.image_files[next_index]
            if next_path not in self.image_cache:
                self.preload_image(next_path)
        
        prev_index = self.current_index - 1
        if prev_index >= 0:
            prev_path = self.image_files[prev_index]
            if prev_path not in self.image_cache:
                self.preload_image(prev_path)
    
    def preload_image(self, image_path):
        """预加载图片"""
        QTimer.singleShot(100, lambda: self._do_preload(image_path))
    
    def _do_preload(self, image_path):
        """执行预加载"""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                if pixmap.width() > 1024 or pixmap.height() > 1024:
                    pixmap = pixmap.scaled(1024, 1024, Qt.KeepAspectRatio, Qt.FastTransformation)
                self.add_to_cache(image_path, pixmap)
        except:
            pass
    
    def adjust_window_size(self):
        """调整窗口大小"""
        if not self.current_pixmap:
            return
        
        desktop = QApplication.desktop()
        screen_geometry = desktop.screenGeometry()
        max_width = int(screen_geometry.width() * 0.9)
        max_height = int(screen_geometry.height() * 0.9)
        
        original_width = self.current_pixmap.width()
        original_height = self.current_pixmap.height()
        
        if original_width > max_width or original_height > max_height - 36:
            scale_w = max_width / original_width
            scale_h = (max_height - 36) / original_height
            scale = min(scale_w, scale_h)
            
            self.display_pixmap = self.current_pixmap.scaled(
                int(original_width * scale),
                int(original_height * scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            self.display_pixmap = QPixmap(self.current_pixmap)
        
        display_width = self.display_pixmap.width()
        display_height = self.display_pixmap.height()
        
        window_width = display_width
        window_height = display_height + 36
        
        self.setFixedSize(window_width, window_height)
        self.image_label.setFixedSize(display_width, display_height)
        
        self.updateGeometry()
        QApplication.processEvents()
        
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.move(x, y)
    
    def update_image_display(self):
        """更新图片显示"""
        if hasattr(self, 'display_pixmap') and self.display_pixmap:
            self.image_label.setPixmap(self.display_pixmap)
        elif self.current_pixmap:
            self.image_label.setPixmap(self.current_pixmap)
    
    def update_info_bar(self, info=None):
        """更新信息栏"""
        try:
            current_path = self.image_files[self.current_index]
            filename = os.path.basename(current_path)
            
            file_stat = os.stat(current_path)
            file_size = file_stat.st_size
            
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            elif file_size < 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
            
            time_str = ""
            if info and 'date_taken' in info:
                time_str = info['date_taken']
            else:
                from datetime import datetime
                modified_time = datetime.fromtimestamp(file_stat.st_mtime)
                time_str = modified_time.strftime('%Y-%m-%d')
            
            dimensions_str = ""
            if self.current_pixmap:
                width = self.current_pixmap.width()
                height = self.current_pixmap.height()
                dimensions_str = f"{width} × {height}"
            
            info_text = f"时间： {time_str}  |  名称: {filename}  |  尺寸: {dimensions_str}  |  大小: {size_str}"
            
        except Exception as e:
            filename = os.path.basename(self.image_files[self.current_index])
            info_text = f"名称: {filename}"
        
        self.info_bar.setText(info_text)
        self._last_info_text = info_text
        
        QTimer.singleShot(10, lambda: self._update_elided_text(info_text))
    
    def _update_elided_text(self, full_text):
        """更新省略号文字"""
        try:
            if self.info_bar.width() <= 0:
                QTimer.singleShot(50, lambda: self._update_elided_text(full_text))
                return
            
            font_metrics = self.info_bar.fontMetrics()
            available_width = self.info_bar.width() - 32
            
            if available_width > 0:
                elided_text = font_metrics.elidedText(full_text, Qt.ElideMiddle, available_width)
                if elided_text != full_text:
                    self.info_bar.setText(elided_text)
                    self.info_bar.setToolTip(full_text)
                else:
                    self.info_bar.setToolTip("")
            
            self._last_info_text = full_text
            
        except Exception as e:
            logging.debug(f"更新省略号文字失败: {e}")
    
    def prev_image(self):
        """上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            if hasattr(self, 'display_pixmap'):
                self.display_pixmap = None
            if hasattr(self, 'current_pixmap'):
                self.current_pixmap = None
            self.load_current_image()
    
    def next_image(self):
        """下一张图片"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            if hasattr(self, 'display_pixmap'):
                self.display_pixmap = None
            if hasattr(self, 'current_pixmap'):
                self.current_pixmap = None
            self.load_current_image()
    
    def delete_current_image(self):
        """删除当前图片 - 移动到回收站"""
        try:
            if self.current_index < 0 or self.current_index >= len(self.image_files):
                return
            
            current_path = self.image_files[self.current_index]
            
            if os.path.exists(current_path):
                # 尝试移动到回收站
                if move_to_recycle_bin(current_path):
                    logging.info(f"已将图片移动到回收站: {current_path}")
                else:
                    # 如果移动到回收站失败，询问用户是否直接删除
                    reply = QMessageBox.question(
                        self, 
                        "删除确认", 
                        f"无法将图片移动到回收站。\n是否直接删除文件？\n\n{os.path.basename(current_path)}",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        os.remove(current_path)
                        logging.info(f"已直接删除图片: {current_path}")
                    else:
                        return  # 用户取消删除
                
                # 先发射删除信号给主窗口，让主窗口先更新列表
                self.image_deleted.emit(current_path)
                
                # 从预览窗口的列表中移除
                if current_path in self.image_files:
                    self.image_files.remove(current_path)
                
                # 如果没有图片了，关闭窗口
                if not self.image_files:
                    self.close()
                    return
                
                # 调整当前索引
                if self.current_index >= len(self.image_files):
                    self.current_index = len(self.image_files) - 1
                
                # 加载下一张图片
                self.load_current_image()
                
        except Exception as e:
            logging.error(f"删除图片失败: {e}")
            QMessageBox.warning(self, "删除失败", f"无法删除图片:\n{str(e)}")
    
    def open_file_location(self):
        """打开文件所在目录并定位到文件"""
        try:
            if self.current_index < 0 or self.current_index >= len(self.image_files):
                return
            
            current_path = self.image_files[self.current_index]
            
            if os.path.exists(current_path):
                # 确保使用绝对路径
                abs_path = os.path.abspath(current_path)
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
                logging.warning(f"文件不存在: {current_path}")
                
        except Exception as e:
            logging.error(f"打开文件位置失败: {e}")
            # 尝试至少打开目录
            try:
                if self.current_index >= 0 and self.current_index < len(self.image_files):
                    dir_path = os.path.dirname(os.path.abspath(self.image_files[self.current_index]))
                    if os.name == 'nt':
                        subprocess.run(['explorer', dir_path], check=False)
                    else:
                        subprocess.run(['xdg-open', dir_path], check=False)
            except:
                pass
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 处理左键双击
            self.left_click_count += 1
            if self.left_click_count == 1:
                self.left_click_timer.start(300)  # 300ms内检测双击
            elif self.left_click_count == 2:
                self.left_click_timer.stop()
                self.left_click_count = 0
                self.close()  # 左键双击关闭窗口
        elif event.button() == Qt.RightButton:
            # 处理右键双击
            self.right_click_count += 1
            if self.right_click_count == 1:
                self.right_click_timer.start(300)  # 300ms内检测双击
            elif self.right_click_count == 2:
                self.right_click_timer.stop()
                self.right_click_count = 0
                self.open_file_location()  # 右键双击打开目录
    
    def handle_left_double_click(self):
        """处理左键双击超时"""
        self.left_click_count = 0
    
    def handle_right_double_click(self):
        """处理右键双击超时"""
        self.right_click_count = 0
    
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Left:
            self.prev_image()
        elif event.key() == Qt.Key_Right:
            self.next_image()
        elif event.key() == Qt.Key_Delete:
            self.delete_current_image()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止所有加载
        self.stop_current_loading()
        
        # 清理缓存
        self.image_cache.clear()
        
        # 发射关闭信号
        self.window_closed.emit()
        
        event.accept()

# 为了兼容性，保留原来的类名
ModernPreviewWindow = OptimizedPreviewWindow