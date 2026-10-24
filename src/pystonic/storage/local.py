from datetime import datetime
import os
from pathlib import Path
import shutil

from pydantic import BaseModel
from loguru import logger


class FilePath(BaseModel):
    name: str
    path: str
    is_dir: bool
    modify_time: datetime
    size: int = 0
    create_time: datetime | None = None


class LocalStorage:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_files(self, directory: str | Path = None):
        list_path = self.root if not directory else self.root.joinpath(directory)

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
        abs_path = self.root.joinpath(path)
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

    def write(self, path: str | Path, content: bytes | str):
        abs_path = self.root.joinpath(path)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("write file: {}", path)
        if isinstance(content, bytes):
            abs_path.write_bytes(content)
        else:
            abs_path.write_text(content)

    def read(self, path: str | Path):
        abs_path = self.root.joinpath(path)
        return abs_path.read_bytes()

    def delete(self, path: str | Path):
        abs_path = self.root.joinpath(path)
        if not abs_path.exists():
            return
        logger.debug("remove path: {}", path)
        if abs_path.is_dir():
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
