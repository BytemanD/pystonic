import threading
import time

from langchain_community.callbacks import OpenAICallbackHandler
from langchain_core.callbacks import BaseCallbackHandler


class RequestHandler(BaseCallbackHandler):
    """统计对话请求次数与耗时。"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0  # 秒

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._starts: dict[str, float] = {}
        self.latencies: list[float] = []  # 每次请求耗时（秒），用于分位数统计

    def __repr__(self) -> str:
        return (
            f"Requests: {self.total_requests}\n"
            f"\tSuccessful: {self.successful_requests}\n"
            f"\tFailed: {self.failed_requests}\n"
            f"Total Latency: {self.total_latency:.2f}s"
        )

    @property
    def avg_latency(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests

    def percentile(self, p: float) -> float:
        """计算当前所有请求耗时的 p 分位（毫秒）。"""
        samples = sorted(self.latencies)
        if not samples:
            return 0.0
        idx = min(len(samples) - 1, max(0, round((p / 100) * (len(samples) - 1))))
        return samples[idx] * 1000

    @property
    def always_verbose(self) -> bool:
        return True

    def reset(self) -> None:
        with self._lock:
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.total_latency = 0.0
            self.latencies = []
            self._starts.clear()

    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs) -> None:
        with self._lock:
            self._starts[run_id] = time.perf_counter()

    def _close(self, run_id, error: bool) -> None:
        with self._lock:
            start = self._starts.pop(run_id, None)
            if start is not None:
                latency = time.perf_counter() - start
                self.total_latency += latency
                self.latencies.append(latency)
            self.total_requests += 1
            if error:
                self.failed_requests += 1
            else:
                self.successful_requests += 1

    def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        self._close(run_id, error=False)

    def on_llm_error(self, error, *, run_id, **kwargs) -> None:
        self._close(run_id, error=True)


def get_request_handler():
    return RequestHandler()


def get_openai_handler():
    return OpenAICallbackHandler()
