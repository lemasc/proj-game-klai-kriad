from collections import defaultdict
from typing import Callable, List, Tuple, Any


class EventManager:
    """
    Event management system for coordinating game components through hooks.

    Allows components to register callbacks for specific events and trigger
    events that execute all registered callbacks in priority order.
    """

    def __init__(self):
        self.hooks: dict[str, List[Tuple[int, Callable]]] = defaultdict(list)

    def register_hook(self, event_name: str, callback: Callable, priority: int = 0) -> None:
        """
        Register a callback function for a specific event.

        Args:
            event_name: Name of the event to listen for
            callback: Function to call when event is triggered
            priority: Execution priority (higher numbers run first)
        """
        self.hooks[event_name].append((priority, callback))
        # Sort by priority (descending order - higher priority first)
        self.hooks[event_name].sort(key=lambda x: x[0], reverse=True)

    def unregister_hook(self, event_name: str, callback: Callable) -> bool:
        """
        Remove a callback from an event.

        Args:
            event_name: Name of the event
            callback: Function to remove

        Returns:
            True if callback was found and removed, False otherwise
        """
        if event_name not in self.hooks:
            return False

        for i, (priority, cb) in enumerate(self.hooks[event_name]):
            if cb == callback:
                self.hooks[event_name].pop(i)
                return True
        return False

    def trigger_event(self, event_name: str, *args, **kwargs) -> List[Any]:
        """
        Execute all callbacks registered for an event.

        Args:
            event_name: Name of the event to trigger
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of return values from all callbacks
        """
        results = []

        for priority, callback in self.hooks[event_name]:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                # Log error but continue with other callbacks
                print(f"Error in event callback for '{event_name}': {e}")
                results.append(None)

        return results

    def has_listeners(self, event_name: str) -> bool:
        """
        Check if any callbacks are registered for an event.

        Args:
            event_name: Name of the event to check

        Returns:
            True if there are registered callbacks, False otherwise
        """
        return len(self.hooks[event_name]) > 0

    def get_event_names(self) -> List[str]:
        """
        Get list of all registered event names.

        Returns:
            List of event names that have registered callbacks
        """
        return list(self.hooks.keys())

    def clear_event(self, event_name: str) -> None:
        """
        Remove all callbacks for a specific event.

        Args:
            event_name: Name of the event to clear
        """
        if event_name in self.hooks:
            del self.hooks[event_name]

    def clear_all(self) -> None:
        """Remove all registered callbacks for all events."""
        self.hooks.clear()

    def trigger_event_chain(self, event_name: str, initial_context: dict, *args, **kwargs) -> dict:
        """
        Execute callbacks in chain, passing accumulated context to each handler.

        Each callback receives the context dictionary and can update it with new values.
        The updated context is passed to the next callback, allowing sequential processing
        where each handler can use and modify shared state (e.g., UI drawing positions).

        Args:
            event_name: Name of the event to trigger
            initial_context: Initial context dictionary to pass to first callback
            *args: Additional positional arguments to pass to callbacks
            **kwargs: Additional keyword arguments to pass to callbacks

        Returns:
            Final context dictionary after all callbacks have executed
        """
        context = initial_context.copy()

        for priority, callback in self.hooks[event_name]:
            try:
                result = callback(context, *args, **kwargs)
                # If callback returns a dict, merge it into context
                if isinstance(result, dict):
                    context.update(result)
            except Exception as e:
                # Log error but continue with other callbacks
                print(f"Error in event callback for '{event_name}': {e}")

        return context