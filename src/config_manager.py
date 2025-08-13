#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
负责读取和保存程序配置
"""

import json
import os
import sys
import logging
from typing import Dict, Any

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file: str = 'config.json'):
        # 确保配置文件路径正确，支持打包后的相对路径
        if not os.path.isabs(config_file):
            # 获取程序运行目录
            if getattr(sys, 'frozen', False):
                # 打包后的可执行文件
                app_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            self.config_file = os.path.join(app_dir, config_file)
        else:
            self.config_file = config_file
            
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "app_icon": "icon.ico",
            "initial_load_count": 30,
            "image_border": True,
            "border_width": 1,
            "border_color": "#e0e0e0",
            "image_shadow": True,
            "shadow_size": 3,
            "shadow_color": "#e0e0e0",
            "image_rounded": True,
            "rounded_size": 6,
            "preview_scale": 80,
            "thumbnail_size": 300,
            "cache_size": 3000,
            "waterfall_columns": 6,
            "window_geometry": None,
            "last_directory": ""
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    default_config.update(loaded_config)
            return default_config
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            return default_config
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置"""
        self.config.update(updates)
        self.save_config()
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取单个配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置单个配置项"""
        self.config[key] = value
        self.save_config()