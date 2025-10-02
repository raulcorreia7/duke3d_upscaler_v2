# Duke3D Upscale Pipeline v2

AI-powered upscaling pipeline for Duke Nukem 3D assets, creating high-quality hightile mods for EDuke32.

## Overview

This pipeline automates the process of converting original Duke Nukem 3D game assets into high-resolution textures with proper alpha handling. The process includes:

1. Extracting assets from game files
2. Converting to PNG format with alpha channels
3. AI upscaling using Real-ESRGAN
4. Proper alpha channel handling to prevent pink halos
5. Final mod packaging

## Directory Structure

```
duke3d_upscaler_v2/
├── files/
│   ├── input/              # Place original game files here
│   ├── output/             # Pipeline output directories
│   ├── models/             # AI models
│   ├── soundfonts/         # Audio soundfonts
│   └── temp/               # Temporary intermediate files
├── src/
│   ├── pipeline/           # Main pipeline code
│   │   ├── phases/         # Pipeline phase implementations
│   │   └── utils/          # Utility modules
│   └── tests/              # Test suite
├── tools/
│   └── build/              # Built tools (kextract, art2img)
├── vendor/
│   ├── art2img/            # ART to PNG conversion tool
│   └── eduke32/            # Duke3D source code and tools
├── docs/
│   ├── decisions/          # Architecture Decision Records
│   ├── user-guide.md       # User documentation
│   ├── tooling.md          # Tool setup and usage
│   └── testing-guide.md    # Testing instructions
├── .pipeline/              # Pipeline configuration and state
├── .gitmodules             # Git submodules configuration
├── pyproject.toml          # Python package configuration
├── Makefile                # Build system
└── README.md               # This file
```

## Quick Start

1. Install dependencies:
   - innoextract
   - ffmpeg
   - fluidsynth
   - git
   - uv (Python package manager)

2. Setup the pipeline:
   ```bash
   make setup
   ```

3. Place your original Duke Nukem 3D game files in `files/input/`

4. Run the full pipeline:
   ```bash
   make all
   ```

5. Find your upscaled mod in `files/output/duke3d/`

## Pipeline Steps

- `make game_files` - Detect and copy input game files
- `make extract` - Extract game files
- `make convert` - Convert assets to PNG32, WAV, and frames
- `make premultiply` - Premultiply alpha to prevent pink halos
- `make extract_alpha` - Extract alpha channels for separate processing
- `make upscale_alpha` - Upscale alpha channels with Lanczos interpolation
- `make upscale` - Apply AI upscaling using Real-ESRGAN
- `make reattach_alpha` - Reattach alpha to upscaled images
- `make verify` - Check for pink artifacts in upscaled images
- `make scrub` - Remove residual magenta pixels
- `make generate_mod` - Generate final mod packages

## Configuration

The pipeline can be configured using `.pipeline/config.yaml`. You can adjust:
- Upscaling model (Real-ESRGAN x4plus or anime variant)
- Audio processing settings
- Verification tolerances
- Scrubbing parameters

## Requirements

- Python 3.8+
- Linux or macOS (Windows support via WSL)
- 16GB+ RAM recommended
- GPU with 8GB+ VRAM recommended for AI upscaling