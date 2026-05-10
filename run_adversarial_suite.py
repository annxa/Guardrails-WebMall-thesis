"""
Script to run the full adversarial task suite across all guardrail configurations.

Configurations:
    - no_rails: baseline agent with no guardrails
    - rule_based: rule-based input/output filtering only
    - prompt_based: defense system prompt only
    - llm_judge: LLM-as-a-judge output filtering only
    - layered: all guardrails enabled
"""

import logging
import os
import bgym
from dotenv import load_dotenv
from pathlib import Path

from webmall_adversarial_overrides.env_args import EnvArgsWebMall
from webmall_adversarial_overrides.exp_args import ExpArgsWebMall
from agentlab.llm.llm_configs import CHAT_MODEL_ARGS_DICT
from agentlab.experiments.launch_exp import run_experiments
from agentlab.agents import dynamic_prompting as dp
from agentlab.agents.generic_agent.generic_agent import GenericAgentArgs, GenericPromptFlags
from agentlab.agents.webmall_adversarial_guarded_agent.guarded_agent import GuardedGenericAgentArgs

current_file = Path(__file__).resolve()
PATH_TO_DOT_ENV_FILE = current_file.parent / ".env"
load_dotenv(PATH_TO_DOT_ENV_FILE)

# Drives both the task file loaded by task.py and the guardrail behaviour.
# Set WEBMALL_TASK_VERSION=v1 or v2 in .env — do not change experiment_version below.
EXPERIMENT_VERSION = os.getenv("WEBMALL_TASK_VERSION", "v2")

# --- Flags ---
FLAGS_AX = GenericPromptFlags(
    obs=dp.ObsFlags(
        use_html=False,
        use_ax_tree=True,
        use_focused_element=True,
        use_error_logs=True,
        use_history=True,
        use_past_error_logs=False,
        use_action_history=True,
        use_think_history=True,
        use_diff=False,
        html_type="pruned_html",
        use_screenshot=False,
        use_som=False,
        extract_visible_tag=True,
        extract_clickable_tag=True,
        extract_coords="False",
        filter_visible_elements_only=False,
    ),
    action=dp.ActionFlags(
        action_set=bgym.HighLevelActionSetArgs(
            subsets=["bid"],
            multiaction=False,
        ),
        long_description=False,
        individual_examples=False,
    ),
    use_plan=False,
    use_criticise=False,
    use_thinking=True,
    use_memory=False,
    use_concrete_example=True,
    use_abstract_example=True,
    use_hints=True,
    enable_chat=False,
    max_prompt_tokens=60_000,
    be_cautious=True,
    extra_instructions=None,
)

# --- Agent configs ---
CHAT_MODEL = CHAT_MODEL_ARGS_DICT["openai/gpt-4.1-2025-04-14"]
CHAT_MODEL_5 = CHAT_MODEL_ARGS_DICT["openai/gpt-5-2025-08-07"]  

AGENT_NO_RAILS = GenericAgentArgs(
    chat_model_args=CHAT_MODEL,
    flags=FLAGS_AX,
)

AGENT_RULE_BASED = GuardedGenericAgentArgs(
    chat_model_args=CHAT_MODEL,
    flags=FLAGS_AX.copy(),
    guardrail_config={
        "rule_based_gl": True,
        "prompt_based_gl": False,
        "llm_judge_gl": False,
        "experiment_version": EXPERIMENT_VERSION,
    }
)

AGENT_PROMPT_BASED = GuardedGenericAgentArgs(
    chat_model_args=CHAT_MODEL,
    flags=FLAGS_AX.copy(),
    guardrail_config={
        "rule_based_gl": False,
        "prompt_based_gl": True,
        "llm_judge_gl": False,
        "experiment_version": EXPERIMENT_VERSION,
    }
)

AGENT_LLM_JUDGE = GuardedGenericAgentArgs(
    chat_model_args=CHAT_MODEL,
    flags=FLAGS_AX.copy(),
    guardrail_config={
        "rule_based_gl": False,
        "prompt_based_gl": False,
        "llm_judge_gl": True,
        "experiment_version": EXPERIMENT_VERSION,
    }
)

AGENT_LAYERED = GuardedGenericAgentArgs(
    chat_model_args=CHAT_MODEL,
    flags=FLAGS_AX.copy(),
    guardrail_config={
        "rule_based_gl": True,
        "prompt_based_gl": True,
        "llm_judge_gl": True,
        "experiment_version": EXPERIMENT_VERSION,
    }
)

AGENT_GPT5_NO_RAILS = GenericAgentArgs(
    chat_model_args=CHAT_MODEL_5,
    flags=FLAGS_AX,
)

# ============================================================
# EXPERIMENT SELECTION — edit these before running
# Agent configs to run: choose any subset of:
#   "no_rails", "rule_based", "prompt_based", "llm_judge", "layered", "gpt5_no_rails"
# Set WEBMALL_TASK_VERSION in .env to match the iteration (v1 or v2).
RUN_AGENTS = ["rule_based"]

# Task categories to run: choose any subset of:
#   "DL", "IS", "TD", "PC", "RA"
RUN_CATEGORIES = [ "DL", "IS", "TD", "PC", "RA" ]
# ============================================================

_ALL_AGENT_CONFIGS = {
    "no_rails": AGENT_NO_RAILS,
    "rule_based": AGENT_RULE_BASED,
    "prompt_based": AGENT_PROMPT_BASED,
    "llm_judge": AGENT_LLM_JUDGE,
    "layered": AGENT_LAYERED,
    "gpt5_no_rails": AGENT_GPT5_NO_RAILS,
}

_ALL_TASK_IDS = [
    "DL_01", "DL_02", "DL_03", "DL_04", "DL_05",
    "IS_01", "IS_02", "IS_03", "IS_04", "IS_05",
    "TD_01", "TD_02", "TD_03", "TD_04", "TD_05",
    "PC_01", "PC_02", "PC_03", "PC_04", "PC_05",
    "RA_01", "RA_02", "RA_03", "RA_04", "RA_05"
]

agent_configs = [_ALL_AGENT_CONFIGS[name] for name in RUN_AGENTS]
TASK_IDS = [t for t in _ALL_TASK_IDS if any(t.startswith(cat) for cat in RUN_CATEGORIES)]

# --- Build experiment list ---
for agent in agent_configs:
    agent.set_benchmark(bgym.DEFAULT_BENCHMARKS["webarena"](), demo_mode="off")

exp_args = []
for agent in agent_configs:
    for task_id in TASK_IDS:
        env_args = EnvArgsWebMall(
            task_name=f"webmall_adversarial.{task_id}",
            task_seed=0,
            max_steps=30,
            headless=True, #toggle True/False to watch agent complete tasks
            record_video=False,
        )
        exp_args.append(
            ExpArgsWebMall(
                agent_args=agent,
                env_args=env_args,
                logging_level=logging.INFO,
            )
        )

if __name__ == "__main__":
    run_experiments(
        n_jobs=1,
        exp_args_list=exp_args,
        study_dir=str(current_file.parent / "task_results_rule_rails_v1"),
        parallel_backend="sequential",
    )
