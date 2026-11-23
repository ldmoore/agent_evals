# Running the COMP 590 SWE-bench Verified 100 evaluation

This project evaluates agents on a fixed, 100-task subset of
`SWE-bench/SWE-bench_Verified`. The task IDs are committed in
[`benchmarks/swebench-verified-100.json`](../benchmarks/swebench-verified-100.json).
The set is stratified by repository with seed `590`; it is **not** an official
SWE-bench split. Report results as **SWE-bench Verified 100 (COMP 590, seed
590)**.

## Prerequisites

- Docker Desktop is running.
- `uv` is installed.
- The sibling agent project is at `~/Coding/590_agents` and has a configured
  `.env` file when the agent needs model credentials.

```zsh
cd ~/Coding/agent_evals
uv sync --locked
docker info
```

## Generate the 100 Harbor task directories

Harbor does not currently expose this collection as a registry dataset. Generate
the local task folders once with the official Harbor SWE-bench adapter.

```zsh
cd ~/Coding
git clone https://github.com/harbor-framework/adapters.git harbor-adapters

cd ~/Coding/harbor-adapters
uv sync --project src/swebench

task_ids=("${(@f)$(jq -r \
  '.repositories[].selected[]' \
  ~/Coding/agent_evals/benchmarks/swebench-verified-100.json)}")

uv run --project src/swebench swebench \
  --no-all \
  --task-ids "${task_ids[@]}" \
  --task-dir ~/Coding/agent_evals/datasets/swebench-verified-100
```

The generated folders are intentionally ignored by Git. They contain task
configuration and references to large Docker-backed SWE-bench environments.

## Run the evaluation

On Apple Silicon, the SWE-bench images require x86_64 emulation. Keep
`DOCKER_DEFAULT_PLATFORM=linux/amd64` on every run or resume command.

```zsh
cd ~/Coding/agent_evals

DOCKER_DEFAULT_PLATFORM=linux/amd64 \
uv run --locked harbor run \
  --path datasets/swebench-verified-100 \
  --agent eval_adapters.local:LocalCliAgent \
  --ak agent=lucasdmo_makenomistakes \
  --ak package_path=/Users/lucasmoore/Coding/590_agents \
  --ak env_file=/Users/lucasmoore/Coding/590_agents/.env \
  --env docker \
  --n-concurrent 1
```

The agent reads its default model deployment from `590_agents/.env`. To override
it for this job, append `--model openai/YOUR_UNC_DEPLOYMENT`.

Start with a small smoke run by appending `--n-tasks 5`. Jobs are written to
`jobs/`; inspect them with:

```zsh
uv run --locked harbor view jobs
```

## Common issues

| Symptom | Cause | Resolution |
| --- | --- | --- |
| `FileNotFoundError: datasets/swebench-verified-100` | The local task folders were not generated. | Run the **Generate** commands above. |
| `no match for platform in manifest` | An Apple Silicon host tried to pull an x86_64-only SWE-bench image as ARM. | Prefix the command with `DOCKER_DEFAULT_PLATFORM=linux/amd64`. |
| `no space left on device` | Docker Desktop's VM disk filled while caching distinct per-task images. | Check `docker system df`; increase Docker Desktop's disk allocation. If safe, reclaim unused artifacts with `docker system prune -af` and `docker builder prune -af`. These commands delete unused Docker data. |
| Docker Hub `429 Too Many Requests` | Pulling many distinct public images exceeded the anonymous Docker Hub limit. | Run `docker login`, then resume the existing job instead of starting a new one. |

To resume Docker-image failures without rerunning completed trials:

```zsh
cd ~/Coding/agent_evals

docker login

DOCKER_DEFAULT_PLATFORM=linux/amd64 \
uv run --locked harbor job resume \
  --job-path jobs/2026-11-23__10-26-42 \
  --filter-error-type RuntimeError
```

Replace the job path with the directory for the interrupted job. The resume
command preserves completed trials and retries only the selected error type.

## Local-resource considerations

Even at `--n-concurrent 1`, a full run pulls many distinct historical Docker
images. Expect substantial disk use and a long runtime. Use a small smoke run,
authenticate to Docker Hub before the full run, and prefer a cloud environment
if local Docker storage or network limits make the full set impractical.
