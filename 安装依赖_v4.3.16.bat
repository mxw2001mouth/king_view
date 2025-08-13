@echo off
chcp 65001 >nul
title 图片管理器 v4.3.15 - 依赖安装工具

echo.
echo ========================================
echo  图片管理器 v4.3.15 依赖安装工具
echo ========================================
echo.
echo 正在安装必要的Python库...
echo.

echo 安装PyQt5（界面框架）...
pip install PyQt5>=5.15.0
if %errorlevel% neq 0 (
    echo  PyQt5 安装失败
    goto :error
)

echo.
echo 安装Pillow（图像处理库）...
pip install Pillow>=10.0.0
if %errorlevel% neq 0 (
    echo  Pillow 安装失败
    goto :error
)

echo.
echo 安装rawpy（RAW格式支持）...
pip install rawpy>=0.18.0
if %errorlevel% neq 0 (
    echo  rawpy 安装失败
    goto :error
)

echo.
echo 安装send2trash（回收站删除）...
pip install send2trash>=1.8.0
if %errorlevel% neq 0 (
    echo  send2trash 安装失败
    goto :error
)

echo.
echo 安装numpy（数值计算）...
pip install numpy>=1.24.0
if %errorlevel% neq 0 (
    echo  numpy 安装失败
    goto :error
)

echo.
echo 安装exifread（EXIF信息读取）...
pip install exifread>=3.0.0
if %errorlevel% neq 0 (
    echo  exifread 安装失败
    goto :error
)

echo.
echo 安装psutil（系统信息）...
pip install psutil>=5.9.0
if %errorlevel% neq 0 (
    echo  psutil 安装失败
    goto :error
)

echo.
echo 安装PyInstaller（打包工具）...
pip install pyinstaller>=5.0.0
if %errorlevel% neq 0 (
    echo  PyInstaller 安装失败
    goto :error
)

echo.
echo 安装图像处理增强（图像处理增强）...
pip install opencv-python>=4.12.0
if %errorlevel% neq 0 (
    echo  opencv-python 安装失败
    goto :error
)

echo.
echo 安装图像格式支持（图像格式支持）...
pip install imageio>=2.37.0
if %errorlevel% neq 0 (
    echo  imageio 安装失败
    goto :error
)

echo.
echo ========================================
echo 所有依赖安装完成！
echo ========================================
echo.
echo 现在可以运行图片管理器了
echo 运行命令: python main_v4.3.15.py
echo 打包命令: python build_v4.3.15.py
echo.
echo 正在运行依赖检查...
python 检查依赖.py
goto :end

:error
echo.
echo ========================================
echo  安装过程中出现错误
echo ========================================
echo.
echo 可能的解决方案:
echo   1. 检查网络连接
echo   2. 更新pip: python -m pip install --upgrade pip
echo   3. 使用国内镜像: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
echo   4. 以管理员身份运行此脚本
echo.

:end
echo 按任意键退出...
pause >nul