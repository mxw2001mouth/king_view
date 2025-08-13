#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查工具 - 确保所有必要的库都已安装
"""

import sys
import importlib

def check_dependencies():
    """检查所有必要的依赖"""
    print(" 检查图片管理器依赖库...")
    print("=" * 50)
    
    # 必要的依赖列表
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('PIL', 'Pillow'),
        ('rawpy', 'rawpy'),
        ('numpy', 'numpy'),
        ('exifread', 'exifread'),
        ('psutil', 'psutil'),
        ('send2trash', 'send2trash'),
        ('cv2', 'opencv-python'),
        ('imageio', 'imageio'),
    ]
    
    missing_packages = []
    installed_packages = []
    
    for module_name, package_name in required_packages:
        try:
            importlib.import_module(module_name)
            print(f" {package_name:<15} - 已安装")
            installed_packages.append(package_name)
        except ImportError:
            print(f" {package_name:<15} - 未安装")
            missing_packages.append(package_name)
    
    print("=" * 50)
    print(f" 检查结果: {len(installed_packages)}/{len(required_packages)} 个依赖已安装")
    
    if missing_packages:
        print(f"\n 缺少以下依赖:")
        for package in missing_packages:
            print(f"   • {package}")
        
        print(f"\n 安装命令:")
        install_cmd = "pip install " + " ".join(missing_packages)
        print(f"   {install_cmd}")
        
        return False
    else:
        print("\n 所有依赖都已正确安装!")
        return True
#检查可选依赖  这个也是必选，所以屏蔽掉。mazh-2025-8-5
#def check_optional_dependencies():
#    print("\n检查可选依赖...")
#    print("-" * 30)
    
#    optional_packages = [
#        ('cv2', 'opencv-python', '图像处理增强'),
#        ('imageio', 'imageio', '图像格式支持'),
#    ]
    
#    for module_name, package_name, description in optional_packages:
#       try:
#            importlib.import_module(module_name)
#            print(f"{package_name:<20} - 已安装 ({description})")
 #       except ImportError:
#            print(f"⚪ {package_name:<20} - 未安装 ({description})")

def main():
    """主函数"""
    # 确保输出使用UTF-8编码
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("图片管理器 v5.0 - 依赖检查工具")
    print("=" * 60)
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("警告: 建议使用Python 3.7或更高版本")
    else:
        print("Python版本符合要求")
    
    print()
    
    # 检查必要依赖
    all_installed = check_dependencies()
    
    # 检查可选依赖
    #check_optional_dependencies()
    
    print("\n" + "=" * 60)
    
    if all_installed:
        print(" 依赖检查完成! 可以正常运行图片管理器")
        print(" 运行命令: python main_v5.0.py")
    else:
        print(" 存在缺失的依赖，请先安装后再运行")
        print(" 安装命令: pip install -r requirements.txt")
    
    print("=" * 60)
    
    return all_installed

if __name__ == '__main__':
    success = main()
    
    print("\n按任意键退出...")
    try:
        input()
    except KeyboardInterrupt:
        pass
    
    sys.exit(0 if success else 1)