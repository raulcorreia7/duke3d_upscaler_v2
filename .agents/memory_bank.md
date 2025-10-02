# Memory Bank

## Project Conventions
- **Directory Structure**: `src/`, `files/`, `tools/`, `docs/` with 7 essential files in root
- **User Workflow**: Drop files in `files/input/`, run `make all`, get output in `files/output/`
- **Build System**: Makefile with phase targets
- **Python Structure**: Source code in `src/pipeline/` with `phases/` and `utils/` subdirectories

## Canonical Commands
```bash
make setup     # Initialize project and build tools
make all       # Run complete pipeline
make clean     # Clean processing directories
```

## Code Style
- Python: Follow PEP 8
- Makefile: Idempotent targets
- Documentation: Markdown with clear headings

## Stack Versions
- Python: 3.8+
- uv: Latest
- Make: GNU Make
- Git: 2.0+

## Lockfile Policy
- Use `uv.lock` for Python dependencies
- Git submodules for external tools
- Semantic versioning for configuration

## Security
- No network writes without explicit directive
- Validate file paths
- Sanitize user inputs
- Minimal permissions for directories