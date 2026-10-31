import os
import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger

from pystonic.infra.storage.objects import FilePath


class LocalStorage:
    SCHEMA = "local://"

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str | Path) -> Path:
        """解析路径并校验不超出 root（防绝对路径/.. 穿越与符号链接逃逸）"""
        abs_path = self.root.joinpath(path)
        if not abs_path.resolve().is_relative_to(self.root.resolve()):
            raise ValueError(f"path {path} is outside of root {self.root}")
        return abs_path

    def list_files(self, directory: str | Path | None = None):
        list_path = self._resolve(directory) if directory else self.root

        def _make_file(name: str):
            abs_path = list_path.joinpath(name)
            return FilePath(
                name=name,
                path=abs_path.relative_to(self.root).as_posix(),
                is_dir=abs_path.is_dir(),
                size=abs_path.stat().st_size,
                modify_time=datetime.fromtimestamp(abs_path.stat().st_mtime),
                create_time=datetime.fromtimestamp(abs_path.stat().st_ctime),
            )

        return [_make_file(x) for x in os.listdir(list_path)]

    def get_file(self, path: str | Path):
        abs_path = self._resolve(path)
        if not abs_path.exists():
            raise FileNotFoundError(f"file/path {path} not exists")
        return FilePath(
            name=abs_path.name,
            path=path,
            is_dir=abs_path.is_dir(),
            size=abs_path.stat().st_size,
            create_time=datetime.fromtimestamp(abs_path.stat().st_ctime),
            modify_time=datetime.fromtimestamp(abs_path.stat().st_mtime),
        )

    def write(self, path: str | Path, content: bytes | str, encoding="utf-8"):
        abs_path = self._resolve(path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("write file: {}", path)
        if isinstance(content, bytes):
            abs_path.write_bytes(content)
        else:
            abs_path.write_text(content, encoding=encoding)

    def read(self, path: str | Path):
        abs_path = self._resolve(path)
        return abs_path.read_bytes()

    def delete(self, path: str | Path):
        abs_path = self._resolve(path)
        if not abs_path.exists():
            return
        logger.debug("delete path: {}", path)
        if abs_path.is_dir():
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
