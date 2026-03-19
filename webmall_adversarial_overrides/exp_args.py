from dataclasses import dataclass
from browsergym.experiments.loop import ExpArgs
from .env_args import EnvArgsWebMall

@dataclass
class ExpArgsWebMall(ExpArgs):
    env_args: EnvArgsWebMall 

