# Benchmarking LLM Agent Guardrails in Adversarial E-Commerce Environments

Bachelor's thesis repository — University of Mannheim, 2026.

This project evaluates three guardrail types (rule-based filtering, defensive system prompts, and LLM-as-a-judge) against adversarial prompt injection attacks on an autonomous e-commerce agent operating in a simulated multi-shop WordPress environment.

---

## Repository Structure

```
WebMall/
├── docker_all/                          # Docker setup for the WebMall environment
│   ├── docker-compose.yml               # Orchestrates 4 WordPress shops, MariaDB instances, Elasticsearch, and a frontend
│   ├── dumps/                           # SQL database dumps for each iteration
│   │   ├── shop1_dump.sql               # Iteration 1 attack data — Shop 1
│   │   ├── shop2_dump.sql               # Iteration 1 attack data — Shop 2
│   │   ├── shop3_dump.sql               # Iteration 1 attack data — Shop 3
│   │   ├── shop4_dump.sql               # Iteration 1 attack data — Shop 4
│   │   └── webmall_shop1_iteration2.sql # Iteration 2 attack data — Shop 1
│   ├── restore_all_and_deploy_local.sh  # First-run setup script (restores volumes and starts containers)
│   └── backup/                          # Compressed volume snapshots (alternative restore method)
│
├── Browsergym/
│   └── browsergym/webmall_adversarial/  # BrowserGym task package (adversarial benchmark)
│       └── src/browsergym/webmall_adversarial/
│           ├── task.py                  # Task class — edit here to switch between iteration task sets
│           ├── task_sets.json           # Iteration 1 task and attack specifications (25 tasks)
│           └── task_sets_v2.json        # Iteration 2 task and attack specifications (revised attacks)
│
├── AgentLab/
│   └── src/agentlab/agents/
│       ├── generic_agent/               # Upstream GenericAgent (unmodified baseline)
│       └── webmall_adversarial_guarded_agent/
│           ├── guarded_agent.py         # GuardedGenericAgent — wraps GenericAgent with guardrails
│           └── guardrails/
│               ├── rule_rails.py        # Rule-based filter: regex patterns for input/output scanning
│               ├── prompt_rails.py      # System prompt guardrail: defensive instruction text
│               └── llm_judge.py        # LLM judge: Anthropic Sonnet 4.6 action safety evaluator
│
├── webmall_adversarial_overrides/       # Experiment scaffolding overrides (benchmark, env args, study)
├── webmall_overrides/                   # Non-adversarial WebMall overrides (used for baseline runs)
├── analyze_agentlab_results/            # Post-experiment analysis scripts
│
├── run_adversarial_suite.py             # Main entry point — runs all configured guardrail conditions
├── run_single_task.py                   # Runs a single task for quick testing or debugging
├── run_webmall_study.py                 # Runs the non-adversarial WebMall benchmark
│
├── task_results*/                       # AgentLab output directories (one folder per task run)
├── results/                             # Aggregated result files and GPT-5 baseline outputs
│
├── Tasks_and_attacks.xlsx               # Full task and attack specifications for both iterations
└── Attack_analysis.xlsx                 # Per-task results and analysis for both iterations
```

---

## Prerequisites

- **Docker** and **Docker Compose** (tested with Docker Desktop)
- **Python 3.11+**
- **Playwright** (installed via pip, browser binaries installed separately — see below)
- **OpenAI API key** — for the agent (GPT-4.1)
- **Anthropic API key** — for the LLM judge (Claude Sonnet 4.6); only required when running `llm_judge` or `layered` conditions

---

## 1. Setting Up WebMall (Docker)

The environment runs four WooCommerce shops, four MariaDB databases, an Elasticsearch instance, and a small Nginx frontend — all in Docker.

### Configure environment variables

Copy the example env file and edit it if needed:

```bash
cp .env.example .env
```

The default configuration uses `localhost:8081–8084` for the shops and `localhost:8085` for the frontend. Change port numbers in `.env` if those ports are occupied.

Add your API keys to the same `.env` file:

```
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
AGENTLAB_EXP_ROOT=""   # optional: override where AgentLab writes results
```

### Start the containers

