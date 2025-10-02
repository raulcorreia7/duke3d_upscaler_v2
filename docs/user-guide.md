# Duke3D Upscale User Guide

This guide provides comprehensive instructions for setting up, building, and using the Duke3D Upscale project to create high-resolution mods for Duke Nukem 3D.

## Quick Start

### For Windows Users

**Important:** On Windows, this project **must** be run from the **MSYS2 MinGW 64-bit** shell.

1. Run `launch_msys2.bat` from the project root to open the correct shell
2. Install dependencies: `make deps-windows-msys`
3. All subsequent commands must be run in this shell

### For All Platforms

1. **Install Dependencies**
   ```sh
   # macOS
   brew install p7zip innoextract make ffmpeg fluidsynth
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install -y p7zip-full innoextract make build-essential ffmpeg fluidsynth
   ```

2. **Clone & Setup**
   ```sh
   git clone <repository-url>
   cd duke3d_upscale
   make setup
   ```

3. **Add Game Assets**
   - Place your Duke Nukem 3D game files (e.g., `setup_duke3d.exe`, `duke3d.grp`) into the `archives/` directory

4. **Build Everything**
   ```sh
   make all
   ```

5. **Play the Game**
   ```sh
   make run_mod  # With upscaled mod
   make run      # Original game
   ```

## Detailed Workflow

### Project Structure

- `archives/`: Your source game files
- `build/`: Generated files and compiled engine
- `docs/`: Project documentation
- `scripts/`: Orchestration scripts
- `tools/`: Python upscaling tools
- `vendor/`: EDuke32 engine source
- `test/`: Unit and integration tests

### Pipeline Overview

The automated pipeline processes your game assets through these stages:

1. **Asset Extraction**: Extract game assets from installers
2. **Engine Building**: Compile EDuke32 engine from source
3. **Asset Processing**: Convert and prepare assets for upscaling
4. **AI Upscaling**: Apply Real-ESRGAN to enhance textures
5. **Quality Assurance**: Verify and clean upscaled assets
6. **Audio Conversion**: Convert VOC/MID files to WAV format
7. **Mod Packaging**: Create final high-resolution mod

### Mod Structure & Configuration

The generated mod uses an additive approach that works alongside the original game:

#### Asset Organization
- `textures/`: Upscaled PNG textures (flat numbering: 0001.png, 0002.png, etc.)
- `animations/`: Enhanced animation files (.ANM)
- `audio/sfx/`: Converted sound effects (VOC → WAV)
- `audio/music/`: Converted music (MID → WAV)
- `maps/`: Game maps (.MAP)
- `extras/`: Additional game assets

#### Configuration Files
- `textures.def`: Maps original texture IDs to upscaled PNG files
- `upscale.con`: Enables high-resolution rendering modes
- `user.con`: Loads texture definitions and settings

#### Packaging Modes

**Unpacked Mode (Default)**
- Directory-based structure for development and testing
- Easy iteration and debugging
- Loaded via `-j` parameter: `eduke32 -j build/upscaled_mod`

**Grouped Mode (Optional)**
- Single-file distribution format
- Compact and easy to share
- Loaded via GRP file parameter

### Advanced Usage

#### Iterative Development
```sh
# Rebuild specific phases
make convert         # Re-convert assets
make upscale         # Re-upscale only
make package         # Re-package mod

# Test changes quickly
make run_mod
```

#### Custom Configuration
- Modify `scripts/lib/config.sh` for custom settings
- Adjust upscale factor, audio conversion, etc.
- See [Implementation Status](implementation-status.md) for available options

#### World Tour Edition
```sh
make setup_worldtour  # Setup World Tour support
make run_worldtour    # Launch with World Tour assets
```

## Troubleshooting

### Common Issues

**`make` command not found**
- Ensure you're in the correct shell (MSYS2 MinGW 64-bit on Windows)
- Verify `make` is installed on your system

**Build fails**
- Run `make doctor` to diagnose issues
- Check for missing dependencies
- Ensure game assets are in `archives/` directory

**Audio conversion issues**
- Verify FFmpeg and FluidSynth are installed
- Check SoundFont file availability
- Audio conversion can be disabled via configuration

**Performance concerns**
- Higher resolutions increase resource usage
- Consider reducing upscale factor for lower-end systems
- Use selective asset processing for targeted enhancements

**GPU Acceleration**
The upscaler supports GPU acceleration for faster processing:
```sh
# Use single GPU (default GPU 0)
USE_GPU=1 make upscale

# Use specific GPU
USE_GPU=1 GPU_ID=1 make upscale

# Use all available GPUs for parallel processing
USE_GPU=1 MULTI_GPU=1 make upscale
```
- GPU acceleration requires CUDA-compatible NVIDIA GPU
- Multi-GPU mode splits workload across all available GPUs
- Fallback to CPU if GPU is not available

### Maintenance

**Start fresh**
```sh
make purge  # Remove all generated files
make setup  # Re-initialize
make all    # Rebuild everything
```

**Update dependencies**
```sh
make vendor_update  # Update EDuke32 engine
make setup          # Refresh tools and dependencies
```

## Technical Details

### DEF File Authoring

The pipeline generates DEF files that use indexed hightiles for optimal performance:

```def
texture 0001 {
  indexed
  pal 0 {
    file "textures/0001.png"
    nocompress
    nodownsize
  }
}
```

**Benefits of Indexed Hightiles:**
- Engine-side palette recoloring (no duplicate files)
- Reduced file size and memory usage
- Better compatibility with palette swap effects
- Graceful fallback on older engine versions

### Pipeline Features

See [Implementation Status](implementation-status.md) for detailed feature matrix and technical implementation details.

## Next Steps

- [Testing Guide](testing-guide.md) - Validation and quality assurance
- [Tooling Reference](tooling.md) - Technical tool documentation
- [Project Plan](plan.md) - Future roadmap and enhancements

---

For developers: See [Implementation Status](implementation-status.md) for technical details about the pipeline architecture and current feature implementation.