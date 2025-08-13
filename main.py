#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片管理器 v4.3.18 - 线程优化版
1. 集成最新的界面美化效果
2. 修复关于窗口显示问题（恢复4.3.6简洁样式）
3. 优化渐变背景和现代化UI元素
4. 增强用户体验和视觉效果
"""

import sys
import os
from PyQt5.QtCore import Qt

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from PyQt5.QtWidgets import QApplication

# 修复导入问题
import main_window_v4_3_performance
from main_window_v4_3_performance import MainWindowPerformance as MainWindow

def main():
    """主函数"""
    # 设置高DPI支持 - 必须在创建QApplication之前
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("ℒℴѵℯ时光微醉⁰ɞ图片管理器")
    app.setApplicationVersion("4.3.18")
    
    # 创建主窗口
    window = MainWindow()
    
    # 设置窗口图标
    try:
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(current_dir, 'app.ico')
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
            app.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"设置图标失败: {e}")
    
    window.show()
    
    # 设置窗口标题 - 统一管理，不再从配置读取
    window.setWindowTitle("ℒℴѵℯ时光微醉⁰ɞ图片管理器 v4.3.18 - 线程优化版")
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
