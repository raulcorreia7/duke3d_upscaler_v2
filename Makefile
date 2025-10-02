# Makefile for Duke3D Upscale Pipeline
# Cross-platform pipeline for creating hightile mods from Duke Nukem 3D assets

.PHONY: help setup all clean check-deps game_files extract convert premultiply extract_alpha upscale_alpha upscale reattach_alpha verify scrub generate_mod

# Default target
all: check-deps game_files extract convert premultiply extract_alpha upscale_alpha upscale reattach_alpha verify scrub generate_mod

# Dependency checking
check-deps:
	@echo "Checking dependencies..."
	@command -v innoextract >/dev/null 2>&1 || (echo "Missing innoextract. Please install it first."; exit 1)
	@command -v ffmpeg >/dev/null 2>&1 || (echo "Missing ffmpeg. Please install it first."; exit 1)
	@command -v fluidsynth >/dev/null 2>&1 || (echo "Missing fluidsynth. Please install it first."; exit 1)
	@command -v uv >/dev/null 2>&1 || (echo "Missing uv. Please install it first."; exit 1)
	@command -v git >/dev/null 2>&1 || (echo "Missing git. Please install it first."; exit 1)
	@echo "All dependencies found."

# Phase dependencies - ensures proper order
extract: game_files
convert: extract
premultiply: convert
extract_alpha: premultiply
upscale_alpha: extract_alpha
upscale: convert
reattach_alpha: upscale extract_alpha upscale_alpha
verify: reattach_alpha
scrub: reattach_alpha
generate_mod: scrub

# Help message
help:
	@echo "Duke3D Upscale Pipeline"
	@echo "======================"
	@echo "Available targets:"
	@echo "  check-deps    - Verify all required dependencies are installed"
	@echo "  setup         - Clone submodules and build tools"
	@echo "  game_files    - Detect and copy input game files"
	@echo "  extract       - Extract game files to files/output/10_extract"
	@echo "  convert       - Convert assets to PNG32, WAV, and frames"
	@echo "  premultiply   - Premultiply alpha to prevent pink halos"
	@echo "  extract_alpha - Extract alpha channels for separate processing"
	@echo "  upscale_alpha - Upscale alpha channels with Lanczos interpolation"
	@echo "  upscale       - Apply AI upscaling using Real-ESRGAN"
	@echo "  reattach_alpha - Reattach alpha to upscaled images"
	@echo "  verify        - Check for pink artifacts in upscaled images"
	@echo "  scrub         - Remove residual magenta pixels"
	@echo "  generate_mod  - Generate final mod packages"
	@echo "  all           - Run all pipeline steps (default)"
	@echo "  clean         - Clean pipeline output directories"
	@echo ""
	@echo "First time setup:"
	@echo "  1. Install dependencies: innoextract, ffmpeg, fluidsynth, git, uv"
	@echo "  2. Run: make setup"
	@echo "  3. Place game files in files/input/ directory"
	@echo "  4. Run: make all"

# Setup target - clone submodules and build tools
setup:
	@echo "Setting up Duke3D Upscale Pipeline..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		python3 -m pip install --user uv; \
	fi
	uv sync
	@echo "Cloning submodules..."
	git submodule update --init --recursive
	@echo "Building kextract and art2img tools..."
	$(MAKE) -C vendor/eduke32 tools-only
	$(MAKE) -C tools/build/art2img
	@echo "Copying built tools..."
	@cp vendor/eduke32/kextract tools/build/eduke32/ 2>/dev/null || true
	@echo "Downloading models and soundfonts..."
	@python -m src.pipeline.main setup
	@echo "Setting up complete. You can now run: make all"

# Game files phase
game_files:
	@echo "Detecting and copying game files..."
	@python -m src.pipeline.main game_files

# Extract phase
extract:
	@echo "Extracting game files..."
	@python -m src.pipeline.main extract

# Convert phase
convert:
	@echo "Converting assets to PNG32, WAV, and frames..."
	@python -m src.pipeline.main convert

# Upscale phase
upscale:
	@echo "Applying AI upscaling using Real-ESRGAN..."
	@python -m src.pipeline.main upscale

# Premultiply phase
premultiply:
	@echo "Premultiplying alpha to prevent pink halos..."
	@python -m src.pipeline.main premultiply

# Extract alpha phase
extract_alpha:
	@echo "Extracting alpha channels for separate processing..."
	@python -m src.pipeline.main extract_alpha

# Upscale alpha phase
upscale_alpha:
	@echo "Upscaling alpha channels with Lanczos interpolation..."
	@python -m src.pipeline.main upscale_alpha

# Reattach alpha phase
reattach_alpha:
	@echo "Reattaching alpha to upscaled images..."
	@python -m src.pipeline.main reattach_alpha

# Verify phase
verify:
	@echo "Checking for pink artifacts in upscaled images..."
	@python -m src.pipeline.main verify

# Scrub phase
scrub:
	@echo "Removing residual magenta pixels..."
	@python -m src.pipeline.main scrub

# Generate mod phase
generate_mod:
	@echo "Generating final mod packages..."
	@python -m src.pipeline.main generate_mod

# Clean pipeline output
clean:
	@echo "Cleaning pipeline output..."
	@rm -rf files/output/00_game/* files/output/10_extract/* files/output/20_convert/* files/output/21_premultiply/* files/output/22_alpha_extract/* files/output/23_alpha_upscale/* files/output/30_upscale/* files/output/31_reattach/* files/output/32_scrub/* files/output/duke3d/* files/temp/* files/models/* files/soundfonts/* .pipeline/* logs/*
	@echo "Clean complete."