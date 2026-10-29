# Contributing to Duke3D Upscale Pipeline v2

AI-powered pipeline that converts Duke Nukem 3D assets into high-resolution hightile mods for
EDuke32. Pipeline phases live in `src/pipeline/phases/`, utilities in `src/pipeline/utils/`,
tests in `src/tests/`. Third-party tool sources are vendored under `vendor/` (git submodules);
do not patch them for pipeline bugs.

## Prerequisites

- Linux or macOS (Windows via WSL), Python 3.8+
- `innoextract`, `ffmpeg`, `fluidsynth`, `git`, and `uv` (verified by `make check-deps`)
- 16 GB+ RAM; a GPU with 8 GB+ VRAM for the Real-ESRGAN upscale phase

## Setup

```bash
make setup    # uv sync, clone submodules, build kextract/art2img, download models
```

Place original Duke Nukem 3D game files in `files/input/`, then run the full pipeline with
`make all`, or single phases in dependency order: `make game_files extract convert premultiply
extract_alpha upscale_alpha upscale reattach_alpha verify scrub generate_mod`.

Tune behavior in `.pipeline/config.yaml` (model choice, audio settings, verify/scrub
tolerances). `make clean` wipes generated output; `make help` lists all targets.

## Tests

```bash
python src/tests/run_tests.py     # runs every test script under src/tests/
```

See `docs/testing-guide.md` for the task-based runners and `docs/tooling.md` for tool setup.
Run the pipeline end to end on a small input when you change a phase.

## Pull request flow

1. Fork the repository and clone your fork (pull submodules:
   `git submodule update --init --recursive`).
2. Branch from `master`: `git checkout -b feature/short-name`.
3. Keep commits scoped to one phase or concern; record decisions that change pipeline
   behavior in `docs/decisions/`.
4. Push and open a pull request against `master`; include `make check-deps` and test results,
   and note hardware used for GPU phases.
