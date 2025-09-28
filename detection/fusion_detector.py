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

        # Detection thresholds
        self.visual_punch_threshold = VISUAL_PUNCH_THRESHOLD
        self.punch_cooldown = PUNCH_COOLDOWN

        # Track last punch time for cooldown
        self.last_punch_time = 0

        # For backward compatibility - will be removed in later phases
        self.motion_analyzer = None
        self.pose_analyzer = None

    def add_strategy(self, strategy: BaseDetectionStrategy) -> None:
        """
        Add a detection strategy to the fusion detector.

        Args:
            strategy: Detection strategy to add
        """
        self.strategies.append(strategy)

    def remove_strategy(self, strategy: BaseDetectionStrategy) -> bool:
        """
        Remove a detection strategy from the fusion detector.

        Args:
            strategy: Detection strategy to remove

        Returns:
            True if strategy was found and removed, False otherwise
        """
        try:
            self.strategies.remove(strategy)
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

    def initialize_strategies(self) -> None:
        """
        Initialize all strategies by triggering setup event.
        This should be called after all strategies are added.
        """
        self.event_manager.trigger_event('setup')

    def cleanup_strategies(self) -> None:
        """Clean up all strategies by triggering cleanup event."""
        self.event_manager.trigger_event('cleanup')

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
        accel_score = 0
        visual_score = 0

        # For new strategy-based approach
        for strategy in self.strategies:
            if strategy.is_strategy_active():
                result = strategy.get_current_results()
                strategy_results[strategy.get_strategy_name()] = result

                # Map strategy results to legacy scoring (temporary compatibility)
                if 'AccelerometerStrategy' in strategy.get_strategy_name():
                    accel_score = result.get('score', 0) if result else 0
                elif 'PoseStrategy' in strategy.get_strategy_name():
                    visual_score = result.get('score', 0) if result else 0

        # Fallback to legacy analyzers if strategies not available
        if not self.strategies and self.motion_analyzer and self.pose_analyzer:
            accel_score, accel_metrics = self._analyze_accelerometer(sensor_data)
            visual_score, visual_metrics = self._analyze_pose(pose_landmarks)
            strategy_results = {
                'legacy_accel': accel_metrics,
                'legacy_pose': visual_metrics
            }

        # Combine scores using weighted average
        combined_score = (accel_score * ACCEL_WEIGHT + visual_score * VISUAL_WEIGHT)

        # Determine if it's a punch using multiple criteria
        is_punch = self._is_punch_detected(accel_score, visual_score, combined_score)

        if is_punch:
            self.last_punch_time = current_time

        return is_punch, combined_score, {
            'strategy_results': strategy_results,
            'combined_score': combined_score,
            'accel_score': accel_score,
            'visual_score': visual_score
        }

    def _analyze_accelerometer(self, sensor_data):
        """Analyze accelerometer data for punch detection."""
        return self.motion_analyzer.analyze_accelerometer_punch(sensor_data)

    def _analyze_pose(self, pose_landmarks):
        """Analyze pose landmarks for punch-like movements."""
        return self.pose_analyzer.analyze_pose_punch(pose_landmarks)

    def _is_punch_detected(self, accel_score, visual_score, combined_score):
        """
        Determine if a punch is detected based on multiple criteria.

        Args:
            accel_score: Accelerometer detection score (0-1)
            visual_score: Visual detection score (0-1)
            combined_score: Combined weighted score (0-1)

        Returns:
            bool: True if punch is detected
        """
        # Punch detected if either:
        # 1. High accelerometer activity OR high visual activity
        # 2. Combined score meets minimum threshold
        high_accel = accel_score > PUNCH_TRIGGER_ACCEL_THRESHOLD
        high_visual = visual_score > self.visual_punch_threshold
        sufficient_combined = combined_score > MINIMUM_COMBINED_SCORE

        return (high_accel or high_visual) and sufficient_combined

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