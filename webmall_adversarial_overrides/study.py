from agentlab.experiments.study import Study
from dataclasses import dataclass
from .configs import WEBMALL_BENCHMARKS
import bgym 
from typing import Dict, Callable
import uuid
from pathlib import Path
from agentlab.agents.agent_args import AgentArgs
import logging
from agentlab.experiments.study import set_demo_mode
from agentlab.experiments.exp_utils import add_dependencies
from .exp_args import ExpArgsWebMall
from agentlab.experiments.study import logger
from .benchmark import WebMallBenchmark

@dataclass
class WebMallStudy(Study):

    benchmark: WebMallBenchmark | str = None

    def __post_init__(self) -> None: 
        BENCHMARKS: Dict[str, Callable[[], WebMallBenchmark]] = {
            **bgym.DEFAULT_BENCHMARKS,
            **WEBMALL_BENCHMARKS,
        }

        self.uuid = uuid.uuid4()

        if isinstance(self.benchmark, str):
            key = self.benchmark.lower()
            self.benchmark = BENCHMARKS[key]()

        if isinstance(self.dir, str):
            self.dir = Path(self.dir)

        # 3. Build the experiment list as in the parent class ------------------
        self.make_exp_args_list()

        assert {type(exp.env_args).__name__ for exp in self.exp_args_list} \
        == {"EnvArgsWebMall"}
    def agents_on_benchmark(
        self,
        agents: list[AgentArgs] | AgentArgs,
        benchmark: bgym.Benchmark,
        demo_mode=False,
        logging_level: int = logging.INFO,
        logging_level_stdout: int = logging.INFO,
        ignore_dependencies=False,
    ):
        """Run one or multiple agents on a benchmark.

        Args:
            agents: list[AgentArgs] | AgentArgs
                The agent configuration(s) to run.
            benchmark: bgym.Benchmark
                The benchmark to run the agents on.
            demo_mode: bool
                If True, the experiments will be run in demo mode.
            logging_level: int
                The logging level for individual jobs.
            logging_level_stdout: int
                The logging level for the stdout.
            ignore_dependencies: bool
                If True, the dependencies will be ignored and all experiments can be run in parallel.

        Returns:
            list[ExpArgs]: The list of experiments to run.

        Raises:
            ValueError: If multiple agents are run on a benchmark that requires manual reset.
        """

        if not isinstance(agents, (list, tuple)):
            agents = [agents]

        if benchmark.name.startswith("visualwebarena") or benchmark.name.startswith("webarena"):
            if len(agents) > 1:
                raise ValueError(
                    f"Only one agent can be run on {benchmark.name} since the instance requires manual reset after each evaluation."
                )

        for agent in agents:
            agent.set_benchmark(
                benchmark, demo_mode
            )  # the agent can adapt (lightly?) to the benchmark

        env_args_list = benchmark.env_args_list
        if demo_mode:
            set_demo_mode(env_args_list)

        exp_args_list = []

        for agent in agents:
            for env_args in env_args_list:
                exp_args = ExpArgsWebMall(
                    agent_args=agent,
                    env_args=env_args,
                    logging_level=logging_level,
                    logging_level_stdout=logging_level_stdout,
                )
                exp_args_list.append(exp_args)

        for i, exp_args in enumerate(exp_args_list):
            exp_args.order = i

        # not required with ray, but keeping around if we would need it for visualwebareana on joblib
        # _flag_sequential_exp(exp_args_list, benchmark)

        if not ignore_dependencies:
            # populate the depends_on field based on the task dependencies in the benchmark
            exp_args_list = add_dependencies(exp_args_list, benchmark.dependency_graph_over_tasks())
        else:
            logger.warning(
                f"Ignoring dependencies for benchmark {benchmark.name}. This could lead to different results."
            )

        return exp_args_list