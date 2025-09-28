from abc import ABC, abstractmethod
from typing import Any, Optional
from game.event_manager import EventManager


class BaseDetectionStrategy(ABC):
    """
    Abstract base class for all detection strategies.

    Detection strategies handle specific types of input (accelerometer, pose, etc.)
    and process them to provide results for fusion. Each strategy manages its own
    lifecycle through event hooks and stores results internally.
    """

    def __init__(self, event_manager: EventManager):
        """
        Initialize the detection strategy.

        Args:
            event_manager: Event manager for registering hooks and listening to events
        """
        self.event_manager = event_manager
        self.current_results: Optional[Any] = None
        self.is_active = False
        self.register_hooks()

    @abstractmethod
    def register_hooks(self) -> None:
        """
        Register event hooks for this strategy.

        Subclasses must implement this to register for relevant events like:
        - 'setup': Initialize strategy resources
        - 'cleanup': Release strategy resources
        - 'frame_received': Process new camera frame
        - 'sensor_data_received': Process new sensor data
        """
        pass

    def get_current_results(self) -> Optional[Any]:
        """
        Get the latest processed results from this strategy.

        Returns:
            Latest results or None if no results available
        """
        return self.current_results

    def update_results(self, results: Any) -> None:
        """
        Update the internal results with new processed data.

        Args:
            results: New results to store
        """
        self.current_results = results

    def activate(self) -> None:
        """Mark this strategy as active and ready to process data."""
        self.is_active = True

    def deactivate(self) -> None:
        """Mark this strategy as inactive."""
        self.is_active = False

    def is_strategy_active(self) -> bool:
        """
        Check if this strategy is currently active.

        Returns:
            True if strategy is active, False otherwise
        """
        return self.is_active

    def setup(self) -> None:
        """
        Initialize strategy resources.

        Override this method to perform strategy-specific setup.
        Called during the 'setup' event.
        """
        self.activate()

    def cleanup(self) -> None:
        """
        Release strategy resources.

        Override this method to perform strategy-specific cleanup.
        Called during the 'cleanup' event.
        """
        self.deactivate()
        self.current_results = None

    def get_strategy_name(self) -> str:
        """
        Get the name of this strategy.

        Returns:
            Strategy class name by default
        """
        return self.__class__.__name__

    def get_strategy_info(self) -> dict:
        """
        Get information about this strategy's current state.

        Returns:
            Dictionary containing strategy status information
        """
        return {
            'name': self.get_strategy_name(),
            'active': self.is_active,
            'has_results': self.current_results is not None,
            'results_type': type(self.current_results).__name__ if self.current_results else None
        }