from browsergym.experiments.loop import EnvArgs
from dataclasses import dataclass

import gymnasium as gym






@dataclass
class EnvArgsWebMall(EnvArgs):
    def make_env(
        self, action_mapping, exp_dir, exp_task_kwargs: dict = {}, use_raw_page_output=False
    ):
        """
        Instantiates the BrowserGym environment corresponding to the arguments (with some tweaks).

        Args:
            action_mapping: overrides the action mapping of the environment.
            exp_dir: will set some environment parameters (e.g., record_video_dir) with respect to the directory where the experiment is running.
            exp_task_kwargs: use with caution! Will override task parameters to experiment-specific values. Useful to set different server configs for different experiments, or output file paths within the experiment's folder (e.g., assistantbench).

        Returns:
            env: the gym environment.
        """
        extra_kwargs = {}
        if self.record_video:
            extra_kwargs["record_video_dir"] = exp_dir
        if self.viewport:
            extra_kwargs["viewport"] = self.viewport
        if self.slow_mo is not None:
            extra_kwargs["slow_mo"] = self.slow_mo
        if self.storage_state:
            extra_kwargs["pw_context_kwargs"] = {"storage_state": self.storage_state}
        if self.task_kwargs is not None:
            extra_kwargs["task_kwargs"] = self.task_kwargs
        if exp_task_kwargs:
            extra_kwargs["task_kwargs"] = extra_kwargs.get("task_kwargs", {}) | exp_task_kwargs

        # assistantbench hack, write the task output (agent prediction) to a file in the experiment's directory
        # TODO: find a better way to deal with this
        if self.task_name.startswith("assistantbench.test"):
            extra_kwargs["task_kwargs"] = extra_kwargs.get("task_kwargs", {}) | {
                "output_file": exp_dir / "assistantbench-prediction.json"
            }

        return gym.make(
            _get_env_name(self.task_name),
            disable_env_checker=True,
            max_episode_steps=self.max_steps,
            headless=self.headless,
            wait_for_user_message=self.wait_for_user_message,
            action_mapping=action_mapping,  # action mapping is provided by the agent
            use_raw_page_output=use_raw_page_output,
            **extra_kwargs,
        )
    
def _get_env_name(task_name: str):
    """Register tasks if needed (lazy import) and return environment name."""

    # lazy benchmark import
    if task_name.startswith("miniwob"):
        import browsergym.miniwob
    elif task_name.startswith("workarena"):
        import browsergym.workarena
    elif task_name.startswith("webarena"):
        import browsergym.webarena
    elif task_name.startswith("visualwebarena"):
        import browsergym.visualwebarena
    elif task_name.startswith("assistantbench"):
        import browsergym.assistantbench
    elif task_name.startswith("weblinx"):
        import weblinx_browsergym
    elif task_name.startswith("webmall_adversarial"):
        import browsergym.webmall_adversarial
    elif task_name.startswith("webmall"):
        import browsergym.webmall
    return f"browsergym/{task_name}"
