# Labs

Labs contains experimental work that is not part of the PyPI 0.3.0 MVP. It has separate build,
release, security, and qualification boundaries.

## Current tracks

| Track | What can be evaluated | Important boundary |
| --- | --- | --- |
| [Native preview](native-preview.md) | Machine profile, terminal workspace, agent-pack validation | Separate Go binary and prerelease |
| [Action router](action-router.md) | Requirements compilation, measured fixture routing, explanations | Effects remain simulated |
| [Local models](local-models.md) | Signed catalog, verified download, runtime supervision design | Public catalog is empty |

## Support boundary

The Python package, browser Workspace, official hosted-model adapters, and SQLite runtime are the
initial MVP. Labs commands are not available from `pip install agentmuru`.

Do not infer production readiness from a source build or deterministic fixture. A Labs feature
moves into the main product only after its distribution, security, migration, clean-machine, and
reference-environment evidence is published.
