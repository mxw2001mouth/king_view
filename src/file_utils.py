#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件工具模块
提供文件操作相关的工具函数，特别是安全删除到回收站的功能
"""

import os
import sys
import logging
import subprocess

def move_to_recycle_bin(file_path: str) -> bool:
    """
    将文件移动到回收站
    优先使用send2trash库，如果不可用则使用系统API
    确保在打包环境中不会弹出命令窗口
    """
    try:
        if not os.path.exists(file_path):
            logging.warning(f"文件不存在: {file_path}")
            return False
        
        # 标准化路径格式，避免路径分隔符问题
        normalized_path = os.path.normpath(file_path)
            
        if os.name == 'nt':  # Windows
            # 方法1: 优先使用send2trash库
            try:
                import send2trash
                # 确保路径格式正确
                send2trash.send2trash(normalized_path)
                logging.info(f"使用send2trash成功删除: {normalized_path}")
                return True
            except ImportError:
                logging.warning("send2trash库不可用，尝试使用系统API")
            except Exception as e:
                logging.error(f"send2trash删除失败: {e}")
                # send2trash失败时，直接尝试系统API，不再重试
            
            # 方法2: 使用Windows Shell32 API（推荐）
            try:
                import ctypes
                from ctypes import wintypes
                
                # 定义SHFILEOPSTRUCT结构
                class SHFILEOPSTRUCT(ctypes.Structure):
                    _fields_ = [
                        ("hwnd", wintypes.HWND),
                        ("wFunc", wintypes.UINT),
                        ("pFrom", wintypes.LPCWSTR),
                        ("pTo", wintypes.LPCWSTR),
                        ("fFlags", wintypes.WORD),
                        ("fAnyOperationsAborted", wintypes.BOOL),
                        ("hNameMappings", wintypes.LPVOID),
                        ("lpszProgressTitle", wintypes.LPCWSTR)
                    ]
                
                # 常量定义
                FO_DELETE = 3
                FOF_ALLOWUNDO = 0x40  # 允许撤销（移动到回收站）
                FOF_NOCONFIRMATION = 0x10  # 不显示确认对话框
                FOF_SILENT = 0x04  # 静默操作
                
                # 调用SHFileOperation
                shell32 = ctypes.windll.shell32
                file_op = SHFILEOPSTRUCT()
                file_op.hwnd = None
                file_op.wFunc = FO_DELETE
                # 使用标准化路径，确保格式正确
                file_op.pFrom = normalized_path + '\0\0'  # 必须以双null结尾
                file_op.pTo = None
                file_op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
                file_op.fAnyOperationsAborted = False
                file_op.hNameMappings = None
                file_op.lpszProgressTitle = None
                
                result = shell32.SHFileOperationW(ctypes.byref(file_op))
                if result == 0:
                    logging.info(f"使用Shell32 API成功删除: {normalized_path}")
                    return True
                else:
                    logging.error(f"Shell32 API删除失败，错误代码: {result}")
                    
            except Exception as e:
                logging.error(f"Shell32 API调用失败: {e}")
            
            # 方法3: 使用PowerShell（隐藏窗口）
            try:
                # 转换路径分隔符为PowerShell兼容格式
                ps_path = normalized_path.replace('\\', '\\\\')
                cmd = f'Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("{ps_path}", "OnlyErrorDialogs", "SendToRecycleBin")'
                
                # 创建启动信息，隐藏窗口
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # 执行PowerShell命令，确保隐藏窗口
                result = subprocess.run(
                    ['powershell.exe', '-WindowStyle', 'Hidden', '-NoProfile', '-Command', cmd], 
                    check=True, 
                    capture_output=True, 
                    text=True,
                    startupinfo=startupinfo, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                logging.info(f"使用PowerShell成功删除: {normalized_path}")
                return True
                
            except subprocess.CalledProcessError as e:
                logging.error(f"PowerShell删除失败: {e.stderr}")
            except Exception as e:
                logging.error(f"PowerShell调用失败: {e}")
                
        else:  # macOS/Linux
            # 方法1: 优先使用send2trash库
            try:
                import send2trash
                send2trash.send2trash(normalized_path)
                logging.info(f"使用send2trash成功删除: {normalized_path}")
                return True
            except ImportError:
                logging.warning("send2trash库不可用，尝试使用系统命令")
            except Exception as e:
                logging.error(f"send2trash删除失败: {e}")
            
            # 方法2: Linux使用gio trash
            if sys.platform.startswith('linux'):
                try:
                    subprocess.run(['gio', 'trash', normalized_path], check=True, capture_output=True)
                    logging.info(f"使用gio trash成功删除: {normalized_path}")
                    return True
                except subprocess.CalledProcessError as e:
                    logging.error(f"gio trash删除失败: {e}")
                except FileNotFoundError:
                    logging.warning("gio命令不可用")
                except Exception as e:
                    logging.error(f"gio trash调用失败: {e}")
            
            # 方法3: macOS使用osascript
            elif sys.platform == 'darwin':
                try:
                    script = f'tell application "Finder" to delete POSIX file "{normalized_path}"'
                    subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
                    logging.info(f"使用osascript成功删除: {normalized_path}")
                    return True
                except subprocess.CalledProcessError as e:
                    logging.error(f"osascript删除失败: {e}")
                except Exception as e:
                    logging.error(f"osascript调用失败: {e}")
        
        # 所有方法都失败
        logging.error(f"所有删除方法都失败: {normalized_path}")
        return False
        
    except Exception as e:
        logging.error(f"删除文件时发生未知错误: {e}")
        return False

def safe_delete_file(file_path: str) -> bool:
    """
    安全删除文件
    首先尝试移动到回收站，如果失败则直接删除
    """
    try:
        # 首先尝试移动到回收站
        if move_to_recycle_bin(file_path):
            return True
        
        # 如果移动到回收站失败，直接删除
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"直接删除文件: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"安全删除文件失败: {e}")
        return False