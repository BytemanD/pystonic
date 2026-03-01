import os
import shutil
from enum import Enum
from pathlib import Path
from typing import List, Literal, Tuple, Union, overload

import humanize
from loguru import logger


class IfExists(str, Enum):
    """文件存在时处理方式"""

    overwrite = "overwrite"
    ignore = "ignore"
    raise_error = "raise_error"


def create_text(
    dir: Path | str,
    file: Path | str,
    content: str = "",
    encoding: str | None = None,
):
    """创建文本文件夹和文件
    Args:
        dir (Path): 根目录
        file_dir (Union[Path, str]): 相对路径
    """
    file_path = Path(dir).joinpath(file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)
    return file_path


@overload
def move_files(
    src: Path,
    dst: Path,
    dry_run: Literal[False],
    recursive: bool = False,
    if_exists: IfExists | str = IfExists.raise_error,
) -> None: ...


@overload
def move_files(
    src: Path,
    dst: Path,
    dry_run: Literal[True],
    recursive: bool = False,
    if_exists: IfExists | str = IfExists.raise_error,
) -> List[Tuple[Path, Path]]: ...


def move_files(
    src: Path,
    dst: Path,
    dry_run: bool = False,
    recursive: bool = False,
    if_exists: Union[IfExists, str] = IfExists.raise_error,
):
    """移动文件
    Args:
        src (Path): 源路径
        dst (Path): 目标路径
        recursive (bool, optional): 是否递归移动. Defaults to False.
    """
    if dst.is_file():
        raise FileExistsError(f"路径 {dst} 不是一个有效的目录")
    if not src.exists():
        raise FileNotFoundError(f"路径 {src} 不存在")
    if src.is_file():
        files = [src]
    elif recursive:
        files = [x for x in src.rglob("*") if x.is_file()]
    else:
        files = [x for x in src.glob("*") if x.is_file()]

    dst.mkdir(parents=True, exist_ok=True)
    files_to_move: List[Tuple[Path, Path]] = []
    for file in files:
        if dst.joinpath(file.name).exists():
            if if_exists == IfExists.raise_error:
                raise FileExistsError(f"目标文件已存在: {dst}")
            if if_exists == IfExists.ignore:
                logger.warning("file '{}' exists", file)
                continue
        files_to_move.append((file, dst.joinpath(file.name)))

    if dry_run:
        return files_to_move
    for file, dst_file in files_to_move:
        if dst_file.exists():
            if if_exists == IfExists.overwrite:
                logger.warning("删除文件: {}", dst_file)
                os.remove(dst.joinpath(file.name))
        shutil.move(file, dst)


@overload
def file_size(path: Path | str, natural: Literal[False] = False) -> int:
    """获取文件大小, 单位: 字节"""
    ...


@overload
def file_size(path: Path | str, natural: Literal[True]) -> str:
    """获取文件大小, 返回人类可读字符串"""
    ...


def file_size(path: Path | str, natural=False) -> int | str:
    """获取文件大小

    Args:
        path (Union[Path, str]): 文件路径

    Returns:
        int | str: 文件大小
    """
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    if natural:
        return humanize.naturalsize(file_path.stat().st_size)
    else:
        return file_path.stat().st_size
