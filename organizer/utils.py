"""工具函数 - 加载配置、文件大小换算等"""

import sys
import os
from pathlib import Path
import yaml


def load_config(config_path: Path = None) -> dict:
    """
    加载 YAML 配置文件。

    Args:
        config_path: 配置文件路径，默认使用项目根目录的 config.yaml

    Returns:
        解析后的配置字典
    """
    if config_path is None:
        # PyInstaller 打包后，文件在临时目录（sys._MEIPASS）
        if getattr(sys, "frozen", False):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent.parent
        config_path = base_dir / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"找不到配置文件：{config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_size(size_bytes: int) -> str:
    """
    把字节数转成人类可读的大小。

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的字符串，如 "1.5 MB"
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在就创建。

    Args:
        path: 目标路径

    Returns:
        创建后的路径（方便链式调用）
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    """
    把文件名中的非法字符替换掉，确保能安全创建文件。

    Args:
        name: 原始文件名

    Returns:
        安全的文件名
    """
    # Windows 文件名不能包含这些字符
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        name = name.replace(char, "_")
    return name.strip()
