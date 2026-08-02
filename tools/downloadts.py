import argparse
import asyncio
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载 TS 分片，支持并行加速。")
    parser.add_argument(
        "--url",
        default="https://v.fengbao11.com/video/hanzhan1994/c7e507e30230/{index:07d}.ts",
        help="含 {index} 占位符的片段 URL 模板。",
    )
    parser.add_argument("--start", type=int, default=1, help="起始分片编号。")
    parser.add_argument(
        "--end",
        type=int,
        default=0,
        help="结束分片编号，0 表示自动检测连续失败后停止。",
    )
    parser.add_argument("--workers", type=int, default=10, help="并行下载任务数。")
    parser.add_argument("--retry", type=int, default=3, help="每个分片的重试次数。")
    parser.add_argument(
        "--max-missing",
        type=int,
        default=10,
        help="连续失败次数达到此值时停止（当未指定 --end 时生效）。",
    )
    parser.add_argument("--output", default=".", help="下载保存目录。")
    return parser.parse_args()


async def download_segment(
    client: httpx.AsyncClient,
    url: str,
    path: Path,
    retry: int,
) -> bool:
    if path.exists():
        print(f"已存在，跳过: {path.name}")
        return True

    for attempt in range(1, retry + 1):
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            path.write_bytes(resp.content)
            print(f"下载成功: {path.name}")
            return True
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                print(f"未找到: {path.name} (404)")
                return False
            print(f"[{path.name}] HTTP {status}，尝试 {attempt}/{retry}。")
        except Exception as exc:
            print(f"[{path.name}] 下载失败: {exc}，尝试 {attempt}/{retry}。")

        if attempt < retry:
            await asyncio.sleep(1)

    print(f"最终失败: {path.name}")
    return False


async def worker(
    index_queue: asyncio.Queue,
    result_queue: asyncio.Queue,
    client: httpx.AsyncClient,
    url_template: str,
    output_dir: Path,
    retry: int,
    semaphore: asyncio.Semaphore,
) -> None:
    while True:
        index = await index_queue.get()
        if index is None:
            index_queue.task_done()
            break

        path = output_dir / f"{index:07d}.ts"
        url = url_template.format(index=index)
        async with semaphore:
            success = await download_segment(client, url, path, retry)
        await result_queue.put((index, success))
        index_queue.task_done()


async def manager(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    index_queue: asyncio.Queue = asyncio.Queue(maxsize=args.workers * 2)
    result_queue: asyncio.Queue = asyncio.Queue()
    stop_event = asyncio.Event()

    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=args.workers * 2, max_keepalive_connections=args.workers),
        follow_redirects=True,
    ) as client:
        semaphore = asyncio.Semaphore(args.workers)
        workers = [
            asyncio.create_task(
                worker(
                    index_queue,
                    result_queue,
                    client,
                    args.url,
                    output_dir,
                    args.retry,
                    semaphore,
                )
            )
            for _ in range(args.workers)
        ]

        async def producer() -> None:
            current = args.start
            while True:
                if args.end and current > args.end:
                    break
                if stop_event.is_set():
                    break
                await index_queue.put(current)
                current += 1
            for _ in range(args.workers):
                await index_queue.put(None)

        async def result_watcher() -> None:
            next_expected = args.start
            consecutive_failures = 0
            buffered_results: dict[int, bool] = {}

            while True:
                if stop_event.is_set() and result_queue.empty():
                    break
                index, success = await result_queue.get()
                buffered_results[index] = success

                while next_expected in buffered_results:
                    if buffered_results.pop(next_expected):
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                    next_expected += 1

                    if args.end:
                        if next_expected > args.end:
                            stop_event.set()
                            break
                    elif consecutive_failures >= args.max_missing:
                        print(
                            f"检测到 {consecutive_failures} 个连续失败，停止下载。"
                        )
                        stop_event.set()
                        break

                result_queue.task_done()

        producer_task = asyncio.create_task(producer())
        watcher_task = asyncio.create_task(result_watcher())

        await producer_task
        await index_queue.join()
        await result_queue.join()
        stop_event.set()
        await watcher_task

        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(manager(args))
