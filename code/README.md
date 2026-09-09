# Paper scripts

Keep all executable paper utilities here: figure generation, table generation,
and one-off analysis. Add scripts only when they are needed.

- Use descriptive names such as `figure_search_progress.py`.
- Give each script a short header with its purpose, exact run command, input
  provenance, and output paths.
- Accept explicit input and output paths; avoid machine-specific paths.
- Keep dependencies with the script (for Python, prefer pinned PEP 723 inline
  dependencies and `uv run code/<script>.py`).
- Write finished figure assets to `figures/` and commit the assets used by the paper.
- Record source experiment IDs or commits and any random seed needed to regenerate
  the output. Keep small required input snapshots under `code/` when appropriate.

The LaTeX project should compile from committed assets without running these scripts.
