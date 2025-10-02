#!/usr/bin/env python3
"""
Main entry point for the Duke3D Upscale Pipeline
"""
import os
import argparse
import logging

from src.pipeline.phases.game_files import GameFilesPhase
from src.pipeline.phases.extract import ExtractPhase
from src.pipeline.phases.convert import ConvertPhase
from src.pipeline.phases.premultiply import PremultiplyPhase
from src.pipeline.phases.extract_alpha import ExtractAlphaPhase
from src.pipeline.phases.upscale_alpha import UpscaleAlphaPhase
from src.pipeline.phases.upscale import UpscalePhase
from src.pipeline.phases.reattach_alpha import ReattachAlphaPhase
from src.pipeline.phases.verify import VerifyPhase
from src.pipeline.phases.scrub import ScrubPhase
from src.pipeline.phases.generate_mod import GenerateModPhase
from src.pipeline.utils.logging import setup_logging
from src.pipeline.utils.state import PipelineState
from src.pipeline.utils.model import download_model
from src.pipeline.utils.soundfont import download_soundfont

def setup_phase(config, state):
    """Setup phase - download models and soundfonts"""
    print("Setting up models and soundfonts...")
    
    # Download Real-ESRGAN model
    model_name = config.get("upscale", {}).get("model", "realesrgan-x4plus")
    model_dir = "files/models"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, f"{model_name}.pth")
    download_model(model_name, model_path, config)
    
    # Download SoundFont
    soundfont_url = config.get("audio", {}).get("soundfont_url")
    soundfont_path = config.get("audio", {}).get("soundfont", "files/soundfonts/Trevor0402_SC-55.sf2")
    if soundfont_url and soundfont_path:
        os.makedirs(os.path.dirname(soundfont_path), exist_ok=True)
        download_soundfont(soundfont_url, soundfont_path)
    
    print("Setup complete.")

def main():
    parser = argparse.ArgumentParser(
        description="Duke3D Upscale Pipeline - AI-powered upscaling for Duke Nukem 3D assets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run complete pipeline
  %(prog)s extract                  # Run only extract phase
  %(prog)s --list                   # List all available phases
  %(prog)s --status                 # Show current pipeline status
  %(prog)s --dry-run all            # Show what would be run without executing
  %(prog)s upscale --skip-completed # Skip already completed phases
  %(prog)s --reset extract          # Reset extract phase status
        """
    )

    # Phase and operation selection
    parser.add_argument("phase", nargs="?", default="all",
                        help="Pipeline phase(s) to run (comma-separated for multiple)")
    parser.add_argument("--list", action="store_true",
                        help="List all available phases and their dependencies")
    parser.add_argument("--status", action="store_true",
                        help="Show current pipeline status")
    parser.add_argument("--reset",
                        help="Reset specific phase status to allow re-running")

    # Configuration options
    parser.add_argument("--config", default=".pipeline/config.yaml",
                        help="Path to configuration file (default: .pipeline/config.yaml)")
    parser.add_argument("--validate-config", action="store_true",
                        help="Validate configuration and exit")

    # Execution options
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without actually executing")
    parser.add_argument("--skip-completed", action="store_true",
                        help="Skip phases that are already marked as completed")
    parser.add_argument("--force", action="store_true",
                        help="Force re-run all phases, ignoring completed status")

    # Logging and output
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level (default: INFO)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")

    args = parser.parse_args()

    try:
        # Handle special operations that don't require full setup
        if args.list:
            _list_phases()
            return

        if args.reset:
            _reset_phase(args.reset, args.config)
            return

        # Import workflow module after argument parsing
        from .workflow import PipelineWorkflow

        # Setup workflow
        workflow = PipelineWorkflow(args.config)

        # Setup logging
        log_level = "DEBUG" if args.verbose else args.log_level
        workflow.setup(validate_config=True, log_level=log_level)

        # Handle configuration validation
        if args.validate_config:
            print("✓ Configuration is valid")
            return

        # Handle status display
        if args.status:
            _show_status(workflow)
            return

        # Parse phase names
        if args.phase == "all":
            phase_names = None  # Will run all phases
        else:
            # Support comma-separated phase names
            phase_names = [p.strip() for p in args.phase.split(',') if p.strip()]
            invalid_phases = [p for p in phase_names if p not in workflow.PHASE_ORDER]
            if invalid_phases:
                print(f"✗ Invalid phases: {', '.join(invalid_phases)}")
                _list_phases()
                return 1

        # Handle setup phase specially
        if args.phase == "setup":
            config = workflow.config
            state = workflow.state
            setup_phase(config, state)
            return

        # Check setup requirements for non-setup phases
        if not _check_setup_requirements():
            if not args.dry_run:
                print("✗ Please run 'make setup' first to build the required tools.")
                return 1

        # Configure execution options
        dry_run = args.dry_run
        skip_completed = args.skip_completed and not args.force

        # Run the specified phases
        if dry_run:
            print("DRY RUN MODE - No actual execution will occur\n")

        workflow.run_phases(
            phase_names=phase_names,
            dry_run=dry_run,
            skip_completed=skip_completed
        )

        if not dry_run:
            print("✓ Pipeline completed successfully")

    except KeyboardInterrupt:
        print("\n✗ Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        return 1

    return 0


def _list_phases():
    """List all available phases with dependencies"""
    from .workflow import PipelineWorkflow

    print("Available pipeline phases:")
    print("=" * 50)

    workflow = PipelineWorkflow()

    for phase_name in workflow.PHASE_ORDER:
        deps = workflow.PHASE_DEPENDENCIES.get(phase_name, [])
        if deps:
            dep_str = f" (after: {', '.join(deps)})"
        else:
            dep_str = ""

        print(f"  {phase_name:<15} {dep_str}")

    print("\nSpecial operations:")
    print("  all              Run complete pipeline")
    print("  setup            Setup models and soundfonts")
    print("\nUse --verbose for detailed logging during execution.")


def _show_status(workflow):
    """Show current pipeline status"""
    status = workflow.get_status()

    print("Pipeline Status:")
    print("=" * 50)
    print(f"Config: {status['config_path']}")
    print()

    for phase_name, phase_info in status['phases'].items():
        phase_status = phase_info['status']
        if phase_status == 'completed':
            status_symbol = "✓"
        elif phase_status.startswith('failed'):
            status_symbol = "✗"
        else:
            status_symbol = "○"

        print(f"  {status_symbol} {phase_name:<15} {phase_status}")

    print()
    print("Legend: ✓ Completed | ✗ Failed | ○ Not run")


def _reset_phase(phase_name: str, config_path: str):
    """Reset a specific phase status"""
    from .workflow import PipelineWorkflow
    from .utils.state import PipelineState

    # Validate phase name
    workflow = PipelineWorkflow()
    if phase_name not in workflow.PHASE_ORDER:
        print(f"✗ Invalid phase: {phase_name}")
        _list_phases()
        return

    # Reset phase status
    state = PipelineState("files/temp/state.json")
    if phase_name in state:
        del state[phase_name]
        print(f"✓ Reset phase: {phase_name}")
    else:
        print(f"✓ Phase {phase_name} was not completed")


def _check_setup_requirements() -> bool:
    """Check if required tools are built"""
    kextract_path = os.path.join("tools/build/eduke32", "kextract")
    art2img_path = os.path.join("tools/build/art2img", "art2img")

    if not os.path.exists(kextract_path) or not os.path.exists(art2img_path):
        return False
    return True

if __name__ == "__main__":
    main()