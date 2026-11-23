# SWE-bench Verified 100

`benchmarks/swebench-verified-100.json` fixes an efficient 100-task evaluation
set drawn from the official `SWE-bench/SWE-bench_Verified` test split. It is not
an official SWE-bench split and results must be described as **SWE-bench
Verified 100 (COMP 590, seed 590)**.

The selection is a random sample stratified by repository: every repository is
represented at least once, and the remaining tasks are allocated
proportionally. The manifest records the exact instance IDs, source, split,
method, and seed so later runs use the same tasks.

## Generate local Harbor tasks

The Harbor registry available to this project does not provide a Lite dataset.
Use the official Harbor SWE-bench adapter to turn the 100 selected Verified
records into local task folders. Do not substitute Lite for this manifest: its
IDs are from Verified.

```sh
git clone https://github.com/harbor-framework/adapters.git ~/Coding/harbor-adapters
cd ~/Coding/harbor-adapters
uv sync --project src/swebench

# Read selected IDs from the committed manifest, then create 100 Harbor tasks.
IDS=$(jq -r '.repositories[].selected[]' \
  ~/Coding/agent_evals/benchmarks/swebench-verified-100.json)
uv run --project src/swebench swebench \
  --no-all --task-ids $IDS \
  --task-dir ~/Coding/agent_evals/datasets/swebench-verified-100
```

This downloads the public benchmark metadata and creates the task directories
once. The generated dataset is intentionally ignored by Git: it contains 100
large Docker-backed task environments.

## Evaluate an agent

Run Harbor from the evaluation checkout after generating the task folders:

```sh
cd ~/Coding/agent_evals
uv run --locked harbor run \
  --path datasets/swebench-verified-100 \
  --agent eval_adapters.local:LocalCliAgent \
  --ak agent=lucasdmo_makenomistakes \
  --ak package_path=/Users/lucasmoore/Coding/590_agents \
  --ak env_file=/Users/lucasmoore/Coding/590_agents/.env \
  --model openai/YOUR_UNC_DEPLOYMENT \
  --env docker \
  --n-concurrent 1
```

Use `--n-tasks 5` for a smoke run. Harbor saves results in `jobs/`; start its
viewer with `uv run --locked harbor view jobs`.
