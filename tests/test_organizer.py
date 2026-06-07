"""测试文件整理大师的各项功能"""

import pytest
import tempfile
import shutil
from pathlib import Path

# 把项目根目录加到 import 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from organizer.scanner import scan_directory, get_stats
from organizer.organizer import organize_files
from organizer.renamer import batch_rename
from organizer.dedup import find_duplicates, handle_duplicates
from organizer.utils import load_config, format_size, safe_filename


# ============================================================
#  测试夹具：创建临时测试目录
# ============================================================

@pytest.fixture
def test_dir():
    """创建一个临时的测试目录，里面有各种类型的文件"""
    tmp = Path(tempfile.mkdtemp())

    # 创建不同类型的测试文件
    (tmp / "photo.jpg").touch()
    (tmp / "document.pdf").touch()
    (tmp / "song.mp3").touch()
    (tmp / "script.py").touch()
    (tmp / "weird.xyz").touch()
    (tmp / "notes.txt").touch()
    (tmp / "archive.zip").touch()

    yield tmp

    # 清理
    shutil.rmtree(tmp)


@pytest.fixture
def config():
    """加载默认配置"""
    return load_config()


# ============================================================
#  扫描器测试
# ============================================================

class TestScanner:
    """测试文件扫描和分类功能"""

    def test_scan_total_files(self, test_dir, config):
        """测试扫描能找到所有文件"""
        result = scan_directory(test_dir, config)
        total = sum(len(files) for files in result.values())
        assert total == 7, f"期望 7 个文件，实际 {total} 个"

    def test_scan_categorizes_images(self, test_dir, config):
        """测试图片文件被正确分类"""
        result = scan_directory(test_dir, config)
        image_files = [f.name for f in result["Images"]]
        assert "photo.jpg" in image_files

    def test_scan_categorizes_documents(self, test_dir, config):
        """测试文档文件被正确分类"""
        result = scan_directory(test_dir, config)
        doc_files = [f.name for f in result["Documents"]]
        assert "document.pdf" in doc_files
        assert "notes.txt" in doc_files

    def test_scan_categorizes_unknown(self, test_dir, config):
        """测试未知类型文件归到 unknown"""
        result = scan_directory(test_dir, config)
        unknown_files = [f.name for f in result["unknown"]]
        assert "weird.xyz" in unknown_files

    def test_get_stats(self, test_dir, config):
        """测试统计信息"""
        result = scan_directory(test_dir, config)
        stats = get_stats(result)
        assert stats["总文件数"] == 7
        assert stats["已分类"] == 6
        assert stats["未分类"] == 1

    def test_empty_directory(self, config):
        """测试空目录"""
        tmp = Path(tempfile.mkdtemp())
        try:
            result = scan_directory(tmp, config)
            total = sum(len(files) for files in result.values())
            assert total == 0
        finally:
            shutil.rmtree(tmp)

    def test_not_a_directory(self):
        """测试传入文件而非目录时抛出错误"""
        with pytest.raises(NotADirectoryError):
            scan_directory(Path("/this/path/does/not/exist"))


# ============================================================
#  整理器测试
# ============================================================

class TestOrganizer:
    """测试文件整理功能"""

    def test_dry_run_no_moves(self, test_dir, config):
        """测试预览模式不会真正移动文件"""
        result = scan_directory(test_dir, config)
        organize_files(test_dir, config, dry_run=True)

        # 文件应该还在原位置
        for files in result.values():
            for f in files:
                assert f.exists(), f"{f.name} 不应该被移动"

    def test_organize_moves_files(self, test_dir, config):
        """测试真正整理后文件已移动"""
        organize_files(test_dir, config, dry_run=False)

        # 检查子文件夹是否存在
        assert (test_dir / "图片").exists()
        assert (test_dir / "文档").exists()
        assert (test_dir / "音频").exists()
        assert (test_dir / "代码").exists()
        assert (test_dir / "压缩包").exists()

        # 检查文件是否在子文件夹中
        assert (test_dir / "图片" / "photo.jpg").exists()
        assert (test_dir / "文档" / "document.pdf").exists()

    def test_organize_returns_moves_list(self, test_dir, config):
        """测试 organize_files 返回移动记录"""
        moves = organize_files(test_dir, config, dry_run=True)
        assert len(moves) == 7
        # 每条记录包含 (源路径, 目标路径, 大小)
        assert len(moves[0]) == 3


# ============================================================
#  重命名测试
# ============================================================

