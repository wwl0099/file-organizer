"""报告生成器 - 生成整理操作汇总报告"""

from pathlib import Path
from datetime import datetime
from organizer.utils import format_size


def generate_report(moves: list, dedup_actions: list = None,
                    renames: list = None, directory: Path = None) -> str:
    """
    根据整理操作生成汇总报告。

    Args:
        moves: organize_files() 返回的移动记录列表
        dedup_actions: handle_duplicates() 返回的删除记录列表（可选）
        renames: batch_rename() 返回的重命名记录列表（可选）
        directory: 被整理的目录路径（可选）

    Returns:
        格式化的报告文本
    """
    report_num = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(f"整理报告_{report_num}.txt")

    lines = []
    lines.append("=" * 60)
    lines.append("          📁 文件整理大师 - 操作报告")
    lines.append("=" * 60)
    lines.append(f"  整理目录 : {directory or '(未指定)'}")
    lines.append(f"  执行时间 : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    # --- 文件分类整理 ---
    if moves:
        lines.append(f"📂 文件分类整理（共移动 {len(moves)} 个文件）")
        lines.append("-" * 40)

        total_size = sum(size for _, _, size in moves)

        # 按分类统计
        from collections import defaultdict
        cat_stats = defaultdict(lambda: {"count": 0, "size": 0})
        for _, dest, size in moves:
            cat = dest.parent.name
            cat_stats[cat]["count"] += 1
            cat_stats[cat]["size"] += size

        for cat, stats in sorted(cat_stats.items()):
            lines.append(f"  📁 {cat}: {stats['count']} 个文件 ({format_size(stats['size'])})")

        lines.append(f"  📦 总大小: {format_size(total_size)}")
        lines.append("")

    # --- 重复文件 ---
    if dedup_actions:
        lines.append(f"🔍 重复文件清理（共删除 {len(dedup_actions)} 个重复文件）")
        lines.append("-" * 40)

        freed = sum(dup.stat().st_size for _, dup in dedup_actions)
        for keep, deleted in dedup_actions[:20]:  # 最多显示 20 条
            lines.append(f"  🗑  {deleted.name}  (保留: {keep.name})")

        if len(dedup_actions) > 20:
            lines.append(f"  ... 还有 {len(dedup_actions) - 20} 条记录")

        lines.append(f"  💾 释放空间: {format_size(freed)}")
        lines.append("")

    # --- 重命名 ---
    if renames:
        lines.append(f"✏️  批量重命名（共 {len(renames)} 个文件）")
        lines.append("-" * 40)
        for old, new in renames[:20]:
            lines.append(f"  {old} → {new}")
        if len(renames) > 20:
            lines.append(f"  ... 还有 {len(renames) - 20} 条记录")
        lines.append("")

    lines.append("=" * 60)
    lines.append("  ✅ 整理完成！")
    lines.append("=" * 60)

    report_text = "\n".join(lines)

    # 保存报告到文件
    report_path.write_text(report_text, encoding="utf-8")
    print(f"\n📄 报告已保存：{report_path}")

    return report_text
