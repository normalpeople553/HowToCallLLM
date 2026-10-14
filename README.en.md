# Model Manual

[中文](README.md) · English

A model API handbook for people and an implementation guide for agents. Start with one of three paths to learn calls, find an exact model, or have an Agent implement the integration.

## Start here

| Entry | What you will find |
|---|---|
| [Human guide](human/README.en.md) | Getting started, complete code walkthroughs, reviewing Agent implementations, common parameters and pitfalls |
| [Model directory](models/README.en.md) | Manuals, parameters, examples, official prices and calling code by provider and exact model |
| [Agent guide](agents/README.en.md) | Integration instructions, resource lookup, code generation, migration and debugging |

The human and Agent guides share official model cards and calling code. Both languages use the same source; execution records stay local and are not published.

## Maintenance and reproduction

[Calling-code directory](en/docs/example-status.md) · [Verification and reproduction](en/docs/verification.md) · [Evidence policy](en/docs/evidence-policy.md) · [Translation checks](scripts/check_translations.py)

Project defaults and maintained examples use paid models, with no silent free-model fallback after an error. Prices link to official pages through the model directory. Existing execution evidence does not verify an Agent's rewrite or arbitrary parameter combinations; the evidence policy defines the boundaries.

Keep keys in environment variables or a Git-ignored .env, never in code, chat, reports or commits. Do not overwrite an existing .env with a template. [Ignore rules](.gitignore) · [Safety and evidence policy](en/docs/evidence-policy.md)

Installation and checks are documented in verification and reproduction. The [CI template](ci/offline-checks.yml) is not enabled as GitHub Actions.

The organization was inspired by [HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter). This project is not affiliated with that project or any model provider. Licensed under the [Unlicense](LICENSE).