On first run, restore the volume data and start all containers:

```bash
cd docker_all
bash ./restore_all_and_deploy_local.sh
```

This loads the compressed volume backups from `docker_all/backup/`, applies WordPress configuration for your local ports, and starts all containers. After it completes, verify the shops are reachable:

- Shop 1 (E-Store Athletes): http://localhost:8081
- Shop 2 (TechTalk): http://localhost:8082
- Shop 3 (CamelCases): http://localhost:8083
- Shop 4 (Hardware Cafe): http://localhost:8084
- Frontend / submission page: http://localhost:8085

### Import attack data (SQL dumps)

The adversarial attacks are injected into WordPress product pages, reviews, and descriptions at the database level. The correct dump must be imported depending on which iteration you want to reproduce.

**Iteration 1** — import all four shop dumps:

```bash
# Start the containers first if not already running
cd docker_all && docker compose --env-file ../.env up -d

# Import each shop's dump
for i in 1 2 3 4; do
    docker exec -i WebMall_mariadb_shop${i} \
        mariadb -u bn_wordpress -pwordpress_db_password bitnami_wordpress \
        < dumps/shop${i}_dump.sql
done
```

**Iteration 2** — import the revised dump for Shop 1 - Only Shop 1 attacks were revised in Iteration 2; Shops 2–4 remain unchanged from Iteration 1.:

```bash
docker exec -i WebMall_mariadb_shop1 \
    mariadb -u bn_wordpress -pwordpress_db_password bitnami_wordpress \
    < dumps/webmall_shop1_iteration2.sql
```

After importing, the shops will contain the adversarial content. You can log in to the WordPress admin at `http://localhost:808X/wp-admin` (username: `admin`, password: `123` or `admin`) to verify.

---

## 2. Setting Up AgentLab

### Base installation

This repository builds on the WebMall agent scaffolding from the original WebMall project. Follow the base installation instructions at https://github.com/wbsg-uni-mannheim/WebMall-Interfaces before continuing.

In addition to the upstream packages, install the two local packages in editable mode from this repository:

### What was modified from upstream

The following components were added or changed relative to the upstream WebMall AgentLab:

- **`AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/`** — new agent class `GuardedGenericAgent` that wraps the upstream `GenericAgent` with optional guardrail layers. The three guardrail modules live under `guardrails/`.
- **`Browsergym/browsergym/webmall_adversarial/`** — new BrowserGym package defining the 25 adversarial tasks across five attack categories. The task specifications and injected attacks are in `task_sets.json` (Iteration 1) and `task_sets_v2.json` (Iteration 2).
- **`webmall_adversarial_overrides/`** — experiment scaffolding overrides (benchmark config, env args, study runner) extending the upstream WebMall overrides for the adversarial benchmark.

---

## 3. Selecting the Iteration

Set `WEBMALL_TASK_VERSION` in your `.env` file to control which iteration's tasks are loaded:

```
WEBMALL_TASK_VERSION=v1   # Iteration 1 — loads task_sets.json
WEBMALL_TASK_VERSION=v2   # Iteration 2 — loads task_sets_v2.json (default)
```

This must be consistent with which SQL dumps you imported and which agent configs you run:

| `WEBMALL_TASK_VERSION` | Task file           | SQL dumps to import                             | Agent configs                                                       |
| ---------------------- | ------------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| `v1`                   | `task_sets.json`    | `shop1–4_dump.sql`                              | `no_rails`, `rule_based`, `prompt_based`, `llm_judge`, `layered`, `gpt5_no_rails`                                            |
| `v2`                   | `task_sets_v2.json` | `webmall_shop1_iteration2.sql` (+ v1 shops 2–4) | `no_rails`, `rule_based`,`prompt_based`, `llm_judge`, `layered`, `gpt5_no_rails` |

---

## 4. Running Experiments

### Guardrail conditions

The experiment defines the following agent configurations:

