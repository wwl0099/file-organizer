"""重复检测 - 用 MD5 哈希找出重复文件"""

import hashlib
from pathlib import Path
from collections import defaultdict


def find_duplicates(directory: Path, min_size: int = 0) -> dict:
    """
    扫描目录，用 MD5 哈希找出重复文件。

    工作原理：
    1. 先按文件大小分组（大小不同的肯定不是重复）
    2. 对同大小文件计算 MD5 哈希
    3. 哈希相同的文件就是重复文件

    Args:
        directory: 要扫描的目录
        min_size: 忽略小于此大小的文件（字节），默认 0 即不忽略

    Returns:
        {
            "hash_value_1": [Path("a.txt"), Path("b_copy.txt")],
            "hash_value_2": [Path("photo.jpg"), Path("photo (1).jpg")],
            ...
        }
        只有重复（≥2个文件）的才会出现在结果中
    """
    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(f"路径不存在或不是文件夹：{directory}")

    # 第一步：按文件大小分组
    size_map = defaultdict(list)
    for item in directory.iterdir():
        if item.is_file() and not item.name.startswith("."):
            size = item.stat().st_size
            if size >= min_size:
                size_map[size].append(item)

    # 第二步：对同大小的文件计算 MD5
    hash_map = defaultdict(list)
    for size, files in size_map.items():
        if len(files) < 2:
            continue  # 只有一个文件的大小，不可能有重复

        for file_path in files:
            file_hash = _md5(file_path)
            hash_map[file_hash].append(file_path)

    # 第三步：只保留有重复的（≥2 个文件 hash 相同）
    duplicates = {
        h: files for h, files in hash_map.items()
        if len(files) >= 2
    }

    return duplicates


def handle_duplicates(duplicates: dict, strategy: str = "keep_newest",
                      dry_run: bool = True) -> list:
    """
    处理找到的重复文件。

    Args:
        duplicates: find_duplicates() 的返回结果
        strategy: 处理策略
            - "list"         只列出，不操作
            - "keep_newest"  保留最新的，删除旧的
            - "keep_oldest"  保留最旧的，删除新的
            - "keep_largest" 保留最大的文件
        dry_run: True=只预览不删除

    Returns:
        [(保留文件, 被删除文件), ...]
    """
    actions = []

    for file_hash, files in duplicates.items():
        if len(files) < 2:
            continue

        # 按选定策略排序，第一个是要保留的
        if strategy == "keep_newest":
            sorted_files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
        elif strategy == "keep_oldest":
            sorted_files = sorted(files, key=lambda f: f.stat().st_mtime)
        elif strategy == "keep_largest":
            sorted_files = sorted(files, key=lambda f: f.stat().st_size, reverse=True)
        else:  # "list" 模式
            continue

        keep = sorted_files[0]
        to_delete = sorted_files[1:]

        for dup in to_delete:
            if not dry_run:
                dup.unlink()  # 真正删除文件

            actions.append((keep, dup))

    return actions


def _md5(file_path: Path, chunk_size: int = 8192) -> str:
    """
    计算文件的 MD5 哈希值。

    分块读取，大文件也不会占太多内存。

    Args:
        file_path: 文件路径
        chunk_size: 每次读取的字节数

    Returns:
        MD5 哈希的十六进制字符串
    """
    md5_hash = hashlib.md5()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            md5_hash.update(chunk)

    return md5_hash.hexdigest()