class TestRenamer:
    """测试批量重命名功能"""

    def test_rename_date_pattern(self, test_dir):
        """测试日期前缀重命名"""
        results = batch_rename(test_dir, pattern="date", custom_text="2026-01-01", dry_run=True)
        # 应该为所有文件生成重命名计划
        assert len(results) == 7
        for old, new in results:
            assert new.startswith("2026-01-01_")

    def test_rename_number_pattern(self, test_dir):
        """测试序号重命名"""
        results = batch_rename(test_dir, pattern="number", custom_text="file_", dry_run=True)
        assert len(results) == 7
        for old, new in results:
            assert new.startswith("file_")

    def test_rename_lower_pattern(self, test_dir):
        """测试小写重命名 - 创建大写文件测试"""
        (test_dir / "UPPERCASE.TXT").touch()
        results = batch_rename(test_dir, pattern="lower", dry_run=True)
        # 应该只有大写的文件会被改名
        assert any("uppercase.txt" in new for _, new in results)

    def test_rename_replace_pattern(self, test_dir):
        """测试替换重命名"""
        (test_dir / "old_name.txt").touch()
        results = batch_rename(test_dir, pattern="replace",
                               custom_text="old->new", dry_run=True)
        assert any("new_name.txt" in new for _, new in results)

    def test_rename_actually_renames(self, test_dir):
        """测试真正执行重命名"""
        results = batch_rename(test_dir, pattern="date",
                               custom_text="test", dry_run=False)
        for old_name, new_name in results:
            new_path = test_dir / new_name
            assert new_path.exists(), f"重命名后的文件应存在: {new_name}"


# ============================================================
#  去重测试
# ============================================================

class TestDedup:
    """测试重复文件检测功能"""

    @pytest.fixture
    def clean_dir(self):
        """创建一个干净的临时目录，没有预置文件"""
        tmp = Path(tempfile.mkdtemp())
        yield tmp
        shutil.rmtree(tmp)

    def test_no_duplicates(self, clean_dir):
        """测试没有重复文件的情况"""
        # 创建内容各不相同的文件
        for i, content in enumerate(["a", "b", "c", "d", "e"]):
            (clean_dir / f"file{i}.txt").write_text(content)
        result = find_duplicates(clean_dir)
        assert len(result) == 0

    def test_find_duplicates(self, clean_dir):
        """测试能找到重复文件"""
        (clean_dir / "a.txt").write_text("hello world")
        (clean_dir / "b.txt").write_text("hello world")
        (clean_dir / "unique.txt").write_text("different")

        result = find_duplicates(clean_dir)
        assert len(result) == 1  # 一组重复

    def test_handle_duplicates_keep_newest(self, clean_dir):
        """测试保留最新策略"""
        (clean_dir / "old.txt").write_text("same content")
        import time
        time.sleep(0.1)  # 确保时间戳不同
        (clean_dir / "new.txt").write_text("same content")

        duplicates = find_duplicates(clean_dir)
        actions = handle_duplicates(duplicates, strategy="keep_newest", dry_run=True)

        assert len(actions) == 1  # 删除 1 个
        keep, delete = actions[0]
        assert keep.name == "new.txt"  # 保留较新的

    def test_handle_duplicates_dry_run(self, clean_dir):
        """测试 dry_run 不会真删除文件"""
        (clean_dir / "a.txt").write_text("same")
        (clean_dir / "b.txt").write_text("same")

        duplicates = find_duplicates(clean_dir)
        handle_duplicates(duplicates, strategy="keep_newest", dry_run=True)

        # 两个文件都应该还在
        assert (clean_dir / "a.txt").exists()
        assert (clean_dir / "b.txt").exists()

    def test_dedup_respects_min_size(self, clean_dir):
        """测试 min_size 参数"""
        (clean_dir / "small.txt").write_text("x")      # 1 byte
        (clean_dir / "large.txt").write_text("hello world!")  # 12 bytes
        (clean_dir / "large2.txt").write_text("hello world!")  # 12 bytes, duplicate

        result = find_duplicates(clean_dir, min_size=5)
        # 只应该包含 large 文件的重复组
        assert len(result) == 1  # large.txt 和 large2.txt 是一组重复


# ============================================================
#  工具函数测试
# ============================================================

class TestUtils:
    """测试工具函数"""

    def test_format_size_bytes(self):
        assert format_size(500) == "500.0 B"

    def test_format_size_kb(self):
        assert format_size(2048) == "2.0 KB"

    def test_format_size_mb(self):
        assert format_size(3 * 1024 * 1024) == "3.0 MB"

    def test_safe_filename_replaces_illegal_chars(self):
        result = safe_filename('file<name>.txt')
        assert '<' not in result
        assert '>' not in result

    def test_safe_filename_normal(self):
        assert safe_filename("normal_file.txt") == "normal_file.txt"

    def test_load_config_returns_dict(self):
        config = load_config()
        assert isinstance(config, dict)
        assert "categories" in config
        assert "settings" in config