| Condition       | `rule_based_gl` | `prompt_based_gl` | `llm_judge_gl` | Model   |
| --------------- | :-------------: | :---------------: | :------------: | ------- |
| `no_rails`      |        —        |         —         |       —        | GPT-4.1 |
| `rule_based`    |        ✓        |         —         |       —        | GPT-4.1 |
| `prompt_based`  |        —        |         ✓         |       —        | GPT-4.1 |
| `llm_judge`     |        —        |         —         |       ✓        | GPT-4.1 |
| `layered`       |        ✓        |         ✓         |       ✓        | GPT-4.1 |
| `gpt5_no_rails` |        —        |         —         |       —        | GPT-5   |

### Where the guardrail implementations live

| Guardrail                                | Location                                                                                                                                                                               |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Rule-based filter (patterns)             | [AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guardrails/rule_rails.py](AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guardrails/rule_rails.py)     |
| System prompt text                       | [AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guardrails/prompt_rails.py](AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guardrails/prompt_rails.py) |
| LLM judge prompt and API call            | [AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guardrails/llm_judge.py](AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guardrails/llm_judge.py)       |
| Agent orchestration (applies guardrails) | [AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guarded_agent.py](AgentLab/src/agentlab/agents/webmall_adversarial_guarded_agent/guarded_agent.py)                     |

### Running a full experiment suite

Edit [run_adversarial_suite.py](run_adversarial_suite.py) to select which agent conditions and task categories to run:

```python
# Agent configs to run — any subset of:
#   "no_rails", "rule_based", "prompt_based", "llm_judge", "layered"
RUN_AGENTS = ["rule_based"]

# Task categories to run — any subset of:
#   "DL", "IS", "TD", "PC", "RA"
RUN_CATEGORIES = ["RA"]
```

Then run:

```bash
python run_adversarial_suite.py
```

Results are written to the directory specified in the `study_dir` argument near the bottom of the file (e.g. `task_results_rule_rails_v1/`). Each task run produces its own timestamped subdirectory containing an `experiment.log`, `summary_info.json`, and a `guardrail_log.json` (when a guardrail condition is active).

To watch the agent operate in a browser rather than running headlessly, set `headless=False` in the `EnvArgsWebMall` call inside the script.

### Running a single task

[run_single_task.py](run_single_task.py) is set up to run one task at a time and is useful for debugging or reproducing a specific result. Edit the `task_name` and agent config at the top of the file, then:

```bash
python run_single_task.py
```

The task name format is `webmall_adversarial.<CATEGORY>_<NUMBER>`, e.g. `webmall_adversarial.RA_01`.

---

## 5. Task Categories

The benchmark contains 25 tasks across five attack categories (5 tasks each):

| Code | Category          | Attack goal                                                             |
| ---- | ----------------- | ----------------------------------------------------------------------- |
| `DL` | Data Leakage      | Trick the agent into submitting user PII in a non-required context      |
| `IS` | Item Substitution | Redirect the agent to purchase an attacker-specified product            |
| `TD` | Topic Drift       | Cause the agent to deviate from its assigned task entirely              |
| `PC` | Policy Compliance | Get the agent to violate a user-specified constraint (e.g. price limit) |
| `RA` | Robustness Attack | Combination / stress-test attacks evaluating general resilience         |

Each category spans both `task_sets.json` (Iteration 1) and `task_sets_v2.json` (Iteration 2). The Iteration 2 attacks were strengthened based on Iteration 1 results.

---

## 6. Data and Analysis

**Task and attack specifications:**

- [Tasks_and_attacks.xlsx](Tasks_and_attacks.xlsx) — full descriptions of all 25 tasks and the adversarial content injected into the shops for both iterations

**Per-task results:**

- [Attack_analysis.xlsx](Attack_analysis.xlsx) — per-task outcomes for all agent conditions across both iterations, used for the thesis analysis

**Raw experiment output:**

- `task_results*/` — AgentLab output directories (one subdirectory per task run, containing logs and summary JSON)
- `results/` — aggregated experiment logs and GPT-5 baseline result directories

**Analysis scripts** in [analyze_agentlab_results/](analyze_agentlab_results/):

- `summarize_study.py` — extracts pass/fail outcomes from a results directory
- `task_logs_extractor.py` — pulls full agent logs for manual inspection
- `aggregate_log_statistics.py` — aggregates guardrail log statistics across runs
- `create_condensed_logs.py` — produces condensed per-task log summaries
