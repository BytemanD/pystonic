from typing import List

import pytest

from pystonic.utils import textutil


@pytest.mark.parametrize(
    "text, expected",
    [
        ("```ls```", ["ls"]),
        ("```\nls\n```", ["ls"]),
        ("```\nls\npwd\n```", ["ls\npwd"]),
        ("```\nls\n\npwd\n```", ["ls\n\npwd"]),
        ("```\nls\nhostname -i\n```", ["ls\nhostname -i"]),
        ("```powershell\nls\n```", ["ls"]),
        ("```python\nls\npwd\n```", ["ls\npwd"]),
    ],
)
def test_find_code_from_markdown_text(text: str, expected: List[str]):
    assert textutil.find_code_blocks_from_markdown(text) == expected
