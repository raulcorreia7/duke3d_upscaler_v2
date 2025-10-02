"""
Error handling and retry utilities for the Duke3D Upscale Pipeline
"""
import time
import logging
import functools
import subprocess
from typing import Any, Callable, Tuple, Union, Optional, Dict
from enum import Enum


class RetryStrategy(Enum):
    """Retry strategies"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


class PipelineError(Exception):
    """Base class for pipeline errors"""
    def __init__(self, message: str, phase: str = None, cause: Exception = None):
        super().__init__(message)
        self.phase = phase
        self.cause = cause
        self.timestamp = None

    def __str__(self):
        if self.phase:
            return f"[{self.phase}] {super().__str__()}"
        return super().__str__()


class ConfigurationError(PipelineError):
    """Raised when configuration is invalid"""
    pass


class PhaseValidationError(PipelineError):
    """Raised when phase input/output validation fails"""
    pass


class DependencyError(PipelineError):
    """Raised when phase dependencies are not satisfied"""
    pass


class ResourceError(PipelineError):
    """Raised when required resources are missing or unavailable"""
    pass


class RetryableError(PipelineError):
    """Error that can be retried"""
    pass


class NonRetryableError(PipelineError):
    """Error that should not be retried (like config issues)"""
    pass


class TimeoutError(PipelineError):
    """Raised when operations timeout"""
    pass


class GPUError(PipelineError):
    """Raised when GPU operations fail"""
    pass


class ModelError(PipelineError):
    """Raised when AI model operations fail"""
    pass


class FileProcessingError(PipelineError):
    """Raised when file processing operations fail"""
    pass


class AudioProcessingError(PipelineError):
    """Raised when audio processing fails"""
    pass


class ImageProcessingError(PipelineError):
    """Raised when image processing fails"""
    pass


def retry_on_exception(
    max_attempts: int = 3,
    delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    backoff_factor: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """
    Decorator for retrying functions on specific exceptions

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between attempts in seconds
        strategy: Retry strategy (linear, exponential, fixed)
        backoff_factor: Multiplier for exponential/linear backoff
        exceptions: Tuple of exceptions to catch and retry on
        logger: Logger instance for logging retry attempts
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if logger is None:
                func_logger = logging.getLogger(func.__module__)
            else:
                func_logger = logger

            last_exception = None
            actual_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt, give up
                        func_logger.error(
                            f"Failed after {max_attempts} attempts: {func.__name__} - {str(e)}"
                        )
                        raise

                    # Log retry attempt
                    func_logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {actual_delay:.1f} seconds..."
                    )

                    time.sleep(actual_delay)

                    # Update delay for next attempt
                    if strategy == RetryStrategy.EXPONENTIAL:
                        actual_delay *= backoff_factor
                    elif strategy == RetryStrategy.LINEAR:
                        actual_delay += delay * backoff_factor
                    # FIXED strategy keeps the same delay

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def safe_subprocess_run(
    command: list,
    check: bool = True,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    text: bool = True,
    logger: Optional[logging.Logger] = None
) -> subprocess.CompletedProcess:
    """
    Safe subprocess execution with better error handling

    Args:
        command: Command to execute as list
        check: Whether to raise CalledProcessError on non-zero exit
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text
        logger: Logger instance

    Returns:
        subprocess.CompletedProcess: Result of subprocess execution
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    cmd_str = ' '.join(str(x) for x in command)
    logger.debug(f"Executing: {cmd_str}")

    try:
        result = subprocess.run(
            command,
            check=check,
            timeout=timeout,
            capture_output=capture_output,
            text=text
        )

        if logger.isEnabledFor(logging.DEBUG):
            if result.stdout:
                logger.debug(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.debug(f"STDERR:\n{result.stderr}")

        return result

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds: {cmd_str}"
        logger.error(error_msg)
        raise RetryableError(error_msg, phase="subprocess")

    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed with exit code {e.returncode}: {cmd_str}"
        if e.stderr:
            error_msg += f"\nSTDERR: {e.stderr.strip()}"
        logger.error(error_msg)

        # Categorize errors
        if "FileNotFoundError" in str(e) or "No such file" in str(e):
            raise NonRetryableError(error_msg, phase="subprocess", cause=e)
        else:
            raise RetryableError(error_msg, phase="subprocess", cause=e)

    except OSError as e:
        error_msg = f"OS error executing command: {cmd_str} - {str(e)}"
        logger.error(error_msg)
        raise NonRetryableError(error_msg, phase="subprocess", cause=e)


class ProgressBar:
    """Simple progress bar utility that doesn't use any external dependencies"""

    def __init__(self, total: int, description: str = "Processing", logger: Optional[logging.Logger] = None):
        self.total = total
        self.current = 0
        self.description = description
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = time.time()
        self.last_update = 0

    def update(self, increment: int = 1, item_description: str = None):
        """Update progress bar"""
        self.current += increment

        # Update at most every 5% or for first/last item to avoid excessive logging
        progress_percent = self.current / self.total
        if (progress_percent - self.last_update >= 0.05 or
            self.current == 1 or
            self.current == self.total):

            elapsed = time.time() - self.start_time
            if self.current > 0:
                estimated_total = elapsed * self.total / self.current
                remaining = estimated_total - elapsed
                self.logger.info(
                    f"{self.description}: {self.current}/{self.total} "
                    f"({progress_percent:.1%}) - "
                    f"Elapsed: {elapsed:.1f}s, "
                    f"ETA: {remaining:.1f}s"
                )
                if item_description:
                    self.logger.info(f"  Current: {item_description}")

            self.last_update = progress_percent

    def finish(self, success: bool = True):
        """Mark progress as finished"""
        elapsed = time.time() - self.start_time
        status = "completed" if success else "failed"
        self.logger.info(
            f"{self.description} {status}: {self.total}/{self.total} items "
            f"in {elapsed:.1f} seconds"
        )


def log_exceptions(phase_name: str):
    """
    Decorator to automatically log exceptions with phase information
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                logger.error(
                    f"Error in phase '{phase_name}' {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise PipelineError(f"Error in {phase_name}: {str(e)}", phase=phase_name, cause=e)
        return wrapper
    return decorator


class ConfigValidator:
    """Utility for validating configuration values"""

    @staticmethod
    def ensure_positive(value: Any, name: str) -> float:
        """Ensure a value is positive"""
        try:
            numeric_value = float(value)
            if numeric_value <= 0:
                raise ValueError(f"{name} must be positive, got {numeric_value}")
            return numeric_value
        except (ValueError, TypeError) as e:
            raise ValueError(f"{name} must be a positive number, got {value}") from e

    @staticmethod
    def ensure_directory_exists(path: str, name: str, create: bool = False) -> str:
        """Ensure a directory exists"""
        if not isinstance(path, str):
            raise ValueError(f"{name} must be a string, got {type(path)}")

        if not os.path.exists(path):
            if create:
                try:
                    os.makedirs(path, exist_ok=True)
                except OSError as e:
                    raise ValueError(f"Failed to create {name} directory '{path}': {e}") from e
            else:
                raise ValueError(f"{name} directory does not exist: '{path}'")
        elif not os.path.isdir(path):
            raise ValueError(f"{name} path exists but is not a directory: '{path}'")

        return path