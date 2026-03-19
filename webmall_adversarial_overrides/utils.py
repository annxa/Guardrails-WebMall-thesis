import numpy as np
from .env_args import EnvArgsWebMall
from browsergym.experiments.loop import SEED_MAX
def make_env_args_list_from_repeat_tasks(
    task_list: list[str],
    max_steps: int,
    n_repeats: int,
    seeds_rng: np.random.RandomState,
    viewport=None,
):
    """
    Generates a list of `len(task_list)` time `n_repeats` environments arguments, using randomly generated seeds.
    """
    env_args_list = []
    for task in task_list:
        for seed in seeds_rng.randint(low=0, high=SEED_MAX, size=n_repeats):
            env_args_list.append(
                EnvArgsWebMall(
                    task_name=task,
                    task_seed=int(seed),
                    max_steps=max_steps,
                    headless=True,
                    record_video=False,
                    wait_for_user_message=False,
                    viewport=viewport,
                    slow_mo=None,
                    storage_state=None,
                    task_kwargs=None,
                )
            )

    return env_args_list
