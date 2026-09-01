# HumanEval+ adapter

Isolated from the frozen SKYT research runtime. No style contracts. No SKYT repair.

The protocol still selects the **most reproduced verified form** (HumanEval+ pass), then measures whether later generations match it. The shipped human solution is an **external baseline**, not that canon.

## Pins

See `experiment_manifest.json` and the preregistered 30-task list in `pilot_task_ids.json` (seed `20260826`).

Official HumanEval+ (`evalplus==0.3.1`, release `v0.1.10`) is pinned at
`dataset_md5 = 916d9bfe7b490c2447245ec91595fa4f`. Loaders refuse a different
hash. This pin does **not** call OpenAI or Anthropic.

## Commands

```
python -m benchmarks.humaneval_plus smoke
```

Smoke does **not** call OpenAI or Anthropic. It checks stitching and, if Docker is running, executes known good / base-only / wrong / infinite programs in a network-disabled `python:3.13-slim` container.

```
python -m benchmarks.humaneval_plus generate
```

Refuses unless you pass `--allow-api`. Do not do that until smoke is green and you intend to spend budget.

```
python -m benchmarks.humaneval_plus run --allow-api --task-id HumanEval/23 --model gpt-4o-mini --temperature 0.0 --n 2 --out-dir outputs/humaneval_plus/dryrun
```

One preregistered pilot task, two samples, no SKYT repair. Not a paper table.

## Pilot (not run yet)

30 tasks × 2 models × 2 temperatures × N=10 = 1,200 generations, after smoke.
