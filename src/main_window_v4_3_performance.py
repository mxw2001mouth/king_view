import os
import logging
import time
from typing import List, Dict, Any, Optional

from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
    QStatusBar, QToolBar, QAction, QMenu, QToolButton, 
    QMessageBox, QFileDialog, QDialog, QApplication
)

# 导入优化版本的组件
from image_processor_optimized import ImageProcessor
from optimized_waterfall_widget_v4_3_performance import OptimizedWaterfallWidget
from optimized_preview_window_v4_3 import OptimizedPreviewWindow
from settings_dialog import SettingsDialog
from config_manager import ConfigManager

class MainWindowPerformance(QMainWindow):
    """主窗口 - 性能优化版"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化图片处理器
        self.image_processor = ImageProcessor()
        
        # 初始化变量
        self.current_directory = ""
        self.image_files = []
        self.total_images = 0
        self.loaded_images = 0
        self.preview_window = None
        
        # 设置窗口属性
        self.setWindowTitle("ℒℴѵℯ时光微醉⁰ɞ图片管理器 - 性能优化版")
        
        # 根据屏幕大小设置窗口尺寸
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # 设置窗口大小为屏幕的80%
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        self.setMinimumSize(1200, 800)
        self.resize(window_width, window_height)
        
        # 恢复上次窗口大小和位置
        self.restore_window_geometry()
        
        # 初始化UI
        self.init_ui()
        
        # 加载设置
        self.load_settings()
        
        # 不自动加载上次打开的文件夹，让用户自己选择
    
    def restore_window_geometry(self):
        """恢复窗口大小和位置"""
        geometry = self.config_manager.get('window_geometry', None)
        if geometry:
            try:
                # 将Base64字符串转换为QByteArray
                from PyQt5.QtCore import QByteArray
                import base64
                byte_data = base64.b64decode(geometry)
                qbyte_array = QByteArray(byte_data)
                self.restoreGeometry(qbyte_array)
            except Exception as e:
                logging.warning(f"恢复窗口几何信息失败: {e}")
    
    def save_window_geometry(self):
        """保存窗口大小和位置"""
        try:
            # 将QByteArray转换为Base64字符串
            geometry = self.saveGeometry()
            import base64
            geometry_str = base64.b64encode(geometry.data()).decode('ascii')
            self.config_manager.set('window_geometry', geometry_str)
        except Exception as e:
            logging.warning(f"保存窗口几何信息失败: {e}")
    
    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 先创建工具栏，确保它显示在顶部
        self.create_toolbar()
        
        # 创建堆叠部件用于切换欢迎界面和图片浏览界面
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # 创建欢迎界面
        self.create_welcome_page()
        
        # 创建图片浏览界面
        self.create_browser_page()
        
        # 默认显示欢迎界面
        self.content_stack.setCurrentIndex(0)
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_welcome_page(self):
        """创建欢迎界面"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        
        # 设置欢迎页面的背景 - 使用渐变背景
        welcome_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f0f9ff, stop:1 #e0f7fa);
        """)
        
        # 创建中心容器 - 添加渐变和阴影效果
        center_container = QWidget()
        center_container.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.9), stop:1 rgba(240, 249, 255, 0.9));
            border-radius: 20px;
            border: 1px solid rgba(59, 130, 246, 0.2);
        """)
        center_container.setFixedWidth(600)  # 固定宽度使界面更集中
        
        # 中心容器布局
        container_layout = QVBoxLayout(center_container)
        container_layout.setContentsMargins(30, 40, 30, 40)
        container_layout.setSpacing(30)
        
        # 头部布局 - 包含图标和标题
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        # 图标 - 添加径向渐变背景
        icon_label = QLabel("🖼️")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 52px;
                color: #3b82f6;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                    stop:0 rgba(59, 130, 246, 0.1), 
                    stop:1 rgba(59, 130, 246, 0.0));
                padding: 8px;
            }
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # 简洁标题 - 添加渐变文字效果
        title_label = QLabel("ℒℴѵℯ时光微醉⁰ɞ")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 400;
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1f2937, stop:0.5 #3b82f6, stop:1 #1f2937);
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 简短描述
        subtitle_label = QLabel("快速浏览和管理您的图片")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #6b7280;
                margin: 0;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        # 主要按钮 - 添加渐变和阴影效果
        start_button = QPushButton("选择文件夹")
        start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4f46e5, stop:1 #3b82f6);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 16px 36px;
                font-size: 15px;
                font-weight: 600;
                min-height: 22px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6366f1, stop:1 #2563eb);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3730a3, stop:1 #1d4ed8);
            }
        """)
        start_button.clicked.connect(self.open_directory)
        start_button.setCursor(Qt.PointingHandCursor)
        
        container_layout.addWidget(header_widget)  # 添加头部布局
        container_layout.addWidget(start_button)   # 添加按钮

        # 功能亮点 - 更简洁
        features_widget = QWidget()
        features_layout = QHBoxLayout(features_widget)
        features_layout.setContentsMargins(0, 0, 0, 0)
        features_layout.setSpacing(20)
        
        # 创建功能点 - 添加卡片效果
        def create_feature_item(icon, text):
            item = QWidget()
            item.setStyleSheet("""
                QWidget {
                    background: rgba(255, 255, 255, 0.7);
                    border-radius: 12px;
                    border: 1px solid rgba(59, 130, 246, 0.1);
                    padding: 8px;
                }
                QWidget:hover {
                    background: rgba(59, 130, 246, 0.05);
                    border-color: rgba(59, 130, 246, 0.2);
                }
            """)
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(12, 12, 12, 12)
            item_layout.setSpacing(6)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                        stop:0 rgba(59, 130, 246, 0.1), 
                        stop:1 rgba(59, 130, 246, 0.0));
                    border-radius: 8px;
                    padding: 4px;
                }
            """)
            icon_label.setAlignment(Qt.AlignCenter)
            
            text_label = QLabel(text)
            text_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #4b5563;
                    font-weight: 600;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
                }
            """)
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setWordWrap(True)
            
            item_layout.addWidget(icon_label)
            item_layout.addWidget(text_label)
            return item
        
        features_layout.addWidget(create_feature_item("⚡", "快速加载"))
        features_layout.addWidget(create_feature_item("🎨", "瀑布流"))
        features_layout.addWidget(create_feature_item("🔍", "全屏预览"))
        
        # 添加到容器
        container_layout.addWidget(features_widget)
        
        # 添加到主布局
        welcome_layout.addStretch(1)
        welcome_layout.addWidget(center_container, 0, Qt.AlignCenter)
        welcome_layout.addStretch(1)
        
        # 添加欢迎页面到堆叠部件
        self.content_stack.addWidget(welcome_widget)
    
    def create_browser_page(self):
        """创建图片浏览界面"""
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f9fafb;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 创建瀑布流组件
        self.waterfall_widget = OptimizedWaterfallWidget(
            self.image_processor, 
            self.config_manager
        )
        
        # 连接信号
        self.waterfall_widget.image_clicked.connect(self.open_preview)
        self.waterfall_widget.image_deleted.connect(self.on_image_deleted)
        self.waterfall_widget.image_loaded.connect(self.on_image_loaded)
        
        # 设置瀑布流组件为滚动区域的部件
        self.scroll_area.setWidget(self.waterfall_widget)
        
        # 连接滚动条信号
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
        browser_layout.addWidget(self.scroll_area)
        
        # 添加图片浏览页面到堆叠部件
        self.content_stack.addWidget(browser_widget)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("""
            QStatusBar {
                background-color: #f9fafb;
                border-top: 1px solid #e5e7eb;
                padding: 8px 16px;
                font-size: 13px;
                color: #4b5563;
                height: 26px;
            }
        """)
        self.setStatusBar(self.statusBar)
        
        # 创建状态标签
        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setStyleSheet("color: #6c757d; font-weight: normal; padding: 2px 8px;")
        self.statusBar.addWidget(self.folder_label, 1)
        
        self.count_label = QLabel("加载状态: 0/0")
        self.count_label.setStyleSheet("color: #6c757d; font-weight: normal; padding: 2px 8px;")
        self.statusBar.addPermanentWidget(self.count_label)
    
    def update_folder_info(self, folder_path: str):
        """更新文件夹信息"""
        if folder_path:
            folder_name = os.path.basename(folder_path)
            self.folder_label.setText(f"当前文件夹: {folder_name}")
        else:
            self.folder_label.setText("未选择文件夹")
            self.folder_label.setStyleSheet("color: #6c757d; font-weight: normal; padding: 2px 8px;")
    def update_load_status(self):
        """更新加载状态"""
        self.count_label.setText(f"加载状态: {self.loaded_images}/{self.total_images}")
        self.count_label.setStyleSheet("color: #6c757d; font-weight: normal; padding: 2px 8px;")
    def on_image_loaded(self):
        """图片加载回调"""
        self.loaded_images += 1
        self.update_load_status()
    
    def on_image_deleted(self, image_path: str):
        """图片删除回调"""
        try:
            # 从图片列表中移除
            if image_path in self.image_files:
                self.image_files.remove(image_path)
                self.total_images = len(self.image_files)
                
                # 检查被删除的图片是否已经加载过，如果是则减少已加载计数
                deleted_thumbnail_was_loaded = False
                if hasattr(self, 'waterfall_widget'):
                    # 在删除缩略图之前检查是否已加载
                    for thumbnail in self.waterfall_widget.thumbnails:
                        if thumbnail.image_path == image_path and thumbnail.loaded:
                            deleted_thumbnail_was_loaded = True
                            break
                    
                    # 通知瀑布流组件移除对应的缩略图
                    self.waterfall_widget.remove_thumbnail_by_path(image_path)
                
                # 如果被删除的图片已经加载过，减少已加载计数
                if deleted_thumbnail_was_loaded and self.loaded_images > 0:
                    self.loaded_images -= 1
                
                self.update_load_status()
                
                # 如果当前预览窗口显示的是被删除的图片，关闭预览窗口
                if hasattr(self, 'preview_window') and self.preview_window:
                    # 检查预览窗口是否显示的是被删除的图片
                    if (hasattr(self.preview_window, 'current_index') and 
                        self.preview_window.current_index < len(self.preview_window.image_files) and
                        self.preview_window.image_files[self.preview_window.current_index] == image_path):
                        # 如果预览窗口显示的就是被删除的图片，让预览窗口自己处理
                        pass
                    else:
                        # 如果不是，只需要从预览窗口的列表中移除
                        if hasattr(self.preview_window, 'image_files') and image_path in self.preview_window.image_files:
                            self.preview_window.image_files.remove(image_path)
                    
        except Exception as e:
            logging.error(f"处理图片删除回调时出错: {e}")
    
    def show_sort_menu(self):
        """显示排序菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e1e5e9;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            QMenu::item {
                padding: 10px 16px;
                border-radius: 8px;
                color: #1f2937;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            QMenu::item:disabled {
                color: #9ca3af;
            }
        """)
        
        # 按名称排序
        name_action = QAction('📝 按名称排序', self)
        name_action.triggered.connect(lambda: self.sort_images('name'))
        menu.addAction(name_action)
        
        # 按日期排序
        date_action = QAction('📅 按日期排序', self)
        date_action.triggered.connect(lambda: self.sort_images('date'))
        menu.addAction(date_action)
        
        # 按大小排序
        size_action = QAction('📏 按大小排序', self)
        size_action.triggered.connect(lambda: self.sort_images('size'))
        menu.addAction(size_action)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
    
    def _reset_view(self):
        """
        一个统一的、可靠的视图重置方法。
        严格遵循“清空内容 -> 强制UI同步 -> 重置滚动条”的顺序。
        """
        if hasattr(self, 'waterfall_widget'):
            self.waterfall_widget.clear_thumbnails()

        QApplication.processEvents()

        if hasattr(self, 'scroll_area'):
            self.scroll_area.verticalScrollBar().setValue(0)

    def sort_images(self, sort_type: str):
        """排序图片"""
        if not self.image_files:
            return
        
        try:
            self._reset_view()

            self.loaded_images = 0
            if sort_type == 'name':
                self.image_files.sort(key=lambda x: os.path.basename(x).lower())
            elif sort_type == 'date':
                self.image_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            elif sort_type == 'size':
                self.image_files.sort(key=lambda x: os.path.getsize(x), reverse=True)

            self.config_manager.set('current_sort', sort_type)

            if hasattr(self, 'waterfall_widget'):
                self.waterfall_widget.set_images(self.image_files)
                
        except Exception as e:
            logging.error(f"排序失败: {e}")
    
    def create_toolbar(self):
        """创建现代化精致工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(13, 13))
        
        # 现代化工具栏样式
        toolbar.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fafbfc);
                border: none;
                border-bottom: 1px solid #d1d9e0;
                spacing: 0px;
                padding: 0px 8px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
                height: 40px;
                min-height: 40px;
                max-height: 40px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px 6px;
                margin: 0px 2px;
                font-size: 13px;
                font-weight: 500;
                color: #24292f;
                min-width: 50px;
                height: 23px;
                text-align: center;
            }
            QToolButton:hover {
                background-color: rgba(175, 184, 193, 0.2);
                border-color: rgba(175, 184, 193, 0.4);
                color: #0969da;
            }
            QToolButton:pressed {
                background-color: rgba(175, 184, 193, 0.3);
                border-color: rgba(175, 184, 193, 0.6);
                color: #0550ae;
            }
            QToolButton:checked {
                background-color: #0969da;
                border-color: #0550ae;
                color: white;
                font-weight: 600;
            }
            QToolBar::separator {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 transparent, stop:0.3 #d1d9e0, stop:0.7 #d1d9e0, stop:1 transparent);
                width: 1px;
                margin: 3px 6px;
            }
        """)
        
        # 创建极简按钮组
        open_action = QAction('打开', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('选择图片文件夹 (Ctrl+O)')
        open_action.triggered.connect(self.open_directory)
        toolbar.addAction(open_action)
        
        refresh_action = QAction('刷新', self)
        refresh_action.setShortcut('F5')
        refresh_action.setStatusTip('重新扫描文件夹 (F5)')
        refresh_action.triggered.connect(self.refresh_images)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()
        
        sort_action = QAction('排序', self)
        sort_action.setStatusTip('排序图片')
        sort_action.triggered.connect(self.show_sort_menu)
        toolbar.addAction(sort_action)
        
        # 创建视图切换下拉菜单
        self.create_view_menu_button(toolbar)
        
        toolbar.addSeparator()
        
        settings_action = QAction('设置', self)
        settings_action.setStatusTip('打开程序设置')
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        # 添加弹性空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        about_action = QAction('关于', self)
        about_action.setStatusTip('关于程序')
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)
    
    def create_view_menu_button(self, toolbar):
        """创建视图切换下拉菜单按钮"""
        view_menu = QMenu(self)
        view_menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e1e5e9;
                border-radius: 4px;
                padding: 3px;
                font-size: 13px;
                font-weight: 500;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 6px;
                color: #24292f;
                margin: 1px;
            }
            QMenu::item:selected {
                background-color: #0969da;
                color: white;
            }
            QMenu::item:checked {
                background-color: #f0f8ff;
                color: #0969da;
                font-weight: 600;
            }
        """)
        
        waterfall_action = QAction('🌊 瀑布流视图', self)
        waterfall_action.setCheckable(True)
        waterfall_action.setChecked(True)
        waterfall_action.triggered.connect(lambda: self.switch_view_mode('waterfall'))
        view_menu.addAction(waterfall_action)
        
        grid_action = QAction('⚏ 网格视图', self)
        grid_action.setCheckable(True)
        grid_action.triggered.connect(lambda: self.switch_view_mode('grid'))
        view_menu.addAction(grid_action)
        
        view_button = QToolButton()
        view_button.setText('视图')
        view_button.setPopupMode(QToolButton.InstantPopup)
        view_button.setMenu(view_menu)
        view_button.setStatusTip('切换视图模式')
        view_button.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px 6px;
                margin: 0px 2px;
                font-size: 13px;
                font-weight: 500;
                color: #24292f;
                min-width: 55px;
                height: 23px;
                text-align: center;
            }
            QToolButton:hover {
                background-color: rgba(175, 184, 193, 0.2);
                border-color: rgba(175, 184, 193, 0.4);
                color: #0969da;
            }
            QToolButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)
        
        toolbar.addWidget(view_button)
        
        self.view_actions = [waterfall_action, grid_action]
        self.current_view_mode = 'waterfall'
    
    def switch_view_mode(self, mode: str):
        """切换视图模式"""
        if hasattr(self, 'view_actions'):
            for action in self.view_actions:
                action.setChecked(False)
            
            if mode == 'waterfall':
                self.view_actions[0].setChecked(True)
            elif mode == 'grid':
                self.view_actions[1].setChecked(True)
        
        self.current_view_mode = mode
        # 保存当前视图模式到配置
        self.config_manager.set('view_mode', mode)
        self.config_manager.set('current_view_mode', mode)
        
        # 强制重置布局
        if hasattr(self, 'waterfall_widget') and hasattr(self.waterfall_widget, 'layout'):
            self.waterfall_widget.layout.invalidate()
            self.waterfall_widget.layout._layout_dirty = True
            if hasattr(self.waterfall_widget.layout, '_cached_layout_height'):
                self.waterfall_widget.layout._cached_layout_height = 0
            if hasattr(self.waterfall_widget.layout, '_cached_layout_width'):
                self.waterfall_widget.layout._cached_layout_width = 0
            if hasattr(self.waterfall_widget.layout, '_cached_item_positions'):
                self.waterfall_widget.layout._cached_item_positions.clear()
        
        # 强制滚动到顶部
        if hasattr(self, 'scroll_area') and self.scroll_area:
            self.scroll_area.verticalScrollBar().setValue(0)
            QApplication.processEvents()
        
        if hasattr(self, 'waterfall_widget'):
            # 设置视图模式前先确保滚动到顶部
            if hasattr(self.waterfall_widget, '_force_scroll_to_top'):
                self.waterfall_widget._force_scroll_to_top()
            
            self.waterfall_widget.set_view_mode(mode)
            
            # 设置视图模式后再次确保滚动到顶部
            if hasattr(self.waterfall_widget, '_force_scroll_to_top'):
                QTimer.singleShot(100, lambda: self.waterfall_widget._force_scroll_to_top())
                QTimer.singleShot(300, lambda: self.waterfall_widget._force_scroll_to_top())
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
    <div style="
        font-family: 'Segoe UI', 'Microsoft YaHei', 'Helvetica', 'Arial', sans-serif;
        background: #ffffff;
        color: #333333;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        max-width: 500px;
        margin: 0 auto;
        border: 1px solid #e9ecef;
    ">

        <!-- 标题区域 -->
        <div style="
            text-align: center;
            padding-bottom: 16px;
            margin-bottom: 24px;
            border-bottom: 1px solid #e9ecef;
        ">
            <h1 style="
                color: #007bff;
                margin: 0 0 8px 0;
                font-size: 28px;
                font-weight: 600;
                letter-spacing: 0.75px;
            ">ℒℴѵℯ时光微醉⁰ɞ</h1>
            <h2 style="
                color: #6c757d;
                margin: 0 0 8px 0;
                font-size: 20px;
                font-weight: 500;
            ">图片管理器</h2>
            <div style="
                color: #adb5bd;
                font-size: 16px;
                font-weight: 500;
                margin: 4px 0;
            ">v4.3.15 · 性能优化版</div>
        </div>

        <!-- 快捷键与鼠标操作（表格模拟两列） -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
            <tr>
                <td width="50%" style="padding-right: 12px;">
                    <div style="
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 16px;
                    ">
                        <h3 style="
                            color: #007bff;
                            margin: 0 0 12px 0;
                            font-size: 18px;
                            font-weight: 600;
                            text-align: center;
                        ">⌨️ 快捷键</h3>
                        <div style="
                            font-size: 16px;
                            line-height: 1.6;
                            color: #495057;
                        ">
                            <div style="margin: 4px 0;"><b>Ctrl+O</b> 打开文件夹</div>
                            <div style="margin: 4px 0;"><b>F5</b> 刷新列表</div>
                            <div style="margin: 4px 0;"><b>Delete</b> 删除图片</div>
                            <div style="margin: 4px 0;"><b>←/→</b> 切换图片</div>
                            <div style="margin: 4px 0;"><b>ESC</b> 退出预览</div>
                        </div>
                    </div>
                </td>
                <td width="50%" style="padding-left: 12px;">
                    <div style="
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 16px;
                    ">
                        <h3 style="
                            color: #007bff;
                            margin: 0 0 12px 0;
                            font-size: 18px;
                            font-weight: 600;
                            text-align: center;
                        ">🖱️ 鼠标操作</h3>
                        <div style="
                            font-size: 16px;
                            line-height: 1.6;
                            color: #495057;
                        ">
                            <div style="margin: 4px 0;"><b>左键</b> 预览图片</div>
                            <div style="margin: 4px 0;"><b>双击</b> 关闭预览</div>
                            <div style="margin: 4px 0;"><b>右键双击</b> 定位文件</div>
                            <div style="margin: 4px 0;"><b>悬停</b> 显示信息</div>
                            <div style="margin: 4px 0;"><b>滚轮</b> 浏览缩放</div>
                        </div>
                    </div>
                </td>
            </tr>
        </table>

        <!-- 开发者信息 -->
        <div style="
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            font-size: 16px;
            color: #495057;
            margin-top: 24px;
        ">
            <div style="margin: 4px 0;"><b>开发者</b> ℒℴѵℯ时光微醉⁰ɞ</div>
            <div style="margin: 4px 0; color: #6c757d;">
                <b>联系</b> 231589322@qq.com
            </div>
            <div style="margin: 8px 0 0 0; font-size: 14px; color: #adb5bd;">
                使用技术：Python • PyQt5 • Pillow • rawpy
            </div>
        </div>

    </div>
    """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("关于 - ℒℴѵℯ时光微醉⁰ɞ图片管理器 - 性能优化版")
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # 设置合适的宽度以支持两列布局
        msg_box.setStyleSheet("""
            QMessageBox {
                min-width: 520px;
                max-width: 600px;
            }
            QMessageBox QLabel {
                min-width: 500px;
                max-width: 580px;
            }
        """)
        
        msg_box.exec_()
        
    def auto_load_last_directory(self):
        """自动加载上次打开的文件夹"""
        last_dir = self.config_manager.get('last_directory', '')
        if last_dir and os.path.exists(last_dir):
            self.current_directory = last_dir
            self.load_images()
    
    def open_directory(self):
        """打开文件夹"""
        last_dir = self.config_manager.get('last_directory', '')
        directory = QFileDialog.getExistingDirectory(
            self, '选择图片文件夹', last_dir
        )
        
        if directory:
            self._reset_view()
            self.current_directory = directory
            self.config_manager.set('last_directory', directory)
            current_sort = self.config_manager.get('current_sort', 'date')
            self.config_manager.set('current_sort', current_sort)
            if hasattr(self, 'waterfall_widget'):
                current_view_mode = getattr(self.waterfall_widget, 'current_view_mode', 'waterfall')
                self.config_manager.set('current_view_mode', current_view_mode)
            self.load_images()
    
    def load_images(self):
        """加载图片"""
        if not self.current_directory:
            # 尝试加载上次打开的文件夹
            last_dir = self.config_manager.get('last_directory', '')
            if last_dir and os.path.exists(last_dir):
                self.current_directory = last_dir
            else:
                return
        
        self.update_folder_info(self.current_directory)
        
        self.image_files = []
        
        # 扫描文件夹中的图片
        for root, dirs, files in os.walk(self.current_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if self.image_processor.is_supported_format(file_path):
                    self.image_files.append(file_path)
        
        # 应用保存的排序方式
        current_sort = self.config_manager.get('current_sort', 'date')
        if current_sort == 'name':
            self.image_files.sort(key=lambda x: os.path.basename(x).lower())
        elif current_sort == 'size':
            self.image_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
        else:  # 默认按日期排序
            self.image_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # 更新统计
        self.total_images = len(self.image_files)
        self.loaded_images = 0
        self.update_load_status()
        
        # 切换到图片浏览界面
        self.content_stack.setCurrentIndex(1)
        
        # 应用保存的视图模式
        if hasattr(self, 'waterfall_widget'):
            saved_view_mode = self.config_manager.get('current_view_mode', 'waterfall')
            if hasattr(self.waterfall_widget, 'set_view_mode'):
                self.waterfall_widget.set_view_mode(saved_view_mode)
        
        # 更新瀑布流
        self.waterfall_widget.set_images(self.image_files)
    
    def refresh_images(self):
        """刷新图片"""
        if self.current_directory:
            self._reset_view()
            self.load_images()
        else:
            # 如果没有当前目录，尝试加载上次打开的文件夹
            last_dir = self.config_manager.get('last_directory', '')
            if last_dir and os.path.exists(last_dir):
                self.current_directory = last_dir
                self._reset_view()
                self.load_images()
    
    def on_scroll(self, value):
        """滚动事件处理"""
        scrollbar = self.scroll_area.verticalScrollBar()
        
        if hasattr(self.waterfall_widget, 'on_scroll_changed'):
            self.waterfall_widget.on_scroll_changed()
        
        if scrollbar.maximum() > 0:
            ratio = value / scrollbar.maximum()
            if ratio > 0.7:
                self.waterfall_widget.load_more()
    
    def open_preview(self, image_path: str, index: int):
        """打开预览窗口"""
        try:
            if not image_path or not os.path.exists(image_path):
                return
            
            if not self.image_files or index >= len(self.image_files):
                return
            
            # 安全关闭之前的预览窗口
            if hasattr(self, 'preview_window') and self.preview_window:
                try:
                    old_preview = self.preview_window
                    self.preview_window = None
                    old_preview.close()
                    old_preview.deleteLater()
                except Exception as e:
                    logging.warning(f"关闭预览窗口时出错: {e}")
                    self.preview_window = None
            
            # 强制处理事件
            QApplication.processEvents()
            
            # 延迟创建预览窗口
            QTimer.singleShot(50, lambda: self._create_preview_window(image_path, index))
            
        except Exception as e:
            logging.error(f"打开预览窗口失败: {e}")
    
    def _create_preview_window(self, image_path: str, index: int):
        """创建预览窗口"""
        try:
            self.preview_window = OptimizedPreviewWindow(
                self.image_files, index, 
                self.image_processor, 
                self.config_manager, 
                self
            )
            
            # 连接信号
            self.preview_window.window_closed.connect(self.on_preview_closed)
            self.preview_window.image_deleted.connect(self.on_image_deleted)
            
            self.preview_window.show()
            self.preview_window.raise_()
            self.preview_window.activateWindow()
            
        except Exception as e:
            logging.error(f"创建预览窗口失败: {e}")
            self.preview_window = None
    
    def on_preview_closed(self):
        """预览窗口关闭回调"""
        self.preview_window = None
    
    def open_settings(self):
        """打开设置对话框"""
        try:
            dialog = SettingsDialog(self.config_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                # 重新加载设置
                self.load_settings()
        except Exception as e:
            logging.error(f"打开设置对话框失败: {e}")
    
    def load_settings(self):
        """加载设置"""
        try:
            config = self.config_manager.get_config()
            
            # 程序标题由主程序统一管理，不再从配置读取
            
            # 通知瀑布流组件更新外观设置
            if hasattr(self, 'waterfall_widget'):
                self.waterfall_widget.apply_appearance_settings(config)
                
        except Exception as e:
            logging.error(f"加载设置失败: {e}")
    
    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_F5:
            self.refresh_images()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_O:
            self.open_directory()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存窗口几何信息
        self.save_window_geometry()
        
        # 关闭预览窗口
        if hasattr(self, 'preview_window') and self.preview_window:
            try:
                self.preview_window.close()
            except Exception:
                pass
        
        # 清理资源
        if hasattr(self, 'waterfall_widget'):
            self.waterfall_widget.cleanup_resources()
        
        super().closeEvent(event)

# 程序入口
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindowPerformance()
    window.show()
    sys.exit(app.exec_())