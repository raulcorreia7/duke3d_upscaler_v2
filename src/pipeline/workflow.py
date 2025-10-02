"""
Pipeline orchestration workflow for the Duke3D Upscale Pipeline
"""
import os
import sys
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .phases.base import AbstractPhase
from .phases.game_files import GameFilesPhase
from .phases.extract import ExtractPhase
from .phases.convert import ConvertPhase
from .phases.premultiply import PremultiplyPhase
from .phases.extract_alpha import ExtractAlphaPhase
from .phases.upscale_alpha import UpscaleAlphaPhase
from .phases.upscale import UpscalePhase
from .phases.reattach_alpha import ReattachAlphaPhase
from .phases.verify import VerifyPhase
from .phases.scrub import ScrubPhase
from .phases.generate_mod import GenerateModPhase
from .utils.state import PipelineState
from .utils.config_validator import ConfigValidator, validate_config_file
from .utils.error_handling import PipelineError, ConfigurationError
from .utils.logging import setup_logging


class PipelineWorkflow:
    """
    Main pipeline workflow orchestrator that manages phase execution
    """

    # Define phase execution order and dependencies
    PHASE_ORDER = [
        "game_files",
        "extract",
        "convert",
        "premultiply",
        "extract_alpha",
        "upscale_alpha",
        "upscale",
        "reattach_alpha",
        "verify",
        "scrub",
        "generate_mod"
    ]

    # Phase dependencies (what needs to be completed before this phase can run)
    PHASE_DEPENDENCIES = {
        "game_files": [],
        "extract": ["game_files"],
        "convert": ["extract"],
        "premultiply": ["convert"],
        "extract_alpha": ["premultiply"],
        "upscale_alpha": ["extract_alpha"],
        "upscale": ["convert"],
        "reattach_alpha": ["upscale", "extract_alpha", "upscale_alpha"],
        "verify": ["reattach_alpha"],
        "scrub": ["reattach_alpha"],
        "generate_mod": ["scrub"]
    }

    def __init__(self, config_path: str = ".pipeline/config.yaml", state_dir: str = "files/temp"):
        """
        Initialize the pipeline workflow

        Args:
            config_path: Path to configuration file
            state_dir: Directory for pipeline state files
        """
        self.config_path = config_path
        self.state_dir = state_dir
        self.logger = None
        self.config = None
        self.state = None
        self.phases = {}
        self.start_time = None
        self.setup_complete = False

    def setup(self, validate_config: bool = True, log_level: str = "INFO"):
        """
        Setup the pipeline workflow

        Args:
            validate_config: Whether to validate the configuration
            log_level: Logging level
        """
        self.start_time = datetime.now()

        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        setup_logging(log_level)
        self.logger.info("Setting up Duke3D Upscale Pipeline workflow")

        # Load and validate configuration
        if validate_config:
            try:
                self.config = validate_config_file(self.config_path)
                self.logger.info(f"Configuration loaded and validated from {self.config_path}")
            except ConfigurationError as e:
                self.logger.error(f"Configuration validation failed: {e}")
                raise
        else:
            import yaml
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"Configuration loaded from {self.config_path}")

        # Setup pipeline state
        state_file = os.path.join(self.state_dir, "state.json")
        os.makedirs(self.state_dir, exist_ok=True)
        self.state = PipelineState(state_file)

        # Create phase instances
        self._create_phases()
        self.logger.info("Pipeline phases initialized")

        self.setup_complete = True

    def _create_phases(self):
        """Create all pipeline phase instances"""
        phase_classes = {
            "game_files": GameFilesPhase,
            "extract": ExtractPhase,
            "convert": ConvertPhase,
            "premultiply": PremultiplyPhase,
            "extract_alpha": ExtractAlphaPhase,
            "upscale_alpha": UpscaleAlphaPhase,
            "upscale": UpscalePhase,
            "reattach_alpha": ReattachAlphaPhase,
            "verify": VerifyPhase,
            "scrub": ScrubPhase,
            "generate_mod": GenerateModPhase
        }

        for phase_name, phase_class in phase_classes.items():
            try:
                self.phases[phase_name] = phase_class(self.config, self.state)
                self.logger.debug(f"Created phase: {phase_name}")
            except Exception as e:
                self.logger.error(f"Failed to create phase {phase_name}: {e}")
                raise PipelineError(f"Failed to initialize phase {phase_name}: {e}", phase=phase_name)

    def validate_phase_dependencies(self, phase_names: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate phase dependencies and return (valid_phases, missing_dependencies)

        Args:
            phase_names: List of phase names to validate

        Returns:
            Tuple of (valid phase names, missing dependencies)
        """
        valid_phases = []
        missing_dependencies = []

        for phase_name in phase_names:
            if phase_name not in self.phases:
                self.logger.error(f"Unknown phase: {phase_name}")
                continue

            # Check dependencies
            deps = self.PHASE_DEPENDENCIES.get(phase_name, [])
            missing_deps = []
            for dep in deps:
                if dep not in self.state or self.state[dep] != "completed":
                    missing_deps.append(dep)

            if missing_deps:
                missing_dependencies.append(f"{phase_name}: missing {'/'.join(missing_deps)}")
            else:
                valid_phases.append(phase_name)

        return valid_phases, missing_dependencies

    def run_phases(self, phase_names: List[str] = None, dry_run: bool = False, skip_completed: bool = True):
        """
        Run pipeline phases

        Args:
            phase_names: List of phase names to run (None for all)
            dry_run: If True, show what would be done without executing
            skip_completed: Skip phases that are already marked as completed
        """
        if not self.setup_complete:
            self.setup()

        if phase_names is None:
            phase_names = self.PHASE_ORDER.copy()

        # Validate phase dependencies
        valid_phases, missing_dependencies = self.validate_phase_dependencies(phase_names)
        if missing_dependencies:
            error_msg = "Phase dependencies not satisfied:\n" + "\n".join(f"  - {dep}" for dep in missing_dependencies)
            raise PipelineError(error_msg)

        if not valid_phases:
            self.logger.error("No valid phases to run")
            return

        self.logger.info(f"Running phases: {', '.join(valid_phases)}")
        if dry_run:
            self.logger.info("DRY RUN MODE - No actual execution will occur")

        for phase_name in valid_phases:
            # Skip if already completed
            if skip_completed and phase_name in self.state and self.state[phase_name] == "completed":
                self.logger.info(f"Skipping {phase_name} (already completed)")
                continue

            self._run_single_phase(phase_name, dry_run)

        self._finish_workflow(dry_run)

    def _run_single_phase(self, phase_name: str, dry_run: bool):
        """
        Run a single phase

        Args:
            phase_name: Name of the phase to run
            dry_run: Whether to perform a dry run
        """
        phase = self.phases[phase_name]
        self.logger.info(f"Starting phase: {phase_name}")

        try:
            if dry_run:
                self.logger.info(f"DRY RUN: Would execute {phase_name}")
                # In dry run, we simulate successful completion
                self.state[phase_name] = "completed"
                self.logger.info(f"DRY RUN: {phase_name} marked as completed")
            else:
                # Check phase validation
                if not phase.validate():
                    raise PipelineError(f"Phase validation failed for {phase_name}")

                # Execute the phase
                phase.execute()

                # Mark as completed
                self.state[phase_name] = "completed"
                self.logger.info(f"Phase {phase_name} completed successfully")

        except Exception as e:
            self.logger.error(f"Phase {phase_name} failed: {e}", exc_info=True)
            # Mark as failed
            self.state[phase_name] = f"failed: {str(e)}"
            raise PipelineError(f"Phase {phase_name} failed: {e}", phase=phase_name, cause=e)

    def _finish_workflow(self, dry_run: bool):
        """Finish the workflow and log summary"""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(elapsed.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)

            self.logger.info(f"Workflow completed in {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")

        if not dry_run:
            # Save workflow summary
            self._save_workflow_summary()

    def _save_workflow_summary(self):
        """Save a summary of the workflow execution"""
        summary = {
            "completed_at": datetime.now().isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "phases": {}
        }

        for phase_name in self.PHASE_ORDER:
            summary["phases"][phase_name] = self.state.get(phase_name, "not_run")

        summary_file = os.path.join(self.state_dir, "workflow_summary.json")
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        self.logger.info(f"Workflow summary saved to {summary_file}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current workflow status

        Returns:
            Dictionary with workflow status
        """
        if not self.setup_complete:
            return {"status": "not_setup"}

        status = {
            "setup": True,
            "config_path": self.config_path,
            "phases": {}
        }

        for phase_name in self.PHASE_ORDER:
            status["phases"][phase_name] = {
                "status": self.state.get(phase_name, "not_run"),
                "can_run": phase_name in self.phases,
                "dependencies": self.PHASE_DEPENDENCIES.get(phase_name, [])
            }

        return status

    def reset_phase(self, phase_name: str):
        """
        Reset a phase's status so it can be re-run

        Args:
            phase_name: Name of the phase to reset
        """
        if phase_name in self.state:
            del self.state[phase_name]
            self.logger.info(f"Reset phase: {phase_name}")


def create_workflow(config_path: str = ".pipeline/config.yaml") -> PipelineWorkflow:
    """
    Convenience function to create a workflow instance

    Args:
        config_path: Path to configuration file

    Returns:
        PipelineWorkflow instance
    """
    return PipelineWorkflow(config_path)


def run_full_pipeline(config_path: str = ".pipeline/config.yaml", log_level: str = "INFO") -> bool:
    """
    Convenience function to run the complete pipeline

    Args:
        config_path: Path to configuration file
        log_level: Logging level

    Returns:
        True if successful, False otherwise
    """
    try:
        workflow = create_workflow(config_path)
        workflow.setup(log_level=log_level)
        workflow.run_phases()
        return True
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        return False