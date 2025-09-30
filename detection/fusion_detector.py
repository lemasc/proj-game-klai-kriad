"""
Detection fusion module that combines detection strategy results.
This module orchestrates multiple detection strategies through an event-driven architecture.
"""

import time
from typing import List, Optional, Any, Dict, Tuple
from detection.detection_config import *
from game.event_manager import EventManager
from detection.base_strategy import BaseDetectionStrategy


class FusionDetector:
    """
    Orchestrates multiple detection strategies and combines their results.
    Uses event-driven architecture to manage strategy lifecycle and data flow.
    """

    def __init__(self, event_manager: EventManager):
        """
        Initialize the fusion detector with event management.

        Args:
            event_manager: Event manager for coordinating strategies
        """
        self.event_manager = event_manager
        self.strategies: List[BaseDetectionStrategy] = []
        self.strategy_weights: Dict[str, float] = {}  # Maps strategy name to weight

        # Detection thresholds
        self.punch_cooldown = PUNCH_COOLDOWN

        # Track last punch time for cooldown
        self.last_punch_time = 0

        # For backward compatibility - will be removed in later phases
        self.motion_analyzer = None
        self.pose_analyzer = None

    def add_strategy(self, strategy: BaseDetectionStrategy, weight: float = 1.0) -> None:
        """
        Add a detection strategy to the fusion detector.

        Args:
            strategy: Detection strategy to add
            weight: Weight for this strategy in fusion (default 1.0)
        """
        self.strategies.append(strategy)
        self.strategy_weights[strategy.get_strategy_name()] = weight

    def remove_strategy(self, strategy: BaseDetectionStrategy) -> bool:
        """
        Remove a detection strategy from the fusion detector.

        Args:
            strategy: Detection strategy to remove

        Returns:
            True if strategy was found and removed, False otherwise
        """
        try:
            strategy_name = strategy.get_strategy_name()
            self.strategies.remove(strategy)
            if strategy_name in self.strategy_weights:
                del self.strategy_weights[strategy_name]
            return True
        except ValueError:
            return False

    def get_strategy_by_name(self, name: str) -> Optional[BaseDetectionStrategy]:
        """
        Get a strategy by its name.

        Args:
            name: Name of the strategy to find

        Returns:
            Strategy instance or None if not found
        """
        for strategy in self.strategies:
            if strategy.get_strategy_name() == name:
                return strategy
        return None

    def detect_punch(self, pose_landmarks=None, sensor_data=None):
        """
        Main punch detection combining results from all active strategies.

        Args:
            pose_landmarks: MediaPipe pose landmarks (for backward compatibility)
            sensor_data: Accelerometer sensor data dictionary (for backward compatibility)

        Returns:
            tuple: (is_punch, combined_score, metrics) where:
                - is_punch: Boolean indicating if a punch was detected
                - combined_score: Float score (0-1) of punch strength
                - metrics: Dictionary with detailed analysis metrics
        """
        current_time = time.time()

        # Check cooldown period
        if current_time - self.last_punch_time < self.punch_cooldown:
            return False, 0, {}

        # Collect results from all active strategies
        strategy_results = {}
        weighted_scores = []
        total_weight = 0

        for strategy in self.strategies:
            if strategy.is_strategy_active():
                result = strategy.get_current_results()
                strategy_name = strategy.get_strategy_name()
                strategy_results[strategy_name] = result

                # Extract score and weight for this strategy
                score = result.get('score', 0) if result else 0
                weight = self.strategy_weights.get(strategy_name, 1.0)

                weighted_scores.append(score * weight)
                total_weight += weight

        # Fuse scores using weighted average
        combined_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0

        # Determine if it's a punch using combined score and strategy results
        is_punch = self._is_punch_detected(strategy_results, combined_score)

        if is_punch:
            self.last_punch_time = current_time

        return is_punch, combined_score, {
            'strategy_results': strategy_results,
            'combined_score': combined_score
        }

    def _is_punch_detected(self, strategy_results: Dict[str, Any], combined_score: float) -> bool:
        """
        Determine if a punch is detected based on strategy results and combined score.

        Args:
            strategy_results: Dictionary of results from each strategy
            combined_score: Combined weighted score (0-1)

        Returns:
            bool: True if punch is detected
        """
        # Check if any strategy is confident about the detection
        any_confident = any(
            result.get('is_confident', False)
            for result in strategy_results.values()
            if result
        )

        # If at least one strategy is confident, register as punch
        if any_confident:
            return True

        # Otherwise, check if combined score meets minimum threshold
        return combined_score > MINIMUM_COMBINED_SCORE

    def reset_cooldown(self):
        """Reset the punch cooldown timer."""
        self.last_punch_time = 0

    def get_active_strategies(self) -> List[BaseDetectionStrategy]:
        """
        Get list of currently active strategies.

        Returns:
            List of active detection strategies
        """
        return [strategy for strategy in self.strategies if strategy.is_strategy_active()]

    def get_strategy_count(self) -> int:
        """
        Get total number of registered strategies.

        Returns:
            Number of strategies
        """
        return len(self.strategies)

    def get_fusion_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the fusion detector and its strategies.

        Returns:
            Dictionary containing fusion detector status
        """
        return {
            'total_strategies': len(self.strategies),
            'active_strategies': len(self.get_active_strategies()),
            'last_punch_time': self.last_punch_time,
            'cooldown_remaining': max(0, self.punch_cooldown - (time.time() - self.last_punch_time)),
            'strategies': [strategy.get_strategy_info() for strategy in self.strategies]
        }