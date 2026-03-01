from typing import Generator, List, Optional

import prettytable

TableStyle = prettytable.TableStyle


class DataTable(prettytable.PrettyTable):
    """DataTable class for displaying data in a table format"""

    def __init__(
        self,
        fields: Optional[List[str]] = None,
        title: Optional[dict] = None,
        index: bool = False,
        **kwargs,
    ):
        title = title or {}
        self.data_fields = fields or []
        self.index = index
        if not fields and title:
            self.data_fields = list(title.keys())
        field_names = [title.get(field, field) for field in self.data_fields]
        super().__init__((self.index and ["#"] or []) + field_names, **kwargs)

    def add_items(self, items: List[dict]):
        """Add items to table"""
        for i, item in enumerate(items, start=1):
            self.add_row(
                (self.index and [i] or [])
                + [item.get(field) for field in self.data_fields]
            )

    def add_object_items(self, items: List[object]):
        """Add items to table"""
        for i, item in enumerate(items, start=1):
            self.add_row(
                (self.index and [i] or [])
                + [getattr(item, field) for field in self.data_fields]
            )

    def set_align(self, kwargs):
        self.align.update(kwargs)

    def length(self):
        return len(self.rows)

    def pages(self, page_size=50) -> Generator[prettytable.PrettyTable, None, None]:
        for start in range(0, len(self.rows), page_size):
            self.start = start
            self.end = start + page_size
            yield self

    def reset_page(self):
        self.start, self.end = 0, len(self.rows)
