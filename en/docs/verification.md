# Verification and reproduction

[中文](../../docs/验证与复现.md) · [Human guide](../../human/README.en.md)

This page defines installation, public offline checks and local live verification. Commands, exit codes and private report fields are implemented by the [unified verifier](../../tests/provider_verify.py), [file executor](../../tests/run_example_files.py) and [locked dependencies](../../requirements-lock.txt). See [parameters and tuning](parameters.md) for field explanations and the [evidence policy](evidence-policy.md) for scope.

## Reproducible environment

At the repository root, create an isolated Python 3.10+ environment and install the full lock file. Private execution records are not included in downloads or required for public offline checks.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -c 'import sys, openai; print(sys.version); print(openai.__version__)'
```

For Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. The [CI template](../../ci/offline-checks.yml) defines a Linux/Windows and Python 3.10/3.13 matrix, but is not currently enabled as GitHub Actions. A template is not evidence that those platforms passed.

## Offline checks

These commands do not read API keys or call model APIs. Simulated responses exercise empty streaming chunks, truncation, tool arguments, and result-return boundaries.

```bash
python -m unittest discover -s tests -p 'test_*.py'
python skills/model-manual/scripts/sync_verification.py --check
python skills/model-manual/scripts/example_catalog.py --check
python skills/model-manual/scripts/model_catalog.py --check
python scripts/render_human_examples.py --check
python tests/check_example_release.py --check
```

See the [official-example index](example-index.md) for functionality. Each model's `examples/sources.json` maintains source and run information; regenerate the derived index after changing a manifest with `python skills/model-manual/scripts/example_catalog.py --write-index`. Offline mocks send no requests. Running an example directly does make real calls; upload examples also send their input files. The historical unified verifier covers only its own tests, not every advanced source file. File results are tracked separately in [example status](example-status.md).

## Maintain language-model lists (no requests)

The [six lists](model-lists/README.md) are generated from `data/model-lists/<vendor>.json`. Check official API IDs, lifecycle, modalities and pricing links, then review both languages and the scope before running:

```bash
python skills/model-manual/scripts/model_catalog.py --write-pages
python skills/model-manual/scripts/model_catalog.py --check
python skills/model-manual/scripts/model_catalog.py --vendor deepseek --model deepseek-v4-pro
```

`--write-pages` generates the index and six vendor pages in both languages; `--check` detects stale generated pages. Filters cannot be combined with page operations. An unmatched exact ID, invalid catalog or stale page exits `2`; success exits `0`. Queries read documentation snapshots and registered code, not private records, keys or the network, and do not inventory live models. Sources must use the corresponding vendor's allowed official HTTPS hosts. Host/schema validation does not automatically verify factual meaning.

Adding discovery entries does not change default cards or example source. Full integration needs a separately maintained exact-model card, parameter guide and actually executed examples. Passing evidence for existing example files does not transfer to newly listed models. [Evidence boundaries](evidence-policy.md)

## Human code-reading pages (no requests)

[Code reading and human review](../../human/examples/README.en.md) displays complete basic calling files for the six maintained models. Maintainers must still verify changed calls. The renderer checks public source, exact model and reading anchors without reading private reports. It creates no new calling code and makes no requests.

```bash
python scripts/render_human_examples.py --write
python scripts/render_human_examples.py --check
```

No arguments defaults to read-only checking. Invalid source, exact model, reading anchors or stale pages exit `2`; successful checking or writing exits `0`. `--write` updates only the 14 reading pages in `human/examples/`. Both editions preserve actual source code, with explanations from one bilingual set of reading prompts. An Agent implementation with changed calling fields or prompts still needs separate verification. See the [publishing policy](evidence-policy.md).

## Local live verification

Maintainers must actually run calling code before publication. Execution records stay local. The unified verifier covers fixed checks; the file executor runs registered originals. Neither inherits the other's results, and missing records do not mean passing. Public private markers mean unpublished records, not public proof or lack of execution. [Publishing policy](evidence-policy.md)

## Unified verifier: fixed checks

Configure only the vendors you intend to verify, using environment variables or the Git-ignored root `.env`. Vendors missing keys are skipped. A full run makes real API requests. [Key policy](evidence-policy.md)

```bash
# Key values are not written to reports.
python tests/verify_calls.py kimi qwen --report /tmp/model-manual-verification.json

# Individual model entry points remain available.
python tests/verify_kimi_k2_6.py --report /tmp/kimi-k2.6-verification.json
python tests/verify_deepseek_flash.py --report /tmp/deepseek-flash-verification.json
```

`/tmp/` is a macOS/Linux example; use an appropriate temporary directory on Windows. Existing reports are not overwritten by default; `--overwrite` is an explicit replacement option. New reports default to Git-ignored `.local/evidence/`; an explicit local path outside the repository is also supported. Do not commit reports, replies, statistics or execution fingerprints to GitHub, or put report paths in public cards.

Local-only reports record the runtime, commit and dirty-worktree marker, endpoint, actual safe parameters, termination, token counts, and classified outcomes. They do not save keys, question text, model answers, reasoning text, tool arguments, or request IDs. Errors retain only a category and permitted business codes, not raw vendor error text. [Implementation and fields](../../tests/provider_verify.py)

The tests define the coverage: ordinary/JSON requests check normal completion and parsable results; tools run a simulated-weather loop; images identify the color of a generated image. One pass proves that fixed example, not general accuracy or another model's capability. [Verifier](../../tests/provider_verify.py)

### Unified-verifier exit codes

| Code | Meaning |
|---|---|
| 0 | All selected tests passed. |
| 1 | At least one test failed. |
| 2 | Rate-limited/skipped tests without a failure, or invalid arguments/report path. |

Rate limits, authentication failures, truncation, and interrupted streams are classified separately. “No exception” is not a passing criterion. [Classification](../../tests/provider_verify.py)

## File execution: original examples and real-network observation

The default command only lists the inventory; it does not read keys or send requests. `--vendor` and `--file` select registered files. [Argument implementation](../../tests/run_example_files.py)

```bash
python tests/run_example_files.py --vendor minimax
python tests/run_example_files.py --file models/deepseek/deepseek-flash/examples/10_vision_files.py
```

**Only the following explicit `--execute` commands run real calls; they may incur charges and upload input.** Use material you are authorized to send. Do not accidentally treat private photos or business files as test fixtures. The executor creates a local teaching image; video requirements depend on the runtime and explicit options. Consult the file manifest and executor. [Input preparation](../../tests/run_example_files.py) · [Example index](example-index.md)

```bash
python tests/run_example_files.py --execute --vendor minimax \
  --report /tmp/model-manual-minimax-files.json

