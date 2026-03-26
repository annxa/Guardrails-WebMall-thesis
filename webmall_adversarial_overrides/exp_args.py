from dataclasses import dataclass
from browsergym.experiments.loop import ExpArgs
from .env_args import EnvArgsWebMall

@dataclass
class ExpArgsWebMall(ExpArgs):
    env_args: EnvArgsWebMall 
    def prepare(self, exp_root):
        super().prepare(exp_root)
        if hasattr(self.agent_args, 'guardrail_config') and self.agent_args.guardrail_config:
            import copy
            self.agent_args = copy.deepcopy(self.agent_args)
            self.agent_args.guardrail_config['log_path'] = self.exp_dir / 'guardrail_log.json'


