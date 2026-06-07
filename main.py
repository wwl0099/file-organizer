"""
文件整理大师 - 主入口
=====================
- 双击运行：交互式菜单，选择文件夹一键整理
- 命令行运行：python main.py scan ~/Downloads
"""

import sys
import os
from pathlib import Path

# 修复 Windows 控制台编码
if sys.platform == "win32":
    os.system("chcp 65001 >nul")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def interactive_mode():
    """双击运行时进入交互菜单模式"""
    print("\n" + "=" * 50)
    print("       📁 文件整理大师 v1.0")
    print("       一键整理你的文件夹！")
    print("=" * 50)

    # 让用户输入要整理的目录
    while True:
        path_input = input("\n📂 请输入要整理的文件夹路径（或拖拽文件夹到这里）: ").strip().strip('"').strip("'")
        if path_input:
            target = Path(path_input)
            if target.is_dir():
                break
            else:
                print(f"   ⚠ 文件夹不存在: {path_input}")
        else:
            print("   ⚠ 请输入一个路径")

    # 显示功能菜单
    while True:
        print(f"\n📁 目标文件夹: {target}")
        print("-" * 40)
        print("  1. 🔍 扫描预览（看看里面有什么）")
        print("  2. 📂 整理文件（按类型归类）")
        print("  3. 🔎 查找重复文件")
        print("  4. 🚀 一键全搞定（分类+去重+报告）")
        print("  5. ✏️  批量重命名")
        print("  6. 🔄 换个文件夹")
        print("  0. ❌ 退出")
        print("-" * 40)

        choice = input("请选择 (1-6): ").strip()

        if choice == "0":
            print("\n👋 再见！")
            break
        elif choice == "6":
            interactive_mode()
            return
        elif choice in ("1", "2", "3", "4", "5"):
            run_action(choice, str(target))
        else:
            print("   ⚠ 请输入 0-6")

    input("\n按 Enter 键关闭窗口...")


def run_action(choice: str, directory: str):
    """执行用户选择的操作"""
    from organizer.cli import main as cli_main
    import argparse

    # 构造对应的命令行参数
    action_map = {
        "1": ["scan", directory],
        "2": ["organize", directory, "--go"],
        "3": ["dedup", directory],
        "4": ["full", directory, "--go"],
        "5": ["rename", directory],
    }

    args = action_map[choice]

    if choice == "5":
        # 重命名需要更多选项
        print("\n  重命名模式:")
        print("    1. 加日期前缀")
        print("    2. 序号编号")
        print("    3. 全部小写")
        print("    4. 替换文字")
        rename_choice = input("  请选择 (1-4): ").strip()
        rename_map = {"1": "date", "2": "number", "3": "lower", "4": "replace"}
        pattern = rename_map.get(rename_choice, "date")
        args.append("-p")
        args.append(pattern)

        if rename_choice == "4":
            old = input("  要替换的文字: ").strip()
            new = input("  替换成: ").strip()
            args.append("-t")
            args.append(f"{old}->{new}")
        elif rename_choice == "2":
            prefix = input("  文件名前缀（如 旅行_）: ").strip()
            args.append("-t")
            args.append(prefix)

        args.append("--go")

    # 调用 CLI 主函数
    sys.argv = ["文件整理大师"] + args
    cli_main()


def cli_mode():
    """命令行模式：python main.py scan ~/Downloads"""
    from organizer.cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    # 如果有命令行参数 → 命令行模式
    # 如果双击运行（无参数）→ 交互菜单模式
    if len(sys.argv) > 1:
        cli_mode()
    else:
        interactive_mode()
