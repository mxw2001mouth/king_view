# 🖼️ 专业图片管理器

一个功能强大的本地图片管理程序，专为Windows 11系统优化，支持常见图片格式和RAW格式，具有瀑布流布局和智能缓存功能。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## ✨ 主要特性

### 📁 格式支持
- ✅ **常见格式**：JPG, PNG, BMP, GIF, TIFF, WebP
- ✅ **RAW格式**：CR2, NEF, ARW, DNG, ORF, RW2, PEF, SRW, RAF, 3FR, FFF, DCR, KDC, MDC, MOS, MRW, NRW, PTX, R3D, RWL, RWZ, X3F, BAY, CRW

### 🎨 界面特性
- ✅ **瀑布流布局**：自适应屏幕分辨率，智能列数计算
- ✅ **智能缩略图**：高质量生成和缓存，支持异步加载
- ✅ **预览模式**：全屏预览，支持鼠标拖拽和窗口位置记忆
- ✅ **信息显示**：拍摄时间/创建时间、文件名称、文件大小
- ✅ **美观界面**：现代化设计，支持悬停效果和动画

### 🚀 操作体验
- ✅ **键盘操作**：左右键切换图片，ESC退出预览
- ✅ **鼠标操作**：透明浮动按钮，支持鼠标翻页
- ✅ **多线程处理**：响应流畅，不阻塞界面
- ✅ **内存管理**：企业级内存管理，防止内存泄漏
- ✅ **错误处理**：完善的异常处理，程序稳定可靠

### ⚙️ 个性化设置
- ✅ **加载设置**：可配置首屏加载图片数量
- ✅ **外观设置**：图片边框、阴影、圆角等
- ✅ **预览设置**：预览图缩放比例调整
- ✅ **程序设置**：标题、图标等自定义

## 🚀 快速开始

### 方法一：一键启动（推荐）

1. **双击运行**：`启动图片管理器.bat`
2. **自动检查**：程序会自动检查和安装依赖
3. **开始使用**：依赖安装完成后自动启动程序

### 方法二：Python环境运行

```bash
# 1. 克隆或下载项目
git clone <项目地址>
cd king_view

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

### 方法三：使用启动脚本

```bash
# 自动检查依赖并启动
python run.py
```

## 📦 打包为EXE

```bash
# 1. 安装打包依赖
python build.py --install-deps

# 2. 打包程序
python build.py

# 3. 运行EXE
dist/图片管理器.exe
```

## 🎯 使用指南

### 基本操作

1. **📂 打开文件夹**
   - 点击工具栏 `📁 打开文件夹` 按钮
   - 或使用快捷键 `Ctrl+O`
   - 选择包含图片的文件夹

2. **🖼️ 浏览图片**
   - 在瀑布流界面中点击任意图片
   - 进入全屏预览模式

3. **⌨️ 预览操作**
   - `←` `→` 键：切换上一张/下一张图片
   - `ESC` 键：退出预览模式
   - 鼠标拖拽：移动预览窗口
   - 浮动按钮：鼠标点击翻页

4. **🔄 其他功能**
   - `F5`：刷新图片列表
   - 排序：按时间、名称、大小排序
   - 设置：个性化配置程序

### 高级功能

- **🎨 外观定制**：边框、阴影、圆角等样式设置
- **⚡ 性能优化**：缓存大小、加载数量等性能调优
- **📊 排序选项**：多种排序方式，满足不同需求
- **👁️ 视图选项**：显示信息、自动刷新等

## ⚙️ 配置文件

程序配置保存在 `config.json` 文件中：

```json
{
    "app_title": "图片管理器",           // 程序标题
    "initial_load_count": 50,          // 首屏加载图片数量
    "image_border": true,              // 是否显示边框
    "border_width": 2,                 // 边框宽度
    "border_color": "#E0E0E0",         // 边框颜色
    "image_shadow": true,              // 是否显示阴影
    "shadow_size": 5,                  // 阴影大小
    "shadow_color": "#808080",         // 阴影颜色
    "image_rounded": true,             // 是否使用圆角
    "rounded_size": 8,                 // 圆角大小
    "preview_scale": 80,               // 预览图缩放比例(%)
    "thumbnail_size": 200,             // 缩略图大小
    "cache_size": 1000                 // 缓存大小
}
```

## 🔧 技术特点

### 核心技术
- **🐍 Python 3.8+**：现代Python特性
- **🖥️ PyQt5**：跨平台GUI框架
- **🖼️ Pillow**：图像处理库
- **📷 rawpy**：RAW格式支持
- **🧠 智能算法**：自适应布局和缓存

### 架构设计
- **📦 模块化设计**：清晰的代码结构
- **🔄 多线程架构**：UI线程和工作线程分离
- **💾 智能缓存**：LRU缓存策略，内存优化
- **🛡️ 异常处理**：完善的错误处理机制
- **📝 日志系统**：详细的运行日志

### 性能优化
- **⚡ 异步加载**：缩略图异步生成
- **🧠 内存管理**：自动垃圾回收，防止内存泄漏
- **💽 磁盘缓存**：智能缓存策略
- **🎯 懒加载**：按需加载图片

## 💻 系统要求

### 最低要求
- **操作系统**：Windows 10 (1903+)
- **Python版本**：3.8+
- **内存**：4GB RAM
- **硬盘**：100MB 可用空间

### 推荐配置
- **操作系统**：Windows 11
- **Python版本**：3.10+
- **内存**：8GB+ RAM
- **硬盘**：1GB+ 可用空间（用于缓存）
- **显卡**：支持硬件加速

## 🐛 故障排除

### 常见问题

**❓ 程序无法启动**
```bash
# 检查Python版本
python --version

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

**❓ RAW格式无法显示**
```bash
# 安装rawpy库
pip install rawpy
```

**❓ 缩略图生成缓慢**
- 在设置中减少缩略图大小
- 增加缓存大小
- 减少初始加载数量

**❓ 内存占用过高**
- 减少初始加载图片数量
- 清除缓存
- 重启程序

### 日志文件
程序运行日志保存在 `image_manager.log` 文件中，可用于问题诊断。

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置
```bash
# 1. 克隆项目
git clone <项目地址>

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装开发依赖
pip install -r requirements.txt

# 4. 运行测试
python test_basic.py
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **Pillow**：强大的图像处理库
- **rawpy**：优秀的RAW格式支持
- **PyQt5**：跨平台GUI框架
- **所有贡献者**：感谢每一位贡献者的努力

---

<div align="center">

**🌟 如果这个项目对你有帮助，请给个Star！🌟**

Made with ❤️ by [开发者]

</div>