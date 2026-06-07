"""扫描器 - 扫描目录并按类型分类文件"""

from pathlib import Path
from collections import defaultdict
from organizer.utils import load_config


def scan_directory(directory: Path, config: dict = None) -> dict:
    """
    扫描指定目录，将文件按类型归类。

    Args:
        directory: 要扫描的目录路径
        config: 配置字典（可选，不传则自动加载）

    Returns:
        {
            "图片": [Path("photo1.jpg"), Path("photo2.png"), ...],
            "文档": [Path("report.pdf"), ...],
            ...
            "unknown": [Path("weird.xyz"), ...]
        }
    """
    if config is None:
        config = load_config()

    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(f"路径不存在或不是文件夹：{directory}")

    # 初始化：每个分类一个空列表
    categories = {cat: [] for cat in config["categories"]}
    categories["unknown"] = []

    # 遍历目录下所有文件（不递归子目录）
    for item in directory.iterdir():
        # 跳过目录、隐藏文件和配置文件本身
        if not item.is_file():
            continue
        if item.name.startswith("."):
            continue

        # 获取文件扩展名（统一小写方便比较）
        ext = item.suffix.lower()

        # 在配置的分类规则中查找匹配
        matched = False
        for cat_name, cat_info in config["categories"].items():
            if ext in cat_info["extensions"]:
                categories[cat_name].append(item)
                matched = True
                break

        # 没有匹配到任何分类 → 放到 unknown
        if not matched:
            categories["unknown"].append(item)

    return categories


def get_stats(categorized: dict) -> dict:
    """
    统计分类结果。

    Args:
        categorized: scan_directory() 的返回结果

    Returns:
        {"总文件数": 42, "已分类": 38, "未分类": 4, "各分类统计": {...}}
    """
    stats = {}
    total = 0
    classified = 0

    for cat_name, files in categorized.items():
        count = len(files)
        stats[cat_name] = count
        total += count
        if cat_name != "unknown":
            classified += count

    return {
        "总文件数": total,
        "已分类": classified,
        "未分类": stats.get("unknown", 0),
        "各分类统计": stats,
    }