python tests/run_example_files.py --execute \
  --file models/deepseek/deepseek-flash/examples/10_vision_files.py \
  --report /tmp/model-manual-deepseek-file.json
```

The report path must be new; old evidence is not overwritten. Reports use a random UUIDv4 `evidence_id` without test dates, timestamps, or execution durations. Each item records source/helper fingerprints, execution status, and actually observed allowlisted metadata such as endpoint, parameters, termination, and usage. Observers do not save keys, messages, answer/reasoning text, raw errors, or request/tool IDs, and do not replace vendor responses. A previous successful process cannot fill gaps in current source identity or network observation. [Executor](../../tests/run_example_files.py) · [Node observer](../../tests/live_fetch.mjs) · [cURL observer](../../tests/live_curl.py)

TypeScript also requires the Node.js environment in [package.json](../../package.json) and dependencies pinned by [package-lock.json](../../package-lock.json); install them at the repository root with `npm ci`. Shell examples require Bash, cURL, and Python. Missing runtimes/inputs, timeouts, and rate limits retain their own statuses; incomplete execution does not imply unsupported capability. [Runtime checks](../../tests/run_example_files.py)

Kimi's local video fixture needs `ffmpeg`. Doubao video requires an explicitly supplied, authorized public HTTPS resource, such as the official tutorial's test video. The executor does not inherit private image/video addresses from the environment. [Input preparation](../../tests/run_example_files.py) · [Doubao tutorial](https://docs.volcengine.com/docs/ark/video-understanding?lang=zh)

```bash
python tests/run_example_files.py --execute --vendor doubao \
  --video-url https://ark-project.tos-cn-beijing.volces.com/doc_video/video-understanding.mp4 \
  --report /tmp/model-manual-doubao-files.json
```

The executor returns `0` only if all files selected in that run pass its checks; otherwise it returns `1`. Invalid command arguments may return `2`. Read statuses, actual requests, and report scope rather than citing an exit code alone. [Classification and exit handling](../../tests/run_example_files.py)

Explanatory code blocks and arbitrary generated combinations are not covered by file-level conclusions. After changing the prompt, budget, thinking mode, media, or protocol, validate the changed path. Simulated weather, order, and inventory results used during real model calls are not real-business verification. [Evidence policy](evidence-policy.md) · [Parameter guide](parameters.md)

### File-level release gate

The [release check](../../tests/check_example_release.py) generates or checks the public calling-code directory by default, without private records, execution hashing or requests. Only explicit `--require-passed` checks local reports against current source and requires real HTTP, normal completion and nonempty content. Missing local records cannot become a pass. [Local notes](../../verification/README.en.md).

```bash
python tests/check_example_release.py --write
python tests/check_example_release.py --check
python tests/check_example_release.py --check --require-passed
```

`--check` verifies public code-directory synchronization without requiring private reports. `--require-passed` separately checks maintainer-local evidence; an unmet gate returns `1`, while a stale page or structurally invalid material returns `2`. View that result locally, not in public pages. [Implementation](../../tests/check_example_release.py)

## Bilingual synchronization and translation review

Both languages use the same official model cards, calling source and attribution manifests; translation does not trigger new API calls. These generators produce both editions, and their check commands detect stale pages in either edition. They read no keys and send no requests.

```bash
python skills/model-manual/scripts/example_catalog.py --write-index
python skills/model-manual/scripts/model_catalog.py --write-pages
python scripts/render_human_examples.py --write
python skills/model-manual/scripts/sync_verification.py
python tests/check_example_release.py --write
python scripts/check_translations.py --check
```

Static translation pairs are recorded in the [manifest](../translations.json). After Chinese prose changes, review the English fields, ranges, unknowns, lifecycle and citations before updating the recorded source hash. `python scripts/check_translations.py --fingerprint docs/来源与核验规则.md` prints a reviewed page's current hash without writing anything. The tool does not automatically certify semantic review. [Bilingual rules](evidence-policy.md)

## Synchronize capability summaries

Public vendor summaries and verification notes derive only from official card sources and publication boundaries, not private reports. After changing official facts, run:

```bash
python skills/model-manual/scripts/sync_verification.py
python skills/model-manual/scripts/sync_verification.py --check
```

The synchronizer sends no requests, reads no private records and outputs no statistics or report links. Maintenance observations are not provider capability guarantees. See [official attribution and local verification notes](verification-status.md) and the [calling-code directory](example-status.md).
