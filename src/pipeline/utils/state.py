"""
State management for the pipeline
"""
import os
import json
import logging
from typing import Dict, Any


class PipelineState:
    """Manage pipeline state in a JSON file"""

    def __init__(self, state_file: str):
        """
        Initialize the state manager.

        :param state_file: Path to the state file
        """
        self.state_file = state_file
        self.state = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.load()

    def load(self):
        """
        Load the state from the file.
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.state = json.load(f)
                self.logger.info("State loaded from %s", self.state_file)
            except Exception as e:
                self.logger.error("Failed to load state from %s: %s", self.state_file, e)
        else:
            self.state = {}
            self.logger.info("State file not found, creating new state")

    def save(self):
        """
        Save the state to the file.
        """
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
            self.logger.info("State saved to %s", self.state_file)
        except Exception as e:
            self.logger.error("Failed to save state to %s: %s", self.state_file, e)

    def get(self, key: str, default=None):
        """
        Get a value from the state.
        """
        return self.state.get(key, default)

    def __setitem__(self, key: str, value: Any):
        """
        Set a value in the state.
        """
        self.state[key] = value
        self.save()

    def __getitem__(self, key: str):
        """
        Get a value from the state.
        """
        return self.state[key]

    def __contains__(self, key: str):
        """
        Check if a key is in the state.
        """
        return key in self.state

    def __delitem__(self, key: str):
        """
        Remove a key from the state.
        """
        del self.state[key]
        self.save()

    def keys(self):
        """
        Get the state keys.
        """
        return self.state.keys()

    def values(self):
        """
        Get the state values.
        """
        return self.state.values()

    def items(self):
        """
        Get the state items.
        """
        return self.state.items()

    def clear(self):
        """
        Clear the state.
        """
        self.state = {}
        self.save()
        self.logger.info("State cleared")