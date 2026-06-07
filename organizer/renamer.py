"""批量重命名 - 按规则批量修改文件名"""

import re
from datetime import datetime
from pathlib import Path


def batch_rename(directory: Path, pattern: str = "date", custom_text: str = "",
                 dry_run: bool = True) -> list:
    """
    对目录下的所有文件执行批量重命名。

    支持的模式：
    - "date"      → 在文件名前加日期前缀，如 "2026-06-07_report.pdf"
    - "number"    → 用序号重命名，如 "001.jpg", "002.jpg"
    - "lower"     → 全部转小写
    - "replace"   → 替换文件名中的指定文字（需配合 custom_text）

    custom_text 格式：
    - pattern="date" 时：不传则用当前日期，也可以传自定义前缀
    - pattern="replace" 时：传 "旧文字->新文字"，如 "截图->screenshot"
    - pattern="number" 时：传前缀文字，如 "photo_"

    Args:
        directory: 目标目录
        pattern: 重命名模式
        custom_text: 附加参数
        dry_run: True=只预览，False=真正执行

    Returns:
        [(旧文件名, 新文件名), ...] 重命名操作记录
    """
    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(f"路径不存在或不是文件夹：{directory}")

    # 获取所有文件（不递归）
    files = sorted(
        [f for f in directory.iterdir() if f.is_file() and not f.name.startswith(".")],
        key=lambda f: f.name
    )

    if pattern == "date":
        prefix = custom_text if custom_text else datetime.now().strftime("%Y-%m-%d")
        rename_pairs = _rename_with_date(files, prefix)

    elif pattern == "number":
        prefix = custom_text if custom_text else ""
        rename_pairs = _rename_with_number(files, prefix)

    elif pattern == "lower":
        rename_pairs = _rename_to_lower(files)

    elif pattern == "replace":
        if "->" not in custom_text:
            raise ValueError("replace 模式需要传 '旧文字->新文字' 格式的 custom_text")
        old, new = custom_text.split("->", 1)
        rename_pairs = _rename_replace(files, old, new)

    else:
        raise ValueError(f"不支持的重命名模式：{pattern}，可选：date, number, lower, replace")

    # 执行重命名
    results = []
    for old_path, new_name in rename_pairs:
        new_path = old_path.parent / new_name

        # 检查是否会覆盖已有文件
        if new_path.exists() and new_path != old_path:
            print(f"  ⚠ 跳过（目标已存在）：{old_path.name} → {new_name}")
            continue

        if not dry_run:
            old_path.rename(new_path)

        results.append((old_path.name, new_name))

    return results


def _rename_with_date(files: list, prefix: str) -> list:
    """在文件名前加日期/前缀"""
    pairs = []
    for f in files:
        new_name = f"{prefix}_{f.name}"
        pairs.append((f, new_name))
    return pairs


def _rename_with_number(files: list, prefix: str) -> list:
    """用序号重命名，保持原扩展名"""
    # 计算需要几位数字（001, 002, ...）
    digits = max(3, len(str(len(files))))
    pairs = []
    for i, f in enumerate(files, start=1):
        new_name = f"{prefix}{i:0{digits}d}{f.suffix}"
        pairs.append((f, new_name))
    return pairs


def _rename_to_lower(files: list) -> list:
    """全部转小写"""
    pairs = []
    for f in files:
        new_name = f.name.lower()
        if new_name != f.name:
            pairs.append((f, new_name))
    return pairs


def _rename_replace(files: list, old: str, new: str) -> list:
    """替换文件名中的文字"""
    pairs = []
    for f in files:
        stem = f.stem  # 不含扩展名的部分
        if old in stem:
            new_stem = stem.replace(old, new)
            new_name = new_stem + f.suffix
            pairs.append((f, new_name))
    return pairs
