#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = config_manager.get_config().copy()
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("设置")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 基本设置选项卡
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "基本设置")
        
        # 外观设置选项卡
        appearance_tab = self.create_appearance_tab()
        tab_widget.addTab(appearance_tab, "外观设置")
        
        # 性能设置选项卡
        performance_tab = self.create_performance_tab()
        tab_widget.addTab(performance_tab, "性能设置")
        
        layout.addWidget(tab_widget)
        
        # 创建按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.apply_button = QPushButton("应用")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_settings)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
    
    def create_basic_tab(self):
        """创建基本设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # 初始加载数量
        self.load_count_spin = QSpinBox()
        self.load_count_spin.setRange(10, 500)
        self.load_count_spin.setSuffix(" 张")
        layout.addRow("首屏加载图片数量:", self.load_count_spin)
        
        # 缩略图大小
        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(100, 500)
        self.thumbnail_size_spin.setSuffix(" px")
        layout.addRow("缩略图大小:", self.thumbnail_size_spin)
        
        # 预览缩放比例
        self.preview_scale_spin = QSpinBox()
        self.preview_scale_spin.setRange(50, 100)
        self.preview_scale_spin.setSuffix(" %")
        layout.addRow("预览图缩放比例:", self.preview_scale_spin)
        
        # 预览窗口大小比例
        self.preview_window_scale_spin = QSpinBox()
        self.preview_window_scale_spin.setRange(50, 100)
        self.preview_window_scale_spin.setSuffix(" %")
        layout.addRow("预览窗口大小比例:", self.preview_window_scale_spin)
        
        return widget
    
    def create_appearance_tab(self):
        """创建外观设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # 图片边框
        border_group = QGroupBox("图片边框")
        border_layout = QVBoxLayout(border_group)
        
        self.border_check = QCheckBox("启用边框")
        border_layout.addWidget(self.border_check)
        
        border_settings = QWidget()
        border_settings_layout = QFormLayout(border_settings)
        
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(1, 10)
        self.border_width_spin.setSuffix(" px")
        border_settings_layout.addRow("边框宽度:", self.border_width_spin)
        
        self.border_color_button = QPushButton()
        self.border_color_button.setFixedHeight(30)
        self.border_color_button.clicked.connect(self.choose_border_color)
        border_settings_layout.addRow("边框颜色:", self.border_color_button)
        
        border_layout.addWidget(border_settings)
        
        # 边框设置启用/禁用
        self.border_check.toggled.connect(border_settings.setEnabled)
        
        layout.addRow(border_group)
        
        # 视图布局设置
        layout_group = QGroupBox("视图布局")
        layout_group_layout = QFormLayout(layout_group)
        
        # 瀑布流列数
        self.waterfall_columns_spin = QSpinBox()
        self.waterfall_columns_spin.setRange(2, 8)
        self.waterfall_columns_spin.setValue(4)
        self.waterfall_columns_spin.setToolTip("设置瀑布流视图的列数 (2-8列)")
        layout_group_layout.addRow("瀑布流列数:", self.waterfall_columns_spin)
        
        # 网格列数
        self.grid_columns_spin = QSpinBox()
        self.grid_columns_spin.setRange(3, 12)
        self.grid_columns_spin.setValue(6)
        self.grid_columns_spin.setToolTip("设置网格视图的列数 (3-12列)")
        layout_group_layout.addRow("网格列数:", self.grid_columns_spin)
        

        
        layout.addRow(layout_group)
        
        # 图片阴影
        shadow_group = QGroupBox("图片阴影")
        shadow_layout = QVBoxLayout(shadow_group)
        
        self.shadow_check = QCheckBox("启用阴影")
        shadow_layout.addWidget(self.shadow_check)
        
        shadow_settings = QWidget()
        shadow_settings_layout = QFormLayout(shadow_settings)
        
        self.shadow_size_spin = QSpinBox()
        self.shadow_size_spin.setRange(1, 20)
        self.shadow_size_spin.setSuffix(" px")
        shadow_settings_layout.addRow("阴影大小:", self.shadow_size_spin)
        
        self.shadow_color_button = QPushButton()
        self.shadow_color_button.setFixedHeight(30)
        self.shadow_color_button.clicked.connect(self.choose_shadow_color)
        shadow_settings_layout.addRow("阴影颜色:", self.shadow_color_button)
        
        shadow_layout.addWidget(shadow_settings)
        
        # 阴影设置启用/禁用
        self.shadow_check.toggled.connect(shadow_settings.setEnabled)
        
        layout.addRow(shadow_group)
        
        # 圆角设置
        rounded_group = QGroupBox("圆角设置")
        rounded_layout = QVBoxLayout(rounded_group)
        
        self.rounded_check = QCheckBox("启用圆角")
        rounded_layout.addWidget(self.rounded_check)
        
        rounded_settings = QWidget()
        rounded_settings_layout = QFormLayout(rounded_settings)
        
        self.rounded_size_spin = QSpinBox()
        self.rounded_size_spin.setRange(1, 50)
        self.rounded_size_spin.setSuffix(" px")
        rounded_settings_layout.addRow("圆角大小:", self.rounded_size_spin)
        
        rounded_layout.addWidget(rounded_settings)
        
        # 圆角设置启用/禁用
        self.rounded_check.toggled.connect(rounded_settings.setEnabled)
        
        layout.addRow(rounded_group)
        
        # 鼠标悬停设置
        hover_group = QGroupBox("鼠标悬停效果")
        hover_layout = QVBoxLayout(hover_group)
        
        self.hover_check = QCheckBox("启用悬停效果")
        hover_layout.addWidget(self.hover_check)
        
        hover_settings = QWidget()
        hover_settings_layout = QFormLayout(hover_settings)
        
        self.hover_color_button = QPushButton()
        self.hover_color_button.setFixedHeight(30)
        self.hover_color_button.clicked.connect(self.choose_hover_color)
        hover_settings_layout.addRow("悬停背景色:", self.hover_color_button)
        
        self.hover_border_color_button = QPushButton()
        self.hover_border_color_button.setFixedHeight(30)
        self.hover_border_color_button.clicked.connect(self.choose_hover_border_color)
        hover_settings_layout.addRow("悬停边框色:", self.hover_border_color_button)
        
        hover_layout.addWidget(hover_settings)
        
        # 悬停设置启用/禁用
        self.hover_check.toggled.connect(hover_settings.setEnabled)
        
        layout.addRow(hover_group)
        
        return widget
    
    def create_performance_tab(self):
        """创建性能设置选项卡"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # 缓存大小
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 5000)
        self.cache_size_spin.setSuffix(" 张")
        layout.addRow("缓存大小:", self.cache_size_spin)
        
        # 缓存信息显示
        self.cache_info_label = QLabel()
        self.cache_info_label.setWordWrap(True)
        layout.addRow("缓存状态:", self.cache_info_label)
        
        # 清除缓存按钮
        clear_cache_button = QPushButton("清除缓存")
        clear_cache_button.clicked.connect(self.clear_cache)
        layout.addRow("", clear_cache_button)
        
        # 检查缓存大小按钮
        check_cache_button = QPushButton("检查缓存大小")
        check_cache_button.clicked.connect(self.check_cache_size)
        layout.addRow("", check_cache_button)
        
        return widget
    
    def choose_border_color(self):
        """选择边框颜色"""
        current_color = QColor(self.config.get('border_color', '#E0E0E0'))
        color = QColorDialog.getColor(current_color, self, "选择边框颜色")
        
        if color.isValid():
            self.config['border_color'] = color.name()
            self.update_color_button(self.border_color_button, color)
    
    def choose_shadow_color(self):
        """选择阴影颜色"""
        current_color = QColor(self.config.get('shadow_color', '#808080'))
        color = QColorDialog.getColor(current_color, self, "选择阴影颜色")
        
        if color.isValid():
            self.config['shadow_color'] = color.name()
            self.update_color_button(self.shadow_color_button, color)
    
    def choose_hover_color(self):
        """选择悬停背景颜色"""
        current_color = QColor(self.config.get('hover_color', '#e3f2fd'))
        color = QColorDialog.getColor(current_color, self, "选择悬停背景颜色")
        
        if color.isValid():
            self.config['hover_color'] = color.name()
            self.update_color_button(self.hover_color_button, color)
    
    def choose_hover_border_color(self):
        """选择悬停边框颜色"""
        current_color = QColor(self.config.get('hover_border_color', '#2196f3'))
        color = QColorDialog.getColor(current_color, self, "选择悬停边框颜色")
        
        if color.isValid():
            self.config['hover_border_color'] = color.name()
            self.update_color_button(self.hover_border_color_button, color)
    
    def update_color_button(self, button, color):
        """更新颜色按钮显示"""
        button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")
    
    def get_cache_size(self):
        """获取缓存大小（字节）"""
        import os
        cache_dir = "cache"
        total_size = 0
        
        if os.path.exists(cache_dir):
            for dirpath, dirnames, filenames in os.walk(cache_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
        
        return total_size
    
    def format_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def update_cache_info(self):
        """更新缓存信息显示"""
        cache_size = self.get_cache_size()
        formatted_size = self.format_size(cache_size)
        
        if cache_size > 2 * 1024 * 1024 * 1024:  # 超过2GB
            self.cache_info_label.setText(f"当前大小: {formatted_size} (⚠️ 缓存较大)")
            self.cache_info_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.cache_info_label.setText(f"当前大小: {formatted_size}")
            self.cache_info_label.setStyleSheet("color: green;")
    
    def check_cache_size(self):
        """检查缓存大小并提示删除"""
        cache_size = self.get_cache_size()
        formatted_size = self.format_size(cache_size)
        
        # 更新显示
        self.update_cache_info()
        
        # 如果超过2GB，提示用户删除
        if cache_size > 2 * 1024 * 1024 * 1024:  # 2GB
            reply = QMessageBox.question(
                self, "缓存过大", 
                f"当前缓存大小为 {formatted_size}，已超过2GB。\n\n"
                "删除缓存可以释放磁盘空间，但可能会影响图片加载速度。\n"
                "是否要删除缓存？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.clear_cache()
                self.update_cache_info()
        else:
            QMessageBox.information(
                self, "缓存检查", 
                f"当前缓存大小为 {formatted_size}，在正常范围内。"
            )
    
    def clear_cache(self):
        """清除缓存"""
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有缓存吗？\n\n删除后可能影响图片加载速度。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            import shutil
            import os
            cache_dir = "cache"
            if os.path.exists(cache_dir):
                try:
                    shutil.rmtree(cache_dir)
                    os.makedirs(cache_dir)
                    QMessageBox.information(self, "完成", "缓存已清除")
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"清除缓存失败: {str(e)}")
            else:
                QMessageBox.information(self, "完成", "缓存目录不存在，无需清除")
    
    def load_settings(self):
        """加载设置"""
        # 基本设置
        self.load_count_spin.setValue(self.config.get('initial_load_count', 100))
        self.thumbnail_size_spin.setValue(self.config.get('thumbnail_size', 200))
        self.preview_scale_spin.setValue(self.config.get('preview_scale', 80))
        self.preview_window_scale_spin.setValue(self.config.get('preview_window_scale', 80))
        
        # 外观设置
        self.border_check.setChecked(self.config.get('image_border', True))
        self.border_width_spin.setValue(self.config.get('border_width', 2))
        
        border_color = QColor(self.config.get('border_color', '#E0E0E0'))
        self.update_color_button(self.border_color_button, border_color)
        
        self.shadow_check.setChecked(self.config.get('image_shadow', True))
        self.shadow_size_spin.setValue(self.config.get('shadow_size', 5))
        
        shadow_color = QColor(self.config.get('shadow_color', '#808080'))
        self.update_color_button(self.shadow_color_button, shadow_color)
        
        self.rounded_check.setChecked(self.config.get('image_rounded', True))
        self.rounded_size_spin.setValue(self.config.get('rounded_size', 8))
        
        # 鼠标悬停设置
        self.hover_check.setChecked(self.config.get('hover_enabled', True))
        
        hover_color = QColor(self.config.get('hover_color', '#e3f2fd'))
        self.update_color_button(self.hover_color_button, hover_color)
        
        hover_border_color = QColor(self.config.get('hover_border_color', '#2196f3'))
        self.update_color_button(self.hover_border_color_button, hover_border_color)
        
        # 视图布局设置
        self.waterfall_columns_spin.setValue(self.config.get('waterfall_columns', 4))
        self.grid_columns_spin.setValue(self.config.get('grid_columns', 6))
        
        # 性能设置
        self.cache_size_spin.setValue(self.config.get('cache_size', 3000))
        
        # 更新缓存信息
        self.update_cache_info()
    
    def apply_settings(self):
        """应用设置"""
        # 收集设置
        self.config.update({
            'initial_load_count': self.load_count_spin.value(),
            'thumbnail_size': self.thumbnail_size_spin.value(),
            'preview_scale': self.preview_scale_spin.value(),
            'preview_window_scale': self.preview_window_scale_spin.value(),
            'image_border': self.border_check.isChecked(),
            'border_width': self.border_width_spin.value(),
            'image_shadow': self.shadow_check.isChecked(),
            'shadow_size': self.shadow_size_spin.value(),
            'image_rounded': self.rounded_check.isChecked(),
            'rounded_size': self.rounded_size_spin.value(),
            'hover_enabled': self.hover_check.isChecked(),
            'waterfall_columns': self.waterfall_columns_spin.value(),
            'grid_columns': self.grid_columns_spin.value(),
            'cache_size': self.cache_size_spin.value()
        })
        
        # 保存设置
        self.config_manager.update_config(self.config)
        
        QMessageBox.information(self, "完成", "设置已保存")
    
    def accept(self):
        """确定按钮"""
        self.apply_settings()
        super().accept()