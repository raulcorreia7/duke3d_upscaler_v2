"""
Abstract base class for pipeline phases
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

class AbstractPhase(ABC):
    """Abstract base class for pipeline phases"""

    def __init__(self, config: Dict[str, Any], state):
        """
        Initialize the phase with configuration and state.

        :param config: Dictionary containing pipeline configuration
        :param state: Pipeline state object
        """
        self.config = config
        self.state = state
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def run(self):
        """
        Execute the phase. This method should be implemented by all concrete phases.
        """
        pass

    def _check_dependencies(self):
        """
        Check for required dependencies for this phase.
        Should be implemented by subclasses if needed.
        """
        pass

    def _validate_inputs(self):
        """
        Validate the inputs for this phase.
        Should be implemented by subclasses if needed.
        """
        pass

    def _validate_outputs(self):
        """
        Validate the outputs of this phase.
        Should be implemented by subclasses if needed.
        """
        pass

    def _update_state(self, key: str, value: Any):
        """
        Update the state with a key-value pair.
        """
        self.state[key] = value
        self.state.save()