"""
文件整理大师 (File Organizer Master)
=====================================
一款 Python 命令行工具，帮你自动整理杂乱的文件夹。

功能：
- 📂 智能分类：按文件类型自动归类到子文件夹
- ✏️  批量重命名：按规则批量修改文件名
- 🔍 重复检测：用 MD5 哈希找出并清理重复文件
- 📊 整理报告：生成漂亮的操作汇总报告

用法：
    python -m organizer scan <目录>       # 扫描并预览
    python -m organizer organize <目录>   # 执行整理
    python -m organizer dedup <目录>      # 查找重复文件
    python -m organizer rename <目录>     # 批量重命名
    python -m organizer full <目录>       # 一键全搞定
"""

__version__ = "1.0.0"
