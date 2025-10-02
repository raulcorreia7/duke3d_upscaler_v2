"""
Logging and progress tracking setup for the Duke3D Upscale Pipeline
"""
import os
import logging
import logging.handlers
import json
import sys
import time
from typing import Dict, Any, Optional, Generator
from datetime import datetime, timedelta
import random
import string


def setup_logging(level: str = "INFO", config: Dict[str, Any] = {}):
    """
    Set up logging for the pipeline.

    :param level: Logging level
    :param config: Pipeline configuration
    """
    # Create the logs directory
    os.makedirs("logs", exist_ok=True)

    # Generate log filename
    if config and "logging" in config:
        log_file = config["logging"]["log_file"]
        if "{rand4}" in log_file:
            # Generate random 4-digit string
            rand4 = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
            log_file = log_file.format(rand4=rand4)
        log_file = os.path.join("logs", log_file)

        console_output = config["logging"].get("console_output", True)
        verbose = config["logging"].get("verbose", False)
    else:
        log_file = "logs/pipeline.log"
        console_output = True
        verbose = False

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = PipelineFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        verbose
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO if not verbose else logging.DEBUG)
        console_formatter = PipelineFormatter(
            '%(name)s - %(levelname)s - %(message)s',
            verbose,
            simple=True
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    logging.info("Logging set up to %s", log_file)
    return log_file


class PipelineFormatter(logging.Formatter):
    """
    Custom formatter to support both structured and human readable output
    """
    def __init__(self, fmt: str, verbose: bool = False, simple: bool = False):
        super().__init__(fmt)
        self.verbose = verbose
        self.simple = simple

    def format(self, record):
        # Format for the standard log
        if self.simple:
            return super().format(record)

        # Add more detailed information for verbose mode
        if self.verbose:
            if hasattr(record, 'exc_info') and record.exc_info:
                formatted = super().format(record)
                # Add file/line info
                formatted += f" ({record.filename}:{record.lineno})"
                return formatted

        return super().format(record)


class ProgressTracker:
    """
    Enhanced progress tracking with ETA and rate information
    """
    def __init__(self, total: int, description: str = "Processing",
                 logger: Optional[logging.Logger] = None,
                 update_interval: float = 0.5):
        """
        Initialize progress tracker

        Args:
            total: Total number of items to process
            description: Description of the operation
            logger: Logger instance
            update_interval: Minimum time between progress updates in seconds
        """
        self.total = total
        self.completed = 0
        self.description = description
        self.logger = logger or logging.getLogger(__name__)
        self.update_interval = update_interval

        self.start_time = time.time()
        self.last_update_time = 0
        self.last_update_count = 0

        # Processed items per second (rolling average)
        self.recent_rates = []
        self.rate_window = 10  # seconds

    def update(self, increment: int = 1, item_description: str = None):
        """
        Update progress

        Args:
            increment: Number of items completed
            item_description: Description of current item being processed
        """
        self.completed += increment
        current_time = time.time()

        # Calculate rate
        elapsed = current_time - self.start_time
        if elapsed > 0:
            current_rate = self.completed / elapsed
            self.recent_rates.append((current_time, self.completed))

            # Keep only recent data points
            cutoff_time = current_time - self.rate_window
            self.recent_rates = [(t, c) for t, c in self.recent_rates if t >= cutoff_time]

        # Update display if enough time has passed or this is the last item
        time_since_last_update = current_time - self.last_update_time
        should_update = (
            time_since_last_update >= self.update_interval or
            self.completed == self.total
        )

        if should_update:
            progress_percent = self.completed / self.total

            # Calculate ETA
            if self.completed > 0 and len(self.recent_rates) >= 2:
                recent_time, recent_count = self.recent_rates[0]
                time_diff = current_time - recent_time
                count_diff = self.completed - recent_count

                if time_diff > 0:
                    rate = count_diff / time_diff
                    remaining = self.total - self.completed
                    if rate > 0:
                        eta_seconds = remaining / rate
                        eta_str = f"ETA: {self._format_duration(eta_seconds)}"
                    else:
                        eta_str = "ETA: unknown"
                else:
                    eta_str = "ETA: unknown"
            else:
                eta_str = "ETA: calculating..."

            # Build progress message
            elapsed_str = self._format_duration(elapsed)

            if item_description and self.completed == self.total:
                self.logger.info(
                    f"{self.description}: {self.completed}/{self.total} "
                    f"({progress_percent:.1%}) - "
                    f"Elapsed: {elapsed_str}, {eta_str}"
                )
                self.logger.info(f"  Final: {item_description}")
            elif item_description:
                self.logger.info(
                    f"{self.description}: {self.completed}/{self.total} "
                    f"({progress_percent:.1%}) - "
                    f"Elapsed: {elapsed_str}, {eta_str}"
                )
                self.logger.info(f"  Current: {item_description}")
            else:
                self.logger.info(
                    f"{self.description}: {self.completed}/{self.total} "
                    f"({progress_percent:.1%}) - "
                    f"Elapsed: {elapsed_str}, {eta_str}"
                )

            self.last_update_time = current_time

    def _format_duration(self, seconds: float) -> str:
        """Format duration in a human readable way"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            remaining = seconds % 3600
            minutes = remaining / 60
            return f"{hours:.0f}h {minutes:.0f}m"

    def finish(self, success: bool = True, summary: str = None):
        """
        Mark progress as finished

        Args:
            success: Whether the operation completed successfully
            summary: Optional summary message
        """
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_duration(elapsed)

        status = "✓ completed" if success else "✗ failed"
        self.logger.info(
            f"{self.description} {status}: {self.total}/{self.total} items "
            f"in {elapsed_str}"
        )

        if summary:
            self.logger.info(f"Summary: {summary}")

        if success and self.total > 0:
            rate = self.total / elapsed
            self.logger.info(f"Average rate: {rate:.1f} items/second")

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        if exc_type is None:
            self.finish(success=True)
        else:
            self.finish(success=False, summary=str(exc_val))


def setup_progress_tracking(config: Dict[str, Any] = None) -> ProgressTracker:
    """
    Setup progress tracking for long-running operations

    Args:
        config: Optional configuration dict

    Returns:
        ProgressTracker instance
    """
    if config and "performance" in config:
        # Could configure progress tracking from config
        pass

    return ProgressTracker


def create_progress(total: int, description: str = "Processing",
                   logger: Optional[logging.Logger] = None) -> ProgressTracker:
    """
    Create a new progress tracker

    Args:
        total: Total number of items to process
        description: Description of the operation
        logger: Logger instance

    Returns:
        ProgressTracker instance
    """
    return ProgressTracker(total, description, logger)


def log_batch_progress(items: list, batch_size: int, description: str = "Batch processing",
                      logger: Optional[logging.Logger] = None) -> Generator:
    """
    Process items in batches with progress tracking

    Args:
        items: List of items to process
        batch_size: Size of each batch
        description: Description of the operation
        logger: Logger instance

    Yields:
        Batch of items
    """
    total_batches = (len(items) + batch_size - 1) // batch_size

    if logger is None:
        logger = logging.getLogger(__name__)

    with ProgressTracker(total_batches, description, logger) as progress:
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            progress.update(1, f"Batch {i//batch_size + 1}/{total_batches} ({len(batch)} items)")
            yield batch