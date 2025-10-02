# Tooling and Dependencies

This document lists tools and dependencies for the revised Duke3D Upscale pipeline, covering extraction, unpacking, preparation, upscaling, mod packaging, model management, scripting, and testing. Focus on macOS; Linux/Windows via equivalents/builders. Deps in `pyproject.toml` for Python, `config.sh` for vars.

## Extraction Tools

- **7z**: Unpacks .zip, .7z, and .grp archives. Install: `brew install p7zip` (macOS), `sudo apt install p7zip-full` (Ubuntu).
- **innoextract**: Extracts Inno Setup installers (.exe). Install: `brew install innoextract` (macOS), `sudo apt install innoextract` (Ubuntu).

- Usage: Automatically used during the build phase to extract assets.

## Unpacking and Preparation Tools

- **kextract**: EDuke32 tool to unpack GRP files (e.g., duke3d.grp) to .art/.pcx/audio. Built in `build/tools/` from submodule.
- **ReBUILD utilities**: Vendored helpers (`art2tga.exe`, `tga2art.exe`, `rff.exe`, `blud2b.exe`, `sfx2wav.exe`, `WinSfx2Wav.exe`) from https://blood.sourceforge.net/rebuild.php (synced via `scripts/vendor.sh`). Extracted under `vendor/rebuild`, copied into `build/tools/`.
- Usage: `convert` runs `art2tga` + `tools/convert_tga_to_png.py` to stage RGBA PNGs in `build/pipeline/<edition>/raw/textures/` (flat with zero-padded IDs).

## Upscaling Tools

- **uv**: Python dependency manager. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`.
- **upscale_simple.py**: Batch script in `tools/`, uses Real-ESRGAN for x4 scaling (PNG tiles from convert). GPU/CPU fallback.
- **Dependencies** (`pyproject.toml`, locked in `uv.lock`): realesrgan, Pillow (image), numpy (processing). Run `uv sync` in setup.sh (creates `.venv`).
- Usage: Called in upscale phase; dry-run flag; outputs upscaled PNGs to `build/pipeline/<edition>/upscaled`, skips existing via checksum.

## Mod Packaging Tools

- **build.sh Phases**: Unified script for package phase; generates `defs.con` (tilefromtexture PNG overrides via script scan), `upscale.con` (gamevars r_hightile=1 r_polymer=1 hud_scale=2 fallbacks).
- **EDuke32 Tools**: kenbuild (defs.con), kengrp (optional GRP packing). Built in `build/tools/` from submodule.
- Usage: Copies PNGs to `build/pipeline/<edition>/mod/`, asserts CON syntax; unpacked for -j load.

## Model Management

- **OpenModelDB Integration**: In `setup.sh`: curl/jq to query API for Real-ESRGAN URL/checksum (stored in `config.sh` as REALESRGAN_MODEL_URL/CHECKSUM), wget download to `tools/models/model.pth`, validate checksum.
- **Refresh**: `make model-refresh` (new target, runs model_refresh.sh for latest from OpenModelDB).
- Fallback: Manual download if network fail; offline use cached.

## Bash Helpers and Scripting

- **scripts/common.sh**: Shared functions: log (colored output), die (error exit), abs_path (resolve), detect_os (platform), download_model (wget with progress), validate_checksum (sha256sum).
- **scripts/config.sh**: UPPER_SNAKE_CASE vars (RAW_ASSETS_DIR=build/raw_assets, UPSCALE_MODEL_URL=https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth, etc.). Source in scripts; no hardcode.
- **Style**: Bash with `set -euo pipefail`, 4-space indent, lower_snake_case locals.

## Wiki Downloader

- **`tools/crawler_manager.py`**: A parallel crawler manager that runs all individual crawlers (e.g., `tools/eduke32_crawler.py`).
- **Usage**: Run `make crawl` to download documentation from all configured wikis in parallel. The concurrency is automatically scaled based on CPU cores but can be overridden (e.g., `make crawl CONCURRENCY=100`).
- **Stateful**: Each crawler maintains its own state, allowing crawls to be resumed if interrupted.

## Testing Tools

- **test/lib/common.sh**: Helpers: assert_file_exists, mock_command (for build.sh phases), assert_grep (CON lines like r_hightile 1).
- **Offline**: No network; mocks for curl/jq/model download, fixtures in test/fixtures/ (.pcx mocks, con templates).
- Run: make test (run_tests.sh).

## Platform Notes

- **macOS (Focus)**: Native hdiutil, brew for most; GPU via Metal if realesrgan supports.
- **Linux**: apt/dnf/pacman equivalents; GPU CUDA/Vulkan.
- **Windows**: MSYS2 (pacman for tools) or WSL (Linux flow); no native hdiutil (use 7z).

## Dependencies Table

| Category | Tools/Deps | Install/Notes |
|----------|------------|--------------|
| Extraction | 7z, innoextract | brew/apt/native; auto-detect in build.sh |
| Unpacking/Preparation | kextract, art2tga, convert_tga_to_png.py | kextract (GRP -> ART); ReBUILD art2tga + Pillow converter (ART -> PNG) |
| Upscaling | uv, realesrgan, Pillow, numpy | uv sync; GPU: realesrgan-ncnn-vulkan optional |
| Model | curl, jq, wget | brew/apt; OpenModelDB query/checksum |
| Mod | kenbuild, kengrp | Built from vendor/eduke32 |
| Scripting | Bash, make, git | Standard; common.sh helpers |
| Wiki | `src/tools/crawler_manager.py` | Run via `make crawl` |
| Testing | common.sh asserts | Offline mocks/fixtures |

See [Project Plan](plan.md) for integration and [Getting Started](getting-started.md) for workflow context.
