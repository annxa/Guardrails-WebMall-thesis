# extended_benchmark.py
from dataclasses import dataclass
import typing
import pandas as pd

# import the original classes / helpers from your package
from browsergym.experiments.benchmark.base import Benchmark, BenchmarkBackend, logger   # adjust import path as needed
from browsergym.experiments.benchmark.utils import prepare_backend
from .env_args import EnvArgsWebMall

@dataclass
class WebMallBenchmark(Benchmark):
    """
    Drop-in replacement for `Benchmark` that recognises the additional
    backend string "webmall" *without* modifying upstream code.
    """
    env_args_list: list[EnvArgsWebMall]

    def __post_init__(self) -> None:          # type: ignore[override]
        # ---- 1. Re-create the metadata block from the parent ----
        if self.task_metadata is None:
            unique_task_names = {env.task_name for env in self.env_args_list}
            self.task_metadata = pd.DataFrame(
                [{"task_name": name} for name in unique_task_names]
            )

        metadata_tasks = set(self.task_metadata["task_name"])
        assert all(env.task_name in metadata_tasks for env in self.env_args_list)

        # ---- 2. Validate backends, but allow our extra one ----
        allowed_backends = set(typing.get_args(BenchmarkBackend))
        allowed_backends.add("webmall")            # <-- new backend

        for backend in self.backends:
            if backend not in allowed_backends:
                raise ValueError(
                    f"Unknown Benchmark backend {backend!r}. "
                    f"Allowed backends: {sorted(allowed_backends)}"
                )
    
    def prepare_backends(self):
        for backend in self.backends:
            logger.info(f"Preparing {backend} backend...")
            if backend != "webmall":
                prepare_backend(backend)
            else:
                import browsergym.webmall
            logger.info(f"{backend} backend ready")