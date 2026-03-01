import tempfile
from pathlib import Path

import pytest

from pystonic.utils.fileutil import create_text, move_files


def test_move_single_file():
    """测试移动单个文件"""
    file1 = "file1.txt"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dst_dir = temp_path.joinpath("destination")
        # 创建源文件
        file1_path = create_text(temp_path, Path("source", file1))
        # 移动文件
        move_files(file1_path.parent, dst_dir)

        # 验证文件已移动
        assert not file1_path.exists()
        assert dst_dir.joinpath(file1).exists()


def test_move_single_file_with_dry_run():
    """测试移动单个文件"""
    file1 = "file1.txt"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dst_dir = temp_path.joinpath("destination")
        # 创建源文件
        file1_path = create_text(temp_path, Path("source", file1))
        # 移动文件
        move_files(file1_path.parent, dst_dir, dry_run=True)

        # 验证文件已移动
        assert file1_path.exists()
        assert not dst_dir.joinpath(file1).exists()


def test_move_nonexistent_file_raises_error():
    """测试移动不存在的文件应抛出异常"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        nonexistent_file = temp_path.joinpath("nonexistent.txt")
        dst_dir = temp_path.joinpath("destination")

        with pytest.raises(FileNotFoundError):
            move_files(nonexistent_file, dst_dir)


def test_move_directory_files_non_recursive():
    """测试移动目录内容（非递归）"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        src_dir = temp_path.joinpath("source")
        dst_dir = temp_path.joinpath("destination")
        src_dir.mkdir()
        # 创建源目录中的文件
        file1 = src_dir.joinpath("file1.txt")
        file1.write_text("content1")

        # 创建子目录（不应被移动，因为非递归）
        subdir = src_dir.joinpath("subdir")
        subdir.mkdir()
        subfile = subdir.joinpath("subfile.txt")
        subfile.write_text("sub content")

        # 移动文件
        move_files(src_dir, dst_dir, recursive=False)

        # 验证结果
        assert not file1.exists()
        assert dst_dir.joinpath(file1.name).exists()
        assert subfile.exists()
        assert not dst_dir.joinpath(subfile.name).exists()


def test_move_directory_files_recursive():
    """测试移动目录内容（递归）"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        src_dir = temp_path.joinpath("source")
        dst_dir = temp_path.joinpath("destination")
        src_dir.mkdir()

        # 创建源目录中的文件
        file1 = src_dir.joinpath("file1.txt")
        file2 = src_dir.joinpath("file2.txt")
        file1.write_text("content1")
        file2.write_text("content2")

        # 创建子目录和文件
        subdir = src_dir.joinpath("subdir")
        subdir.mkdir()
        subfile = subdir.joinpath("subfile.txt")
        subfile.write_text("sub content")

        # 移动文件
        move_files(src_dir, dst_dir, recursive=True)

        # 验证结果 - 所有文件都应该被移动
        assert not file1.exists()
        assert not file2.exists()
        assert not subfile.exists()

        assert dst_dir.joinpath(file1.name).exists()
        assert dst_dir.joinpath(file2.name).exists()
        assert dst_dir.joinpath(subfile.name).exists()


def test_move_files_with_file_exists_error():
    file1 = "file1.txt"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dst_dir = temp_path.joinpath("destination")
        # 创建源文件
        file1_path = create_text(temp_dir, file1, content="foo")
        dst_file1_path = create_text(temp_dir, dst_dir.joinpath(file1), content="bar")

        # 移动文件
        with pytest.raises(FileExistsError, match="目标文件已存在"):
            move_files(file1_path.parent, dst_dir)

        # 验证文件已移动
        assert file1_path.exists()
        assert dst_file1_path.exists()
        assert dst_file1_path.read_text() == "bar"


def test_move_files_with_ignore():
    file1 = "file1.txt"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dst_dir = temp_path.joinpath("destination")
        # 创建源文件
        file1_path = create_text(temp_dir, file1, content="foo")
        dst_file1_path = create_text(temp_dir, dst_dir.joinpath(file1), content="bar")

        # 移动文件
        move_files(file1_path.parent, dst_dir, if_exists="ignore")

        # 验证文件已移动
        assert file1_path.exists()
        assert dst_file1_path.exists()
        assert dst_file1_path.read_text() == "bar"


def test_move_files_with_overwrite():
    file1 = "file1.txt"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dst_dir = temp_path.joinpath("destination")
        # 创建源文件
        file1_path = create_text(temp_dir, Path("source", file1), "foo")
        dst_file1_path = create_text(temp_dir, dst_dir.joinpath(file1), "bar")

        # 移动文件
        move_files(file1_path.parent, dst_dir, if_exists="overwrite")

        # 验证文件已移动
        assert not file1_path.exists()
        assert dst_file1_path.exists()
        assert dst_file1_path.read_text() == "foo"
