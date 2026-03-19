from .benchmark import WebMallBenchmark
import numpy as np
from browsergym.experiments.benchmark.configs import DEFAULT_HIGHLEVEL_ACTION_SET_ARGS
from .utils import make_env_args_list_from_repeat_tasks
from browsergym.experiments.benchmark.metadata.utils import (
    task_metadata,
    task_list_from_metadata,
)

WEBMALL_BENCHMARKS = {
    "webmall_adversarial_v1.0": lambda: WebMallBenchmark(
        name="webmall_adversarial_v1.0",
        high_level_action_set_args=DEFAULT_HIGHLEVEL_ACTION_SET_ARGS["webarena"],
        is_multi_tab=True,
        supports_parallel_seeds=True,
        backends=["webmall_adversarial"],
        env_args_list=make_env_args_list_from_repeat_tasks(
            task_list=task_list_from_metadata(metadata=task_metadata("webmall_adversarial")),
            max_steps=50,
            n_repeats=1,
            seeds_rng=np.random.RandomState(42),
        ),
        task_metadata=task_metadata("webmall_adversarial"),
    ),
}
