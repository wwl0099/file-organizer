"""命令行界面 - 解析用户命令并调用对应功能"""

import argparse
import sys
import os
from pathlib import Path
from organizer import __version__

# 修复 Windows 控制台编码问题（否则 emoji 会报错）
if sys.platform == "win32":
    os.system("chcp 65001 >nul")  # 切换控制台到 UTF-8 编码
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 使用 rich 库的 print，自动处理编码问题
from rich.console import Console
from rich.table import Table
console = Console()


def build_parser() -> argparse.ArgumentParser:
    """
    构建命令行参数解析器。

    支持的命令：
        scan      扫描并预览文件分类
        organize  执行文件整理
        rename    批量重命名
        dedup     查找重复文件
        full      一键整理（分类 + 去重 + 报告）
        undo      撤销上次整理
    """
    parser = argparse.ArgumentParser(
        prog="文件整理大师",
        description="📁 文件整理大师 - 一键整理杂乱的文件夹，支持分类、重命名、去重",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python -m organizer scan ~/Downloads          # 预览下载文件夹的文件分类
  python -m organizer organize ~/Downloads      # 整理下载文件夹
  python -m organizer organize ~/Downloads --go  # 真正执行（不加 --go 只是预览）
  python -m organizer dedup ~/Pictures          # 查找图片文件夹的重复文件
  python -m organizer rename ~/Photos -p date   # 给照片加日期前缀
  python -m organizer full ~/Desktop --go       # 一键整理桌面
        """,
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"文件整理大师 v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ---- scan 命令 ----
    scan_parser = subparsers.add_parser("scan", help="扫描目录，预览文件分类")
    scan_parser.add_argument("directory", type=str, help="要扫描的目录路径")
    scan_parser.add_argument("-c", "--config", type=str, help="自定义配置文件路径")

    # ---- organize 命令 ----
    org_parser = subparsers.add_parser("organize", help="整理目录中的文件")
    org_parser.add_argument("directory", type=str, help="要整理的目录路径")
    org_parser.add_argument("--go", action="store_true",
                            help="真正执行移动操作（不加此参数只是预览）")
    org_parser.add_argument("-c", "--config", type=str, help="自定义配置文件路径")

    # ---- rename 命令 ----
    rename_parser = subparsers.add_parser("rename", help="批量重命名文件")
    rename_parser.add_argument("directory", type=str, help="要重命名的目录路径")
    rename_parser.add_argument("-p", "--pattern", type=str, default="date",
                               choices=["date", "number", "lower", "replace"],
                               help="重命名模式：date(加日期) number(序号) lower(小写) replace(替换)")
    rename_parser.add_argument("-t", "--text", type=str, default="",
                               help="附加文本（date=前缀, number=前缀, replace=旧->新）")
    rename_parser.add_argument("--go", action="store_true",
                               help="真正执行重命名操作")

    # ---- dedup 命令 ----
    dedup_parser = subparsers.add_parser("dedup", help="查找重复文件")
    dedup_parser.add_argument("directory", type=str, help="要扫描重复文件的目录")
    dedup_parser.add_argument("--delete", action="store_true",
                              help="删除重复文件（保留最新的那份）")
    dedup_parser.add_argument("-s", "--strategy", type=str, default="keep_newest",
                              choices=["list", "keep_newest", "keep_oldest", "keep_largest"],
                              help="处理策略：list=只列 keep_newest=留新删旧 keep_oldest=留旧删新 keep_largest=留大删小")

    # ---- full 命令（一键全搞定）----
    full_parser = subparsers.add_parser("full", help="一键整理：分类 + 去重 + 报告")
    full_parser.add_argument("directory", type=str, help="要整理的目录路径")
    full_parser.add_argument("--go", action="store_true",
                             help="真正执行（不加此参数只是预览）")

    # ---- undo 命令 ----
    undo_parser = subparsers.add_parser("undo", help="撤销上次整理操作")
    undo_parser.add_argument("directory", type=str, help="要撤销整理的目录路径")

    return parser


def main():
    """命令行入口主函数"""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 根据子命令分发到对应处理函数
    if args.command == "scan":
        cmd_scan(args)

    elif args.command == "organize":
        cmd_organize(args)

    elif args.command == "rename":
        cmd_rename(args)

    elif args.command == "dedup":
        cmd_dedup(args)

    elif args.command == "full":
        cmd_full(args)

    elif args.command == "undo":
        cmd_undo(args)


# ============================================================
#  各命令的具体实现
# ============================================================

def cmd_scan(args):
    """扫描命令：预览文件分类情况"""
    from organizer.scanner import scan_directory, get_stats
    from organizer.utils import load_config

    directory = Path(args.directory)
    config = load_config(Path(args.config)) if args.config else load_config()

    console.print(f"\n🔍 正在扫描：{directory}\n")

    categorized = scan_directory(directory, config)
    stats = get_stats(categorized)

    # 打印统计信息
    console.print(f"  总文件数：{stats['总文件数']}")
    console.print(f"  已分类  ：{stats['已分类']}")
    console.print(f"  未分类  ：{stats['未分类']}")
    console.print(f"\n{'─' * 40}")

    for cat_name, files in sorted(categorized.items()):
        if not files:
            continue
        emoji = _cat_emoji(cat_name)
        console.print(f"\n  {emoji} {cat_name}（{len(files)} 个）")
        for f in files[:10]:  # 每类最多显示 10 个
            size_mb = f.stat().st_size / (1024 * 1024)
            console.print(f"      {f.name}  ({size_mb:.1f} MB)")
        if len(files) > 10:
            console.print(f"      ... 还有 {len(files) - 10} 个文件")

    console.print(f"\n{'─' * 40}")
    console.print("💡 提示：运行 organize 命令来执行整理\n")


def cmd_organize(args):
    """整理命令：将文件移动到分类子文件夹"""
    from organizer.organizer import organize_files
    from organizer.utils import load_config, format_size

    directory = Path(args.directory)
    config = load_config(Path(args.config)) if args.config else load_config()
    dry_run = not args.go  # 默认预览模式

    if dry_run:
        console.print(f"\n🔍 【预览模式】正在分析：{directory}")
        console.print("   （加 --go 参数才会真正移动文件）\n")
    else:
        console.print(f"\n🚀 正在整理：{directory}\n")

    moves = organize_files(directory, config, dry_run=dry_run)

    if not moves:
        console.print("  ✅ 没有需要移动的文件！")
        return

    # 按分类统计
    from collections import defaultdict
    cat_stats = defaultdict(lambda: {"count": 0, "size": 0})
    for _, dest, size in moves:
        cat = dest.parent.name
        cat_stats[cat]["count"] += 1
        cat_stats[cat]["size"] += size

    total_size = sum(size for _, _, size in moves)

    for cat, stats in sorted(cat_stats.items()):
        console.print(f"  📁 {cat}: {stats['count']} 个文件 → {format_size(stats['size'])}")

    console.print(f"\n  📦 共 {len(moves)} 个文件，总计 {format_size(total_size)}")

    if dry_run:
        console.print("\n💡 这是预览结果，加 --go 参数执行真正的整理\n")
    else:
        console.print("\n✅ 整理完成！\n")


def cmd_rename(args):
    """重命名命令：批量修改文件名"""
    from organizer.renamer import batch_rename

    directory = Path(args.directory)
    dry_run = not args.go

    if dry_run:
        console.print(f"\n🔍 【预览模式】模式：{args.pattern}")
        console.print("   （加 --go 参数才会真正重命名）\n")
    else:
        console.print(f"\n✏️  正在重命名，模式：{args.pattern}\n")

    results = batch_rename(directory, pattern=args.pattern,
                           custom_text=args.text, dry_run=dry_run)

    if not results:
        console.print("  没有文件需要重命名")
        return

    for old, new in results:
        console.print(f"  {old} → {new}")

    console.print(f"\n  共 {len(results)} 个文件")

    if dry_run:
        console.print("💡 这是预览结果，加 --go 参数执行真正的重命名\n")
    else:
        console.print("✅ 重命名完成！\n")


def cmd_dedup(args):
    """去重命令：查找和删除重复文件"""
    from organizer.dedup import find_duplicates, handle_duplicates
    from organizer.utils import format_size

    directory = Path(args.directory)

    console.print(f"\n🔍 正在查找重复文件：{directory}\n")

    duplicates = find_duplicates(directory)

    if not duplicates:
        console.print("  ✅ 没有发现重复文件！\n")
        return

    total_dup = sum(len(files) - 1 for files in duplicates.values())
    console.print(f"  ⚠ 发现 {len(duplicates)} 组重复，共 {total_dup} 个冗余文件\n")

    if args.delete:
        strategy = args.strategy
        console.print(f"  处理策略：{strategy}\n")
        actions = handle_duplicates(duplicates, strategy=strategy, dry_run=False)

        freed = sum(dup.stat().st_size for _, dup in actions)
        for keep, deleted in actions:
            console.print(f"  🗑  {deleted.name}  (保留: {keep.name})")

        console.print(f"\n  💾 释放空间：{format_size(freed)}")
        console.print("✅ 重复文件已清理！\n")
    else:
        # 只列出
        for file_hash, files in duplicates.items():
            total_size = sum(f.stat().st_size for f in files)
            console.print(f"  重复组（{format_size(total_size)}，{len(files)} 个副本）:")
            for f in files:
                console.print(f"      {f.name}")
            console.print()

        console.print(f"💡 加 --delete 参数来删除重复文件\n")


def cmd_full(args):
    """一键整理：分类 + 去重 + 报告"""
    from organizer.organizer import organize_files
    from organizer.dedup import find_duplicates, handle_duplicates
    from organizer.reporter import generate_report
    from organizer.utils import load_config

    directory = Path(args.directory)
    config = load_config()
    dry_run = not args.go

    if dry_run:
        console.print(f"\n🔍 【预览模式】完整整理：{directory}")
        console.print("   （加 --go 参数才会真正执行）\n")
    else:
        console.print(f"\n🚀 完整整理开始：{directory}\n")

    # 步骤 1：分类整理
    console.print("━" * 40)
    console.print("  步骤 1/3：文件分类...")
    moves = organize_files(directory, config, dry_run=dry_run)
    if moves:
        console.print(f"  ✅ {len(moves)} 个文件将被分类")

    # 步骤 2：查找重复
    console.print("\n  步骤 2/3：查找重复文件...")
    duplicates = find_duplicates(directory)
    dedup_actions = []
    if duplicates:
        dedup_actions = handle_duplicates(duplicates, strategy="keep_newest",
                                          dry_run=dry_run)
        if dedup_actions:
            console.print(f"  ⚠ 发现 {len(dedup_actions)} 个重复文件")
    if not duplicates:
        console.print("  ✅ 没有重复文件")

    # 步骤 3：生成报告
    console.print("\n  步骤 3/3：生成报告...")
    report = generate_report(moves, dedup_actions, directory=directory)
    console.print(report)

    if dry_run:
        console.print("\n💡 这是预览结果，加 --go 参数执行真正的整理\n")
    else:
        console.print("\n✅ 全部整理完成！\n")


def cmd_undo(args):
    """撤销命令：撤销整理操作"""
    console.print("\n⚠ 撤销功能需要之前整理的记录文件")
    console.print("  （此功能需要完善，暂时不可用）\n")


def _cat_emoji(cat_name: str) -> str:
    """给分类分配一个可爱的 emoji"""
    emoji_map = {
        "Images": "🖼️",
        "Documents": "📄",
        "Audio": "🎵",
        "Video": "🎬",
        "Archives": "📦",
        "Code": "💻",
        "Programs": "⚙️",
        "unknown": "❓",
    }
    return emoji_map.get(cat_name, "📎")
