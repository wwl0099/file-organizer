"""核心整理器 - 将散乱的文件移动到分类子文件夹中"""

import shutil
from pathlib import Path
from organizer.utils import load_config, ensure_dir


def organize_files(directory: Path, config: dict = None, dry_run: bool = True) -> list:
    """
    把目录中的文件按类型整理到子文件夹。

    工作原理：
    1. 扫描目录，识别每个文件的类型
    2. 在目录下创建子文件夹（如 "图片"、"文档"）
    3. 把文件移动到对应的子文件夹

    Args:
        directory: 要整理的目标目录
        config: 配置字典（可选）
        dry_run: True=只预览不移动, False=真正移动

    Returns:
        [(源路径, 目标路径, 文件大小), ...] 每次移动操作的记录
    """
    # 延迟导入，避免循环依赖
    from organizer.scanner import scan_directory

    if config is None:
        config = load_config()

    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(f"路径不存在或不是文件夹：{directory}")

    # 第一步：扫描分类
    categorized = scan_directory(directory, config)
    settings = config.get("settings", {})

    # 第二步：对每个分类创建子文件夹并移动文件
    moves = []

    for cat_name, files in categorized.items():
        if not files:  # 跳过空分类
            continue

        # 确定目标子文件夹名字
        if cat_name == "unknown":
            folder_name = settings.get("unknown_folder_name", "其他")
        else:
            folder_name = config["categories"][cat_name]["folder"]

        dest_dir = directory / folder_name

        # 只在有文件时才创建文件夹
        if not dry_run:
            ensure_dir(dest_dir)

        for file_path in files:
            dest_path = dest_dir / file_path.name

            # 如果目标位置已经有同名文件，加个序号避免覆盖
            if dest_path.exists() and not dry_run:
                dest_path = _avoid_overwrite(dest_path)

            size = file_path.stat().st_size

            if not dry_run:
                shutil.move(str(file_path), str(dest_path))

            moves.append((file_path, dest_path, size))

    return moves


def _avoid_overwrite(path: Path) -> Path:
    """
    如果文件已存在，在文件名后添加序号避免覆盖。
    如：report.pdf → report (1).pdf
    """
    stem = path.stem      # 文件名（不含扩展名）
    suffix = path.suffix  # 扩展名
    parent = path.parent
    counter = 1

    while path.exists():
        path = parent / f"{stem} ({counter}){suffix}"
        counter += 1

    return path


def undo_organize(moves: list) -> list:
    """
    撤销整理操作：把文件移回原来的位置。

    Args:
        moves: organize_files() 返回的移动记录

    Returns:
        成功撤销的移动记录列表
    """
    undone = []
    for source, dest, _ in moves:
        if dest.exists():
            shutil.move(str(dest), str(source))
            undone.append((source, dest))
    return undone
