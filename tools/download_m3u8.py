import asyncio
import re
import sys
import time
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin

import httpx


def parse_m3u8(content: str, base_url: str) -> list[str]:
    urls = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(urljoin(base_url, line))
    return urls


async def download_segment(
    client: httpx.AsyncClient,
    url: str,
    output_dir: Path,
    index: int,
    semaphore: asyncio.Semaphore,
) -> Tuple[int, Path, bool]:
    filename = output_dir / f"{index:07d}.ts"
    async with semaphore:
        resp = await client.get(url)
        resp.raise_for_status()
        filename.write_bytes(resp.content)
        return index, filename, True


async def download_m3u8(
    m3u8_url: str,
    output_dir: str = ".",
    concurrency: int = 16,
):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        print(f"Fetching playlist: {m3u8_url}")
        resp = await client.get(m3u8_url)
        resp.raise_for_status()
        content = resp.text

        # handle master playlist (select first variant)
        if "EXT-X-STREAM-INF" in content:
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m3u8_url = urljoin(m3u8_url, line)
                print(f"Master playlist detected, using variant: {m3u8_url}")
                resp = await client.get(m3u8_url)
                resp.raise_for_status()
                content = resp.text
                break

        segment_urls = parse_m3u8(content, m3u8_url)
        total = len(segment_urls)
        if total == 0:
            print("No segments found.")
            return

        print(f"Found {total} segments, concurrency={concurrency}")

        semaphore = asyncio.Semaphore(concurrency)
        tasks = [
            download_segment(client, url, output_path, i, semaphore)
            for i, url in enumerate(segment_urls)
        ]

        start = time.time()
        done = 0
        failed = 0

        for coro in asyncio.as_completed(tasks):
            index, filename, ok = await coro
            done += 1
            if not ok:
                failed += 1
            if done % 50 == 0 or done == total:
                elapsed = time.time() - start
                speed = done / elapsed if elapsed > 0 else 0
                print(f"  [{done}/{total}] {speed:.1f} seg/s")

        elapsed = time.time() - start
        print(f"\nDone: {total - failed}/{total} segments in {elapsed:.1f}s")
        if failed:
            print(f"  {failed} segments failed")


def main():
    if len(sys.argv) < 2:
        print("Usage: python download_m3u8.py <m3u8_url> [output_dir] [concurrency]")
        print("  concurrency defaults to 16")
        sys.exit(1)

    m3u8_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 16

    asyncio.run(download_m3u8(m3u8_url, output_dir, concurrency))


if __name__ == "__main__":
    main()
